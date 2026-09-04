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


def test_dogfood_skill_is_repo_scoped_and_shared_by_codex_and_claude() -> None:
    claude = ROOT / ".claude/skills/dogfood"
    codex = ROOT / ".agents/skills/dogfood"

    assert claude.is_dir() and not claude.is_symlink()
    assert codex.is_symlink()
    assert codex.readlink() == Path("../../.claude/skills/dogfood")
    assert codex.resolve(strict=True) == claude.resolve(strict=True)
    assert frontmatter(codex / "SKILL.md")["name"] == "dogfood"


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


def test_public_discovery_metadata_agrees_across_hosts() -> None:
    """Both host manifests and the Claude catalog describe one product (parity, spec 11.1).

    The sentence itself is editorial and not pinned (spec 11.2): what must hold is that
    Codex, Claude, and the catalog do not drift apart, and that the Codex interface
    short description equals the one the skill's own openai.yaml carries.
    """
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    marketplace = json_object(".claude-plugin/marketplace.json")
    openai = yaml.safe_load(read("plugins/skiphow/skills/skiphow/agents/openai.yaml"))

    assert codex["description"].strip()
    assert codex["description"] == claude["description"] == marketplace["description"]
    assert codex["keywords"] == claude["keywords"]
    assert codex["interface"]["shortDescription"].strip()
    assert codex["interface"]["shortDescription"] == openai["interface"]["short_description"]


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


def test_owner_skill_description_and_case_matrix_carry_both_polarities() -> None:
    """The discovery case matrix must keep positive and negative cases (spec 11.3 class 3).

    The wording of the description is editorial and not pinned; it only has to fit the
    host limit and say something.
    """
    description = frontmatter(SKILL)["description"]
    assert isinstance(description, str)
    assert 0 < len(description.strip()) <= 1024

    cases = json.loads(read("tests/skill-discovery-cases.json"))
    assert isinstance(cases, list) and cases
    assert len({case["id"] for case in cases}) == len(cases)
    kinds = {case["kind"] for case in cases}
    assert any(kind.startswith("negative_") for kind in kinds)
    assert any(not kind.startswith("negative_") for kind in kinds)
    assert all(case["should_select"] for case in cases if not case["kind"].startswith("negative_"))
    assert all(not case["should_select"] for case in cases if case["kind"].startswith("negative_"))
    assert all(case["prompt"].strip() for case in cases)


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


def test_session_hook_is_inert_when_it_ships() -> None:
    """Safety shape of the hook (spec 11.1), not its matcher topology (spec 11.2)."""
    hooks_dir = PLUGIN / "hooks"
    if not hooks_dir.is_dir() or not any(hooks_dir.iterdir()):
        return
    assert [path.name for path in hooks_dir.iterdir()] == ["hooks.json"]
    payload = json_object("plugins/skiphow/hooks/hooks.json")
    assert set(payload["hooks"]) == {"SessionStart"}
    groups = payload["hooks"]["SessionStart"]
    assert groups
    forbidden = re.compile(
        r"\b(?:curl|wget|nc|ssh|scp|nslookup|dig|python|node|sh|bash|zsh|eval|"
        r"source|cat|cp|mv|rm|mkdir|touch|tee|chmod|git|pip|npm)\b"
    )
    for group in groups:
        sources = group["matcher"].split("|")
        assert set(sources) <= check.SESSION_START_SOURCES
        for handler in group["hooks"]:
            assert set(handler) == {"type", "command", "timeout"}
            assert handler["type"] == "command"
            command = handler["command"]
            assert isinstance(command, str)
            match = check.SAFE_ECHO_COMMAND.fullmatch(command)
            assert match, command
            assert not set(match.group(1)) & set("$`\\|&;<>()*?[]{}!#~'\"")
            assert forbidden.search(command) is None, command
            if {"compact", "resume"} & set(sources):
                assert check.HANDOFF_STATE_REFERENCE.search(command) is None
            timeout = handler["timeout"]
            assert isinstance(timeout, int) and not isinstance(timeout, bool)
            assert 0 < timeout <= check.HOOK_TIMEOUT_CEILING
    assert check.validate_continuity_hook() == []


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
