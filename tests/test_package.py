"""Structural contracts for the published plugin package."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/skiphow"
SKILL = PLUGIN / "skills/skiphow/SKILL.md"
CHECK = importlib.util.spec_from_file_location(
    "skiphow_check_shape", ROOT / "scripts/check.py"
)
assert CHECK and CHECK.loader
check = importlib.util.module_from_spec(CHECK)
CHECK.loader.exec_module(check)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def json_object(relative: str) -> dict:
    value = json.loads(read(relative))
    assert isinstance(value, dict)
    return value


def frontmatter(path: Path) -> dict:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    assert match, path
    value = yaml.safe_load(match.group(1))
    assert isinstance(value, dict)
    return value


def test_both_hosts_package_one_owner_skill_with_internal_methods() -> None:
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    assert codex["name"] == claude["name"] == "skiphow"
    assert codex["skills"] == claude["skills"] == "./skills/"
    assert "hooks" not in codex and "agents" not in codex
    assert "hooks" not in claude and "agents" not in claude
    skill_dirs = sorted(path for path in (PLUGIN / "skills").iterdir() if path.is_dir())
    assert skill_dirs == [PLUGIN / "skills/skiphow"]
    assert set(PLUGIN.rglob("SKILL.md")) == {path / "SKILL.md" for path in skill_dirs}
    assert not any(
        path.is_file() or path.is_symlink()
        for path in (PLUGIN / "agents").glob("**/*")
    )
    shipped_top_level = {
        path.name
        for path in PLUGIN.iterdir()
        if path.is_file()
        or path.is_symlink()
        or any(child.is_file() or child.is_symlink() for child in path.rglob("*"))
    }
    assert shipped_top_level <= check.ALLOWED_PLUGIN_TOP_LEVEL
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
    assert "version" not in marketplace.get("metadata", {})
    assert "version" not in marketplace["plugins"][0]
    assert release not in read("README.md")
    assert f"| {release.rsplit('.', 1)[0]}.x | Yes |" in read("SECURITY.md")


def every_uses(node: object) -> list[str]:
    """Collect every action reference, including reusable workflows."""
    if isinstance(node, dict):
        found = [node["uses"]] if isinstance(node.get("uses"), str) else []
        return found + [item for value in node.values() for item in every_uses(value)]
    if isinstance(node, list):
        return [item for value in node for item in every_uses(value)]
    return []


def test_workflows_are_sha_pinned_with_least_privilege() -> None:
    for name, granted in (("ci.yml", "read"), ("release.yml", "write")):
        workflow = yaml.safe_load(read(f".github/workflows/{name}"))
        uses = every_uses(workflow)
        assert uses, name
        assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in uses), (
            name,
            uses,
        )
        assert workflow["permissions"] == {"contents": granted}, name
        assert all("permissions" not in job for job in workflow["jobs"].values()), name


def test_pages_workflow_requires_a_manual_publication_action() -> None:
    workflow = yaml.safe_load(read(".github/workflows/pages.yml"))
    triggers = workflow.get("on", workflow.get(True))
    assert triggers == {"workflow_dispatch": None}
    assert workflow["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }
    uses = every_uses(workflow)
    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in uses)
    upload = next(
        step
        for step in workflow["jobs"]["deploy"]["steps"]
        if step.get("uses", "").startswith("actions/upload-pages-artifact@")
    )
    assert upload["with"] == {"path": "site"}


def test_release_refuses_a_tag_outside_main() -> None:
    workflow = yaml.safe_load(read(".github/workflows/release.yml"))
    steps = workflow["jobs"]["release"]["steps"]
    guard = next(
        step for step in steps if step.get("name") == "Require the tag commit to be on main"
    )
    commands = [line.strip() for line in guard["run"].splitlines() if line.strip()]
    assert commands == [
        "git fetch --no-tags origin main",
        'git merge-base --is-ancestor "${GITHUB_SHA}" origin/main',
    ]


def test_every_skill_has_valid_discovery_metadata() -> None:
    skill_dirs = sorted(path for path in (PLUGIN / "skills").iterdir() if path.is_dir())
    names: set[str] = set()
    for directory in skill_dirs:
        metadata = frontmatter(directory / "SKILL.md")
        assert metadata["name"] == directory.name
        assert 0 < len(metadata["description"].strip()) <= 1024
        assert metadata["name"] not in names
        names.add(metadata["name"])
        assert check.validate_skill_directory(directory) == []
    assert "skiphow" in names


def test_owner_skill_discovery_contract_and_case_matrix_are_precise() -> None:
    description = frontmatter(SKILL)["description"]
    assert isinstance(description, str)
    assert "product owner's current-project request" in description
    assert "plain-language outcome" in description
    assert "nontechnical product owner" not in description
    for excluded in (
        "unrelated conversation",
        "mandatory development workflow",
        "runtime orchestrator",
    ):
        assert excluded in description
    assert "build those capabilities in the current project remains in scope" in description

    cases = json.loads(read("tests/skill-discovery-cases.json"))
    assert isinstance(cases, list)
    assert {case["kind"] for case in cases} == {
        "direct",
        "indirect",
        "incomplete",
        "negative_unrelated",
        "negative_mandatory_workflow",
        "negative_runtime_orchestration",
        "edge_current_project_capability",
    }
    assert all(case["should_select"] for case in cases if not case["kind"].startswith("negative_"))
    assert all(not case["should_select"] for case in cases if case["kind"].startswith("negative_"))


def test_static_site_matches_its_canonical_contract() -> None:
    assert check.validate_site() == []


def test_progressive_skill_resources_are_dynamic_and_links_resolve() -> None:
    assert check.validate_plugin_links() == []
    for skill_file in sorted((PLUGIN / "skills").glob("*/SKILL.md")):
        assert check.validate_skill_markdown_reachability(skill_file.parent) == []


def test_package_validator_accepts_one_owner_skill_and_dynamic_resources() -> None:
    assert check.validate_plugin_static() == []
    discovered = {path.parent.name for path in (PLUGIN / "skills").glob("*/SKILL.md")}
    assert discovered == {"skiphow"}
    references = {path.name for path in (SKILL.parent / "references").glob("*.md")}
    assert len(references) > 1
    assert check.validate_skill_markdown_reachability(SKILL.parent) == []


def test_adapted_skills_have_pinned_source_provenance() -> None:
    sources = PLUGIN / "SOURCES.json"
    notices = PLUGIN / "THIRD_PARTY_NOTICES.md"
    assert sources.is_file() and notices.is_file()
    skills = {path.parent.name for path in (PLUGIN / "skills").glob("*/SKILL.md")}
    assert check.validate_third_party_sources(skills) == []


def test_continuity_hook_is_the_only_hook() -> None:
    hooks_dir = PLUGIN / "hooks"
    assert [path.name for path in hooks_dir.iterdir()] == ["hooks.json"]
    payload = json_object("plugins/skiphow/hooks/hooks.json")
    assert set(payload["hooks"]) == {"SessionStart"}
    groups = payload["hooks"]["SessionStart"]
    assert len(groups) == 2
    assert {
        frozenset(group["matcher"].split("|")) for group in groups
    } == check.CONTINUITY_GROUPS
    sources = [source for group in groups for source in group["matcher"].split("|")]
    assert sorted(sources) == ["clear", "compact", "resume", "startup"]
    for group in groups:
        (handler,) = group["hooks"]
        assert set(handler) == {"type", "command", "timeout"}
        assert handler["type"] == "command"
        assert isinstance(handler["command"], str)
        assert check.SAFE_ECHO_COMMAND.fullmatch(handler["command"])
        assert isinstance(handler["timeout"], int)
        assert not isinstance(handler["timeout"], bool)
        assert handler["timeout"] > 0


def test_package_has_no_versioned_model_ids_or_personal_paths() -> None:
    scanned = 0
    for path in PLUGIN.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        assert check.PERSONAL_PATH.search(text) is None, path
        assert check.CONCRETE_MODEL_ID.search(text) is None, path
    assert scanned > 0
    for identifier in (
        "claude-fable-5",
        "fable-5",
        "gpt-oss-120b",
        "claude-opus-5",
        "o3",
    ):
        assert check.CONCRETE_MODEL_ID.search(identifier), identifier
    for personal in ("/Users/person", "C:\\users\\person\\x", "~/.claude"):
        assert check.PERSONAL_PATH.search(personal), personal
