"""Repository contracts for the plugin-only package."""

from __future__ import annotations

import json
from pathlib import Path
import re

from markdown_it import MarkdownIt
import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/skiphow"
SKILL = PLUGIN / "skills/skiphow/SKILL.md"
REFERENCES = frozenset(
    {
        "decision.md",
        "delivery.md",
        "diagnosis.md",
        "github.md",
        "intake.md",
        "long-work.md",
        "model-routing.md",
    }
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def json_object(relative: str) -> dict:
    value = json.loads(read(relative))
    assert isinstance(value, dict)
    return value


def code_tokens(text: str) -> set[str]:
    return set(re.findall(r"`([A-Z][A-Z_]+)`", text))


def skill_links() -> set[Path]:
    links: set[Path] = set()
    for token in MarkdownIt("commonmark").parse(SKILL.read_text(encoding="utf-8")):
        for child in token.children or ():
            if child.type == "link_open" and child.attrGet("href"):
                links.add((SKILL.parent / child.attrGet("href")).resolve())
    return links


def test_both_hosts_package_the_same_canonical_skill() -> None:
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    assert codex["name"] == claude["name"] == "skiphow"
    assert codex["skills"] == claude["skills"] == "./skills/"
    assert sorted(PLUGIN.rglob("SKILL.md")) == [SKILL]
    assert {
        path.name
        for path in PLUGIN.iterdir()
        if path.is_file() or any(child.is_file() for child in path.rglob("*"))
    } == {
        ".claude-plugin",
        ".codex-plugin",
        "LICENSE",
        "skills",
    }
    assert (PLUGIN / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_marketplaces_publish_only_the_plugin_directory() -> None:
    codex = json_object(".agents/plugins/marketplace.json")
    claude = json_object(".claude-plugin/marketplace.json")
    assert len(codex["plugins"]) == 1
    assert codex["plugins"][0]["source"] == {
        "source": "local",
        "path": "./plugins/skiphow",
    }
    assert len(claude["plugins"]) == 1
    assert claude["plugins"][0]["source"] == "./plugins/skiphow"


def test_release_metadata_uses_one_version() -> None:
    release = read("VERSION").strip()
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    marketplace = json_object(".claude-plugin/marketplace.json")
    assert codex["version"] == claude["version"] == release
    assert marketplace["metadata"]["version"] == release
    assert marketplace["plugins"][0]["version"] == release


def test_retired_runtime_paths_are_absent() -> None:
    retired = (
        "src/skiphow",
        "schemas",
        "pyproject.toml",
        "plugins/skiphow/scripts",
        "adapters/claude",
        ".claude-plugin/plugin.json",
    )

    def contains_file(relative: str) -> bool:
        path = ROOT / relative
        return path.is_file() or (
            path.is_dir() and any(item.is_file() for item in path.rglob("*"))
        )

    assert not [relative for relative in retired if contains_file(relative)]


def test_skill_is_implicitly_available_and_has_four_internal_routes() -> None:
    metadata = yaml.safe_load(read("plugins/skiphow/skills/skiphow/agents/openai.yaml"))
    assert metadata["policy"]["allow_implicit_invocation"] is True
    assert {"RESPOND", "RECORD", "DELIVER", "CONTROL"}.issubset(
        code_tokens(SKILL.read_text(encoding="utf-8"))
    )


def test_progressive_references_are_complete_and_reachable() -> None:
    reference_root = SKILL.parent / "references"
    actual = {path.name for path in reference_root.glob("*.md")}
    assert actual == REFERENCES
    linked = skill_links()
    for name in REFERENCES:
        assert (reference_root / name).resolve() in linked


def test_named_behavior_contracts_are_kept_in_lazy_references() -> None:
    intake = code_tokens(read("plugins/skiphow/skills/skiphow/references/intake.md"))
    routing = code_tokens(read("plugins/skiphow/skills/skiphow/references/model-routing.md"))
    delivery = code_tokens(read("plugins/skiphow/skills/skiphow/references/delivery.md"))
    assert {"NEW", "UPDATE", "DUPLICATE", "RELATED", "NEEDS_RESEARCH", "DISMISSED"} <= intake
    assert {"FAST", "STANDARD", "DEEP", "UNVERIFIED"} <= routing
    assert {"DELIVER", "NEEDS_RESEARCH", "DISMISSED"} <= delivery


def test_lazy_policy_keeps_release_authority_and_recovery_contracts() -> None:
    skill = read("plugins/skiphow/skills/skiphow/SKILL.md")
    github = read("plugins/skiphow/skills/skiphow/references/github.md")
    long_work = read("plugins/skiphow/skills/skiphow/references/long-work.md")
    routing = read("plugins/skiphow/skills/skiphow/references/model-routing.md")
    assert "Delivery authority also permits" in skill
    assert "private security channel" in skill
    assert "competing active operation" in github
    assert "disable owned pending auto-merge" in long_work
    assert "current authority and later restrictions" in long_work
    assert "effective model" in routing
    assert "record `BLOCKED`" in routing


def test_plugin_has_no_hooks_or_personal_paths() -> None:
    assert not [path for path in PLUGIN.rglob("*") if "hooks" in path.parts]
    manifests = (
        json_object("plugins/skiphow/.codex-plugin/plugin.json"),
        json_object("plugins/skiphow/.claude-plugin/plugin.json"),
    )
    assert all("hooks" not in manifest for manifest in manifests)
    personal = re.compile(
        r"/(?:Users|home)/[^/\s]+/|[A-Za-z]:[\\/]Users[\\/][^\\/\s]+[\\/]"
    )
    for path in PLUGIN.rglob("*"):
        if path.is_file():
            assert personal.search(path.read_text(encoding="utf-8")) is None
