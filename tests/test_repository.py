"""Structural contracts for the plugin-only package.

These tests check package shape and the few semantic invariants whose absence
caused a field failure. Other prose remains free to change.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/skiphow"
SKILL = PLUGIN / "skills/skiphow/SKILL.md"
CHECK = importlib.util.spec_from_file_location("skiphow_check_shape", ROOT / "scripts/check.py")
_MODULE = importlib.util.module_from_spec(CHECK)
CHECK.loader.exec_module(_MODULE)
VERSIONED_MODEL = _MODULE.CONCRETE_MODEL_ID
PERSONAL_PATH = _MODULE.PERSONAL_PATH
DOGFOOD_SPEC = importlib.util.spec_from_file_location(
    "skiphow_dogfood_sessions", ROOT / ".claude/skills/dogfood/sessions.py"
)
DOGFOOD = importlib.util.module_from_spec(DOGFOOD_SPEC)
DOGFOOD_SPEC.loader.exec_module(DOGFOOD)


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


# Package shape


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
    assert not any(path.is_file() or path.is_symlink() for path in (PLUGIN / "agents").glob("**/*"))
    shipped_top_level = {
        path.name
        for path in PLUGIN.iterdir()
        if path.is_file()
        or path.is_symlink()
        or any(child.is_file() or child.is_symlink() for child in path.rglob("*"))
    }
    assert shipped_top_level <= _MODULE.ALLOWED_PLUGIN_TOP_LEVEL
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


def every_uses(node: object) -> list[str]:
    """Collect every `uses` value, including job-level reusable workflows."""
    if isinstance(node, dict):
        found = [node["uses"]] if isinstance(node.get("uses"), str) else []
        return found + [item for value in node.values() for item in every_uses(value)]
    if isinstance(node, list):
        return [item for value in node for item in every_uses(value)]
    return []


def test_workflows_are_sha_pinned_with_least_privilege() -> None:
    """A job-level `uses` is a dependency too, and permissions is a whole mapping.

    The step-level regex this replaced ignored reusable workflows, and the
    permissions regex matched a prefix, so an added `id-token: write` stayed green.
    """
    for name, granted in (("ci.yml", "read"), ("release.yml", "write")):
        workflow = yaml.safe_load(read(f".github/workflows/{name}"))
        uses = every_uses(workflow)
        assert uses, name
        assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in uses), (name, uses)
        assert workflow["permissions"] == {"contents": granted}, name
        assert all("permissions" not in job for job in workflow["jobs"].values()), name


def test_release_refuses_a_tag_outside_main() -> None:
    workflow = yaml.safe_load(read(".github/workflows/release.yml"))
    steps = workflow["jobs"]["release"]["steps"]
    guard = next(step for step in steps if step.get("name") == "Require the tag commit to be on main")
    commands = [line.strip() for line in guard["run"].splitlines() if line.strip()]
    assert commands == [
        "git fetch --no-tags origin main",
        'git merge-base --is-ancestor "${GITHUB_SHA}" origin/main',
    ]


# Skill wiring


def test_every_skill_has_valid_discovery_metadata() -> None:
    skill_dirs = sorted(path for path in (PLUGIN / "skills").iterdir() if path.is_dir())
    names: set[str] = set()
    for directory in skill_dirs:
        skill_file = directory / "SKILL.md"
        metadata = frontmatter(skill_file)
        assert metadata["name"] == directory.name
        assert 0 < len(metadata["description"].strip()) <= 1024
        assert metadata["name"] not in names
        names.add(metadata["name"])
        assert _MODULE.validate_skill_directory(directory) == []
    assert "skiphow" in names


def test_progressive_skill_resources_are_dynamic_and_links_resolve() -> None:
    assert _MODULE.validate_plugin_links() == []
    for skill_file in sorted((PLUGIN / "skills").glob("*/SKILL.md")):
        assert _MODULE.validate_skill_markdown_reachability(skill_file.parent) == []


def test_package_validator_accepts_one_owner_skill_and_dynamic_resources() -> None:
    assert _MODULE.validate_plugin_static() == []
    discovered = {path.parent.name for path in (PLUGIN / "skills").glob("*/SKILL.md")}
    assert discovered == {"skiphow"}
    references = {path.name for path in (SKILL.parent / "references").glob("*.md")}
    assert len(references) > 1
    assert _MODULE.validate_skill_markdown_reachability(SKILL.parent) == []


def test_adapted_skills_have_pinned_source_provenance() -> None:
    sources = PLUGIN / "SOURCES.json"
    notices = PLUGIN / "THIRD_PARTY_NOTICES.md"
    assert sources.is_file() and notices.is_file()
    skills = {path.parent.name for path in (PLUGIN / "skills").glob("*/SKILL.md")}
    assert _MODULE.validate_third_party_sources(skills) == []


def write_transcript(tmp_path: Path, records: list[dict], name: str = "session") -> Path:
    path = tmp_path / f"{name}.jsonl"
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    return path


def claude_call(
    tool_id: str,
    tool: str,
    inputs: dict,
    output: object = "completed",
    *,
    is_error: bool = False,
) -> list[dict]:
    assistant_uuid = f"{tool_id}-assistant-record"
    return [
        {
            "type": "assistant",
            "uuid": assistant_uuid,
            "message": {
                "content": [
                    {"type": "tool_use", "id": tool_id, "name": tool, "input": inputs}
                ]
            },
        },
        {
            "type": "user",
            "uuid": f"{tool_id}-result-record",
            "parentUuid": assistant_uuid,
            "sourceToolAssistantUUID": assistant_uuid,
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "is_error": is_error,
                        "content": output,
                    }
                ]
            },
        },
    ]


def host_cache_root(home: Path) -> Path:
    return home / "plugins/cache/skiphow/skiphow"


def claude_read(
    tool_id: str,
    path: str,
    content: str,
    *,
    framed_output: str | None = None,
    start_line: int = 1,
    num_lines: int | None = None,
    total_lines: int | None = None,
) -> list[dict]:
    lines = content.splitlines()
    count = len(lines) if num_lines is None else num_lines
    output = (
        "\n".join(f"{number}\t{line}" for number, line in enumerate(lines, 1))
        if framed_output is None
        else framed_output
    )
    records = claude_call(tool_id, "Read", {"file_path": path}, output)
    records[1]["toolUseResult"] = {
        "file": {
            "filePath": path,
            "content": content,
            "startLine": start_line,
            "numLines": count,
            "totalLines": count if total_lines is None else total_lines,
        }
    }
    return records


def codex_command(
    command: str,
    output: str = "",
    *,
    succeeded: bool = True,
    item_id: str = "command-1",
) -> list[dict]:
    return [
        {
            "type": "item.started",
            "item": {
                "id": item_id,
                "type": "command_execution",
                "command": command,
                "aggregated_output": "",
                "exit_code": None,
                "status": "in_progress",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": item_id,
                "type": "command_execution",
                "command": command,
                "aggregated_output": output,
                "status": "completed" if succeeded else "failed",
                "exit_code": 0 if succeeded else 1,
            },
        },
    ]


def codex_usage(**overrides: object) -> dict[str, object]:
    usage: dict[str, object] = {
        "input_tokens": 1,
        "cached_input_tokens": 0,
        "output_tokens": 1,
        "reasoning_output_tokens": 0,
    }
    usage.update(overrides)
    return usage


def codex_mcp_result(content: list[object] | None = None) -> dict[str, object]:
    return {
        "content": [] if content is None else content,
        "structured_content": None,
    }


def reference_info(
    monkeypatch: pytest.MonkeyPatch,
    records: list[dict],
    *,
    body: str = "",
    source: str = "contract_bytes_unavailable",
    version: str = "2.0.0",
    name: str = "testing",
) -> dict:
    monkeypatch.setattr(DOGFOOD, "version_reference_names", lambda _version: {name})
    monkeypatch.setattr(
        DOGFOOD,
        "package_reference",
        lambda _version, _name, _roots=(): (body, source),
    )
    return DOGFOOD.detect_references(Path("unused.jsonl"), records, version)[name]


def test_dogfood_reference_catalog_and_identity_are_observations() -> None:
    current = {path.stem for path in (SKILL.parent / "references").glob("*.md")}
    assert current <= set(DOGFOOD.REFERENCES)
    assert tuple(sorted(set(DOGFOOD.REFERENCES))) == DOGFOOD.REFERENCES
    records = [
        {"timestamp": "2026-08-27T10:00:00Z", "cwd": "/repo", "gitBranch": "main"},
        {"timestamp": "2026-08-27T10:00:01Z"},
        {"timestamp": "2026-08-27T10:00:02Z", "gitBranch": "task"},
        {"timestamp": "2026-08-27T10:00:03Z", "cwd": "/tmp/repo-task"},
    ]
    assert DOGFOOD.identity_transitions(records) == [
        {"at": "2026-08-27T10:00:00Z", "cwd": "/repo", "branch": "main"},
        {"at": "2026-08-27T10:00:02Z", "cwd": "/repo", "branch": "task"},
        {"at": "2026-08-27T10:00:03Z", "cwd": "/tmp/repo-task", "branch": "task"},
    ]


def test_dogfood_skill_signals_name_only_observed_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = host_cache_root(DOGFOOD.claude_home())
    base = str(cache / "2.0.0/skills")
    body = "# SkipHow\n\nExact owner body."
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    records: list[dict] = []
    activation = claude_call(
        "skill-owner",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    activation[0]["uuid"] = "skill-call"
    activation[1]["uuid"] = "skill-result"
    activation[1]["parentUuid"] = "skill-call"
    activation[1]["sourceToolAssistantUUID"] = "skill-call"
    records += activation
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-result",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": (
                    f"Base directory for this skill: {base}/skiphow\n{body}"
                )
            },
        }
    )
    records += claude_call(
        "read-product",
        "Read",
        {"file_path": "/project/.agents/skills/product-decisions/SKILL.md"},
    )
    records += claude_call(
        "search-research",
        "Grep",
        {"path": "/project/.agents/skills/research/SKILL.md", "pattern": "claim"},
    )
    records += claude_call(
        "write-testing",
        "Edit",
        {"file_path": "/project/.agents/skills/testing/SKILL.md"},
    )
    assert DOGFOOD.detect_skills(records) == [
        {
            "name": "product-decisions",
            "source": "project",
            "version": "unknown",
            "signals": {"read_action_observed": 1},
        },
        {
            "name": "research",
            "source": "project",
            "version": "unknown",
            "signals": {"search_action_observed": 1},
        },
        {
            "name": "skiphow",
            "source": "plugin",
            "version": "2.0.0",
            "signals": {"activated": 1, "body_observed": 1},
        },
        {
            "name": "testing",
            "source": "project",
            "version": "unknown",
            "signals": {"write_action_succeeded": 1},
        },
    ]


def test_dogfood_skill_attribution_cannot_be_spoofed_inside_tool_input() -> None:
    records = claude_call(
        "spoofed-skill",
        "Skill",
        {"skill": "skiphow", "attributionPlugin": "skiphow"},
        "Skill loaded",
    )
    assert DOGFOOD.detect_skills(records) == []


def test_dogfood_failed_semantic_path_is_not_a_successful_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "/project/.agents/skills/skiphow/references/testing.md"
    records = claude_call("failed-read", "Read", {"file_path": path}, "missing", is_error=True)
    info = reference_info(monkeypatch, records)
    assert info == {
        "verdict": "path_action_failed",
        "basis": "tool_event",
        "matching_line_values": "unavailable",
        "artifact_source": "contract_bytes_unavailable",
        "actions": ["path_action_failed"],
        "mismatched_path_versions": [],
    }


def test_dogfood_shell_comments_quotes_and_assignments_are_not_path_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "/repo/plugins/skiphow/skills/skiphow/references/testing.md"
    command = f"NOTE={path} printf '%s' '{path} is quoted prose' # ignored {path}"
    info = reference_info(monkeypatch, codex_command(command))
    assert info == {
        "verdict": "not_observed",
        "basis": "transcript_absence_only",
        "matching_line_values": "unavailable",
        "artifact_source": "contract_bytes_unavailable",
        "actions": ["none"],
        "mismatched_path_versions": [],
    }


def test_dogfood_nested_shell_and_outer_redirect_are_neutral_path_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    testing = str(SKILL.parent / "references/testing.md")
    research = str(SKILL.parent / "references/research.md")
    records = codex_command(f"sh -c 'cat {testing}' > {research}")
    monkeypatch.setattr(
        DOGFOOD, "version_reference_names", lambda _version: {"research", "testing"}
    )
    evidence = DOGFOOD.detect_references(Path("unused"), records, "unknown")
    for name in ("research", "testing"):
        assert evidence[name] == {
            "verdict": "not_observed",
            "basis": "transcript_absence_only",
            "matching_line_values": "unavailable",
            "artifact_source": "contract_bytes_unavailable",
            "actions": ["none"],
            "mismatched_path_versions": [],
        }


@pytest.mark.parametrize("artifact_source", ["tag", "cache"])
def test_dogfood_exact_body_output_wins_regardless_of_exit_or_path_label(
    monkeypatch: pytest.MonkeyPatch,
    artifact_source: str,
) -> None:
    testing_body = "testing first\ntesting second\ntesting third"
    research_body = "research first\nresearch second\nresearch third"
    wrong_path = str(SKILL.parent / "references/research.md")
    records = claude_call(
        "failed-shell",
        "Bash",
        {"command": f"cat {wrong_path}"},
        testing_body,
        is_error=True,
    )
    monkeypatch.setattr(
        DOGFOOD, "version_reference_names", lambda _version: {"research", "testing"}
    )
    monkeypatch.setattr(
        DOGFOOD,
        "package_reference",
        lambda _version, name, _roots=(): (
            testing_body if name == "testing" else research_body,
            artifact_source,
        ),
    )
    evidence = DOGFOOD.detect_references(Path("unused"), records, "2.0.0")
    assert evidence["testing"] == {
        "verdict": "body_observed",
        "basis": "complete_artifact_text_in_model_output",
        "matching_line_values": "3/3",
        "artifact_source": artifact_source,
        "actions": ["none"],
        "mismatched_path_versions": [],
    }
    assert evidence["research"]["verdict"] == "not_observed"
    assert evidence["research"]["actions"] == ["none"]


def test_dogfood_blank_reference_artifact_is_not_observed_in_arbitrary_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "/project/.agents/skills/skiphow/references/testing.md"
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": path},
        "unrelated successful output",
    )
    info = reference_info(monkeypatch, records, body="\n", source="tag")
    assert info == {
        "verdict": "read_action_observed",
        "basis": "tool_event",
        "matching_line_values": "unavailable",
        "artifact_source": "tag",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
    }


def test_dogfood_flat_codex_tool_output_is_not_exact_model_visible_text() -> None:
    assert DOGFOOD.codex_item_output(
        {
            "type": "command_execution",
            "aggregated_output": "raw command output",
            "error": {"message": "raw command error"},
        }
    ) == ""

    content = [{"type": "text", "text": "first"}]
    assert DOGFOOD.codex_item_output(
        {
            "type": "mcp_tool_call",
            "result": {
                "content": content,
                "structured_content": {"visible": "structured"},
            },
        }
    ) == ""
    assert DOGFOOD.codex_item_output(
        {
            "type": "mcp_tool_call",
            "result": {"content": content, "structured_content": None},
        }
    ) == ""
    assert DOGFOOD.codex_item_output(
        {
            "type": "mcp_tool_call",
            "result": None,
            "error": {"message": "visible failure"},
        }
    ) == ""


def test_dogfood_codex_mcp_resource_output_is_not_claimed_as_exact_text() -> None:
    start = {
        "type": "item.started",
        "item": {
            "id": "mcp",
            "type": "mcp_tool_call",
            "server": "docs",
            "tool": "read",
            "arguments": {"uri": "doc://result"},
            "result": None,
            "error": None,
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "item": {
            "id": "mcp",
            "type": "mcp_tool_call",
            "server": "docs",
            "tool": "read",
            "arguments": {"uri": "doc://result"},
            "result": {
                "content": [
                    {
                        "type": "resource",
                        "resource": {
                            "uri": "doc://result",
                            "mimeType": "text/plain",
                            "text": "embedded resource output",
                        },
                    }
                ],
                "structured_content": None,
            },
            "error": None,
            "status": "completed",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "succeeded"
    assert event["output"] == ""


def test_dogfood_matching_lines_do_not_infer_that_a_body_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line\nfourth exact line"
    path = "/project/.agents/skills/skiphow/references/testing.md"
    records = claude_call("read-testing", "Read", {"file_path": path}, "second exact line")
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info == {
        "verdict": "matching_lines_observed",
        "basis": "matching_decoded_line_text",
        "matching_line_values": "1/4",
        "artifact_source": "tag",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
    }


def test_dogfood_unknown_contract_never_reads_other_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "/project/.agents/skills/skiphow/references/testing.md"

    def unexpected(*_args: object) -> tuple[str, str]:
        raise AssertionError("unknown versions must not compare repository HEAD")

    monkeypatch.setattr(DOGFOOD, "package_reference", unexpected)
    monkeypatch.setattr(DOGFOOD, "version_reference_names", lambda _version: {"testing"})
    action = DOGFOOD.detect_references(
        Path("unused"), claude_call("read-testing", "Read", {"file_path": path}), "unknown"
    )["testing"]
    absent = DOGFOOD.detect_references(Path("unused"), [], "unknown")["testing"]
    assert action == {
        "verdict": "read_action_observed",
        "basis": "tool_event",
        "matching_line_values": "unavailable",
        "artifact_source": "contract_bytes_unavailable",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
    }
    assert absent == {
        "verdict": "not_observed",
        "basis": "transcript_absence_only",
        "matching_line_values": "unavailable",
        "artifact_source": "contract_bytes_unavailable",
        "actions": ["none"],
        "mismatched_path_versions": [],
    }


def test_dogfood_unavailable_contract_yields_only_action_or_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "/project/.agents/skills/skiphow/references/testing.md"
    calls: list[tuple[str, str, tuple[str, ...]]] = []

    def unavailable(
        version: str, name: str, roots: tuple[str, ...] = ()
    ) -> tuple[str, str]:
        calls.append((version, name, roots))
        return "", "contract_bytes_unavailable"

    monkeypatch.setattr(DOGFOOD, "version_reference_names", lambda _version: {"testing"})
    monkeypatch.setattr(DOGFOOD, "package_reference", unavailable)
    action = DOGFOOD.detect_references(
        Path("unused"),
        claude_call("read-testing", "Read", {"file_path": path}),
        "99.0.0",
    )["testing"]
    absent = DOGFOOD.detect_references(Path("unused"), [], "99.0.0")["testing"]
    assert calls == [
        ("99.0.0", "testing", ()),
        ("99.0.0", "testing", ()),
    ]
    assert action["verdict"] == "read_action_observed"
    assert action["artifact_source"] == "contract_bytes_unavailable"
    assert action["matching_line_values"] == "unavailable"
    assert absent == {
        "verdict": "not_observed",
        "basis": "transcript_absence_only",
        "matching_line_values": "unavailable",
        "artifact_source": "contract_bytes_unavailable",
        "actions": ["none"],
        "mismatched_path_versions": [],
    }


def test_dogfood_assistant_prose_never_observes_reference_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    records = [
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": body}]},
        }
    ]
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info == {
        "verdict": "not_observed",
        "basis": "transcript_absence_only",
        "matching_line_values": "0/3",
        "artifact_source": "tag",
        "actions": ["none"],
        "mismatched_path_versions": [],
    }


def test_dogfood_split_semantic_tool_result_text_reconstructs_exact_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = "/project/.agents/skills/skiphow/references/testing.md"
    output = [
        {"type": "text", "text": "first exact line\nsecond exact line"},
        {"type": "text", "text": "third exact line"},
    ]
    records = claude_call("read-testing", "Read", {"file_path": path}, output)
    info = reference_info(monkeypatch, records, body=body, source="cache")
    assert info == {
        "verdict": "body_observed",
        "basis": "complete_artifact_text_in_model_output",
        "matching_line_values": "3/3",
        "artifact_source": "cache",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
    }


def test_dogfood_decodes_an_exact_complete_claude_read_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = "/project/.agents/skills/skiphow/references/testing.md"
    records = claude_read("read-testing", path, body)
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info == {
        "verdict": "body_observed",
        "basis": "complete_artifact_text_in_model_output",
        "matching_line_values": "3/3",
        "artifact_source": "tag",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
    }


@pytest.mark.parametrize(
    "failure",
    [
        "wrong_path",
        "partial_start",
        "boolean_start",
        "float_start",
        "line_count",
        "boolean_count",
        "total_lines",
        "boolean_total",
        "float_total",
        "wrong_number",
        "leading_zero",
        "space_separator",
        "vertical_tab",
        "metadata_content",
    ],
)
def test_dogfood_does_not_decode_an_unproven_claude_read_frame(
    failure: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = (
        "only exact line"
        if failure in {"boolean_count", "boolean_total"}
        else "first exact line\nsecond exact line\nthird exact line"
    )
    path = "/project/.agents/skills/skiphow/references/testing.md"
    records = claude_read("read-testing", path, body)
    file_result = records[1]["toolUseResult"]["file"]
    if failure == "wrong_path":
        file_result["filePath"] = "/project/other.md"
    elif failure == "partial_start":
        file_result["startLine"] = 2
    elif failure == "boolean_start":
        file_result["startLine"] = True
    elif failure == "float_start":
        file_result["startLine"] = 1.0
    elif failure == "line_count":
        file_result["numLines"] = 2
    elif failure == "boolean_count":
        file_result["numLines"] = True
    elif failure == "total_lines":
        file_result["totalLines"] = 4
    elif failure == "boolean_total":
        file_result["totalLines"] = True
    elif failure == "float_total":
        file_result["totalLines"] = 3.0
    elif failure == "wrong_number":
        records[1]["message"]["content"][0]["content"] = (
            "1\tfirst exact line\n3\tsecond exact line\n4\tthird exact line"
        )
    elif failure == "leading_zero":
        records[1]["message"]["content"][0]["content"] = (
            "01\tfirst exact line\n2\tsecond exact line\n3\tthird exact line"
        )
    elif failure == "space_separator":
        records[1]["message"]["content"][0]["content"] = (
            "1 first exact line\n2 second exact line\n3 third exact line"
        )
    elif failure == "vertical_tab":
        records[1]["message"]["content"][0]["content"] = (
            "1\tfirst exact line\v2\tsecond exact line\v3\tthird exact line"
        )
    else:
        file_result["content"] = "different metadata body"

    raw_output = records[1]["message"]["content"][0]["content"]
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.decoded_event_output(event) == raw_output
    if len(body.splitlines()) > 1:
        info = reference_info(monkeypatch, records, body=body, source="tag")
        assert info["verdict"] == "read_action_observed"
        assert info["matching_line_values"] == "0/3"


def test_dogfood_does_not_share_one_read_frame_across_multiple_results() -> None:
    raw_a = "1\talpha\n2\tbeta"
    raw_b = "1\tgamma\n2\tdelta"
    records = [
        {
            "type": "assistant",
            "uuid": "read-calls",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "read-a",
                        "name": "Read",
                        "input": {"file_path": "/project/a.md"},
                    },
                    {
                        "type": "tool_use",
                        "id": "read-b",
                        "name": "Read",
                        "input": {"file_path": "/project/b.md"},
                    },
                ]
            },
        },
        {
            "type": "user",
            "uuid": "read-results",
            "parentUuid": "read-calls",
            "sourceToolAssistantUUID": "read-calls",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "read-a",
                        "is_error": False,
                        "content": raw_a,
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "read-b",
                        "is_error": False,
                        "content": raw_b,
                    },
                ]
            },
            "toolUseResult": {
                "file": {
                    "filePath": "/project/a.md",
                    "content": "alpha\nbeta",
                    "startLine": 1,
                    "numLines": 2,
                    "totalLines": 2,
                }
            },
        },
    ]
    events = DOGFOOD.terminal_tool_events(records)
    assert [event["outcome"] for event in events] == ["succeeded", "succeeded"]
    assert [event["structured_result"] for event in events] == [{}, {}]
    assert [DOGFOOD.decoded_event_output(event) for event in events] == [raw_a, raw_b]


@pytest.mark.parametrize(
    ("artifact_eol", "observed_eol"),
    [("\n", "\r\n"), ("\r\n", "\n")],
)
def test_dogfood_reference_body_treats_lf_and_crlf_as_equivalent(
    artifact_eol: str,
    observed_eol: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = ("first exact line", "second exact line", "third exact line")
    artifact = artifact_eol.join(lines)
    observed = observed_eol.join(lines)
    framed = observed_eol.join(
        f"{number}\t{line}" for number, line in enumerate(lines, 1)
    )
    path = "/project/.agents/skills/skiphow/references/testing.md"
    records = claude_read(
        "read-testing",
        path,
        observed,
        framed_output=framed,
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.decoded_event_output(event) == observed
    info = reference_info(monkeypatch, records, body=artifact, source="tag")
    assert info == {
        "verdict": "body_observed",
        "basis": "complete_artifact_text_in_model_output",
        "matching_line_values": "3/3",
        "artifact_source": "tag",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
    }


def test_dogfood_read_frame_does_not_normalize_before_it_is_proven(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = ("first exact line", "second exact line", "third exact line")
    body = "\r\n".join(lines)
    raw = "\n".join(
        f"{number}\t{line}" for number, line in enumerate(lines, 1)
    )
    path = "/project/.agents/skills/skiphow/references/testing.md"
    records = claude_read("read-testing", path, body, framed_output=raw)
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.decoded_event_output(event) == raw
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"
    assert info["matching_line_values"] == "0/3"


def test_dogfood_mismatched_installed_path_is_reported_but_not_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = str(
        host_cache_root(DOGFOOD.claude_home())
        / "1.14.2/skills/skiphow/references/testing.md"
    )
    records = claude_call("read-testing", "Read", {"file_path": path})
    info = reference_info(monkeypatch, records, body="2.0 exact body", source="tag")
    assert info["verdict"] == "version_mismatch_path_observed"
    assert info["actions"] == ["version_mismatch_path_observed"]
    assert info["mismatched_path_versions"] == ["1.14.2"]


def test_dogfood_uses_only_semantic_tool_path_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    testing = "/project/.agents/skills/skiphow/references/testing.md"
    research = "/project/.agents/skills/skiphow/references/research.md"
    records: list[dict] = []
    records += claude_call(
        "grep-prose",
        "Grep",
        {"path": "/project/src", "pattern": research},
    )
    records += claude_call("read-testing", "Read", {"file_path": testing})
    evidence = DOGFOOD.detect_references(Path("unused"), records, "unknown")
    assert "research" not in evidence
    assert evidence["testing"]["verdict"] == "read_action_observed"


def test_dogfood_unresolved_and_ambiguous_claude_actions_are_explicit() -> None:
    unresolved_path = "/project/.agents/skills/skiphow/references/testing.md"
    ambiguous_path = "/project/.agents/skills/skiphow/references/research.md"
    unresolved = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "unresolved",
                    "name": "Read",
                    "input": {"file_path": unresolved_path},
                }
            ]
        },
    }
    duplicated_calls = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "duplicate",
                        "name": "Read",
                        "input": {"file_path": ambiguous_path},
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "duplicate",
                        "name": "Read",
                        "input": {"file_path": ambiguous_path},
                    }
                ]
            },
        },
    ]
    evidence = DOGFOOD.detect_references(
        Path("unused"), [unresolved, *duplicated_calls], "unknown"
    )
    assert evidence["testing"]["verdict"] == "path_action_unresolved"
    assert evidence["research"]["verdict"] == "path_action_ambiguous"


def test_dogfood_pairs_only_one_later_result_with_one_call(tmp_path: Path) -> None:
    result_before_call = {
        "type": "user",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "early",
                    "is_error": False,
                    "content": "done",
                }
            ]
        },
    }
    early_write = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "early",
                    "name": "Write",
                    "input": {"file_path": "/repo/early.py"},
                }
            ]
        },
    }
    duplicate_calls = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "duplicate",
                        "name": name,
                        "input": payload,
                    }
                ]
            },
        }
        for name, payload in (
            ("Write", {"file_path": "/repo/duplicate.py"}),
            ("Agent", {"subagent_type": "reviewer", "description": "Review"}),
        )
    ]
    duplicate_result = {
        "type": "user",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "duplicate",
                    "is_error": False,
                    "content": "done",
                }
            ]
        },
    }
    records = [result_before_call, early_write, *duplicate_calls, duplicate_result]
    assert DOGFOOD.claude_tool_results(records) == {}
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 0)
    assert data["successful_structured_write_actions"] == []
    assert data["successful_structured_delegations"] == []
    assert len(DOGFOOD.unpaired_tool_calls(records)) == 3
    assert data["confounders"]["unpaired_tool_call_count"] == 3


@pytest.mark.parametrize(
    "result_identity",
    [
        {"uuid": "result"},
        {
            "uuid": "result",
            "parentUuid": "assistant-b",
            "sourceToolAssistantUUID": "assistant-b",
        },
        {
            "parentUuid": "assistant-a",
            "sourceToolAssistantUUID": "assistant-a",
        },
    ],
)
def test_dogfood_claude_result_lineage_must_match_the_call_record(
    result_identity: dict,
    tmp_path: Path,
) -> None:
    call = {
        "type": "assistant",
        "uuid": "assistant-a",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "write",
                    "name": "Write",
                    "input": {"file_path": "/repo/a.py"},
                },
                {
                    "type": "tool_use",
                    "id": "ask",
                    "name": "AskUserQuestion",
                    "input": {},
                },
            ]
        },
    }
    mismatched_result = {
        "type": "user",
        **result_identity,
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "write",
                    "is_error": False,
                    "content": "written",
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "ask",
                    "is_error": False,
                    "content": "owner answer",
                },
            ]
        },
    }
    records = [call, mismatched_result]
    assert DOGFOOD.claude_tool_results(records) == {}
    assert len(DOGFOOD.unpaired_tool_calls(records)) == 2
    assert DOGFOOD.owner_turns(records) == []
    assert DOGFOOD.owner_activity_record_indexes(records) == set()
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 100)
    assert data["successful_structured_write_actions"] == []


def test_dogfood_claude_call_record_uuid_must_be_unique() -> None:
    first_call = {
        "type": "assistant",
        "uuid": "duplicate-assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "first",
                    "name": "Write",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    second_call = {
        "type": "assistant",
        "uuid": "duplicate-assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "second",
                    "name": "Read",
                    "input": {"file_path": "/repo/b.py"},
                }
            ]
        },
    }
    result = {
        "type": "user",
        "uuid": "result",
        "parentUuid": "duplicate-assistant",
        "sourceToolAssistantUUID": "duplicate-assistant",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "first",
                    "is_error": False,
                    "content": "written",
                }
            ]
        },
    }
    records = [first_call, second_call, result]
    assert DOGFOOD.claude_tool_results(records) == {}
    assert len(DOGFOOD.unpaired_tool_calls(records)) == 2


def test_dogfood_failed_claude_result_accepts_string_tool_use_metadata(
    tmp_path: Path,
) -> None:
    records = claude_call(
        "read-failed",
        "Read",
        {"file_path": "/repo/missing.py"},
        "file not found",
        is_error=True,
    )
    records[1]["toolUseResult"] = "Error: file not found"
    transcript = write_transcript(tmp_path, records)
    parsed, broken = DOGFOOD.iter_records(transcript)
    assert broken == 0
    assert parsed == records
    assert DOGFOOD.claude_tool_results(parsed) == {
        "read-failed": (False, "file not found")
    }
    (event,) = DOGFOOD.terminal_tool_events(parsed)
    assert event["outcome"] == "failed"
    assert event["output"] == "file not found"


def test_dogfood_empty_claude_ids_are_ambiguous_and_unpaired() -> None:
    records = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "",
                        "name": "Read",
                        "input": {
                            "file_path": (
                                "/project/.agents/skills/skiphow/references/testing.md"
                            )
                        },
                    }
                ]
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "",
                        "is_error": False,
                        "content": "done",
                    }
                ]
            },
        },
    ]
    assert DOGFOOD.claude_tool_results(records) == {}
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert event["id"] == ""
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False
    assert len(DOGFOOD.unpaired_tool_calls(records)) == 1


def test_dogfood_claude_pairs_only_assistant_calls_with_nonhuman_user_results() -> None:
    assistant_calls = {
        "type": "assistant",
        "uuid": "assistant-calls",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_id,
                    "name": "Read",
                    "input": {"file_path": f"/repo/{tool_id}.md"},
                }
                for tool_id in ("external", "assistant-result", "human-result")
            ]
        },
    }
    call_in_user_record = {
        "type": "user",
        "userType": "external",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "user-call",
                    "name": "Read",
                    "input": {"file_path": "/repo/user-call.md"},
                }
            ]
        },
    }
    external_result = {
        "type": "user",
        "userType": "external",
        "uuid": "external-results",
        "parentUuid": "assistant-calls",
        "sourceToolAssistantUUID": "assistant-calls",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "external",
                    "is_error": False,
                    "content": "external result",
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "user-call",
                    "is_error": False,
                    "content": "cannot pair with a user call",
                },
            ]
        },
    }
    assistant_result = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "assistant-result",
                    "is_error": False,
                    "content": "wrong record role",
                }
            ]
        },
    }
    human_result = {
        "type": "user",
        "origin": {"kind": "human"},
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "human-result",
                    "is_error": False,
                    "content": "human text is not a tool result",
                }
            ]
        },
    }
    records = [
        assistant_calls,
        call_in_user_record,
        external_result,
        assistant_result,
        human_result,
    ]
    assert DOGFOOD.claude_tool_results(records) == {
        "external": (True, "external result")
    }
    calls, results = DOGFOOD.claude_tool_occurrences(records)
    assert set(calls) == {"external", "assistant-result", "human-result"}
    assert set(results) == {"external", "user-call"}


def test_dogfood_codex_requires_one_later_terminal_with_same_type_and_command() -> None:
    start = {
        "type": "item.started",
        "timestamp": "start",
        "item": {
            "id": "cmd",
            "type": "command_execution",
            "command": "git status --short",
            "aggregated_output": "",
            "exit_code": None,
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "timestamp": "end",
        "item": {
            "id": "cmd",
            "type": "command_execution",
            "command": "git status --short",
            "status": "completed",
            "exit_code": 0,
            "aggregated_output": "clean",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event == {
        "host": "codex",
        "id": "cmd",
        "tool": "command_execution",
        "input": terminal["item"],
        "succeeded": True,
        "outcome": "succeeded",
        "output": "",
        "at": "end",
    }
    assert DOGFOOD.unpaired_tool_calls([start, terminal]) == {}

    for contradictory_item in (
        {**terminal["item"], "command": "git diff"},
        {
            "id": "cmd",
            "type": "web_search",
            "query": "git status --short",
            "status": "completed",
        },
    ):
        contradictory = {**terminal, "item": contradictory_item}
        (event,) = DOGFOOD.codex_tool_events([start, contradictory])
        assert event["outcome"] == "ambiguous"
        assert event["succeeded"] is False
        assert event["input"] == contradictory_item
        assert event["output"] == ""
        assert event["at"] == "end"
        assert DOGFOOD.unpaired_tool_calls([start, contradictory]) == {
            "codex:cmd:0": 0
        }


@pytest.mark.parametrize(
    ("status", "exit_code", "outcome"),
    [
        ("completed", 0, "succeeded"),
        ("failed", 1, "failed"),
        ("failed", None, "failed"),
        ("declined", -1, "failed"),
        ("declined", None, "failed"),
    ],
)
def test_dogfood_codex_command_terminal_status_matches_exit_code(
    status: str,
    exit_code: int | None,
    outcome: str,
) -> None:
    item = {
        "id": "command",
        "type": "command_execution",
        "command": "true",
        "aggregated_output": "",
        "exit_code": exit_code,
        "status": status,
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is True
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == outcome
    assert event["succeeded"] is (outcome == "succeeded")


@pytest.mark.parametrize(
    ("status", "exit_code"),
    [
        ("completed", 1),
        ("completed", -1),
        ("completed", None),
        ("failed", 0),
        ("declined", 0),
        ("declined", 1),
        ("declined", -2),
    ],
)
def test_dogfood_codex_command_rejects_contradictory_terminal_status(
    status: str,
    exit_code: object,
) -> None:
    item = {
        "id": "command",
        "type": "command_execution",
        "command": "true",
        "aggregated_output": "",
        "exit_code": exit_code,
        "status": status,
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is False
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False


@pytest.mark.parametrize(
    ("item_type", "started_fields", "completed_fields", "changed_fields"),
    [
        (
            "collab_tool_call",
            {
                "tool": "spawn_agent",
                "sender_thread_id": "root",
                "receiver_thread_ids": [],
                "prompt": "Review",
                "agents_states": {},
            },
            {
                "tool": "spawn_agent",
                "sender_thread_id": "root",
                "receiver_thread_ids": ["child"],
                "prompt": "Review",
                "agents_states": {
                    "child": {"status": "completed", "message": "done"}
                },
            },
            {
                "tool": "spawn_agent",
                "sender_thread_id": "root",
                "receiver_thread_ids": ["child"],
                "prompt": "Different",
                "agents_states": {
                    "child": {"status": "completed", "message": "done"}
                },
            },
        ),
        (
            "mcp_tool_call",
            {
                "server": "github",
                "tool": "search",
                "arguments": {"q": "bug"},
                "result": None,
                "error": None,
            },
            {
                "server": "github",
                "tool": "search",
                "arguments": {"q": "bug"},
                "result": codex_mcp_result(),
                "error": None,
            },
            {
                "server": "other",
                "tool": "search",
                "arguments": {"q": "bug"},
                "result": codex_mcp_result(),
                "error": None,
            },
        ),
    ],
)
def test_dogfood_codex_requires_stable_structured_action_identity(
    item_type: str,
    started_fields: dict,
    completed_fields: dict,
    changed_fields: dict,
) -> None:
    start = {
        "type": "item.started",
        "item": {
            "id": "action",
            "type": item_type,
            **started_fields,
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "item": {
            "id": "action",
            "type": item_type,
            **completed_fields,
            "status": "completed",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "succeeded"
    assert event["succeeded"] is True
    assert DOGFOOD.unpaired_tool_calls([start, terminal]) == {}

    contradictory = {
        "type": "item.completed",
        "item": {
            "id": "action",
            "type": item_type,
            **changed_fields,
            "status": "completed",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, contradictory])
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False
    assert len(DOGFOOD.unpaired_tool_calls([start, contradictory])) == 1


@pytest.mark.parametrize(
    ("tool", "receivers", "prompt"),
    [
        ("spawn_agent", [], "Review"),
        ("send_input", ["child"], "Continue"),
        ("close_agent", ["child"], None),
        ("wait", ["child-a", "child-a", "child-b"], None),
        ("wait", [], None),
    ],
)
def test_dogfood_codex_collab_starts_match_producer_shapes(
    tool: str,
    receivers: list[str],
    prompt: str | None,
) -> None:
    item = {
        "id": "collab",
        "type": "collab_tool_call",
        "tool": tool,
        "sender_thread_id": "root",
        "receiver_thread_ids": receivers,
        "prompt": prompt,
        "agents_states": {},
        "status": "in_progress",
    }
    assert DOGFOOD.codex_start_valid(item) is True
    assert DOGFOOD.codex_event_valid({"type": "item.started", "item": item}) is True


@pytest.mark.parametrize(
    ("tool", "receivers", "prompt", "states"),
    [
        ("spawn_agent", ["child"], "Review", {}),
        ("spawn_agent", [], None, {}),
        (
            "spawn_agent",
            [],
            "Review",
            {"child": {"status": "running", "message": None}},
        ),
        ("send_input", [], "Continue", {}),
        ("send_input", ["child-a", "child-b"], "Continue", {}),
        ("send_input", ["child"], None, {}),
        (
            "send_input",
            ["child"],
            "Continue",
            {"child": {"status": "running", "message": None}},
        ),
        ("close_agent", [], None, {}),
        ("close_agent", ["child-a", "child-b"], None, {}),
        ("close_agent", ["child"], "Close", {}),
        (
            "close_agent",
            ["child"],
            None,
            {"child": {"status": "running", "message": None}},
        ),
        ("wait", [], "Wait", {}),
        (
            "wait",
            [],
            None,
            {"child": {"status": "running", "message": None}},
        ),
    ],
)
def test_dogfood_codex_collab_rejects_impossible_start_shapes(
    tool: str,
    receivers: list[str],
    prompt: str | None,
    states: dict,
) -> None:
    item = {
        "id": "collab",
        "type": "collab_tool_call",
        "tool": tool,
        "sender_thread_id": "root",
        "receiver_thread_ids": receivers,
        "prompt": prompt,
        "agents_states": states,
        "status": "in_progress",
    }
    assert DOGFOOD.codex_start_valid(item) is False
    assert DOGFOOD.codex_event_valid({"type": "item.started", "item": item}) is False


def test_dogfood_codex_wait_terminal_may_report_a_receiver_subset() -> None:
    start = {
        "type": "item.started",
        "item": {
            "id": "wait",
            "type": "collab_tool_call",
            "tool": "wait",
            "sender_thread_id": "root",
            "receiver_thread_ids": ["child-a", "child-a", "child-b"],
            "prompt": None,
            "agents_states": {},
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "item": {
            "id": "wait",
            "type": "collab_tool_call",
            "tool": "wait",
            "sender_thread_id": "root",
            "receiver_thread_ids": ["child-a"],
            "prompt": None,
            "agents_states": {
                "child-a": {"status": "completed", "message": "done"},
            },
            "status": "completed",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "unverified"
    assert DOGFOOD.unpaired_tool_calls([start, terminal]) == {}

    unrelated = {
        **terminal,
        "item": {
            **terminal["item"],
            "receiver_thread_ids": ["child-a", "child-c"],
            "agents_states": {
                "child-a": {"status": "completed", "message": "done"},
                "child-c": {"status": "completed", "message": "done"},
            },
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, unrelated])
    assert event["outcome"] == "ambiguous"
    assert DOGFOOD.unpaired_tool_calls([start, unrelated]) == {"codex:wait:0": 0}


def test_dogfood_codex_mcp_arguments_compare_json_types_strictly() -> None:
    start = {
        "type": "item.started",
        "item": {
            "id": "mcp",
            "type": "mcp_tool_call",
            "server": "docs",
            "tool": "read",
            "arguments": {"page": 1, "flags": [True]},
            "result": None,
            "error": None,
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "item": {
            "id": "mcp",
            "type": "mcp_tool_call",
            "server": "docs",
            "tool": "read",
            "arguments": {"page": True, "flags": [1]},
            "result": codex_mcp_result(),
            "error": None,
            "status": "completed",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False
    assert DOGFOOD.unpaired_tool_calls([start, terminal]) == {"codex:mcp:0": 0}


def test_dogfood_codex_web_search_without_status_stays_unverified() -> None:
    records = [
        {
            "type": "item.started",
            "timestamp": "start",
            "item": {
                "id": "web",
                "type": "web_search",
                "query": "SkipHow",
                "action": {"type": "search", "query": "SkipHow"},
                "status": "in_progress",
            },
        },
        {
            "type": "item.completed",
            "timestamp": "end",
            "item": {
                "id": "web",
                "type": "web_search",
                "query": "SkipHow",
                "action": {"type": "search", "query": "SkipHow"},
            },
        },
    ]
    (event,) = DOGFOOD.codex_tool_events(records)
    assert event["outcome"] == "unverified"
    assert event["succeeded"] is False
    assert event["at"] == "end"
    assert DOGFOOD.unpaired_tool_calls(records) == {}


def test_dogfood_codex_accepts_a_terminal_only_file_change() -> None:
    terminal = {
        "type": "item.completed",
        "timestamp": "end",
        "item": {
            "id": "change",
            "type": "file_change",
            "status": "completed",
            "changes": [{"path": "/repo/a.py", "kind": "update"}],
        },
    }
    (event,) = DOGFOOD.codex_tool_events([terminal])
    assert event == {
        "host": "codex",
        "id": "change",
        "tool": "file_change",
        "input": terminal["item"],
        "succeeded": True,
        "outcome": "succeeded",
        "output": "",
        "at": "end",
    }
    assert DOGFOOD.unpaired_tool_calls([terminal]) == {}


def test_dogfood_codex_accepts_a_started_file_change_with_its_terminal() -> None:
    changes = [{"path": "/repo/a.py", "kind": "update"}]
    start = {
        "type": "item.started",
        "timestamp": "start",
        "item": {
            "id": "change",
            "type": "file_change",
            "status": "in_progress",
            "changes": changes,
        },
    }
    terminal = {
        "type": "item.completed",
        "timestamp": "end",
        "item": {
            "id": "change",
            "type": "file_change",
            "status": "completed",
            "changes": changes,
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "succeeded"
    assert event["succeeded"] is True
    assert event["at"] == "end"
    assert DOGFOOD.unpaired_tool_calls([start, terminal]) == {}


def test_dogfood_codex_file_change_identity_is_order_insensitive() -> None:
    start = {
        "type": "item.started",
        "item": {
            "id": "change",
            "type": "file_change",
            "status": "in_progress",
            "changes": [
                {"path": "/repo/a.py", "kind": "update"},
                {"path": "/repo/b.py", "kind": "delete"},
            ],
        },
    }
    terminal = {
        "type": "item.completed",
        "item": {
            "id": "change",
            "type": "file_change",
            "status": "completed",
            "changes": list(reversed(start["item"]["changes"])),
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "succeeded"
    assert DOGFOOD.unpaired_tool_calls([start, terminal]) == {}


@pytest.mark.parametrize(
    "changes",
    [
        {"path": "/repo/a.py", "kind": "update"},
        [{"path": "", "kind": "update"}],
        [{"path": "/repo/a.py", "kind": "replace"}],
        [{"path": "/repo/a.py"}],
        [
            {"path": "/repo/a.py", "kind": "update"},
            {"path": "/repo/a.py", "kind": "delete"},
        ],
    ],
)
def test_dogfood_codex_file_change_requires_the_exact_changes_schema(
    changes: object,
) -> None:
    item = {
        "id": "change",
        "type": "file_change",
        "status": "completed",
        "changes": changes,
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is False
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False


@pytest.mark.parametrize(
    "item",
    [
        {
            "id": "command",
            "type": "command_execution",
            "command": "true",
            "status": "completed",
            "exit_code": 0,
            "aggregated_output": "",
        },
        {
            "id": "mcp",
            "type": "mcp_tool_call",
            "server": "github",
            "tool": "search",
            "arguments": {"q": "bug"},
            "result": codex_mcp_result(),
            "error": None,
            "status": "completed",
        },
        {
            "id": "collab",
            "type": "collab_tool_call",
            "tool": "spawn_agent",
            "sender_thread_id": "root",
            "receiver_thread_ids": ["child"],
            "prompt": "Review",
            "agents_states": {
                "child": {"status": "completed", "message": "done"}
            },
            "status": "completed",
        },
        {
            "id": "web",
            "type": "web_search",
            "query": "SkipHow",
            "action": {"type": "search", "query": "SkipHow"},
        },
    ],
)
def test_dogfood_codex_accepts_terminal_only_mapped_tool_events(item: dict) -> None:
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "timestamp": "end", "item": item}]
    )
    assert event["input"] == item
    expected = "unverified" if item["type"] == "web_search" else "succeeded"
    assert event["outcome"] == expected
    assert event["succeeded"] is (expected == "succeeded")
    assert event["output"] == ""
    assert event["at"] == "end"


@pytest.mark.parametrize(
    ("status", "result", "error", "outcome"),
    [
        ("completed", codex_mcp_result(), None, "succeeded"),
        ("failed", codex_mcp_result(), None, "failed"),
        ("failed", None, {"message": "failed"}, "failed"),
    ],
)
def test_dogfood_codex_mcp_terminal_status_matches_result_or_error(
    status: str,
    result: object,
    error: object,
    outcome: str,
) -> None:
    item = {
        "id": "mcp",
        "type": "mcp_tool_call",
        "server": "docs",
        "tool": "read",
        "arguments": {"uri": "doc://result"},
        "result": result,
        "error": error,
        "status": status,
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is True
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == outcome
    assert event["succeeded"] is (outcome == "succeeded")
    assert event["output"] == ""


@pytest.mark.parametrize(
    ("status", "result", "error"),
    [
        ("completed", None, None),
        ("completed", None, {"message": "failed"}),
        ("completed", codex_mcp_result(), {"message": "failed"}),
        ("failed", None, None),
        ("failed", codex_mcp_result(), {"message": "failed"}),
    ],
)
def test_dogfood_codex_mcp_rejects_contradictory_terminal_payloads(
    status: str,
    result: object,
    error: object,
) -> None:
    item = {
        "id": "mcp",
        "type": "mcp_tool_call",
        "server": "docs",
        "tool": "read",
        "arguments": {},
        "result": result,
        "error": error,
        "status": status,
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is False
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False


@pytest.mark.parametrize(
    ("tool", "status", "receivers", "prompt", "states", "outcome"),
    [
        (
            "wait",
            "completed",
            ["child"],
            None,
            {"child": {"status": "completed", "message": "done"}},
            "unverified",
        ),
        (
            "wait",
            "failed",
            ["child"],
            None,
            {"child": {"status": "errored", "message": "failed"}},
            "unverified",
        ),
        (
            "wait",
            "failed",
            ["child"],
            None,
            {"child": {"status": "not_found", "message": None}},
            "unverified",
        ),
        (
            "spawn_agent",
            "completed",
            ["child"],
            "Review",
            {"child": {"status": "running", "message": None}},
            "succeeded",
        ),
        ("spawn_agent", "failed", [], "Review", {}, "failed"),
        (
            "spawn_agent",
            "failed",
            ["child"],
            "Review",
            {"child": {"status": "errored", "message": "failed"}},
            "succeeded",
        ),
        (
            "send_input",
            "completed",
            ["child"],
            "Continue",
            {"child": {"status": "running", "message": None}},
            "unverified",
        ),
        (
            "close_agent",
            "completed",
            ["child"],
            None,
            {"child": {"status": "shutdown", "message": None}},
            "unverified",
        ),
    ],
)
def test_dogfood_codex_collab_terminal_status_matches_agent_states(
    tool: str,
    status: str,
    receivers: list[str],
    prompt: str | None,
    states: dict,
    outcome: str,
) -> None:
    item = {
        "id": "collab",
        "type": "collab_tool_call",
        "tool": tool,
        "sender_thread_id": "root",
        "receiver_thread_ids": receivers,
        "prompt": prompt,
        "agents_states": states,
        "status": status,
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is True
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == outcome
    assert event["succeeded"] is (outcome == "succeeded")


@pytest.mark.parametrize(
    "state",
    [
        {"status": "running", "message": "not a terminal message"},
        {"status": "pending_init", "message": "not a terminal message"},
        {"status": "interrupted", "message": "not a terminal message"},
        {"status": "shutdown", "message": "not a terminal message"},
        {"status": "not_found", "message": "not a terminal message"},
        {"status": "errored", "message": None},
    ],
)
def test_dogfood_codex_collab_rejects_impossible_state_messages(
    state: dict,
) -> None:
    assert DOGFOOD.codex_collab_states_valid({"child": state}) is False


@pytest.mark.parametrize(
    ("tool", "prompt", "terminal_state"),
    [
        ("send_input", "Continue", {"status": "running", "message": None}),
        ("close_agent", None, {"status": "shutdown", "message": None}),
    ],
)
def test_dogfood_codex_nonspawn_collab_terminal_pairs_but_stays_unverified(
    tool: str,
    prompt: str | None,
    terminal_state: dict,
) -> None:
    start = {
        "type": "item.started",
        "item": {
            "id": "collab",
            "type": "collab_tool_call",
            "tool": tool,
            "sender_thread_id": "root",
            "receiver_thread_ids": ["child"],
            "prompt": prompt,
            "agents_states": {},
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "item": {
            **start["item"],
            "agents_states": {"child": terminal_state},
            "status": "completed",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "unverified"
    assert event["succeeded"] is False
    assert DOGFOOD.unpaired_tool_calls([start, terminal]) == {}


@pytest.mark.parametrize(
    ("tool", "status", "receivers", "states"),
    [
        (
            "wait",
            "completed",
            ["child"],
            {"child": {"status": "errored", "message": "failed"}},
        ),
        (
            "wait",
            "completed",
            ["child"],
            {"child": {"status": "not_found", "message": None}},
        ),
        (
            "wait",
            "failed",
            ["child"],
            {"child": {"status": "completed", "message": "done"}},
        ),
        ("spawn_agent", "completed", [], {}),
        (
            "spawn_agent",
            "completed",
            ["child-a", "child-b"],
            {
                "child-a": {"status": "running", "message": None},
                "child-b": {"status": "running", "message": None},
            },
        ),
        (
            "spawn_agent",
            "failed",
            ["child-a", "child-b"],
            {
                "child-a": {"status": "errored", "message": "failed"},
                "child-b": {"status": "not_found", "message": None},
            },
        ),
    ],
)
def test_dogfood_codex_collab_rejects_contradictory_terminals(
    tool: str,
    status: str,
    receivers: list[str],
    states: dict,
) -> None:
    item = {
        "id": "collab",
        "type": "collab_tool_call",
        "tool": tool,
        "sender_thread_id": "root",
        "receiver_thread_ids": receivers,
        "prompt": "Review" if tool == "spawn_agent" else None,
        "agents_states": states,
        "status": status,
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is False
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False


@pytest.mark.parametrize(
    ("tool", "receivers", "prompt", "states"),
    [
        ("send_input", [], "Continue", {}),
        (
            "send_input",
            ["child-a", "child-b"],
            "Continue",
            {
                "child-a": {"status": "completed", "message": "done"},
                "child-b": {"status": "completed", "message": "done"},
            },
        ),
        (
            "send_input",
            ["child"],
            None,
            {"child": {"status": "completed", "message": "done"}},
        ),
        ("close_agent", [], None, {}),
        (
            "close_agent",
            ["child-a", "child-b"],
            None,
            {
                "child-a": {"status": "shutdown", "message": None},
                "child-b": {"status": "shutdown", "message": None},
            },
        ),
        (
            "close_agent",
            ["child"],
            "Close",
            {"child": {"status": "shutdown", "message": None}},
        ),
        ("wait", [], "Wait", {}),
    ],
)
def test_dogfood_codex_collab_rejects_impossible_terminal_tool_shapes(
    tool: str,
    receivers: list[str],
    prompt: str | None,
    states: dict,
) -> None:
    item = {
        "id": "collab",
        "type": "collab_tool_call",
        "tool": tool,
        "sender_thread_id": "root",
        "receiver_thread_ids": receivers,
        "prompt": prompt,
        "agents_states": states,
        "status": "completed",
    }
    assert DOGFOOD.codex_terminal_shape_valid(item) is False
    (event,) = DOGFOOD.codex_tool_events(
        [{"type": "item.completed", "item": item}]
    )
    assert event["outcome"] == "ambiguous"


def test_dogfood_codex_reads_terminal_status_only_from_the_item() -> None:
    start = {
        "type": "item.started",
        "item": {
            "id": "command",
            "type": "command_execution",
            "command": "true",
            "aggregated_output": "",
            "exit_code": None,
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "status": "completed",
        "item": {
            "id": "command",
            "type": "command_execution",
            "command": "true",
            "exit_code": 0,
            "aggregated_output": "",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False


@pytest.mark.parametrize(
    ("records", "outcomes", "unpaired"),
    [
        (
            [
                {
                    "type": "item.started",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "aggregated_output": "",
                        "exit_code": None,
                        "status": "in_progress",
                    },
                }
            ],
            ["unresolved"],
            1,
        ),
        (
            [
                {
                    "type": "item.completed",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "status": "completed",
                        "exit_code": 0,
                        "aggregated_output": "",
                    },
                },
                {
                    "type": "item.started",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "aggregated_output": "",
                        "exit_code": None,
                        "status": "in_progress",
                    },
                },
            ],
            ["ambiguous"],
            1,
        ),
        (
            [
                {
                    "type": "item.started",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "aggregated_output": "",
                        "exit_code": None,
                        "status": "in_progress",
                    },
                },
                {
                    "type": "item.started",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "aggregated_output": "",
                        "exit_code": None,
                        "status": "in_progress",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "status": "completed",
                        "exit_code": 0,
                        "aggregated_output": "",
                    },
                },
            ],
            ["ambiguous"],
            2,
        ),
        (
            [
                {
                    "type": "item.started",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "aggregated_output": "",
                        "exit_code": None,
                        "status": "in_progress",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "status": "completed",
                        "exit_code": 0,
                        "aggregated_output": "",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "cmd",
                        "type": "command_execution",
                        "command": "true",
                        "status": "completed",
                        "exit_code": 0,
                        "aggregated_output": "",
                    },
                },
            ],
            ["ambiguous"],
            1,
        ),
    ],
)
def test_dogfood_codex_cardinality_and_order_fail_closed(
    records: list[dict], outcomes: list[str], unpaired: int
) -> None:
    assert [event["outcome"] for event in DOGFOOD.codex_tool_events(records)] == outcomes
    assert len(DOGFOOD.unpaired_tool_calls(records)) == unpaired


def test_dogfood_external_user_text_and_ordered_answers_are_observable() -> None:
    external = {
        "type": "user",
        "userType": "external",
        "promptSource": "typed",
        "timestamp": "2026-08-27T10:00:00Z",
        "message": {"content": "ordinary owner prompt"},
    }
    unattributed_external = {
        "type": "user",
        "userType": "external",
        "timestamp": "2026-08-27T10:00:00.500Z",
        "message": {"content": "historical owner prompt without typed provenance"},
    }
    early_answer = {
        "type": "user",
        "timestamp": "2026-08-27T10:00:01Z",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "ask",
                    "is_error": False,
                    "content": "too early",
                }
            ]
        },
    }
    ask = {
        "type": "assistant",
        "timestamp": "2026-08-27T10:00:02Z",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "ask",
                    "name": "AskUserQuestion",
                    "input": {},
                }
            ]
        },
    }
    assert DOGFOOD.owner_turns(
        [external, unattributed_external, early_answer, ask]
    ) == [
        {
            "at": "2026-08-27T10:00:00Z",
            "channel": "external_typed",
            "said": "ordinary owner prompt",
        },
        {
            "at": "2026-08-27T10:00:00.500Z",
            "channel": "external_unspecified",
            "said": "historical owner prompt without typed provenance",
        },
    ]


def test_dogfood_owner_command_wrapper_requires_one_exact_complete_frame() -> None:
    valid = (
        "<command-message>SkipHow request</command-message>\n"
        "<command-name>/skiphow</command-name>\n"
        "<command-args>create the event</command-args>"
    )
    record = {
        "type": "user",
        "origin": {"kind": "human"},
        "message": {"content": valid},
    }
    assert DOGFOOD.owner_turns([record]) == [
        {"at": "", "channel": "command_args", "said": "create the event"}
    ]
    unresolved = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "pending",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    assert DOGFOOD.owner_activity_record_indexes([unresolved, record]) == {1}
    assert DOGFOOD.ended_mid_tool([unresolved, record]) is False

    malformed = [
        valid + "\ntrailing transcript text",
        valid.replace("</command-args>", ""),
        valid.replace("/skiphow", "skiphow"),
        valid.replace(
            "<command-name>/skiphow</command-name>",
            "<command-name>/skiphow</command-name>\n"
            "<command-name>/other</command-name>",
        ),
    ]
    assert DOGFOOD.owner_turns(
        [
            {
                "type": "user",
                "origin": {"kind": "human"},
                "message": {"content": text},
            }
            for text in malformed
        ]
    ) == []


def test_dogfood_historical_external_plain_text_is_direct_owner_input() -> None:
    records = [
        {
            "type": "user",
            "userType": "external",
            "message": {"content": "historical owner request"},
        },
        {
            "type": "user",
            "userType": "external",
            "message": {
                "content": "<task-notification>host lifecycle text</task-notification>"
            },
        },
    ]
    assert DOGFOOD.owner_turns(records) == [
        {
            "at": "",
            "channel": "external_unspecified",
            "said": "historical owner request",
        }
    ]
    assert DOGFOOD.owner_activity_record_indexes(records) == {0}


def test_dogfood_queued_image_owner_activity_ends_a_trailing_tool_call() -> None:
    unresolved = {
        "type": "assistant",
        "uuid": "pending-call",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "pending",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    image_prompt = {
        "type": "user",
        "attachment": {
            "type": "queued_command",
            "commandMode": "prompt",
            "prompt": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "AA==",
                    },
                }
            ],
        },
    }
    assert DOGFOOD.owner_turns([unresolved, image_prompt]) == []
    assert DOGFOOD.owner_activity_record_indexes([unresolved, image_prompt]) == {1}
    assert DOGFOOD.ended_mid_tool([unresolved, image_prompt]) is False


def test_dogfood_assistant_text_after_a_same_record_tool_call_is_later_activity() -> None:
    record = {
        "type": "assistant",
        "uuid": "pending-call",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "pending",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                },
                {"type": "text", "text": "I cannot continue without the file."},
            ]
        },
    }
    assert len(DOGFOOD.unpaired_tool_calls([record])) == 1
    assert DOGFOOD.ended_mid_tool([record]) is False


def test_dogfood_only_unique_terminal_free_calls_count_as_trailing_unresolved() -> None:
    claude = {
        "type": "assistant",
        "uuid": "claude-pending",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "pending",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    assert DOGFOOD.unresolved_tool_calls([claude]) == {
        "claude:pending:0:0": 0
    }
    assert DOGFOOD.ended_mid_tool([claude]) is True

    duplicate_claude = [claude, {**claude, "uuid": "claude-duplicate"}]
    assert len(DOGFOOD.unpaired_tool_calls(duplicate_claude)) == 2
    assert DOGFOOD.unresolved_tool_calls(duplicate_claude) == {}
    assert DOGFOOD.ended_mid_tool(duplicate_claude) is False

    codex = {
        "type": "item.started",
        "item": {
            "id": "command",
            "type": "command_execution",
            "command": "true",
            "aggregated_output": "",
            "exit_code": None,
            "status": "in_progress",
        },
    }
    assert DOGFOOD.unresolved_tool_calls([codex]) == {"codex:command:0": 0}
    assert DOGFOOD.ended_mid_tool([codex]) is True
    duplicate_codex = [codex, codex]
    assert len(DOGFOOD.unpaired_tool_calls(duplicate_codex)) == 2
    assert DOGFOOD.unresolved_tool_calls(duplicate_codex) == {}
    assert DOGFOOD.ended_mid_tool(duplicate_codex) is False


def test_dogfood_codex_todo_update_is_later_activity_after_an_unresolved_call() -> None:
    records = [
        {
            "type": "item.started",
            "item": {
                "id": "command",
                "type": "command_execution",
                "command": "true",
                "aggregated_output": "",
                "exit_code": None,
                "status": "in_progress",
            },
        },
        {
            "type": "item.updated",
            "item": {
                "id": "todo",
                "type": "todo_list",
                "items": [{"text": "inspect", "completed": True}],
            },
        },
    ]
    assert len(DOGFOOD.unpaired_tool_calls(records)) == 1
    assert DOGFOOD.ended_mid_tool(records) is False


def test_dogfood_meta_human_records_are_not_owner_turns() -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "isMeta": True,
            "message": {"content": "host metadata"},
        },
        {
            "type": "user",
            "origin": {"kind": "human"},
            "promptSource": "typed",
            "message": {"content": "actual owner text"},
        },
    ]
    assert DOGFOOD.owner_turns(records) == [
        {"at": "", "channel": "typed", "said": "actual owner text"}
    ]


def test_dogfood_owner_turns_preserve_transcript_order_not_timestamp_order() -> None:
    records = [
        {
            "type": "user",
            "timestamp": "2026-08-27T10:00:03Z",
            "origin": {"kind": "human"},
            "message": {"content": "first in transcript"},
        },
        {
            "type": "user",
            "timestamp": "2026-08-27T10:00:01Z",
            "userType": "external",
            "promptSource": "typed",
            "message": {"content": "second in transcript"},
        },
        {
            "type": "user",
            "timestamp": "2026-08-27T10:00:02Z",
            "attachment": {
                "type": "queued_command",
                "commandMode": "prompt",
                "prompt": "third in transcript",
            },
        },
    ]
    assert [turn["said"] for turn in DOGFOOD.owner_turns(records)] == [
        "first in transcript",
        "second in transcript",
        "third in transcript",
    ]


def test_dogfood_sidechain_agent_message_is_not_a_root_report() -> None:
    root = {
        "type": "item.completed",
        "item": {"id": "root", "type": "agent_message", "text": "root result"},
    }
    sidechain = {
        "type": "item.completed",
        "isSidechain": True,
        "item": {
            "id": "delegate",
            "type": "agent_message",
            "text": "delegate result",
        },
    }
    assert DOGFOOD.assistant_text(sidechain) == ""
    assert DOGFOOD.final_assistant_text([root, sidechain]) == "root result"


def test_dogfood_broken_json_marks_sequence_claims_unverified(tmp_path: Path) -> None:
    transcript = tmp_path / "broken.jsonl"
    transcript.write_text(
        json.dumps({"type": "turn.started"}) + "\n{broken json\n",
        encoding="utf-8",
    )
    data = DOGFOOD.digest(transcript, 0)
    assert data["unparseable_lines"] == 1
    assert data["confounders"]["turn_sequence"] == "unverified_incomplete_transcript"
    assert data["confounders"]["trailing_unresolved_tool_call"] == "unknown"
    assert data["confounders"]["unpaired_tool_call_count"] == "unknown"
    assert data["confounders"]["contract_sequence"] == "unverified_incomplete_transcript"


@pytest.mark.parametrize(
    "invalid_record",
    [
        [],
        {"type": "user", "message": []},
        {"type": "user", "origin": []},
        {"type": "user", "attachment": []},
        {"type": "item.completed", "item": []},
        {"type": "assistant", "message": {"usage": []}},
        {"type": "turn.completed", "usage": []},
        {"type": "assistant", "message": {"model": 7}},
        {"type": "user", "timestamp": 7},
        {"type": "user", "userType": "external", "promptSource": []},
        {
            "type": "user",
            "attachment": {
                "type": "queued_command",
                "commandMode": "prompt",
                "prompt": [{"type": "text", "text": []}],
            },
        },
        {"type": "turn.started", "cwd": "/work/\u0000invalid"},
        {"type": "user", "message": {"content": 7}},
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": []}]},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "tool", "name": [], "input": {}}
                ]
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool",
                        "is_error": False,
                        "content": {"type": []},
                    }
                ]
            },
        },
        {
            "type": "item.completed",
            "item": {"id": "command", "type": [], "status": "completed"},
        },
        {
            "type": "item.completed",
            "item": {
                "id": "command",
                "type": "command_execution",
                "status": [],
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "change",
                "type": "file_change",
                "changes": [{"path": "/repo/a.py", "kind": []}],
                "status": "completed",
            },
        },
        {
            "type": "item.started",
            "item": {
                "id": "collab",
                "type": "collab_tool_call",
                "tool": [],
                "sender_thread_id": "root",
                "receiver_thread_ids": ["child"],
                "prompt": "Review",
                "agents_states": {
                    "child": {"status": "running", "message": None}
                },
                "status": "in_progress",
            },
        },
        {
            "type": "item.started",
            "item": {
                "id": "collab",
                "type": "collab_tool_call",
                "tool": "spawn_agent",
                "sender_thread_id": "root",
                "receiver_thread_ids": ["child"],
                "prompt": "Review",
                "agents_states": {
                    "child": {"status": [], "message": None}
                },
                "status": "in_progress",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "mcp",
                "type": "mcp_tool_call",
                "server": "github",
                "tool": "search",
                "arguments": {"q": "bug"},
                "result": {
                    "content": {},
                    "structured_content": None,
                },
                "error": None,
                "status": "completed",
            },
        },
        {"type": "turn.completed", "usage": {"input_tokens": True}},
    ],
)
def test_dogfood_iter_records_rejects_malformed_nested_schema(
    invalid_record: object,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started", "thread_id": "valid"}
    transcript = tmp_path / "schema.jsonl"
    transcript.write_text(
        json.dumps(valid) + "\n" + json.dumps(invalid_record) + "\n",
        encoding="utf-8",
    )
    assert DOGFOOD.iter_records(transcript) == ([valid], 1)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity", "1e400"])
def test_dogfood_iter_records_rejects_nonstandard_or_nonfinite_json_numbers(
    constant: str,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started", "thread_id": "valid"}
    transcript = tmp_path / "nonfinite.jsonl"
    transcript.write_text(
        json.dumps(valid) + f'\n{{"type":"turn.started","value":{constant}}}\n',
        encoding="utf-8",
    )
    assert DOGFOOD.iter_records(transcript) == ([valid], 1)


def test_dogfood_codex_mcp_content_accepts_arbitrary_json_scalars(
    tmp_path: Path,
) -> None:
    record = {
        "type": "item.completed",
        "item": {
            "id": "mcp",
            "type": "mcp_tool_call",
            "server": "docs",
            "tool": "read",
            "arguments": {},
            "result": {
                "content": [7, True, None, {"nested": ["text", 3]}],
                "structured_content": None,
            },
            "error": None,
            "status": "completed",
        },
    }
    assert DOGFOOD.iter_records(write_transcript(tmp_path, [record])) == ([record], 0)
    (event,) = DOGFOOD.codex_tool_events([record])
    assert event["outcome"] == "succeeded"
    assert event["output"] == ""


@pytest.mark.parametrize("bound", [-(1 << 63), (1 << 64) - 1])
def test_dogfood_iter_records_accepts_serde_json_integer_bounds(
    bound: int,
    tmp_path: Path,
) -> None:
    records = claude_call(
        "json-bound",
        "Read",
        {"file_path": "/repo/a", "nested": {"value": bound}},
    )
    assert DOGFOOD.iter_records(write_transcript(tmp_path, records)) == (records, 0)


@pytest.mark.parametrize("outside", [-(1 << 63) - 1, 1 << 64])
def test_dogfood_iter_records_rejects_integers_outside_serde_json_range(
    outside: int,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started"}
    invalid = {
        "type": "assistant",
        "uuid": "json-outside",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "json-outside",
                    "name": "Read",
                    "input": {"file_path": "/repo/a", "nested": {"value": outside}},
                }
            ]
        },
    }
    assert DOGFOOD.iter_records(write_transcript(tmp_path, [valid, invalid])) == (
        [valid],
        1,
    )


def test_dogfood_iter_records_accepts_official_codex_lifecycle_envelopes(
    tmp_path: Path,
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "thread"},
        {"type": "turn.started"},
        {"type": "turn.completed", "usage": codex_usage()},
        {"type": "turn.failed", "error": {"message": "failed"}},
        {
            "type": "item.completed",
            "item": {"id": "message", "type": "agent_message", "text": "done"},
        },
        {
            "type": "item.completed",
            "item": {"id": "reasoning", "type": "reasoning", "text": "summary"},
        },
        {
            "type": "item.started",
            "item": {
                "id": "todo",
                "type": "todo_list",
                "items": [{"text": "inspect", "completed": False}],
            },
        },
        {
            "type": "item.updated",
            "item": {
                "id": "todo",
                "type": "todo_list",
                "items": [{"text": "inspect", "completed": True}],
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "todo",
                "type": "todo_list",
                "items": [{"text": "inspect", "completed": True}],
            },
        },
        {
            "type": "item.completed",
            "item": {"id": "warning", "type": "error", "message": "warning"},
        },
        {"type": "error", "message": "fatal"},
    ]
    assert DOGFOOD.iter_records(write_transcript(tmp_path, records)) == (records, 0)


@pytest.mark.parametrize(
    "item",
    [
        {
            "id": "command",
            "type": "command_execution",
            "command": "true",
            "aggregated_output": "",
            "exit_code": None,
            "status": "in_progress",
        },
        {
            "id": "change",
            "type": "file_change",
            "changes": [{"path": "/repo/a.py", "kind": "update"}],
            "status": "in_progress",
        },
        {
            "id": "mcp",
            "type": "mcp_tool_call",
            "server": "docs",
            "tool": "read",
            "arguments": {"uri": "doc://item"},
            "result": None,
            "error": None,
            "status": "in_progress",
        },
        {
            "id": "collab",
            "type": "collab_tool_call",
            "tool": "wait",
            "sender_thread_id": "root",
            "receiver_thread_ids": [],
            "prompt": None,
            "agents_states": {},
            "status": "in_progress",
        },
    ],
)
def test_dogfood_reconciled_in_progress_item_is_open_not_terminal(
    item: dict,
    tmp_path: Path,
) -> None:
    record = {"type": "item.completed", "item": item}
    assert DOGFOOD.iter_records(write_transcript(tmp_path, [record])) == (
        [record],
        0,
    )
    (event,) = DOGFOOD.codex_tool_events([record])
    assert event["outcome"] == "unresolved"
    assert event["succeeded"] is False
    assert len(DOGFOOD.unpaired_tool_calls([record])) == 1
    assert DOGFOOD.ended_mid_tool([record]) is True


def test_dogfood_reconciled_in_progress_item_does_not_close_an_existing_start() -> None:
    item = {
        "id": "command",
        "type": "command_execution",
        "command": "true",
        "aggregated_output": "",
        "exit_code": None,
        "status": "in_progress",
    }
    records = [
        {"type": "item.started", "item": item},
        {"type": "item.completed", "item": item},
    ]
    (event,) = DOGFOOD.codex_tool_events(records)
    assert event["outcome"] == "unresolved"
    assert DOGFOOD.unpaired_tool_calls(records) == {"codex:command:0": 0}
    assert DOGFOOD.ended_mid_tool(records) is True


@pytest.mark.parametrize(
    "invalid",
    [
        {"type": "thread.started"},
        {"type": "thread.started", "thread_id": 7},
        {"type": "turn.completed"},
        {"type": "turn.completed", "usage": []},
        {"type": "turn.failed"},
        {"type": "turn.failed", "error": {"message": 7}},
        {"type": "item.started"},
        {"type": "item.updated", "item": []},
        {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "missing id"},
        },
        {
            "type": "item.completed",
            "item": {"id": 7, "type": "agent_message", "text": "wrong id"},
        },
        {"type": "error"},
        {"type": "error", "message": 7},
        {"type": "turn.unknown"},
        {
            "type": "item.completed",
            "item": {"id": "unknown", "type": "unknown_item"},
        },
        {
            "type": "item.unknown",
            "item": {"id": "message", "type": "agent_message", "text": "done"},
        },
    ],
)
def test_dogfood_iter_records_rejects_invalid_codex_lifecycle_envelopes(
    invalid: dict,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started"}
    transcript = write_transcript(tmp_path, [valid, invalid])
    assert DOGFOOD.iter_records(transcript) == ([valid], 1)


def test_dogfood_iter_records_rejects_duplicate_json_keys(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "duplicate-keys.jsonl"
    transcript.write_text(
        '{"type":"turn.started"}\n'
        '{"type":"item.completed","item":{"id":"command",'
        '"type":"command_execution","command":"true",'
        '"aggregated_output":"","status":"failed","exit_code":1,'
        '"status":"completed","exit_code":0}}\n',
        encoding="utf-8",
    )
    assert DOGFOOD.iter_records(transcript) == ([{"type": "turn.started"}], 1)


@pytest.mark.parametrize(
    "item",
    [
        {"id": "message", "type": "agent_message"},
        {"id": "message", "type": "agent_message", "text": 7},
        {"id": "reasoning", "type": "reasoning"},
        {"id": "reasoning", "type": "reasoning", "text": 7},
        {"id": "todo", "type": "todo_list"},
        {"id": "todo", "type": "todo_list", "items": {}},
        {"id": "todo", "type": "todo_list", "items": ["inspect"]},
        {
            "id": "todo",
            "type": "todo_list",
            "items": [{"completed": False}],
        },
        {
            "id": "todo",
            "type": "todo_list",
            "items": [{"text": 7, "completed": False}],
        },
        {
            "id": "todo",
            "type": "todo_list",
            "items": [{"text": "inspect"}],
        },
        {
            "id": "todo",
            "type": "todo_list",
            "items": [{"text": "inspect", "completed": 1}],
        },
        {"id": "warning", "type": "error"},
        {"id": "warning", "type": "error", "message": 7},
    ],
)
def test_dogfood_iter_records_rejects_invalid_codex_text_and_todo_items(
    item: dict,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started"}
    invalid = {"type": "item.completed", "item": item}
    assert DOGFOOD.iter_records(write_transcript(tmp_path, [valid, invalid])) == (
        [valid],
        1,
    )


@pytest.mark.parametrize("bound", [-(1 << 63), (1 << 63) - 1])
def test_dogfood_iter_records_accepts_rust_i64_usage_bounds(
    bound: int,
    tmp_path: Path,
) -> None:
    with_optional = {
        "type": "turn.completed",
        "usage": codex_usage(
            input_tokens=bound,
            cached_input_tokens=bound,
            cache_write_input_tokens=bound,
            output_tokens=bound,
            reasoning_output_tokens=bound,
        ),
    }
    without_optional = {"type": "turn.completed", "usage": codex_usage()}
    records = [with_optional, without_optional]
    assert DOGFOOD.iter_records(write_transcript(tmp_path, records)) == (records, 0)


@pytest.mark.parametrize("invalid", [-(1 << 63) - 1, 1 << 63, True, 1.0])
def test_dogfood_iter_records_rejects_values_outside_rust_i64_usage(
    invalid: object,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started"}
    invalid_record = {
        "type": "turn.completed",
        "usage": codex_usage(input_tokens=invalid),
    }
    assert DOGFOOD.iter_records(
        write_transcript(tmp_path, [valid, invalid_record])
    ) == ([valid], 1)


@pytest.mark.parametrize(
    "missing",
    [
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    ],
)
def test_dogfood_iter_records_requires_official_codex_usage_fields(
    missing: str,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started"}
    usage = codex_usage()
    del usage[missing]
    invalid = {"type": "turn.completed", "usage": usage}
    assert DOGFOOD.iter_records(write_transcript(tmp_path, [valid, invalid])) == (
        [valid],
        1,
    )


@pytest.mark.parametrize("record_type", ["item.started", "item.completed"])
@pytest.mark.parametrize("item_id", [None, "", 7])
def test_dogfood_iter_records_rejects_invalid_codex_tool_ids(
    record_type: str,
    item_id: object,
    tmp_path: Path,
) -> None:
    valid = {"type": "turn.started", "thread_id": "valid"}
    invalid = {
        "type": record_type,
        "item": {
            "type": "command_execution",
            "command": "true",
            "aggregated_output": "",
            "exit_code": None if record_type == "item.started" else 0,
            "status": "in_progress" if record_type == "item.started" else "completed",
        },
    }
    if item_id is not None:
        invalid["item"]["id"] = item_id
    transcript = write_transcript(tmp_path, [valid, invalid])
    assert DOGFOOD.iter_records(transcript) == ([valid], 1)


def test_dogfood_invalid_utf8_json_and_schema_suppress_positive_digest_claims(
    tmp_path: Path,
) -> None:
    valid_records = claude_call(
        "edit",
        "Edit",
        {"file_path": "/repo/a.py"},
        "updated",
    )
    valid_records[0]["message"]["model"] = "provider-model"
    transcript = tmp_path / "incomplete.jsonl"
    payload = b"".join(
        json.dumps(record).encode("utf-8") + b"\n" for record in valid_records
    )
    transcript.write_bytes(
        payload
        + b"\xff\n"
        + b"{broken json\n"
        + json.dumps({"type": "user", "message": []}).encode("utf-8")
        + b"\n"
    )
    data = DOGFOOD.digest(transcript, 100)
    assert data["unparseable_lines"] == 3
    assert data["plugin_version_values_observed"] == [
        "unverified_incomplete_transcript"
    ]
    assert data["skill_body_injections"] == "unverified"
    assert data["skills"] == []
    assert data["command_results"] == {}
    assert data["successful_structured_delegations"] == []
    assert data["successful_structured_write_actions"] == []
    assert data["confounders"] == {
        "compaction_observed": "unknown",
        "legacy_reports_observed": 0,
        "trailing_unresolved_tool_call": "unknown",
        "unpaired_tool_call_count": "unknown",
        "turn_sequence": "unverified_incomplete_transcript",
        "plugin_version_identity": "unverified_incomplete_transcript",
        "contract_sequence": "unverified_incomplete_transcript",
    }
    assert data["report"]["selection_status"] == "unverified_incomplete_transcript"
    assert data["report"]["legacy_contract_scoring"] == (
        "unverified_incomplete_transcript"
    )
    assert data["report"]["headings_not_observed"] == (
        "unverified_incomplete_transcript"
    )
    rendered = DOGFOOD.render_digest(data)
    assert "SKILLS\n  UNVERIFIED: incomplete transcript" in rendered
    assert "OBSERVED SUCCESSFUL STRUCTURED DELEGATIONS (UNVERIFIED)" in rendered
    assert "OBSERVED SUCCESSFUL STRUCTURED WRITE ACTIONS (UNVERIFIED)" in rendered
    assert rendered.count(
        "UNVERIFIED: incomplete transcript; absence cannot be established"
    ) == 3


def test_dogfood_incomplete_transcript_suppresses_a_concrete_plugin_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "# SkipHow\n\nExact owner body."
    base = str(
        host_cache_root(DOGFOOD.claude_home()) / "2.0.0/skills/skiphow"
    )
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    monkeypatch.setattr(
        DOGFOOD, "version_reference_names", lambda _version: {"testing"}
    )
    records = claude_call(
        "skill-owner",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-owner-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": f"Base directory for this skill: {base}\n{body}"
            },
        }
    )
    assert DOGFOOD.skill_injection_observations(records)["skill-owner"][
        "version"
    ] == "2.0.0"
    transcript = tmp_path / "incomplete-version.jsonl"
    transcript.write_bytes(
        b"".join(
            json.dumps(record).encode("utf-8") + b"\n" for record in records
        )
        + b"{broken json\n"
    )
    data = DOGFOOD.digest(transcript, 100)
    assert data["unparseable_lines"] == 1
    assert data["plugin_version_values_observed"] == [
        "unverified_incomplete_transcript"
    ]
    assert data["skill_body_injections"] == "unverified"
    assert data["skills"] == []
    assert data["references"]["testing"] == {
        "verdict": "unverified_unparseable_transcript",
        "basis": "contract_sequence_incomplete",
        "matching_line_values": "unavailable",
        "artifact_source": "not_evaluated",
        "actions": ["not_evaluated"],
        "mismatched_path_versions": [],
    }
    assert data["confounders"]["plugin_version_identity"] == (
        "unverified_incomplete_transcript"
    )
    assert data["confounders"]["contract_sequence"] == (
        "unverified_incomplete_transcript"
    )
    assert "2.0.0" not in json.dumps(data, sort_keys=True)


def test_dogfood_legacy_report_selection_applies_only_to_1_1_through_1_13() -> None:
    records = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Result\nlegacy\nEvidence\nold proof"}
                ]
            },
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "current final"}]},
        },
    ]
    legacy = "Result\nlegacy\nEvidence\nold proof"
    assert DOGFOOD.report_text(records, ["1.0.9"]) == "current final"
    assert DOGFOOD.report_text(records, ["1.1.0"]) == legacy
    assert DOGFOOD.report_text(records, ["1.13.9"]) == legacy
    assert DOGFOOD.report_text(records, ["1.14.0"]) == "current final"
    assert DOGFOOD.report_text(records, ["2.0.0"]) == "current final"
    assert DOGFOOD.report_text(records, ["unknown"]) == "current final"


def test_dogfood_observes_only_an_exact_complete_skiphow_skill_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = (
        "---\nname: skiphow\ndescription: Own the project request.\n---\n"
        "# SkipHow\n\nFinish the authorized result.\n"
    )
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    base = str(
        host_cache_root(DOGFOOD.claude_home()) / "2.0.0/skills/skiphow"
    )

    def observed_records(tool_id: str, observed_body: str) -> list[dict]:
        records = claude_call(
            tool_id,
            "Skill",
            {"skill": "skiphow:skiphow"},
            "Skill loaded",
        )
        records[0]["uuid"] = f"{tool_id}-call"
        records[1]["uuid"] = f"{tool_id}-result"
        records[1]["parentUuid"] = f"{tool_id}-call"
        records[1]["sourceToolAssistantUUID"] = f"{tool_id}-call"
        records.append(
            {
                "type": "user",
                "uuid": f"{tool_id}-injection",
                "parentUuid": f"{tool_id}-result",
                "userType": "external",
                "isMeta": True,
                "sourceToolUseID": tool_id,
                "message": {
                    "content": (
                        f"Base directory for this skill: {base}\n{observed_body}"
                    )
                },
            }
        )
        return records

    exact = observed_records("exact-skill", body)
    assert DOGFOOD.successful_skill_result_ids(exact) == {"exact-skill"}
    assert DOGFOOD.skill_injection_observations(exact) == {
        "exact-skill": {
            "status": "body_observed",
            "name": "skiphow",
            "text": f"Base directory for this skill: {base}\n{body}",
            "source": "plugin",
            "version": "2.0.0",
            "artifact_source": "tag",
            "attribution": "explicit_skill_call",
            "at": "",
        }
    }

    suffixed = observed_records("suffixed-skill", f"{body}\nextra suffix")
    assert DOGFOOD.skill_injection_observations(suffixed)["suffixed-skill"][
        "status"
    ] == "body_unverified"

    arguments_wrapper = observed_records(
        "arguments-wrapper", f"{body}\n\n\n\nARGUMENTS: owner request"
    )
    assert DOGFOOD.skill_injection_observations(arguments_wrapper)[
        "arguments-wrapper"
    ]["status"] == "body_observed"


@pytest.mark.parametrize(
    ("artifact_eol", "injection_eol"),
    [("\n", "\r\n"), ("\r\n", "\n")],
)
def test_dogfood_skill_body_treats_lf_and_crlf_as_equivalent(
    artifact_eol: str,
    injection_eol: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = (
        "---",
        "name: skiphow",
        "description: Exact.",
        "---",
        "# SkipHow",
        "",
        "Finish.",
    )
    artifact = artifact_eol.join(lines) + artifact_eol
    observed = injection_eol.join(lines) + injection_eol
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (artifact, "tag"),
    )
    base = host_cache_root(DOGFOOD.claude_home()) / "2.0.0/skills/skiphow"
    records = claude_call(
        "skill-owner",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-owner-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": (
                    f"Base directory for this skill: {base}"
                    f"{injection_eol}{observed}"
                )
            },
        }
    )
    assert DOGFOOD.skill_injection_observations(records)["skill-owner"][
        "status"
    ] == "body_observed"


def test_dogfood_skill_body_does_not_normalize_lone_carriage_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = ("# SkipHow", "", "Finish.")
    artifact = "\n".join(lines) + "\n"
    observed = "\r".join(lines) + "\r"
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (artifact, "tag"),
    )
    base = host_cache_root(DOGFOOD.claude_home()) / "2.0.0/skills/skiphow"
    records = claude_call(
        "skill-owner",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-owner-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": f"Base directory for this skill: {base}\n{observed}"
            },
        }
    )
    assert DOGFOOD.skill_injection_observations(records)["skill-owner"][
        "status"
    ] == "body_unverified"


def test_dogfood_skill_body_requires_explicit_skiphow_and_a_matching_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "# SkipHow\n\nExact root body."
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    cache = host_cache_root(DOGFOOD.claude_home())

    def records_for(invoked: str, base_name: str, tool_id: str) -> list[dict]:
        records = claude_call(tool_id, "Skill", {"skill": invoked}, "Skill loaded")
        records[0]["uuid"] = f"{tool_id}-call"
        records[1]["uuid"] = f"{tool_id}-result"
        records[1]["parentUuid"] = f"{tool_id}-call"
        records[1]["sourceToolAssistantUUID"] = f"{tool_id}-call"
        records.append(
            {
                "type": "user",
                "uuid": f"{tool_id}-injection",
                "parentUuid": f"{tool_id}-result",
                "userType": "external",
                "isMeta": True,
                "sourceToolUseID": tool_id,
                "message": {
                    "content": (
                        "Base directory for this skill: "
                        f"{cache}/2.0.0/skills/{base_name}\n{body}"
                    )
                },
            }
        )
        return records

    different_skill = records_for(
        "skiphow:research", "skiphow", "different-skill"
    )
    assert DOGFOOD.successful_skill_result_ids(different_skill) == {
        "different-skill"
    }
    assert DOGFOOD.skill_injection_observations(different_skill) == {
        "different-skill": {
            "status": "activation_path_mismatch",
            "attribution": "explicit_skill_call",
            "at": "",
        }
    }

    unattributed = records_for("research", "research", "unattributed")
    assert DOGFOOD.successful_skill_result_ids(unattributed) == set()
    assert DOGFOOD.skill_injection_observations(unattributed) == {}

    different_base = records_for(
        "skiphow:skiphow", "testing", "different-base"
    )
    assert DOGFOOD.successful_skill_result_ids(different_base) == {"different-base"}
    assert DOGFOOD.skill_injection_observations(different_base) == {
        "different-base": {
            "status": "activation_path_mismatch",
            "attribution": "explicit_skill_call",
            "at": "",
        }
    }


@pytest.mark.parametrize(
    "base",
    [
        "/skills/skiphow",
        "/skills/skiphow/SKILL.md",
        "/cache/skiphow/skiphow/2.0.0/skills/skiphow",
        "/cache/skiphow/skiphow/2.0.0/skills/skiphow/SKILL.md",
        "docs/plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow",
        "/cache/skiphow/skiphow/2.0.0/skills/skiphow/references/testing.md",
        "/project/.agents/skills/skiphow",
        (
            "plugins/skiphow/skills/container/.claude/plugins/cache/skiphow/"
            "skiphow/2.0.0/skills/skiphow"
        ),
        str(
            DOGFOOD.repository_root()
            / "plugins/skiphow/skills/container/.claude/plugins/cache/skiphow/"
            "skiphow/2.0.0/skills/skiphow"
        ),
        (
            "/tmp/.codex/plugins/cache/skiphow/skiphow/9.9.9/skills/container/"
            ".claude/plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow"
        ),
        "plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow",
    ],
)
def test_dogfood_skill_injection_rejects_a_non_plugin_root_base(
    base: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "# SkipHow\n\nExact root body."
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    records = claude_call(
        "skill-owner", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
    )
    records[0]["uuid"] = "skill-call"
    records[1]["uuid"] = "skill-result"
    records[1]["parentUuid"] = "skill-call"
    records[1]["sourceToolAssistantUUID"] = "skill-call"
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-result",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": f"Base directory for this skill: {base}\n{body}"
            },
        }
    )
    assert DOGFOOD.skill_injection_observations(records) == {
        "skill-owner": {
            "status": "activation_path_mismatch",
            "attribution": "explicit_skill_call",
            "at": "",
        }
    }


@pytest.mark.parametrize(
    "base",
    [
        str(
            DOGFOOD.claude_home()
            / "plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow"
        ),
        str(
            DOGFOOD.codex_home()
            / "plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow"
        ),
        r"C:\Users\person\.claude\plugins\cache\skiphow\skiphow\2.0.0\skills\skiphow",
    ],
)
def test_dogfood_skill_injection_accepts_exact_plugin_cache_roots(
    base: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "# SkipHow\n\nExact root body."
    seen_calls: list[tuple[str, str, str]] = []

    def root(version: str, name: str, observed_root: str) -> tuple[str, str]:
        seen_calls.append((version, name, observed_root))
        return body, "tag"

    monkeypatch.setattr(DOGFOOD, "package_skill", root)
    records = claude_call(
        "skill-owner", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
    )
    records[0]["uuid"] = "skill-call"
    records[1]["uuid"] = "skill-result"
    records[1]["parentUuid"] = "skill-call"
    records[1]["sourceToolAssistantUUID"] = "skill-call"
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-result",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": f"Base directory for this skill: {base}\n{body}"
            },
        }
    )
    assert DOGFOOD.skill_injection_observations(records)["skill-owner"][
        "status"
    ] == "body_observed"
    rooted = DOGFOOD.recognized_path_root(base)
    assert rooted is not None
    assert seen_calls == [("2.0.0", "skiphow", rooted[3])]


@pytest.mark.parametrize(
    "token",
    [
        "https://example.test/.agents/skills/testing/SKILL.md",
        "`/repo/.agents/skills/testing/SKILL.md`",
        "$HOME/.agents/skills/testing/SKILL.md",
        "<project>/.agents/skills/testing/SKILL.md",
        "docs/plugins/cache/skiphow/skiphow/2.0.0/skills/testing/SKILL.md",
        "See /repo/.agents/skills/testing/SKILL.md",
        "$PROJECT/.agents/skills/testing/SKILL.md",
        "/repo/.agents/skills/testing/SKILL.md/child",
        "/repo/.agents/skills/testing/references/nested.md",
        "/repo/.agents/skills/outer/.agents/skills/testing/SKILL.md",
    ],
)
def test_dogfood_rejects_documentation_tokens_and_nested_skill_roots(token: str) -> None:
    assert DOGFOOD.skill_paths(token, require_file=True) == []


@pytest.mark.parametrize(
    "token",
    [
        "https://example.test/.agents/skills/skiphow/references/testing.md",
        "`/repo/.agents/skills/skiphow/references/testing.md`",
        "$HOME/.agents/skills/skiphow/references/testing.md",
        "<project>/.agents/skills/skiphow/references/testing.md",
        (
            "docs/plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow/"
            "references/testing.md"
        ),
        "See /repo/.agents/skills/skiphow/references/testing.md",
        "$PROJECT/.agents/skills/skiphow/references/testing.md",
        "/repo/.agents/skills/skiphow/references/testing.md/child",
        "/repo/.agents/skills/not-skiphow/references/testing.md",
        (
            "/repo/.agents/skills/skiphow/references/archive/.agents/skills/"
            "skiphow/references/testing.md"
        ),
    ],
)
def test_dogfood_rejects_documentation_tokens_and_nested_reference_roots(
    token: str,
) -> None:
    assert DOGFOOD.reference_name_from_path(token) is None


def test_dogfood_accepts_exact_paths_whose_parent_directories_have_spaces() -> None:
    skill = "/Project With Spaces/.agents/skills/testing/SKILL.md"
    reference = (
        "/Project With Spaces/.agents/skills/skiphow/references/testing.md"
    )
    assert DOGFOOD.skill_paths(skill, require_file=True) == [
        {
            "name": "testing",
            "source": "project",
            "version": "unknown",
            "_root": "/Project With Spaces/.agents/skills",
            "_needle": skill,
        }
    ]
    assert DOGFOOD.reference_name_from_path(reference) == "testing"
    evidence = DOGFOOD.detect_references(
        Path("unused"),
        claude_call("read-testing", "Read", {"file_path": reference}),
        "unknown",
    )
    assert evidence["testing"]["verdict"] == "read_action_observed"


def test_dogfood_project_reference_path_is_a_discovery_marker(tmp_path: Path) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/session.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "cwd": "/external/project",
                "message": {
                    "content": (
                        "Inspect .agents/skills/skiphow/references/testing.md"
                    )
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert DOGFOOD.contains_marker(transcript) is True
    assert [row["session"] for row in DOGFOOD.discover(home, None)] == ["session"]


def test_dogfood_claude_config_dir_is_the_discovery_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured = tmp_path / "configured-claude"
    legacy = tmp_path / "legacy-claude"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(configured))
    monkeypatch.setenv("CLAUDE_HOME", str(legacy))
    transcript = configured / "projects/project/config-session.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "cwd": "/work/customer-app",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert DOGFOOD.claude_home() == configured
    assert [
        row["session"] for row in DOGFOOD.discover(DOGFOOD.claude_home(), None)
    ] == ["config-session"]


def test_dogfood_cli_home_also_binds_activation_cache_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    custom_home = tmp_path / "custom-claude"
    unrelated_home = tmp_path / "configured-elsewhere"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(unrelated_home))
    body = "# SkipHow\n\nExact custom-home body.\n"
    base = host_cache_root(custom_home) / "2.0.0/skills/skiphow"
    base.mkdir(parents=True)
    (base / "SKILL.md").write_text(body, encoding="utf-8")
    records = claude_call(
        "skill-owner",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-owner-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": f"Base directory for this skill: {base}\n{body}"
            },
        }
    )
    transcript = custom_home / "projects/project/custom-home-session.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sessions.py",
            "--home",
            str(custom_home),
            "digest",
            "custom-home-session",
            "--json",
        ],
    )
    DOGFOOD.main()
    data = json.loads(capsys.readouterr().out)
    assert data["plugin_version_values_observed"] == ["2.0.0"]
    assert data["skill_body_injections"] == 1
    assert data["skills"] == [
        {
            "name": "skiphow",
            "source": "plugin",
            "version": "2.0.0",
            "signals": {"activated": 1, "body_observed": 1},
        }
    ]


def test_dogfood_explicit_path_outside_home_retains_both_host_cache_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    selected_home = tmp_path / "selected-home"
    claude_home = tmp_path / "claude-home"
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_home))
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    body = "# SkipHow\n\nExact Codex-cache body.\n"
    base = host_cache_root(codex_home) / "2.0.0/skills/skiphow"
    base.mkdir(parents=True)
    (base / "SKILL.md").write_text(body, encoding="utf-8")
    records = claude_call(
        "skill-owner",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-owner-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-owner",
            "message": {
                "content": f"Base directory for this skill: {base}\n{body}"
            },
        }
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    transcript = write_transcript(outside, records, "explicit-session")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sessions.py",
            "--home",
            str(selected_home),
            "digest",
            str(transcript),
            "--json",
        ],
    )
    DOGFOOD.main()
    data = json.loads(capsys.readouterr().out)
    assert data["plugin_version_values_observed"] == ["2.0.0"]
    assert data["skill_body_injections"] == 1


def test_dogfood_coverage_requires_anchored_unfenced_exact_count_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    (research / "receipts.md").write_text(
        "\n".join(
            [
                "# Receipts",
                "Negated prose: Audited `deadbeef-session` · 3 records · plugin 2.0.0 · fake",
                "```text",
                "Audited `deadbeef-session` · 3 records · plugin 2.0.0 · fenced fake",
                "```",
                "Audited `facefeed-session` · 3 records · plugin unknown · exact receipt",
                "Audited `cafebabe-session` · 2 records · plugin 1.14.2,2.0.0 · stale receipt",
                "Audited `mixed-unknown-session` · 4 records · plugin unknown,2.0.0 · partial identity",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    receipts = DOGFOOD.audit_receipts(
        (research / "receipts.md").read_text(encoding="utf-8")
    )
    assert receipts == [
        ("facefeed-session", 3, frozenset({"unknown"})),
        ("cafebabe-session", 2, frozenset({"1.14.2", "2.0.0"})),
        ("mixed-unknown-session", 4, frozenset({"unknown", "2.0.0"})),
    ]
    rows = [
        {
            "session": "deadbeef-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "deadbeef-session",
            "excluded": None,
            "records": 3,
            "unreadable_lines": 0,
            "versions": ["2.0.0"],
        },
        {
            "session": "facefeed-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "facefeed-session",
            "excluded": None,
            "records": 3,
            "unreadable_lines": 0,
            "versions": ["unknown"],
        },
        {
            "session": "cafebabe-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "cafebabe-session",
            "excluded": None,
            "records": 3,
            "unreadable_lines": 0,
            "versions": ["2.0.0", "1.14.2"],
        },
    ]
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(DOGFOOD, "discover", lambda _home, _since: rows)
    output = DOGFOOD.coverage(tmp_path / "home")
    lines = output.splitlines()
    assert next(line for line in lines if "deadbeef" in line).endswith("UNAUDITED")
    assert next(line for line in lines if "facefeed" in line).endswith("covered")
    assert next(line for line in lines if "cafebabe" in line).endswith("STALE")


def test_dogfood_coverage_matches_current_plugin_identity_order_insensitively(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    (research / "receipts.md").write_text(
        "\n".join(
            [
                "Audited `mixed-version-session` · 1195 records · plugin 1.7.0 · historical receipt",
                "Audited `mixed-version-session` · 4868 records · plugin 1.7.0,1.10.0 · current receipt",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = [
        {
            "session": "mixed-version-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "mixed-versions",
            "excluded": None,
            "records": 4868,
            "unreadable_lines": 0,
            "versions": ["1.10.0", "1.7.0"],
        }
    ]
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(DOGFOOD, "discover", lambda _home, _since: rows)
    output = DOGFOOD.coverage(tmp_path / "home")
    assert output.splitlines()[-1].endswith("covered")


@pytest.mark.parametrize(
    "unknown_source",
    ["successful_skill_without_injection", "unattributed_project_body"],
)
def test_dogfood_contract_identity_is_canonical_for_digest_discovery_and_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unknown_source: str,
) -> None:
    home = tmp_path / "claude-home"
    cache = host_cache_root(home)
    body = "# SkipHow\n\nExact installed body.\n"
    installed = cache / "2.0.0/skills/skiphow"
    installed.mkdir(parents=True)
    (installed / "SKILL.md").write_text(body, encoding="utf-8")

    records = [
        {
            "type": "user",
            "timestamp": "2026-08-27T09:00:00Z",
            "cwd": "/work/customer-app",
            "origin": {"kind": "human"},
            "message": {"content": "Use skiphow:skiphow"},
        }
    ]
    records += claude_call(
        "known-skill", "Skill", {"skill": "skiphow:skiphow"}, "loaded"
    )
    records.append(
        {
            "type": "user",
            "uuid": "known-skill-injection",
            "parentUuid": "known-skill-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "known-skill",
            "message": {
                "content": f"Base directory for this skill: {installed}\n{body}"
            },
        }
    )
    if unknown_source == "successful_skill_without_injection":
        records += claude_call(
            "unlinked-skill", "Skill", {"skill": "skiphow:skiphow"}, "loaded"
        )
    else:
        records.append(
            {
                "type": "user",
                "uuid": "project-skill-injection",
                "userType": "external",
                "isMeta": True,
                "message": {
                    "content": (
                        "Base directory for this skill: .agents/skills/skiphow\n"
                        "# Project-local SkipHow"
                    )
                },
            }
        )

    transcript = home / "projects/project/canonical-identity-session.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    data = DOGFOOD.digest(transcript, 100, home)
    assert data["plugin_version_values_observed"] == ["2.0.0", "unknown"]
    assert data["confounders"]["plugin_version_identity"] == "partially_unknown"
    (row,) = DOGFOOD.discover(home, None)
    assert row["versions"] == ["2.0.0", "unknown"]

    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    (research / "receipt.md").write_text(
        "Audited `canonical-identity-session` · "
        f"{len(records)} records · plugin unknown,2.0.0 · exact identity\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    assert DOGFOOD.coverage(home).splitlines()[-1].endswith("covered")


def test_dogfood_coverage_supports_full_ids_and_flags_ambiguous_prefixes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    (research / "receipts.md").write_text(
        "\n".join(
            [
                "Audited `badc0ffe-session` · 3 records · plugin 2.0.0 · exact receipt",
                "Audited `deadbeef` · 3 records · plugin 2.0.0 · ambiguous prefix",
                "Audited `facefeed-session` · 3 records · plugin 2.0.0 · exact full id",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = [
        {
            "session": "badc0ffe-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "unreadable",
            "excluded": None,
            "records": 3,
            "unreadable_lines": 1,
            "versions": ["unverified_incomplete_transcript"],
        },
        {
            "session": "facefeed-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "exact-full-id",
            "excluded": None,
            "records": 3,
            "unreadable_lines": 0,
            "versions": ["2.0.0"],
        },
        *[
            {
                "session": session,
                "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
                "project": project,
                "excluded": None,
                "records": 3,
                "unreadable_lines": 0,
                "versions": ["2.0.0"],
            }
            for session, project in (
                ("deadbeef-first", "first"),
                ("deadbeef-second", "second"),
            )
        ],
    ]
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(DOGFOOD, "discover", lambda _home, _since: rows)
    output = DOGFOOD.coverage(tmp_path / "home")
    lines = output.splitlines()
    assert next(line for line in lines if "badc0ffe" in line).endswith(
        "UNVERIFIED_UNREADABLE"
    )
    assert next(line for line in lines if "facefeed" in line).endswith("covered")
    duplicate_lines = [line for line in lines if "deadbeef" in line]
    assert len(duplicate_lines) == 2
    assert all(line.endswith("AMBIGUOUS_PREFIX") for line in duplicate_lines)


def test_dogfood_coverage_matches_unique_eight_hex_prefix_receipts_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    (research / "receipts.md").write_text(
        "\n".join(
            [
                "Audited `a1b2c3d4` · 4868 records · plugin 1.7.0,1.10.0 · exact short receipt",
                "Audited `c0ffee00` · 1195 records · plugin 1.7.0 · stale count",
                "Audited `f00dbabe` · 4868 records · plugin 1.7.0 · stale identity",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = [
        {
            "session": session,
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": project,
            "excluded": None,
            "records": 4868,
            "unreadable_lines": 0,
            "versions": versions,
        }
        for session, project, versions in (
            ("a1b2c3d4-full-session", "covered", ["1.10.0", "1.7.0"]),
            ("c0ffee00-full-session", "stale-count", ["1.7.0"]),
            (
                "f00dbabe-full-session",
                "stale-identity",
                ["1.10.0", "1.7.0"],
            ),
        )
    ]
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(DOGFOOD, "discover", lambda _home, _since: rows)
    output = DOGFOOD.coverage(tmp_path / "home")
    lines = output.splitlines()
    assert next(line for line in lines if "a1b2c3d4" in line).endswith("covered")
    assert next(line for line in lines if "c0ffee00" in line).endswith("STALE")
    assert next(line for line in lines if "f00dbabe" in line).endswith("STALE")


@pytest.mark.parametrize(
    "payload",
    [
        (
            b'{"type":"user","timestamp":"2026-08-27T10:00:00Z",'
            b'"cwd":"/work/customer-app","attributionPlugin" :  "skiphow"}\n'
        ),
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "cwd": "/work/customer-app",
                "message": {
                    "content": (
                        r"C:\Users\person\.agents\skills\skiphow\references\testing.md"
                    )
                },
            }
        ).encode("utf-8")
        + b"\n",
    ],
)
def test_dogfood_marker_scanner_accepts_json_spacing_and_escaped_windows_paths(
    payload: bytes,
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/marker-session.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_bytes(payload)
    assert DOGFOOD.contains_marker(transcript) is True
    assert [row["session"] for row in DOGFOOD.discover(home, None)] == [
        "marker-session"
    ]


def test_dogfood_since_keeps_a_candidate_with_an_unreadable_marker_line(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/broken-marker.jsonl"
    transcript.parent.mkdir(parents=True)
    valid = {
        "type": "user",
        "timestamp": "2026-08-20T12:00:00Z",
        "cwd": "/work/customer-app",
        "origin": {"kind": "human"},
        "message": {"content": "ordinary old prompt"},
    }
    transcript.write_bytes(
        json.dumps(valid).encode("utf-8")
        + b"\n"
        + b'{"timestamp":"2026-08-20T13:00:00Z","skill":"skiphow:skiphow"\n'
    )
    (row,) = DOGFOOD.discover(home, "2026-08-25")
    assert row["session"] == "broken-marker"
    assert row["started"] == "2026-08-20T12:00:00Z"
    assert row["candidate_marker_window"] == ["unknown", "unknown"]
    assert row["candidate_marker_local_dates"] == ["unknown", "unknown"]
    assert row["candidate_marker_date_status"] == (
        "unverified_incomplete_transcript"
    )
    assert row["records"] == 1
    assert row["unreadable_lines"] == 1
    assert row["versions"] == ["unverified_incomplete_transcript"]
    assert row["excluded"] is None


def test_dogfood_list_text_and_json_apply_the_same_all_filter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    marker = "skiphow:skiphow"
    for session, cwd in (
        ("external-session", "/work/customer-app"),
        ("selfdev-session", str(DOGFOOD.repository_root())),
    ):
        (project / f"{session}.jsonl").write_text(
            json.dumps(
                {
                    "type": "user",
                    "timestamp": "2026-08-27T10:00:00Z",
                    "cwd": cwd,
                    "message": {"content": marker},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def run(*arguments: str) -> str:
        monkeypatch.setattr(
            sys,
            "argv",
            ["sessions.py", "--home", str(home), "list", *arguments],
        )
        DOGFOOD.main()
        return capsys.readouterr().out

    default_text = run()
    default_json = json.loads(run("--json"))
    all_text = run("--all")
    all_json = json.loads(run("--all", "--json"))
    assert "external" in default_text
    assert "selfdev-" not in default_text
    assert [row["session"] for row in default_json] == ["external-session"]
    assert "external" in all_text
    assert "selfdev-" in all_text
    assert {row["session"] for row in all_json} == {
        "external-session",
        "selfdev-session",
    }
    selfdev = next(row for row in all_json if row["session"] == "selfdev-session")
    assert selfdev["excluded"] == "self-development"


def test_dogfood_discover_filters_by_marker_date_not_chat_start(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    marker = "Inspect .agents/skills/skiphow/references/testing.md"

    def write_session(name: str, records: list[dict]) -> None:
        (project / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(record) for record in records) + "\n",
            encoding="utf-8",
        )

    write_session(
        "old-chat-new-marker",
        [
            {
                "type": "user",
                "timestamp": "2026-08-20T12:00:00Z",
                "cwd": "/work/customer-app",
                "origin": {"kind": "human"},
                "message": {"content": "ordinary old prompt"},
            },
            {
                "type": "user",
                "timestamp": "2026-08-30T12:00:00Z",
                "cwd": "/work/customer-app",
                "message": {"content": marker},
            },
        ],
    )
    write_session(
        "new-chat-old-marker",
        [
            {
                "type": "user",
                "timestamp": "2026-08-20T12:00:00Z",
                "cwd": "/work/customer-app",
                "message": {"content": marker},
            },
            {
                "type": "assistant",
                "timestamp": "2026-08-30T12:00:00Z",
                "cwd": "/work/customer-app",
                "message": {"content": "later unrelated activity"},
            },
        ],
    )
    write_session(
        "undated-marker",
        [
            {
                "type": "user",
                "cwd": "/work/customer-app",
                "message": {"content": marker},
            }
        ],
    )

    rows = {
        row["session"]: row for row in DOGFOOD.discover(home, "2026-08-25")
    }
    assert set(rows) == {"old-chat-new-marker", "undated-marker"}
    included = rows["old-chat-new-marker"]
    assert included["started"] == "2026-08-20T12:00:00Z"
    assert included["candidate_marker_window"] == [
        "2026-08-30T12:00:00Z",
        "2026-08-30T12:00:00Z",
    ]
    assert included["candidate_marker_local_dates"] == [
        "2026-08-30",
        "2026-08-30",
    ]
    assert rows["undated-marker"]["candidate_marker_window"] == [
        "unknown",
        "unknown",
    ]
    assert rows["undated-marker"]["candidate_marker_local_dates"] == [
        "unknown",
        "unknown",
    ]


def test_dogfood_discover_can_select_one_exact_marker_day(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    marker = "skiphow:skiphow"

    def write_session(name: str, dates: list[str]) -> None:
        records = [
            {
                "type": "user",
                "timestamp": f"{day}T12:00:00Z",
                "cwd": "/work/customer-app",
                "message": {"content": marker},
            }
            for day in dates
        ]
        (project / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(record) for record in records) + "\n",
            encoding="utf-8",
        )

    write_session("spans-day", ["2026-08-27", "2026-08-28"])
    write_session("other-day", ["2026-08-28"])
    (project / "mixed-date-uncertain.jsonl").write_text(
        "\n".join(
            json.dumps(record)
            for record in (
                {
                    "type": "user",
                    "timestamp": "2026-08-26T12:00:00Z",
                    "cwd": "/work/customer-app",
                    "message": {"content": marker},
                },
                {
                    "type": "user",
                    "cwd": "/work/customer-app",
                    "message": {"content": marker},
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "undated.jsonl").write_text(
        json.dumps(
            {
                "type": "user",
                "cwd": "/work/customer-app",
                "message": {"content": marker},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rows = DOGFOOD.discover(home, None, "2026-08-27")
    assert {row["session"] for row in rows} == {
        "mixed-date-uncertain",
        "spans-day",
        "undated",
    }
    uncertain = next(
        row for row in rows if row["session"] == "mixed-date-uncertain"
    )
    assert uncertain["excluded"] is None
    assert uncertain["candidate_marker_local_dates"] == [
        "2026-08-26",
        "2026-08-26",
    ]
    assert uncertain["candidate_marker_date_status"] == (
        "unverified_undated_marker_records"
    )
    assert uncertain["undated_marker_records"] == 1
    assert "mixed-date-uncertain" in {
        row["session"] for row in DOGFOOD.discover(home, "2026-08-27")
    }
    undated = next(row for row in rows if row["session"] == "undated")
    assert undated["excluded"] is None
    assert undated["candidate_marker_local_dates"] == ["unknown", "unknown"]
    assert undated["candidate_marker_date_status"] == (
        "unverified_missing_or_invalid_timestamp"
    )
    assert undated["undated_marker_records"] == 1
    assert "undated" in {
        row["session"] for row in DOGFOOD.discover(home, "2026-08-27")
    }


def test_dogfood_exact_empty_tag_does_not_fall_through_to_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = (
        tmp_path
        / "plugins/cache/skiphow/skiphow/9.9.9/skills/skiphow/references"
    )
    cache.mkdir(parents=True)
    (cache / "ghost-reference.md").write_text("ghost", encoding="utf-8")
    (cache.parent / "SKILL.md").write_text("cached root", encoding="utf-8")
    monkeypatch.setattr(DOGFOOD, "claude_home", lambda: tmp_path)
    monkeypatch.setattr(
        DOGFOOD.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )
    assert DOGFOOD.version_reference_names("9.9.9") == set()
    assert DOGFOOD.package_reference("9.9.9", "ghost-reference") == ("", "tag")
    assert DOGFOOD.package_skill_root("9.9.9") == ("", "tag")


def test_dogfood_ambiguous_session_prefix_fails_closed(tmp_path: Path) -> None:
    first = tmp_path / "projects/one/prefix-a.jsonl"
    second = tmp_path / "projects/two/prefix-b.jsonl"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="ambiguous transcript prefix"):
        DOGFOOD.resolve(tmp_path, "prefix")


def test_dogfood_turn_sequence_uses_explicit_events_and_claude_is_not_observed() -> None:
    claude_records = [
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "done"}]},
        }
    ]
    assert DOGFOOD.codex_turn_status(claude_records) == "not_observed"
    assert DOGFOOD.codex_turn_status([{"type": "turn.started"}]) == "open_sequence"
    assert DOGFOOD.codex_turn_status(
        [
            {"type": "turn.started"},
            {"type": "turn.completed", "usage": codex_usage()},
        ]
    ) == "completed"
    assert DOGFOOD.codex_turn_status(
        [
            {"type": "turn.started"},
            {"type": "turn.failed", "error": {"message": "failed"}},
        ]
    ) == "failed"
    assert DOGFOOD.codex_turn_status(
        [{"type": "turn.started"}, {"type": "error", "message": "warning"}]
    ) == "open_sequence"
    assert DOGFOOD.codex_turn_status(
        [
            {"type": "turn.started"},
            {"type": "error", "message": "warning"},
            {"type": "turn.completed", "usage": codex_usage()},
        ]
    ) == "completed"


@pytest.mark.parametrize(
    "terminals",
    [
        [
            {"type": "turn.completed", "usage": codex_usage()},
            {"type": "turn.completed", "usage": codex_usage()},
        ],
        [
            {"type": "turn.completed", "usage": codex_usage()},
            {"type": "turn.failed", "error": {"message": "failed"}},
        ],
        [
            {"type": "turn.failed", "error": {"message": "first"}},
            {"type": "turn.failed", "error": {"message": "second"}},
        ],
    ],
)
def test_dogfood_multiple_turn_outcome_envelopes_are_ambiguous(
    terminals: list[dict],
) -> None:
    assert DOGFOOD.codex_turn_status([{"type": "turn.started"}, *terminals]) == (
        "ambiguous_sequence"
    )


@pytest.mark.parametrize(
    "terminal",
    [
        {"type": "turn.completed", "usage": codex_usage()},
        {"type": "turn.failed", "error": {"message": "failed"}},
    ],
)
def test_dogfood_overlapping_turn_starts_are_ambiguous(
    terminal: dict,
) -> None:
    assert DOGFOOD.codex_turn_status(
        [{"type": "turn.started"}, {"type": "turn.started"}, terminal]
    ) == "ambiguous_sequence"


@pytest.mark.parametrize(
    ("records", "status"),
    [
        (
            [
                {"type": "turn.started"},
                {"type": "turn.completed", "usage": codex_usage()},
                {"type": "turn.started"},
                {"type": "turn.failed", "error": {"message": "failed"}},
            ],
            "failed",
        ),
        (
            [
                {"type": "turn.started"},
                {"type": "turn.failed", "error": {"message": "failed"}},
                {"type": "turn.started"},
                {"type": "turn.completed", "usage": codex_usage()},
            ],
            "completed",
        ),
        (
            [
                {"type": "turn.started"},
                {"type": "turn.completed", "usage": codex_usage()},
                {"type": "turn.started"},
            ],
            "open_sequence",
        ),
    ],
)
def test_dogfood_sequential_turns_preserve_the_latest_state(
    records: list[dict],
    status: str,
) -> None:
    assert DOGFOOD.codex_turn_status(records) == status


def test_dogfood_owner_text_is_not_silently_clipped(tmp_path: Path) -> None:
    owner_text = "owner-visible request " * 1200
    transcript = write_transcript(
        tmp_path,
        [
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "origin": {"kind": "human"},
                "promptSource": "typed",
                "message": {"content": [{"type": "text", "text": owner_text}]},
            }
        ],
    )
    data = DOGFOOD.digest(transcript, 40)
    assert data["owner_turns"] == [
        {
            "at": "2026-08-27T10:00:00Z",
            "channel": "typed",
            "said": owner_text.strip(),
        }
    ]


def test_dogfood_report_truncation_is_explicitly_marked(tmp_path: Path) -> None:
    report = "0123456789" * 30
    transcript = write_transcript(
        tmp_path,
        [{"type": "assistant", "message": {"content": [{"type": "text", "text": report}]}}],
    )
    data = DOGFOOD.digest(transcript, 37)
    assert data["report"]["text"] == report[-37:]
    assert data["report"]["omitted_prefix_chars"] == len(report) - 37


def test_dogfood_digest_exposes_only_successful_write_actions(tmp_path: Path) -> None:
    records: list[dict] = []
    records += claude_call("edit-ok", "Edit", {"file_path": "/repo/a.py"})
    records += claude_call(
        "write-failed",
        "Write",
        {"file_path": "/repo/b.py"},
        "denied",
        is_error=True,
    )
    records.append(
        {
            "type": "item.completed",
            "timestamp": "2026-08-27T10:00:01Z",
            "item": {
                "id": "change-ok",
                "type": "file_change",
                "status": "completed",
                "changes": [{"path": "/repo/c.py", "kind": "update"}],
            },
        }
    )
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 100)
    assert data["successful_structured_write_actions"] == [
        {"at": "", "tool": "Edit", "path": "/repo/a.py"},
        {"at": "2026-08-27T10:00:01Z", "tool": "file_change", "path": "/repo/c.py"},
    ]


def test_dogfood_mixed_versions_use_the_observation_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records: list[dict] = [{"type": "thread.started", "thread_id": "mixed"}]
    body = "# SkipHow\n\nExact owner body."
    cache = host_cache_root(DOGFOOD.claude_home())
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    for tool_id, version in (("skill-old", "1.14.2"), ("skill-new", "2.0.0")):
        activation = claude_call(
            tool_id,
            "Skill",
            {"skill": "skiphow:skiphow"},
            "Skill loaded",
        )
        activation[0]["uuid"] = f"{tool_id}-call"
        activation[1]["uuid"] = f"{tool_id}-result"
        activation[1]["parentUuid"] = f"{tool_id}-call"
        activation[1]["sourceToolAssistantUUID"] = f"{tool_id}-call"
        records += activation
        records.append(
            {
                "type": "user",
                "uuid": f"{tool_id}-injection",
                "parentUuid": f"{tool_id}-result",
                "userType": "external",
                "isMeta": True,
                "sourceToolUseID": tool_id,
                "message": {
                    "content": (
                        "Base directory for this skill: "
                        f"{cache}/{version}/skills/skiphow\n{body}"
                    )
                },
            }
        )
    monkeypatch.setattr(DOGFOOD, "version_reference_names", lambda _version: {"testing"})
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 100)
    assert data["plugin_version_values_observed"] == ["1.14.2", "2.0.0"]
    assert data["confounders"]["plugin_version_identity"] == "mixed"
    assert data["references"] == {
        "testing": {
            "verdict": "unverified_contract_identity",
            "basis": "mixed",
            "matching_line_values": "unavailable",
            "artifact_source": "contract_identity_unsettled",
            "actions": ["not_evaluated"],
            "mismatched_path_versions": [],
        }
    }


def test_dogfood_skill_injection_requires_a_paired_successful_root_result(
    tmp_path: Path,
) -> None:
    quoted = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Base directory for this skill: "
                        "/cache/skiphow/skiphow/9.9.9/skills/skiphow"
                    ),
                }
            ]
        },
    }
    records = [quoted]
    records += claude_call(
        "failed-skill",
        "Skill",
        {"skill": "skiphow:skiphow"},
        (
            "Base directory for this skill: "
            "/cache/skiphow/skiphow/8.8.8/skills/skiphow"
        ),
        is_error=True,
    )
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 100)
    assert data["plugin_version_values_observed"] == ["unknown"]
    assert data["skill_body_injections"] == 0


def test_dogfood_sidechain_events_do_not_change_root_state() -> None:
    records = [
        {"type": "turn.started", "cwd": "/root-project", "gitBranch": "main"},
        {
            "type": "turn.completed",
            "usage": codex_usage(),
            "isSidechain": True,
            "isCompactSummary": True,
            "cwd": "/delegate-project",
            "gitBranch": "delegate",
        },
    ]
    assert DOGFOOD.codex_turn_status(records) == "open_sequence"
    assert DOGFOOD.compaction_status(records) == "unknown"
    assert DOGFOOD.identity_transitions(records) == [
        {"at": "", "cwd": "/root-project", "branch": "main"}
    ]


def test_dogfood_marks_references_absent_from_an_exact_older_package() -> None:
    body, source = DOGFOOD.package_reference("1.6.1", "worktrees")
    assert body == ""
    assert source == "absent_in_version"


def test_dogfood_prefers_the_exact_observed_cache_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    claude_home = tmp_path / "claude"
    codex_home = tmp_path / "codex"
    observed_root = host_cache_root(claude_home)
    other_root = host_cache_root(codex_home)
    for root, skill_body, reference_body in (
        (observed_root, "observed skill", "observed reference"),
        (other_root, "different skill", "different reference"),
    ):
        skill = root / version / "skills/skiphow/SKILL.md"
        reference = root / version / "skills/skiphow/references/testing.md"
        reference.parent.mkdir(parents=True)
        skill.write_text(skill_body, encoding="utf-8")
        reference.write_text(reference_body, encoding="utf-8")

    monkeypatch.setattr(DOGFOOD, "claude_home", lambda: claude_home)
    monkeypatch.setattr(DOGFOOD, "codex_home", lambda: codex_home)
    monkeypatch.setattr(
        DOGFOOD,
        "tagged_artifact",
        lambda _version, _relative: ("tag bytes", "tag"),
    )
    assert DOGFOOD.package_skill(version, "skiphow", str(observed_root)) == (
        "observed skill",
        "observed_cache_path",
    )
    assert DOGFOOD.package_reference(
        version, "testing", (str(observed_root),)
    ) == ("observed reference", "observed_cache_path")
    assert DOGFOOD.package_reference(
        version, "testing", (str(observed_root), str(other_root))
    ) == ("", "observed_cache_roots_disagree_or_are_incomplete")
    assert DOGFOOD.package_reference(
        version, "testing", (str(observed_root), str(tmp_path / "missing-root"))
    ) == ("", "observed_cache_roots_disagree_or_are_incomplete")
    assert DOGFOOD.package_reference(
        version, "testing", (str(tmp_path / "missing-root"),)
    ) == ("tag bytes", "tag")
    assert DOGFOOD.package_skill(version, "skiphow") == ("tag bytes", "tag")
    assert DOGFOOD.package_reference(version, "testing") == ("tag bytes", "tag")

    calls: list[tuple[str, str, tuple[str, ...]]] = []

    def package_reference(
        seen_version: str,
        name: str,
        roots: tuple[str, ...] = (),
    ) -> tuple[str, str]:
        calls.append((seen_version, name, roots))
        return "observed reference", "observed_cache_path"

    monkeypatch.setattr(DOGFOOD, "package_reference", package_reference)
    monkeypatch.setattr(DOGFOOD, "version_reference_names", lambda _version: {"testing"})
    reference_path = str(
        observed_root / version / "skills/skiphow/references/testing.md"
    )
    evidence = DOGFOOD.detect_references(
        Path("unused"),
        claude_call("read-testing", "Read", {"file_path": reference_path}),
        version,
    )
    assert calls == [(version, "testing", (str(observed_root),))]
    assert evidence["testing"]["artifact_source"] == "observed_cache_path"
    assert evidence["testing"]["verdict"] == "read_action_observed"


def test_dogfood_prefers_exact_version_cache_and_never_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached = (
        tmp_path
        / "plugins/cache/skiphow/skiphow/99.99.99"
        / "skills/skiphow/references/testing.md"
    )
    cached.parent.mkdir(parents=True)
    cached.write_text("exact cached contract", encoding="utf-8")
    monkeypatch.setattr(DOGFOOD, "claude_home", lambda: tmp_path)
    assert DOGFOOD.package_reference("99.99.99", "testing") == (
        "exact cached contract",
        "cache",
    )


def test_every_adr_status_agrees_with_the_index() -> None:
    """An ADR whose own Status omits its amendment reads as still in force.

    Five ADRs disagreed with the index at once, in both directions, leaving
    superseded Decisions -- Codex `[agents]` config, shipped role files -- looking
    current to anyone who opened the file rather than the table.
    """
    index = read("docs/decisions/README.md")
    rows = dict(re.findall(r"\| \[(\d{4})\]\([^)]+\) \| [^|]+ \| ([^|]+) \|", index))
    decisions = sorted((ROOT / "docs/decisions").glob("0*.md"))
    assert {path.name[:4] for path in decisions} == set(rows)
    for path in decisions:
        status = re.search(r"## Status\n\n(.+)", path.read_text(encoding="utf-8")).group(1)
        amended = set()
        for clause in re.split(r"(?<=[.])\s+", status):
            if re.search(r"\b(?:amended|superseded) by\b", clause, re.IGNORECASE):
                amended |= set(re.findall(r"ADR (\d{4})", clause))
        assert amended == set(re.findall(r"\b(\d{4})\b", rows[path.name[:4]])), path.name


def test_continuity_hook_is_the_only_hook() -> None:
    hooks_dir = PLUGIN / "hooks"
    assert [path.name for path in hooks_dir.iterdir()] == ["hooks.json"]
    payload = json_object("plugins/skiphow/hooks/hooks.json")
    assert set(payload["hooks"]) == {"SessionStart"}
    groups = payload["hooks"]["SessionStart"]
    assert len(groups) == 2
    assert {
        frozenset(group["matcher"].split("|")) for group in groups
    } == _MODULE.CONTINUITY_GROUPS
    sources = [source for group in groups for source in group["matcher"].split("|")]
    assert sorted(sources) == ["clear", "compact", "resume", "startup"]
    for group in groups:
        (handler,) = group["hooks"]
        assert handler["type"] == "command"
        assert handler["command"].startswith("sh -c ")
        if {"compact", "resume"} & set(group["matcher"].split("|")):
            assert _MODULE.HOOK_COMMAND.fullmatch(handler["command"])
        else:
            assert _MODULE.HOOK_NOTICE_COMMAND.fullmatch(handler["command"])
        assert "cat " not in handler["command"]
        assert "tail " not in handler["command"]
        assert handler.get("timeout", 600) <= 30


def test_package_has_no_versioned_model_ids_or_personal_paths() -> None:
    """Both scans are the release checker's own, over every shipped file.

    A second, narrower regex here meant the suite could stay green on an ID the
    release gate rejects, or on one neither pattern happened to name.
    """
    scanned = 0
    for path in PLUGIN.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        assert PERSONAL_PATH.search(text) is None, path
        assert VERSIONED_MODEL.search(text) is None, path
    assert scanned > 0
    for identifier in ("claude-fable-5", "fable-5", "gpt-oss-120b", "claude-opus-5", "o3"):
        assert VERSIONED_MODEL.search(identifier), identifier
    for personal in ("/Users/person", "C:\\users\\person\\x", "~/.claude"):
        assert PERSONAL_PATH.search(personal), personal
