"""Structural contracts for the plugin-only package.

These tests check what the package contains and how it is wired, not the
wording of the policy. Prose is free to change; structure is not.
"""

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
        "engineering.md",
        "github.md",
        "intake.md",
        "long-work.md",
        "model-routing.md",
    }
)
VERSIONED_MODEL = re.compile(
    r"\b(?:gpt-\d|claude-\d|claude-(?:opus|sonnet|haiku)-|(?:opus|sonnet|haiku)-\d|gemini-\d|o[1-9]-)",
    re.IGNORECASE,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def json_object(relative: str) -> dict:
    value = json.loads(read(relative))
    assert isinstance(value, dict)
    return value


def code_tokens(text: str) -> set[str]:
    return set(re.findall(r"`([A-Z][A-Z_]+)`", text))


def frontmatter(path: Path) -> dict:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    assert match, path
    value = yaml.safe_load(match.group(1))
    assert isinstance(value, dict)
    return value


def skill_links() -> set[Path]:
    links: set[Path] = set()
    pending = [SKILL]
    seen: set[Path] = set()
    while pending:
        source = pending.pop()
        if source in seen:
            continue
        seen.add(source)
        for token in MarkdownIt("commonmark").parse(source.read_text(encoding="utf-8")):
            for child in token.children or ():
                if child.type != "link_open" or not child.attrGet("href"):
                    continue
                candidate = (source.parent / child.attrGet("href")).resolve()
                if candidate.suffix == ".md" and candidate.is_relative_to(SKILL.parent):
                    links.add(candidate)
                    pending.append(candidate)
    return links


def headings(relative: str) -> list[str]:
    return re.findall(r"^#{1,6} (.+)$", read(relative), re.MULTILINE)


def fenced_blocks(relative: str) -> list[str]:
    return re.findall(r"```(?:text)?\n(.*?)```", read(relative), re.DOTALL)


# Package shape


def test_both_hosts_package_the_same_canonical_skill() -> None:
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    assert codex["name"] == claude["name"] == "skiphow"
    assert codex["skills"] == claude["skills"] == "./skills/"
    assert "hooks" not in codex and "agents" not in codex
    assert "hooks" not in claude and "agents" not in claude
    assert sorted(PLUGIN.rglob("SKILL.md")) == [SKILL]
    assert {
        path.name
        for path in PLUGIN.iterdir()
        if path.is_file() or any(child.is_file() for child in path.rglob("*"))
    } == {".claude-plugin", ".codex-plugin", "agents", "hooks", "LICENSE", "skills"}
    assert (PLUGIN / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_marketplaces_publish_only_the_plugin_directory() -> None:
    codex = json_object(".agents/plugins/marketplace.json")
    claude = json_object(".claude-plugin/marketplace.json")
    assert len(codex["plugins"]) == 1
    assert codex["plugins"][0]["source"] == {"source": "local", "path": "./plugins/skiphow"}
    assert len(claude["plugins"]) == 1
    assert claude["plugins"][0]["source"] == "./plugins/skiphow"


def test_release_metadata_uses_one_version() -> None:
    release = read("VERSION").strip()
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    marketplace = json_object(".claude-plugin/marketplace.json")
    assert codex["version"] == claude["version"] == release
    assert "version" not in marketplace.get("metadata", {})
    assert "version" not in marketplace["plugins"][0]
    assert release not in read("README.md")
    assert f"| {release.rsplit('.', 1)[0]}.x | Yes |" in read("SECURITY.md")


def test_workflows_are_sha_pinned_with_least_privilege() -> None:
    for name in ("ci.yml", "release.yml"):
        workflow = read(f".github/workflows/{name}")
        uses = re.findall(r"^\s*- uses: ([^\s]+)", workflow, re.MULTILINE)
        assert uses, name
        assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in uses), name
    assert re.search(r"^permissions:\n  contents: read$", read(".github/workflows/ci.yml"), re.MULTILINE)
    assert re.search(r"^permissions:\n  contents: write$", read(".github/workflows/release.yml"), re.MULTILINE)



# Skill wiring


def test_skill_is_implicitly_available_and_has_four_internal_routes() -> None:
    metadata = yaml.safe_load(read("plugins/skiphow/skills/skiphow/agents/openai.yaml"))
    assert metadata["policy"]["allow_implicit_invocation"] is True
    assert {"RESPOND", "RECORD", "DELIVER", "CONTROL"} <= code_tokens(SKILL.read_text(encoding="utf-8"))


def test_progressive_references_are_complete_and_reachable() -> None:
    reference_root = SKILL.parent / "references"
    actual = {path.relative_to(reference_root).as_posix() for path in reference_root.rglob("*.md")}
    assert actual == REFERENCES
    assert skill_links() == {(reference_root / name).resolve() for name in REFERENCES}


def test_report_and_record_formats_are_fenced() -> None:
    report = fenced_blocks("plugins/skiphow/skills/skiphow/SKILL.md")
    assert any(
        block.split() == ["Result", "Evidence", "Rulings", "and", "findings", "Saved", "follow-ups", "Limits"]
        for block in report
    )
    handoff = fenced_blocks("plugins/skiphow/skills/skiphow/references/long-work.md")
    labels = {line.split(":")[0].strip("- ") for block in handoff for line in block.splitlines() if line.startswith("- ")}
    assert labels == {"Recorded", "Outcome", "Selected scope", "Authority", "Done", "In progress", "Blockers", "Next safe action"}
    inbox = fenced_blocks("plugins/skiphow/skills/skiphow/references/intake.md")
    assert any("Disposition" in block and "Recorded" in block for block in inbox)


def test_named_contracts_stay_in_lazy_references() -> None:
    intake = code_tokens(read("plugins/skiphow/skills/skiphow/references/intake.md"))
    routing = read("plugins/skiphow/skills/skiphow/references/model-routing.md")
    review = code_tokens(read("plugins/skiphow/skills/skiphow/references/engineering.md"))
    assert {"NEW", "UPDATE", "DUPLICATE", "RELATED", "NEEDS_RESEARCH", "DISMISSED"} <= intake
    # `BLOCKED` left this reference in 1.10.0 with the escalation ladder it belonged to.
    # The ladder binds wherever a delegate exists, so it lives in the root now (ADR 0016).
    assert {"FAST", "STANDARD", "DEEP", "UNVERIFIED"} <= code_tokens(routing)
    assert "BLOCKED" not in code_tokens(routing)
    assert {"scout", "builder", "reviewer"} <= set(re.findall(r"`(\w+)`", routing))
    # Review findings carry the skill's four tags. A second findings vocabulary in a
    # reference contradicts the root contract, which is how `PERSISTED` reached a report.
    tags = code_tokens(read("plugins/skiphow/skills/skiphow/SKILL.md"))
    assert {"TRACKED", "SAVED", "UNSAVED", "DISMISSED", "BLOCKED"} <= tags
    assert not review & {"RESOLVED", "PERSISTED"}
    for relative in ("long-work.md", "github.md", "delivery.md"):
        assert {"BLOCKED", "UNVERIFIED"} & code_tokens(read(f"plugins/skiphow/skills/skiphow/references/{relative}"))


# Host adapters


def test_agent_adapters_route_roles_to_family_aliases() -> None:
    agents = {path.stem: frontmatter(path) for path in (PLUGIN / "agents").glob("*.md")}
    assert set(agents) == {"scout", "builder", "reviewer"}
    assert agents["scout"]["model"] == "haiku"
    assert agents["builder"]["model"] == "sonnet"
    assert agents["reviewer"]["model"] == "inherit"
    assert agents["scout"]["effort"] == "low"
    assert "effort" not in agents["reviewer"]
    assert agents["builder"]["isolation"] == "worktree"
    for role, meta in agents.items():
        assert meta["name"] == role
        assert meta["description"].strip()
        assert not ({"hooks", "mcpServers", "permissionMode"} & set(meta))
        tools = str(meta.get("tools", ""))
        if role == "builder":
            assert "Edit" in tools and "Write" in tools
        else:
            assert "Edit" not in tools and "Write" not in tools


def test_continuity_hook_is_the_only_hook() -> None:
    hooks_dir = PLUGIN / "hooks"
    assert [path.name for path in hooks_dir.iterdir()] == ["hooks.json"]
    payload = json_object("plugins/skiphow/hooks/hooks.json")
    assert set(payload["hooks"]) == {"SessionStart"}
    groups = payload["hooks"]["SessionStart"]
    sources = [source for group in groups for source in group["matcher"].split("|")]
    assert sorted(sources) == ["clear", "compact", "resume", "startup"]
    for group in groups:
        (handler,) = group["hooks"]
        assert handler["type"] == "command"
        assert handler["command"].startswith("sh -c ")
        assert ".skiphow/handoff.md" in handler["command"]
        assert handler.get("timeout", 600) <= 30


def test_package_has_no_versioned_model_ids_or_personal_paths() -> None:
    personal = re.compile(r"/(?:Users|home)/[^/\s]+/|[A-Za-z]:[\\/]Users[\\/][^\\/\s]+[\\/]")
    for path in PLUGIN.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert personal.search(text) is None, path
            assert VERSIONED_MODEL.search(text) is None, path
