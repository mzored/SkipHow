"""Structural contracts for the plugin-only package.

These tests check package shape and the few semantic invariants whose absence
caused a field failure. Other prose remains free to change.
"""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
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


def cached_reference_path(name: str, version: str = "2.0.0") -> str:
    return str(
        host_cache_root(DOGFOOD.claude_home())
        / version
        / "skills/skiphow/references"
        / f"{name}.md"
    )


TEST_EVIDENCE_A = "sha256-v1:" + "a" * 64
TEST_EVIDENCE_B = "sha256-v1:" + "b" * 64


def coverage_receipt(
    session: str,
    records: int,
    plugin_versions: list[str],
    evidence_fingerprint: str | None,
) -> dict:
    return {
        "session": session,
        "records": records,
        "plugin_versions": plugin_versions,
        "evidence_fingerprint": evidence_fingerprint,
    }


def write_coverage_sidecar(
    repository: Path,
    receipts: list[dict],
    audit_date: str = "2026-08-27",
) -> Path:
    research = repository / "docs/research" / audit_date
    research.mkdir(parents=True, exist_ok=True)
    base = research / f"field-audit-{audit_date}"
    base.with_name(base.name + ".md").write_text(
        "# Sanitized field audit\n", encoding="utf-8"
    )
    sidecar = base.with_name(base.name + ".receipts.json")
    sidecar.write_text(
        json.dumps(
            {
                "schema": DOGFOOD.COVERAGE_SCHEMA,
                "source": DOGFOOD.COVERAGE_SOURCE,
                "receipts": receipts,
            }
        ),
        encoding="utf-8",
    )
    return sidecar


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
        "\n".join(
            f"{number}\t{line}" for number, line in enumerate(lines, start_line)
        )
        if framed_output is None
        else framed_output
    )
    inputs: dict[str, object] = {"file_path": path}
    if start_line != 1:
        inputs["offset"] = start_line
    records = claude_call(tool_id, "Read", inputs, output)
    records[1]["toolUseResult"] = {
        "type": "text",
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
        DOGFOOD, "version_reference_roster", lambda _version: ({name}, True)
    )
    monkeypatch.setattr(
        DOGFOOD,
        "package_reference",
        lambda _version, _name, _roots=(): (body, source),
    )
    return DOGFOOD.detect_references(Path("unused.jsonl"), records, version)[name]


def test_dogfood_contributor_policy_has_no_single_cause_or_adr_scoring_gate() -> None:
    skill = read(".claude/skills/dogfood/SKILL.md")
    checklist = read(".claude/skills/dogfood/references/checklist.md")
    assert "one cause" not in skill
    assert "one sentence" not in skill
    assert "Name the file and the sentence" not in skill
    assert "cause or causes" in skill
    assert "cause or causes" in checklist
    assert "governing text or gap" in checklist
    assert "tag conformance" not in skill
    assert "Grep ADR `## Revalidation triggers` first" not in checklist
    assert "at least one typed\n  input path exists" in skill
    assert "recognized\n  file/content shape" in skill
    assert "all input and result paths agree" in checklist
    assert "internally consistent partial-frame metadata" in checklist


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
    info = reference_info(monkeypatch, records, version="unknown")
    assert info == {
        "verdict": "path_action_failed",
        "basis": "tool_event",
        "matching_line_values": "unavailable",
        "artifact_source": "contract_bytes_unavailable",
        "actions": ["path_action_failed"],
        "mismatched_path_versions": [],
        "mismatched_path_sources": [],
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
        "mismatched_path_sources": [],
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
    monkeypatch.setattr(
        DOGFOOD,
        "version_reference_roster",
        lambda _version: ({"research", "testing"}, True),
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
            "mismatched_path_sources": [],
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
        "version_reference_roster",
        lambda _version: ({"research", "testing"}, True),
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
        "mismatched_path_sources": [],
    }
    assert evidence["research"]["verdict"] == "not_observed"
    assert evidence["research"]["actions"] == ["none"]


@pytest.mark.parametrize("case", ["failed", "result_only", "path_conflict"])
def test_dogfood_exact_read_body_output_does_not_require_path_provenance(
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    testing = cached_reference_path("testing")
    if case == "failed":
        records = claude_call(
            "read-testing", "Read", {"file_path": testing}, body, is_error=True
        )
    elif case == "result_only":
        records = claude_call("read-testing", "Read", {}, body)
    else:
        records = claude_call(
            "read-testing", "Read", {"file_path": testing}, body
        )
        records[1]["toolUseResult"] = {
            "type": "text",
            "file": {
                "filePath": cached_reference_path("research"),
                "content": body,
            }
        }
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "body_observed"
    assert info["basis"] == "complete_artifact_text_in_model_output"
    assert info["matching_line_values"] == "3/3"


@pytest.mark.parametrize("body", ["\n", " ", " \n"])
def test_dogfood_blank_reference_artifact_is_not_observed_in_arbitrary_output(
    body: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = cached_reference_path("testing")
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": path},
        "unrelated successful output",
    )
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info == {
        "verdict": "read_action_observed",
        "basis": "tool_event",
        "matching_line_values": "unavailable",
        "artifact_source": "tag",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
        "mismatched_path_sources": [],
    }


@pytest.mark.parametrize(
    ("artifact", "observed"),
    [
        (" ", " "),
        (
            "---\nname: skiphow\ndescription: metadata only\n---\n",
            "---\nname: skiphow\ndescription: metadata only\n---\n",
        ),
    ],
)
def test_dogfood_skill_without_instructions_is_never_exact_body_evidence(
    artifact: str,
    observed: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = (
        host_cache_root(DOGFOOD.claude_home())
        / "2.0.0/skills/skiphow"
    )
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (artifact, "tag"),
    )
    records = claude_call(
        "skill-call", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
    )
    records.append(
        {
            "type": "user",
            "uuid": "skill-injection",
            "parentUuid": "skill-call-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill-call",
            "message": {
                "content": f"Base directory for this skill: {base}\n{observed}"
            },
        }
    )
    observation = DOGFOOD.skill_injection_observations(records)["skill-call"]
    assert observation["status"] == "body_unverified"
    assert "body_fingerprint" not in observation


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


def test_dogfood_exact_path_read_proves_only_the_observed_excerpt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line\nfourth exact line"
    path = cached_reference_path("testing")
    records = claude_call("read-testing", "Read", {"file_path": path}, "second exact line")
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info == {
        "verdict": "exact_excerpt_observed",
        "basis": "exact_path_read_result",
        "matching_line_values": "1/4",
        "artifact_source": "tag",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
        "mismatched_path_sources": [],
    }


def test_dogfood_unknown_typed_result_content_cannot_prove_visible_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line"
    path = cached_reference_path("testing")
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": path},
        [{"type": "opaque_metadata", "content": body}],
    )
    assert DOGFOOD.transcript_record_valid(records[1]) is True
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert event["output"] == ""
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"
    assert info["matching_line_values"] == "0/2"

    typeless_wrapper = {
        "content": [{"type": "text", "text": "visible exact text"}]
    }
    assert DOGFOOD.result_content_text(typeless_wrapper) == ""
    assert DOGFOOD.result_content_payload_valid(typeless_wrapper) is False
    for opaque_content in (
        42,
        {"type": "text", "text": 7},
        [{"type": "text", "text": "hidden nested text"}],
    ):
        opaque = {"type": "opaque_metadata", "content": opaque_content}
        assert DOGFOOD.result_content_payload_valid([opaque]) is True
        assert DOGFOOD.result_content_text([opaque]) == ""
    assert DOGFOOD.result_content_payload_valid(
        {"type": None, "content": "not a typeless wrapper"}
    ) is False
    text_with_opaque_extra = {
        "type": "text",
        "text": "visible text",
        "content": 42,
    }
    assert DOGFOOD.result_content_payload_valid([text_with_opaque_extra]) is True
    assert DOGFOOD.result_content_text([text_with_opaque_extra]) == "visible text"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "type": "search_result",
            "source": "https://example.test/result",
            "title": "Result",
            "content": [
                {"type": "text", "text": "first exact line"},
                {"type": "text", "text": "second exact line"},
            ],
        },
        {
            "type": "document",
            "source": {
                "type": "text",
                "media_type": "text/plain",
                "data": "first exact line\nsecond exact line",
            },
        },
        {
            "type": "document",
            "source": {
                "type": "content",
                "content": "first exact line\nsecond exact line",
            },
        },
        {
            "type": "document",
            "source": {
                "type": "content",
                "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": "AA==",
                            },
                        },
                    {
                        "type": "text",
                        "text": "first exact line\nsecond exact line",
                    },
                ],
            },
        },
    ],
)
def test_dogfood_official_claude_text_bearing_results_prove_visible_text(
    payload: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line"
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": cached_reference_path("testing")},
        [payload],
    )
    assert DOGFOOD.result_content_payload_valid([payload]) is True
    assert DOGFOOD.result_content_text([payload]) == body
    assert reference_info(monkeypatch, records, body=body, source="tag")[
        "verdict"
    ] == "body_observed"


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "output_text", "text": "first exact line\nsecond exact line"},
        {
            "type": "resource",
            "resource": {
                "uri": "doc://result",
                "text": "first exact line\nsecond exact line",
            },
        },
    ],
)
def test_dogfood_non_claude_result_types_stay_opaque(
    payload: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line"
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": cached_reference_path("testing")},
        [payload],
    )
    assert DOGFOOD.result_content_payload_valid([payload]) is True
    assert DOGFOOD.result_content_text([payload]) == ""
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"
    assert info["matching_line_values"] == "0/2"


@pytest.mark.parametrize(
    "payload",
    [
        ["first exact line\nsecond exact line"],
        [{"content": "first exact line\nsecond exact line"}],
        {"content": {"content": "first exact line\nsecond exact line"}},
        {"type": "search_result", "title": "x", "content": []},
        {"type": "search_result", "source": "x", "title": 7, "content": []},
        {"type": "search_result", "source": "x", "title": "x", "content": "x"},
        {
            "type": "search_result",
            "source": "x",
            "title": "x",
            "content": [{"type": "image"}],
        },
        {"type": "document"},
        {"type": "document", "source": []},
        {"type": "document", "source": {"type": None}},
        {
            "type": "document",
            "source": {"type": "text", "media_type": "text/html", "data": "x"},
        },
        {"type": "document", "source": {"type": "text", "media_type": "text/plain"}},
        {"type": "document", "source": {"type": "content", "content": 7}},
        {"type": "document", "source": {"type": "content", "content": [7]}},
        {
            "type": "document",
            "source": {"type": "content", "content": [{"content": "x"}]},
        },
        {
            "type": "document",
            "source": {
                "type": "content",
                "content": [{"type": "text", "text": 7}],
            },
        },
    ],
)
def test_dogfood_malformed_claude_text_bearing_results_fail_closed(
    payload: object,
) -> None:
    assert DOGFOOD.result_content_payload_valid(payload) is False
    assert DOGFOOD.result_content_text(payload) == ""


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "text", "text": "only exact line"},
        {
            "type": "search_result",
            "source": "source",
            "title": "title",
            "content": [{"type": "text", "text": "only exact line"}],
        },
        {"content": [{"type": "text", "text": "only exact line"}]},
    ],
)
def test_dogfood_bare_object_tool_results_cannot_prove_visible_text(
    payload: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "only exact line"
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": cached_reference_path("testing")},
        payload,
    )
    assert DOGFOOD.transcript_record_valid(records[1]) is False
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert event["output"] == ""
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"


@pytest.mark.parametrize(
    "failure",
    [
        "missing_result_type",
        "wrong_result_type",
        "missing_range",
        "offset_mismatch",
        "string_offset",
        "string_limit",
        "invalid_truncation_flag",
    ],
)
def test_dogfood_read_exact_provenance_requires_the_official_text_shape(
    failure: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = cached_reference_path("testing")
    records = claude_read(
        "read-testing", path, "second exact line", start_line=2, total_lines=3
    )
    records[0]["message"]["content"][0]["input"]["offset"] = 2
    structured = records[1]["toolUseResult"]
    file_result = structured["file"]
    if failure == "missing_result_type":
        del structured["type"]
    elif failure == "wrong_result_type":
        structured["type"] = "image"
    elif failure == "missing_range":
        del file_result["totalLines"]
    elif failure == "offset_mismatch":
        records[0]["message"]["content"][0]["input"]["offset"] = 99
    elif failure == "string_offset":
        records[0]["message"]["content"][0]["input"]["offset"] = "2"
    elif failure == "string_limit":
        records[0]["message"]["content"][0]["input"]["limit"] = "1"
    else:
        file_result["truncatedByTokenCap"] = "false"

    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "invalid"
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"
    assert info["basis"] == "tool_event"
    assert info["matching_line_values"] == "0/3"


@pytest.mark.parametrize(
    ("offset", "start_line", "truncated"),
    [(0, 0, False), (0, 1, True), (2, 2, False)],
)
def test_dogfood_read_exact_provenance_accepts_official_offset_relations(
    offset: int,
    start_line: int,
    truncated: bool,
) -> None:
    path = cached_reference_path("testing")
    records = claude_read(
        "read-testing", path, "exact line", start_line=start_line, total_lines=3
    )
    request = records[0]["message"]["content"][0]["input"]
    request["offset"] = offset
    if not truncated:
        request["limit"] = 1
    records[1]["toolUseResult"]["file"]["truncatedByTokenCap"] = truncated
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "valid"
    assert DOGFOOD.decoded_event_output(event) == "exact line"


def test_dogfood_read_exact_provenance_accepts_default_truncated_pagination() -> None:
    path = cached_reference_path("testing")
    records = claude_read(
        "read-testing", path, "exact line", start_line=1, total_lines=3
    )
    records[1]["toolUseResult"]["file"]["truncatedByTokenCap"] = True
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "valid"
    assert DOGFOOD.decoded_event_output(event) == "exact line"


@pytest.mark.parametrize("case", ["offset", "limit", "pages"])
def test_dogfood_truncated_read_requires_the_host_auto_pagination_branch(
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = cached_reference_path("testing")
    start = 2 if case == "offset" else 1
    content = "second exact line" if start == 2 else "first exact line"
    records = claude_read(
        "read-testing", path, content, start_line=start, total_lines=3
    )
    request = records[0]["message"]["content"][0]["input"]
    if case == "limit":
        request["limit"] = 1
    elif case == "pages":
        request["pages"] = "1"
    records[1]["toolUseResult"]["file"]["truncatedByTokenCap"] = True
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "invalid"
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"


@pytest.mark.parametrize(
    "pages",
    [
        "1",
        " 1 ",
        "1x",
        "1.9",
        "+2",
        "01",
        "1 - 3",
        "1-3x",
        "1-3-5",
        "999",
        "999-1018",
        "\ufeff1",
        "1-\ufeff2",
        "\u20281\u2029",
        "\u00a01",
    ],
)
def test_dogfood_read_pages_matches_the_host_validator(pages: str) -> None:
    path = cached_reference_path("testing")
    records = claude_read("read-testing", path, "exact line", total_lines=3)
    records[0]["message"]["content"][0]["input"]["pages"] = pages
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "valid"
    assert DOGFOOD.decoded_event_output(event) == "exact line"


@pytest.mark.parametrize(
    "pages",
    [
        42,
        None,
        True,
        {},
        [],
        "",
        "bad",
        "1-",
        "1--3",
        "0",
        "-1",
        "3-1",
        "999-1019",
        "9" * 309,
        "9" * 5000,
        "1" + "0" * 309,
        "9007199254740992-9007199254741011",
        "\u00851",
        "1-\u00852",
        "\u001c1",
        "\u001d1",
        "\u001e1",
        "\u001f1",
        "\u180e1",
    ],
)
def test_dogfood_read_pages_rejects_non_host_shapes(
    pages: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = cached_reference_path("testing")
    records = claude_read("read-testing", path, "exact line", total_lines=3)
    records[0]["message"]["content"][0]["input"]["pages"] = pages
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "invalid"
    info = reference_info(
        monkeypatch, records, body="exact line\nother line", source="tag"
    )
    assert info["verdict"] == "read_action_observed"


def test_dogfood_read_exact_provenance_accepts_an_empty_far_eof_result() -> None:
    path = cached_reference_path("testing")
    records = claude_read(
        "read-testing",
        path,
        "",
        framed_output="",
        start_line=25,
        num_lines=0,
        total_lines=22,
    )
    records[0]["message"]["content"][0]["input"].update(
        {"offset": 25, "limit": 10}
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "valid"
    assert DOGFOOD.decoded_event_output(event) == ""


def test_dogfood_read_exact_provenance_accepts_one_selected_blank_line() -> None:
    path = cached_reference_path("testing")
    records = claude_read(
        "read-testing",
        path,
        "",
        start_line=1,
        num_lines=1,
        total_lines=1,
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "valid"
    assert DOGFOOD.decoded_event_output(event) == ""


def test_dogfood_read_exact_provenance_rejects_zero_start_overlong_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first\nsecond\nthird\nfourth"
    path = cached_reference_path("testing")
    records = claude_read(
        "read-testing",
        path,
        body,
        start_line=0,
        num_lines=4,
        total_lines=3,
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.structured_read_file(event)[0] == "invalid"
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"
    assert info["basis"] == "tool_event"


@pytest.mark.parametrize("selected_field", ["file_path", "path"])
def test_dogfood_exact_excerpt_requires_all_read_paths_to_agree(
    selected_field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    selected = cached_reference_path("testing")
    source = str(
        SKILL.parent / "references/testing.md"
    )
    other_field = "path" if selected_field == "file_path" else "file_path"
    records = claude_call(
        "read-testing",
        "Read",
        {selected_field: selected, other_field: source},
        "second exact line",
    )
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "matching_lines_observed"
    assert info["basis"] == "matching_decoded_line_text"
    assert info["actions"] == [
        "path_action_ambiguous",
        "source_mismatch_path_observed",
    ]
    assert info["mismatched_path_sources"] == ["source"]


def test_dogfood_exact_excerpt_requires_read_result_path_to_agree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    selected = cached_reference_path("testing")
    source = str(SKILL.parent / "references/testing.md")
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": selected},
        "second exact line",
    )
    records[1]["toolUseResult"] = {
        "type": "text",
        "file": {
            "filePath": source,
            "content": "second exact line",
            "startLine": 1,
            "numLines": 1,
            "totalLines": 1,
        }
    }
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.event_path_payloads(event) == [selected, source]
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "matching_lines_observed"
    assert info["basis"] == "matching_decoded_line_text"
    assert info["actions"] == [
        "path_action_ambiguous",
        "source_mismatch_path_observed",
    ]


@pytest.mark.parametrize("duplicate_input", [False, True])
def test_dogfood_exact_excerpt_accepts_agreeing_structured_read_paths(
    duplicate_input: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    selected = cached_reference_path("testing")
    inputs = {"file_path": selected}
    if duplicate_input:
        inputs["path"] = selected
    records = claude_call(
        "read-testing",
        "Read",
        inputs,
        "second exact line",
    )
    records[1]["toolUseResult"] = {
        "type": "text",
        "file": {
            "filePath": selected,
            "content": "second exact line",
            "startLine": 1,
            "numLines": 1,
            "totalLines": 1,
        }
    }
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "exact_excerpt_observed"
    assert info["basis"] == "exact_path_read_result"


@pytest.mark.parametrize(
    ("start_line", "content", "expected_matching"),
    [(1, "first exact line", "1/3"), (2, "second exact line", "1/3")],
)
def test_dogfood_exact_excerpt_decodes_an_internally_consistent_partial_read(
    start_line: int,
    content: str,
    expected_matching: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = cached_reference_path("testing")
    records = claude_read(
        "partial-read",
        path,
        content,
        start_line=start_line,
        total_lines=3,
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.decoded_event_output(event) == content
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "exact_excerpt_observed"
    assert info["basis"] == "exact_path_read_result"
    assert info["matching_line_values"] == expected_matching


def test_dogfood_exact_excerpt_rejects_contradictory_structured_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = cached_reference_path("testing")
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": path},
        "second exact line",
    )
    records[1]["toolUseResult"] = {
        "type": "text",
        "file": {
            "filePath": path,
            "content": "different metadata line",
            "startLine": 2,
            "numLines": 1,
            "totalLines": 3,
        }
    }
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "matching_lines_observed"
    assert info["basis"] == "matching_decoded_line_text"
    assert info["matching_line_values"] == "1/3"


def test_dogfood_read_rejects_impossible_unframed_range_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "only exact line"
    path = cached_reference_path("testing")
    records = claude_call(
        "read-testing", "Read", {"file_path": path}, body
    )
    records[1]["toolUseResult"] = {
        "type": "text",
        "file": {
            "filePath": path,
            "content": body,
            "startLine": 99,
            "numLines": 1,
            "totalLines": 3,
        }
    }
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "body_observed"
    assert info["basis"] == "complete_artifact_text_in_model_output"
    assert info["actions"] == ["read_action_observed"]


@pytest.mark.parametrize(
    "structured_result",
    ["different structured text", ["different structured text"], {"content": "different"}],
)
def test_dogfood_read_rejects_present_unrecognized_structured_results(
    structured_result: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "only exact line"
    path = cached_reference_path("testing")
    records = claude_call(
        "read-testing", "Read", {"file_path": path}, body
    )
    records[1]["toolUseResult"] = structured_result
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert event["structured_result_present"] is True
    assert DOGFOOD.read_result_content_agrees(event, body) is False
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "body_observed"
    assert info["basis"] == "complete_artifact_text_in_model_output"


def test_dogfood_result_only_read_path_is_action_not_exact_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = cached_reference_path("testing")
    records = claude_call("read-testing", "Read", {}, "second exact line")
    records[1]["toolUseResult"] = {
        "type": "text",
        "file": {
            "filePath": path,
            "content": "second exact line",
            "startLine": 2,
            "numLines": 1,
            "totalLines": 3,
        }
    }
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.event_path_payloads(event) == [path]
    assert DOGFOOD.unambiguous_read_path(event) is None
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "matching_lines_observed"
    assert info["actions"] == ["read_action_observed"]


def test_dogfood_unattributed_matching_lines_remain_weak_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    records = claude_call(
        "shell-output",
        "Bash",
        {"command": "opaque command"},
        "second exact line",
    )
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "matching_lines_observed"
    assert info["basis"] == "matching_decoded_line_text"
    assert info["matching_line_values"] == "1/3"


def test_dogfood_unknown_contract_never_reads_other_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "/project/.agents/skills/skiphow/references/testing.md"

    def unexpected(*_args: object) -> tuple[str, str]:
        raise AssertionError("unknown versions must not compare repository HEAD")

    monkeypatch.setattr(DOGFOOD, "package_reference", unexpected)
    monkeypatch.setattr(DOGFOOD, "version_reference_names", lambda _version: {"testing"})
    monkeypatch.setattr(
        DOGFOOD, "version_reference_roster", lambda _version: ({"testing"}, True)
    )
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
        "mismatched_path_sources": [],
    }
    assert absent == {
        "verdict": "not_observed",
        "basis": "transcript_absence_only",
        "matching_line_values": "unavailable",
        "artifact_source": "contract_bytes_unavailable",
        "actions": ["none"],
        "mismatched_path_versions": [],
        "mismatched_path_sources": [],
    }


def test_dogfood_unavailable_contract_yields_only_action_or_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = cached_reference_path("testing", "99.0.0")
    calls: list[tuple[str, str, tuple[str, ...]]] = []

    def unavailable(
        version: str, name: str, roots: tuple[str, ...] = ()
    ) -> tuple[str, str]:
        calls.append((version, name, roots))
        return "", "contract_bytes_unavailable"

    monkeypatch.setattr(DOGFOOD, "version_reference_names", lambda _version: {"testing"})
    monkeypatch.setattr(
        DOGFOOD, "version_reference_roster", lambda _version: ({"testing"}, True)
    )
    monkeypatch.setattr(DOGFOOD, "package_reference", unavailable)
    action = DOGFOOD.detect_references(
        Path("unused"),
        claude_call("read-testing", "Read", {"file_path": path}),
        "99.0.0",
    )["testing"]
    absent = DOGFOOD.detect_references(Path("unused"), [], "99.0.0")["testing"]
    assert calls == [
        (
            "99.0.0",
            "testing",
            (str(host_cache_root(DOGFOOD.claude_home())),),
        ),
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
        "mismatched_path_sources": [],
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
        "mismatched_path_sources": [],
    }


def test_dogfood_split_semantic_tool_result_text_reconstructs_exact_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = cached_reference_path("testing")
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
        "mismatched_path_sources": [],
    }


def test_dogfood_decodes_an_exact_complete_claude_read_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = cached_reference_path("testing")
    records = claude_read("read-testing", path, body)
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info == {
        "verdict": "body_observed",
        "basis": "complete_artifact_text_in_model_output",
        "matching_line_values": "3/3",
        "artifact_source": "tag",
        "actions": ["read_action_observed"],
        "mismatched_path_versions": [],
        "mismatched_path_sources": [],
    }


@pytest.mark.parametrize(
    ("separator", "padding"), [("\t", ""), (":", ""), ("→", "   ")]
)
def test_dogfood_decodes_official_claude_read_line_separators(
    separator: str,
    padding: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "\tleading tab\nplain line"
    path = cached_reference_path("testing")
    framed = (
        f"{padding}1{separator}\tleading tab\n"
        f"{padding}2{separator}plain line"
    )
    records = claude_read(
        "read-testing", path, body, framed_output=framed, total_lines=2
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.decoded_event_output(event) == body
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "body_observed"
    assert info["matching_line_values"] == "2/2"


@pytest.mark.parametrize(
    "framed",
    [
        "1;\tleading tab\n2;plain line",
        "1:\tleading tab\n2→plain line",
    ],
)
def test_dogfood_read_separator_never_overrides_structured_content_agreement(
    framed: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "\tleading tab\nplain line"
    path = cached_reference_path("testing")
    records = claude_read(
        "read-testing", path, body, framed_output=framed, total_lines=2
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.decoded_event_output(event) == framed
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"
    assert info["matching_line_values"] == "0/2"


def test_dogfood_colon_read_frame_requires_the_host_tab_aware_trigger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "plain first line\nplain second line"
    path = cached_reference_path("testing")
    framed = "1:plain first line\n2:plain second line"
    records = claude_read(
        "read-testing", path, body, framed_output=framed, total_lines=2
    )
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.decoded_event_output(event) == framed
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "read_action_observed"


@pytest.mark.parametrize(
    "failure",
    [
        "wrong_path",
        "partial_start",
        "boolean_start",
        "float_start",
        "line_count",
        "boolean_count",
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
    path = cached_reference_path("testing")
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
        assert info["verdict"] == (
            "path_action_ambiguous"
            if failure == "wrong_path"
            else "read_action_observed"
        )
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
                "type": "text",
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
    path = cached_reference_path("testing")
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
        "mismatched_path_sources": [],
    }


def test_dogfood_read_frame_does_not_normalize_before_it_is_proven(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = ("first exact line", "second exact line", "third exact line")
    body = "\r\n".join(lines)
    raw = "\n".join(
        f"{number}\t{line}" for number, line in enumerate(lines, 1)
    )
    path = cached_reference_path("testing")
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
    assert info["mismatched_path_sources"] == []


@pytest.mark.parametrize(
    ("path", "source"),
    [
        (
            "/project/.agents/skills/skiphow/references/testing.md",
            "project",
        ),
        (
            "plugins/skiphow/skills/skiphow/references/testing.md",
            "source",
        ),
    ],
)
def test_dogfood_known_plugin_contract_rejects_other_reference_sources(
    path: str,
    source: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = claude_call(
        "read-other-source",
        "Read",
        {"file_path": path},
        "project local body",
    )
    info = reference_info(
        monkeypatch,
        records,
        body="plugin 2.0.0 body",
        source="tag",
    )
    assert info["verdict"] == "source_mismatch_path_observed"
    assert info["actions"] == ["source_mismatch_path_observed"]
    assert info["mismatched_path_versions"] == []
    assert info["mismatched_path_sources"] == [source]


@pytest.mark.parametrize(
    ("path", "expected_kind", "expected_version"),
    [
        (
            r"plugins\skiphow\skills\skiphow\references\testing.md",
            "source",
            "unknown",
        ),
        (
            r"C:\Users\Person\.CLAUDE\PLUGINS\CACHE\SKIPHOW\SKIPHOW\2.0.0\SKILLS\SKIPHOW\REFERENCES\TESTING.MD",
            "cache",
            "2.0.0",
        ),
        (
            r"\\Server\Share\.CoDeX\PlUgInS\CaChE\SkIpHoW\SkIpHoW\2.0.0\SkIlLs\SkIpHoW\ReFeReNcEs\TeStInG.Md",
            "cache",
            "2.0.0",
        ),
        (
            r"//Server/Share/.CoDeX/PlUgInS/CaChE/SkIpHoW/SkIpHoW/2.0.0/SkIlLs/SkIpHoW/ReFeReNcEs/TeStInG.Md",
            "cache",
            "2.0.0",
        ),
        (
            r".claude\plugins\cache\skiphow\skiphow\2.0.0\skills\skiphow\references\testing.md",
            "cache",
            "2.0.0",
        ),
        (
            ".codex/plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow/references/testing.md",
            "cache",
            "2.0.0",
        ),
    ],
)
def test_dogfood_recognizes_windows_skiphow_paths_case_insensitively(
    path: str,
    expected_kind: str,
    expected_version: str,
) -> None:
    rooted = DOGFOOD.recognized_path_root(path)
    assert rooted is not None
    assert rooted[:3:2] == (expected_kind, expected_version)
    assert DOGFOOD.reference_name_from_path(path) == "testing"


def test_dogfood_read_path_agreement_follows_windows_case_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    path = (
        r"C:\Users\Person\.claude\plugins\cache\skiphow\skiphow\2.0.0"
        r"\skills\skiphow\references\testing.md"
    )
    records = claude_call(
        "read-testing",
        "Read",
        {"file_path": path, "offset": 2},
        "second exact line",
    )
    records[1]["toolUseResult"] = {
        "type": "text",
        "file": {
            "filePath": path.upper(),
            "content": "second exact line",
            "startLine": 2,
            "numLines": 1,
            "totalLines": 3,
        }
    }
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert DOGFOOD.unambiguous_read_path(event) is not None
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] == "exact_excerpt_observed"

    posix_records = claude_call(
        "read-posix",
        "Read",
        {"file_path": "/repo/.agents/skills/skiphow/references/testing.md"},
        "second exact line",
    )
    posix_records[1]["toolUseResult"] = {
        "type": "text",
        "file": {
            "filePath": "/REPO/.agents/skills/skiphow/references/testing.md",
            "content": "second exact line",
        }
    }
    (posix_event,) = DOGFOOD.terminal_tool_events(posix_records)
    assert DOGFOOD.unambiguous_read_path(posix_event) is None
    assert DOGFOOD.read_path_evidence_conflicts(posix_event) is True


def test_dogfood_windows_path_identity_rejects_unicode_expanding_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = (
        r"C:\Users\Straße\.claude\plugins\cache\skiphow\skiphow\2.0.0"
        r"\skills\skiphow\references\testing.md"
    )
    returned = requested.replace("Straße", "STRASSE")
    records = claude_read(
        "read-testing",
        requested,
        "second exact line",
        start_line=2,
        total_lines=3,
    )
    records[1]["toolUseResult"]["file"]["filePath"] = returned
    (event,) = DOGFOOD.terminal_tool_events(records)

    assert DOGFOOD.comparable_path_token(requested) != DOGFOOD.comparable_path_token(
        returned
    )
    assert DOGFOOD.unambiguous_read_path(event) is None
    assert DOGFOOD.read_path_evidence_conflicts(event) is True
    info = reference_info(
        monkeypatch,
        records,
        body="first exact line\nsecond exact line\nthird exact line",
        source="tag",
    )
    assert info["verdict"] == "path_action_ambiguous"


def test_dogfood_path_identity_keeps_windows_and_native_semantics_distinct() -> None:
    windows = (
        r".claude\plugins\cache\skiphow\skiphow\2.0.0"
        r"\skills\skiphow\references\testing.md"
    )
    native = windows.replace("\\", "/")
    records = claude_read(
        "read-testing",
        windows,
        "exact line",
        start_line=1,
        total_lines=1,
    )
    records[1]["toolUseResult"]["file"]["filePath"] = native
    (event,) = DOGFOOD.terminal_tool_events(records)

    assert DOGFOOD.comparable_path_token(windows) != DOGFOOD.comparable_path_token(
        native
    )
    assert DOGFOOD.unambiguous_read_path(event) is None
    assert DOGFOOD.read_path_evidence_conflicts(event) is True


def test_dogfood_foreign_windows_cache_root_cannot_prove_an_exact_excerpt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line\nthird exact line"
    selected_root = (
        r"C:\Users\Owner\.claude\plugins\cache\skiphow\skiphow"
    )
    foreign_path = (
        r"D:\Other\.claude\plugins\cache\skiphow\skiphow\2.0.0"
        r"\skills\skiphow\references\testing.md"
    )
    records = claude_read(
        "read-testing",
        foreign_path,
        "second exact line",
        start_line=2,
        total_lines=3,
    )
    monkeypatch.setattr(
        DOGFOOD,
        "observed_cache_reference_roster",
        lambda _roots, _version: ({"testing"}, True),
    )
    monkeypatch.setattr(
        DOGFOOD,
        "package_reference",
        lambda _version, _name, _roots=(): (body, "observed_cache_path"),
    )
    info = DOGFOOD.detect_references(
        Path("unused"), records, "2.0.0", (selected_root,)
    )["testing"]
    assert info["verdict"] == "matching_lines_observed"
    assert info["basis"] == "matching_decoded_line_text"
    assert info["actions"] == ["source_mismatch_path_observed"]
    assert info["mismatched_path_sources"] == ["cache_root"]


def test_dogfood_does_not_rewrite_backslashes_in_a_posix_path() -> None:
    path = r"/repo/literal\plugins\skiphow\skills\skiphow\SKILL.md"
    assert DOGFOOD.canonical_path_token(path) == path
    assert DOGFOOD.skill_paths(path, require_file=True) == []


def test_dogfood_distinguishes_posix_triple_slash_from_windows_paths() -> None:
    posix = "///repo/.AGENTS/SKILLS/SKIPHOW/REFERENCES/TESTING.MD"
    assert DOGFOOD.windows_path_semantics(posix) is False
    assert DOGFOOD.reference_name_from_path(posix) is None

    drive = (
        "C://Users/Person/.CLAUDE/PLUGINS/CACHE/SKIPHOW/SKIPHOW/2.0.0/"
        "SKILLS/SKIPHOW/REFERENCES/TESTING.MD"
    )
    assert DOGFOOD.windows_path_semantics(drive) is True
    assert DOGFOOD.reference_name_from_path(drive) == "testing"
    assert DOGFOOD.comparable_path_token(drive) == DOGFOOD.comparable_path_token(
        drive.replace("C://", "c:/").lower()
    )


@pytest.mark.parametrize(
    "repo",
    [
        Path("/tmp/.agents/skills/container"),
        Path("/tmp/.claude/plugins/cache/skiphow/skiphow/9.9.9/skills/container"),
        DOGFOOD.claude_home()
        / "plugins/cache/skiphow/skiphow/9.9.9/skills/container",
    ],
)
def test_dogfood_exact_repository_source_root_precedes_outer_markers(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: repo)
    path = repo / "plugins/skiphow/skills/skiphow/SKILL.md"
    (hit,) = DOGFOOD.skill_paths(str(path), require_file=True)
    assert hit["source"] == "plugin"
    assert hit["version"] == "unknown"
    assert hit["name"] == "skiphow"


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


@pytest.mark.parametrize("tool", ["Glob", "Grep"])
@pytest.mark.parametrize("selector", [r"references\testing.md", r".\references\testing.md"])
def test_dogfood_composes_relative_windows_glob_and_grep_paths(
    tool: str,
    selector: str,
) -> None:
    selector_field = "pattern" if tool == "Glob" else "glob"
    records = claude_call(
        f"{tool}-{selector}",
        tool,
        {
            "path": r".agents\skills\skiphow",
            selector_field: selector,
        },
    )
    assert DOGFOOD.observed_reference_names(records) == {"testing"}


def test_dogfood_relative_cache_paths_do_not_override_contract_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = (
        ".claude/plugins/cache/skiphow/skiphow/2.0.0/"
        "skills/skiphow/references/testing.md"
    )
    records = claude_call("read-testing", "Read", {"file_path": path})
    seen_roots: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        DOGFOOD, "version_reference_names", lambda _version: {"testing"}
    )
    monkeypatch.setattr(
        DOGFOOD, "version_reference_roster", lambda _version: ({"testing"}, True)
    )

    def artifact(
        _version: str, _name: str, roots: tuple[str, ...] = ()
    ) -> tuple[str, str]:
        seen_roots.append(roots)
        return "", "tag"

    monkeypatch.setattr(DOGFOOD, "package_reference", artifact)
    DOGFOOD.detect_references(Path("unused"), records, "2.0.0")
    assert seen_roots == [()]


@pytest.mark.parametrize(
    ("tool", "inputs"),
    [
        (
            "Glob",
            {
                "path": "/repo/.agents/skills/skiphow",
                "pattern": "references/testing.md",
            },
        ),
        (
            "Grep",
            {
                "path": "/repo/.agents/skills/skiphow",
                "glob": "references/testing.md",
                "pattern": "needle",
            },
        ),
    ],
)
def test_dogfood_composes_exact_search_base_and_selector(
    tool: str,
    inputs: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = claude_call("search", tool, inputs, "ok")
    (event,) = DOGFOOD.terminal_tool_events(records)
    expected = "/repo/.agents/skills/skiphow/references/testing.md"
    assert expected in DOGFOOD.event_path_payloads(event)
    assert DOGFOOD.observed_reference_names(records) == {"testing"}
    info = reference_info(monkeypatch, records, version="unknown")
    assert info["verdict"] == "search_action_observed"
    assert info["actions"] == ["search_action_observed"]


@pytest.mark.parametrize("tool", ["Glob", "Grep"])
def test_dogfood_does_not_compose_wildcard_selector_as_one_file(tool: str) -> None:
    inputs = {
        "path": "/repo/.agents/skills/skiphow",
        "pattern": "references/*.md" if tool == "Glob" else "needle",
    }
    if tool == "Grep":
        inputs["glob"] = "references/*.md"
    records = claude_call("search", tool, inputs, "ok")
    (event,) = DOGFOOD.terminal_tool_events(records)
    assert all("*" not in path for path in DOGFOOD.event_path_payloads(event))
    assert DOGFOOD.observed_reference_names(records) == set()


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


def test_dogfood_codex_tool_pairing_cannot_cross_turn_boundaries(
    tmp_path: Path,
) -> None:
    start, terminal = codex_command("true", item_id="cross-turn")
    records = [
        {"type": "turn.started"},
        start,
        {"type": "turn.completed", "usage": codex_usage()},
        {"type": "turn.started"},
        terminal,
        {"type": "turn.completed", "usage": codex_usage()},
    ]
    (event,) = DOGFOOD.codex_tool_events(records)
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False
    assert event["ambiguous_inputs"] == [start["item"], terminal["item"]]
    assert len(DOGFOOD.unpaired_tool_calls(records)) == 1
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 100)
    assert data["command_results"] == {}


def test_dogfood_codex_lifecycle_index_is_not_rebuilt_per_tool_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records: list[dict] = [
        {"type": "thread.started", "thread_id": "linear-thread"},
        {"type": "turn.started"},
    ]
    for index in range(250):
        records.extend(
            codex_command(
                f"command {index}", item_id=f"linear-command-{index}"
            )
        )
    records.append({"type": "turn.completed", "usage": codex_usage()})
    assert all(DOGFOOD.transcript_record_valid(record) for record in records)

    original = DOGFOOD.codex_turn_memberships
    calls = 0

    def counted(items: list[dict]) -> tuple[bool, dict[int, int]]:
        nonlocal calls
        calls += 1
        return original(items)

    monkeypatch.setattr(DOGFOOD, "codex_turn_memberships", counted)
    assert DOGFOOD.unpaired_tool_calls(records) == {}
    assert calls <= 4
    calls = 0
    events = DOGFOOD.codex_tool_events(records)
    assert len(events) == 250
    assert all(event["outcome"] == "succeeded" for event in events)
    assert calls <= 4


def test_dogfood_codex_item_ids_cannot_cross_item_types_or_responses(
    tmp_path: Path,
) -> None:
    start, terminal = codex_command("true", item_id="reused")
    response = {
        "type": "item.completed",
        "item": {"id": "reused", "type": "agent_message", "text": "premature"},
    }
    records = [start, response, terminal]
    assert all(DOGFOOD.transcript_record_valid(record) for record in records)
    assert DOGFOOD.codex_item_identity_ambiguities(records) == {"reused"}
    (event,) = DOGFOOD.codex_tool_events(records)
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False
    assert DOGFOOD.codex_turn_status(records) == "ambiguous_sequence"
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 1_000)
    assert data["command_results"] == {}
    assert data["report"]["selection_status"] == "unverified_later_activity"

    duplicate_responses = [
        {
            "type": "item.completed",
            "item": {"id": "answer", "type": "agent_message", "text": text},
        }
        for text in ("first", "second")
    ]
    assert DOGFOOD.codex_item_identity_ambiguities(duplicate_responses) == {
        "answer"
    }
    assert DOGFOOD.terminal_root_response(duplicate_responses) == (
        "",
        "unverified_ambiguous_sequence",
    )

    thread_without_turn = [
        {"type": "thread.started", "thread_id": "thread"},
        terminal,
        {
            "type": "item.completed",
            "item": {"id": "answer-2", "type": "agent_message", "text": "done"},
        },
    ]
    assert all(
        DOGFOOD.transcript_record_valid(record) for record in thread_without_turn
    )
    assert DOGFOOD.codex_turn_status(thread_without_turn) == "ambiguous_sequence"
    (thread_event,) = DOGFOOD.codex_tool_events(thread_without_turn)
    assert thread_event["outcome"] == "ambiguous"
    assert DOGFOOD.terminal_root_response(thread_without_turn) == (
        "",
        "unverified_ambiguous_sequence",
    )


@pytest.mark.parametrize(
    "event_types",
    [
        ["item.completed", "item.started"],
        ["item.updated", "item.started", "item.completed"],
        ["item.started", "item.completed", "item.updated"],
    ],
)
def test_dogfood_codex_todo_lifecycle_order_fails_closed(
    event_types: list[str],
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "thread"},
        {"type": "turn.started"},
        *[
            {
                "type": event_type,
                "item": {
                    "id": "todo",
                    "type": "todo_list",
                    "items": [{"text": event_type, "completed": False}],
                },
            }
            for event_type in event_types
        ],
        {
            "type": "item.completed",
            "item": {"id": "answer", "type": "agent_message", "text": "done"},
        },
        {"type": "turn.completed", "usage": codex_usage()},
    ]
    assert all(DOGFOOD.transcript_record_valid(record) for record in records)
    assert DOGFOOD.codex_item_identity_ambiguities(records) == {"todo"}
    assert DOGFOOD.codex_turn_status(records) == "ambiguous_sequence"
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "unverified_ambiguous_sequence",
    )


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


def test_dogfood_failed_spawn_with_receiver_is_not_successful_delegation(
    tmp_path: Path,
) -> None:
    terminal = {
        "type": "item.completed",
        "item": {
            "id": "collab",
            "type": "collab_tool_call",
            "tool": "spawn_agent",
            "sender_thread_id": "root",
            "receiver_thread_ids": ["child"],
            "prompt": "Review",
            "agents_states": {
                "child": {"status": "errored", "message": "failed"}
            },
            "status": "failed",
        },
    }
    (event,) = DOGFOOD.codex_tool_events([terminal])
    assert event["outcome"] == "failed"
    data = DOGFOOD.digest(write_transcript(tmp_path, [terminal]), 100)
    assert data["successful_structured_delegations"] == []


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


def test_dogfood_codex_file_changes_follow_windows_path_identity() -> None:
    start_path = r"C:\Repo\File.py"
    terminal_path = r"c:/repo/file.py"
    start = {
        "type": "item.started",
        "item": {
            "id": "change",
            "type": "file_change",
            "changes": [{"path": start_path, "kind": "update"}],
            "status": "in_progress",
        },
    }
    terminal = {
        "type": "item.completed",
        "item": {
            "id": "change",
            "type": "file_change",
            "changes": [{"path": terminal_path, "kind": "update"}],
            "status": "completed",
        },
    }
    assert DOGFOOD.comparable_path_token(start_path) == (
        DOGFOOD.comparable_path_token(terminal_path)
    )
    (event,) = DOGFOOD.codex_tool_events([start, terminal])
    assert event["outcome"] == "succeeded"

    duplicate_target = {
        **terminal["item"],
        "changes": [
            {"path": start_path, "kind": "update"},
            {"path": terminal_path, "kind": "delete"},
        ],
    }
    assert DOGFOOD.codex_file_changes_valid(duplicate_target["changes"]) is False
    assert DOGFOOD.codex_item_wire_valid(duplicate_target) is False

    posix_start = {
        **start,
        "item": {
            **start["item"],
            "changes": [{"path": "/repo/file.py", "kind": "update"}],
        },
    }
    posix_terminal = {
        **terminal,
        "item": {
            **terminal["item"],
            "changes": [{"path": "/repo/File.py", "kind": "update"}],
        },
    }
    (posix_event,) = DOGFOOD.codex_tool_events([posix_start, posix_terminal])
    assert posix_event["outcome"] == "ambiguous"


def test_dogfood_ambiguous_codex_id_preserves_every_structured_target() -> None:
    def item(path: str, status: str) -> dict:
        return {
            "id": "change",
            "type": "file_change",
            "status": status,
            "changes": [{"path": path, "kind": "update"}],
        }

    mismatch = [
        {"type": "item.started", "item": item("/repo/alpha.py", "in_progress")},
        {"type": "item.completed", "item": item("/repo/beta.py", "completed")},
    ]
    (mismatch_event,) = DOGFOOD.codex_tool_events(mismatch)
    assert mismatch_event["outcome"] == "ambiguous"
    assert DOGFOOD.event_path_payloads(mismatch_event) == [
        "/repo/alpha.py",
        "/repo/beta.py",
    ]

    records = [
        {"type": "item.started", "item": item("/repo/alpha.py", "in_progress")},
        {"type": "item.started", "item": item("/repo/beta.py", "in_progress")},
        {"type": "item.completed", "item": item("/repo/gamma.py", "completed")},
        {"type": "item.completed", "item": item("/repo/delta.py", "completed")},
    ]
    (event,) = DOGFOOD.codex_tool_events(records)
    assert event["outcome"] == "ambiguous"
    assert event["ambiguous_inputs"] == [record["item"] for record in records]
    assert DOGFOOD.event_path_payloads(event) == [
        "/repo/alpha.py",
        "/repo/beta.py",
        "/repo/gamma.py",
        "/repo/delta.py",
    ]

    reconciled_snapshot = [
        {
            "type": "item.started",
            "item": item(r"C:\Repo\Alpha.py", "in_progress"),
        },
        {
            "type": "item.completed",
            "item": item("c:/repo/alpha.py", "in_progress"),
        },
        {
            "type": "item.completed",
            "item": item("/repo/beta.py", "completed"),
        },
    ]
    (reconciled_event,) = DOGFOOD.codex_tool_events(reconciled_snapshot)
    assert reconciled_event["outcome"] == "ambiguous"
    assert reconciled_event["ambiguous_inputs"] == [
        record["item"] for record in reconciled_snapshot
    ]
    assert DOGFOOD.event_path_payloads(reconciled_event) == [
        r"C:\Repo\Alpha.py",
        "c:/repo/alpha.py",
        "/repo/beta.py",
    ]

    sidechain_collision = {
        "type": "item.completed",
        "isSidechain": True,
        "item": item("/delegate/private.py", "completed"),
    }
    scoped_records = [records[0], sidechain_collision, records[-1]]
    (scoped_event,) = DOGFOOD.codex_tool_events(scoped_records)
    assert scoped_event["outcome"] == "ambiguous"
    assert scoped_event["ambiguous_inputs"] == [
        scoped_records[0]["item"],
        scoped_records[-1]["item"],
    ]
    assert DOGFOOD.event_path_payloads(scoped_event) == [
        "/repo/alpha.py",
        "/repo/delta.py",
    ]


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
            "failed",
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
    assert DOGFOOD.owner_turns([unresolved, image_prompt]) == [
        {
            "at": "",
            "channel": "queued_attachment",
            "said": "[non-text owner input]",
        }
    ]
    assert DOGFOOD.owner_activity_record_indexes([unresolved, image_prompt]) == {1}
    assert DOGFOOD.ended_mid_tool([unresolved, image_prompt]) is False


@pytest.mark.parametrize(
    "later_block",
    [
        {"type": "text", "text": "I cannot continue without the file."},
        {"type": "thinking", "thinking": "still working"},
        {
            "type": "tool_result",
            "tool_use_id": "wrong-role-result",
            "content": "later result",
        },
    ],
)
def test_dogfood_same_record_substantive_block_is_later_activity(
    later_block: dict,
) -> None:
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
                later_block,
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


@pytest.mark.parametrize(
    "hidden_flag",
    ["isMeta", "isCompactSummary", "isVisibleInTranscriptOnly"],
)
def test_dogfood_hidden_plumbing_does_not_close_a_trailing_tool_call(
    hidden_flag: str,
) -> None:
    open_call = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "open",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    hidden = {
        "type": "assistant",
        hidden_flag: True,
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "hidden",
                    "name": "Read",
                    "input": {"file_path": "/repo/b.py"},
                }
            ]
        },
    }
    records = [open_call, hidden]
    assert DOGFOOD.unresolved_tool_calls(records) == {"claude:open:0:0": 0}
    assert DOGFOOD.ended_mid_tool(records) is True


def test_dogfood_virtual_claude_records_do_not_create_visible_evidence(
    tmp_path: Path,
) -> None:
    records = claude_call(
        "virtual-agent",
        "Agent",
        {"subagent_type": "reviewer", "description": "hidden work"},
        "done",
    )
    for record in records:
        record["isVirtual"] = True
        record["timestamp"] = "2099-01-01T00:00:00Z"
        record["cwd"] = "/virtual/project"
        record["gitBranch"] = "virtual-branch"
        record["version"] = "virtual-host"
    records.append(
        {
            "type": "assistant",
            "isVirtual": True,
            "message": {"content": [{"type": "text", "text": "virtual answer"}]},
        }
    )
    assert all(DOGFOOD.transcript_record_valid(record) for record in records)
    assert DOGFOOD.claude_tool_results(records) == {}
    assert DOGFOOD.terminal_tool_events(records) == []
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "no_applicable_assistant_text",
    )
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 1_000)
    assert data["successful_structured_delegations"] == []
    assert data["report"]["text"] == "(no assistant text found)"
    assert data["window"] == ["unknown", "unknown"]
    assert data["project"] == "unknown"
    assert data["branch"] == "unknown"
    assert data["host"] == "unknown"


def test_dogfood_virtual_codex_lifecycle_and_terminal_create_no_root_evidence(
    tmp_path: Path,
) -> None:
    start, terminal = codex_command(
        "printf hidden", "hidden output", item_id="virtual-command"
    )
    records = [
        {"type": "thread.started", "thread_id": "virtual-thread"},
        {"type": "turn.started", "cwd": "/virtual/project"},
        start,
        terminal,
        {
            "type": "item.completed",
            "item": {
                "id": "virtual-answer",
                "type": "agent_message",
                "text": "virtual answer",
            },
        },
        {"type": "turn.completed", "usage": codex_usage()},
    ]
    for record in records:
        record["isVirtual"] = True

    assert all(DOGFOOD.transcript_record_valid(record) for record in records)
    assert DOGFOOD.codex_thread_identity(records) == ("not_observed", "")
    assert DOGFOOD.codex_turn_status(records) == "not_observed"
    assert DOGFOOD.terminal_tool_events(records) == []
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "no_applicable_assistant_text",
    )
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 1_000)
    assert data["command_results"] == {}
    assert data["report"]["text"] == "(no assistant text found)"
    assert data["confounders"]["thread_identity"] == "not_observed"


@pytest.mark.parametrize(
    ("outer_type", "message_role"),
    [("assistant", "user"), ("user", "assistant")],
)
def test_dogfood_claude_message_role_must_match_its_envelope(
    outer_type: str,
    message_role: str,
) -> None:
    record = {
        "type": outer_type,
        "message": {"role": message_role, "content": []},
    }
    assert DOGFOOD.transcript_record_valid(record) is False


def test_dogfood_model_visible_peer_meta_input_is_later_activity() -> None:
    open_call = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "open",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    peer = {
        "type": "user",
        "userType": "external",
        "isMeta": True,
        "message": {"content": "Peer agent supplied new model-visible input."},
    }
    assert DOGFOOD.model_visible_meta_input_record(peer) is True
    assert DOGFOOD.record_has_later_root_activity(peer) is True
    assert DOGFOOD.ended_mid_tool([open_call, peer]) is False
    assert DOGFOOD.terminal_root_response(
        [
            {"type": "assistant", "message": {"content": "premature"}},
            peer,
        ]
    ) == ("", "unverified_later_activity")


def test_dogfood_model_visible_skill_injection_is_later_activity() -> None:
    open_call = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "open",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    base = host_cache_root(DOGFOOD.claude_home()) / "2.0.0/skills/skiphow"
    injection = {
        "type": "user",
        "userType": "external",
        "isMeta": True,
        "message": {
            "content": (
                f"Base directory for this skill: {base}\n"
                "# SkipHow\n\nExact model-visible owner contract."
            )
        },
    }
    assert DOGFOOD.model_visible_skill_frame_record(injection) is True
    assert DOGFOOD.ended_mid_tool([open_call, injection]) is False


@pytest.mark.parametrize(
    "later",
    [
        {"type": "user", "message": {"content": "new root input"}},
        {
            "type": "user",
            "origin": {"kind": "hook"},
            "message": {"content": "new host input"},
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": "AA==",
                        },
                    }
                ]
            },
        },
        {
            "type": "user",
            "message": {
                "content": "<task-notification>later host activity</task-notification>"
            },
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "thinking", "thinking": "later"}]},
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "future_activity", "value": "later"}]},
        },
        {
            "type": "assistant",
            "message": {"stop_reason": "end_turn", "content": []},
        },
    ],
)
def test_dogfood_every_substantive_visible_root_record_is_later_activity(
    later: dict,
) -> None:
    open_call = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "open",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    premature = {"type": "assistant", "message": {"content": "premature"}}
    assert DOGFOOD.record_has_later_root_activity(later) is True
    assert DOGFOOD.terminal_root_response([premature, later]) == (
        "",
        "unverified_later_activity",
    )
    assert DOGFOOD.ended_mid_tool([open_call, later]) is False


@pytest.mark.parametrize(
    "payload",
    [
        {"prompt": "queued text"},
        {"command": "queued text"},
        {"prompt": [{"type": "text", "text": "queued text"}]},
        {
            "prompt": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "AA==",
                    },
                }
            ]
        },
        {"prompt": "<task-notification>later host activity</task-notification>"},
        {"prompt": "  ", "command": "actual queued text"},
    ],
)
def test_dogfood_every_queued_attachment_payload_is_later_activity(
    payload: dict,
) -> None:
    open_call = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "open",
                    "name": "Read",
                    "input": {"file_path": "/repo/a.py"},
                }
            ]
        },
    }
    later = {
        "type": "user",
        "attachment": {
            "type": "queued_command",
            "commandMode": "prompt",
            **payload,
        },
    }
    assert DOGFOOD.transcript_record_valid(later) is True
    assert DOGFOOD.queued_attachment_activity(later) is True
    assert DOGFOOD.record_has_later_root_activity(later) is True
    assert DOGFOOD.ended_mid_tool([open_call, later]) is False


@pytest.mark.parametrize(
    "payload",
    [
        {"prompt": ""},
        {"prompt": "  "},
        {"prompt": [{"type": "text", "text": "\t"}]},
        {"prompt": "  ", "command": "\t"},
    ],
)
def test_dogfood_empty_queued_attachment_payload_is_not_later_activity(
    payload: dict,
) -> None:
    record = {
        "type": "user",
        "attachment": {
            "type": "queued_command",
            "commandMode": "prompt",
            **payload,
        },
    }
    assert DOGFOOD.transcript_record_valid(record) is True
    assert DOGFOOD.queued_attachment_activity(record) is False
    assert DOGFOOD.record_has_later_root_activity(record) is False


@pytest.mark.parametrize(
    "later",
    [
        {"type": "user", "message": {"content": "  "}},
        {"type": "assistant", "message": {"content": []}},
        {"type": "assistant", "message": {"content": "\n"}},
    ],
)
def test_dogfood_empty_visible_envelopes_are_not_later_activity(later: dict) -> None:
    assert DOGFOOD.record_has_later_root_activity(later) is False


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


@pytest.mark.parametrize("stop_reason", ["end_turn", "stop_sequence", "refusal"])
def test_dogfood_terminal_claude_stop_reasons_allow_a_terminal_response(
    stop_reason: str,
) -> None:
    record = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "stop_reason": stop_reason,
            "content": [{"type": "text", "text": "done"}],
        },
    }
    assert DOGFOOD.transcript_record_valid(record) is True
    assert DOGFOOD.terminal_root_response([record]) == (
        "done",
        "terminal_root_response",
    )


@pytest.mark.parametrize(
    "stop_reason",
    [
        "compaction",
        "tool_use",
        "max_tokens",
        "pause_turn",
        "model_context_window_exceeded",
    ],
)
def test_dogfood_nonterminal_claude_stop_reasons_fail_response_selection_closed(
    stop_reason: str,
) -> None:
    record = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "stop_reason": stop_reason,
            "content": [{"type": "text", "text": "partial"}],
        },
    }
    assert DOGFOOD.transcript_record_valid(record) is True
    assert DOGFOOD.terminal_root_response([record]) == (
        "",
        "unverified_nonterminal_stop_reason",
    )


def test_dogfood_compaction_stop_reason_is_positive_compaction_evidence() -> None:
    record = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "stop_reason": "compaction",
            "content": [{"type": "text", "text": "partial"}],
        },
    }
    assert DOGFOOD.transcript_record_valid(record) is True
    assert DOGFOOD.compaction_status([record]) is True
    assert DOGFOOD.compaction_status([{**record, "isSidechain": True}]) == "unknown"


def test_dogfood_null_stop_reason_is_valid_partial_assistant_evidence() -> None:
    partial = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "stop_reason": None,
            "content": [{"type": "text", "text": "partial chunk"}],
        },
    }
    final = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "final chunk"}],
        },
    }
    assert DOGFOOD.transcript_record_valid(partial) is True
    assert DOGFOOD.terminal_root_response([partial]) == (
        "",
        "unverified_nonterminal_stop_reason",
    )
    assert DOGFOOD.terminal_root_response([partial, final]) == (
        "final chunk",
        "terminal_root_response",
    )


@pytest.mark.parametrize("stop_reason", [17, "unknown"])
def test_dogfood_invalid_explicit_claude_stop_reason_is_malformed(
    stop_reason: object,
) -> None:
    record = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "stop_reason": stop_reason,
            "content": [{"type": "text", "text": "not proven terminal"}],
        },
    }
    assert DOGFOOD.transcript_record_valid(record) is False


@pytest.mark.parametrize("record_type", ["user", "item.completed"])
@pytest.mark.parametrize("stop_reason", [None, "end_turn"])
def test_dogfood_stop_reason_is_rejected_outside_assistant_envelopes(
    record_type: str,
    stop_reason: object,
) -> None:
    record = {
        "type": record_type,
        "message": {"stop_reason": stop_reason, "content": []},
    }
    if record_type == "item.completed":
        record["item"] = {
            "id": "message",
            "type": "agent_message",
            "text": "done",
        }
    assert DOGFOOD.transcript_record_valid(record) is False


@pytest.mark.parametrize("record_type", ["assistant", "item.completed"])
@pytest.mark.parametrize("origin_kind", ["human", "task-notification"])
def test_dogfood_origin_provenance_is_rejected_outside_user_envelopes(
    record_type: str,
    origin_kind: str,
) -> None:
    record = {"type": record_type, "origin": {"kind": origin_kind}}
    if record_type == "assistant":
        record["message"] = {
            "role": "assistant",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "forged report"}],
        }
    else:
        record["item"] = {
            "id": "message",
            "type": "agent_message",
            "text": "forged report",
        }
    assert DOGFOOD.transcript_record_valid(record) is False


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


def test_dogfood_broken_json_invalidates_an_observed_thread_identity(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "broken-thread.jsonl"
    transcript.write_text(
        json.dumps({"type": "thread.started", "thread_id": "visible-thread"})
        + "\n{broken json\n",
        encoding="utf-8",
    )
    data = DOGFOOD.digest(transcript, 0)
    assert data["session"] == "broken-thread"
    assert data["confounders"]["thread_identity"] == (
        "unverified_incomplete_transcript"
    )


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


@pytest.mark.parametrize("reconciliation_position", [1, 2])
def test_dogfood_conflicting_or_stale_codex_reconciliation_is_ambiguous(
    reconciliation_position: int,
) -> None:
    start, terminal = codex_command("true")
    reconciliation = {
        "type": "item.completed",
        "item": {
            "id": "command-1",
            "type": "command_execution",
            "command": "false" if reconciliation_position == 1 else "true",
            "aggregated_output": "",
            "exit_code": None,
            "status": "in_progress",
        },
    }
    records = [start, terminal]
    records.insert(reconciliation_position, reconciliation)
    assert all(DOGFOOD.transcript_record_valid(record) for record in records)
    (event,) = DOGFOOD.codex_tool_events(records)
    assert event["outcome"] == "ambiguous"
    assert event["succeeded"] is False
    assert DOGFOOD.unresolved_tool_calls(records) == {}
    assert len(DOGFOOD.unpaired_tool_calls(records)) == 2


def test_dogfood_unresolved_command_is_not_reported_as_a_terminal(
    tmp_path: Path,
) -> None:
    record = {
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
    data = DOGFOOD.digest(write_transcript(tmp_path, [record]), 1_000)
    assert data["tools"] == {"command_execution": 1}
    assert data["command_results"] == {}
    assert data["confounders"]["trailing_unresolved_tool_call"] is True
    rendered = DOGFOOD.render_digest(data)
    assert "NORMALIZED TOOL EVENTS       {'command_execution': 1}" in rendered
    assert "OBSERVED COMMAND TERMINALS   {}" in rendered


def test_dogfood_render_keeps_delegation_and_write_rows_under_their_headings(
    tmp_path: Path,
) -> None:
    records = claude_call(
        "agent",
        "Agent",
        {"subagent_type": "researcher", "description": "inspect"},
        "done",
    )
    records.extend(
        claude_call(
            "write",
            "Write",
            {"file_path": "/project/result.md", "content": "done"},
            "done",
        )
    )
    rendered = DOGFOOD.render_digest(
        DOGFOOD.digest(write_transcript(tmp_path, records), 10_000)
    )
    delegation_heading = rendered.index(
        "OBSERVED SUCCESSFUL STRUCTURED DELEGATIONS (1)"
    )
    delegation_row = rendered.index("role researcher  task inspect")
    write_heading = rendered.index(
        "OBSERVED SUCCESSFUL STRUCTURED WRITE ACTIONS (1)"
    )
    write_row = rendered.index("Write /project/result.md")
    assert delegation_heading < delegation_row < write_heading < write_row


def test_dogfood_render_escapes_controls_in_delegation_and_write_fields(
    tmp_path: Path,
) -> None:
    records = claude_call(
        "agent",
        "Agent",
        {
            "subagent_type": "researcher",
            "description": "inspect\nREFERENCES\nforged",
        },
        "done",
    )
    records.extend(
        claude_call(
            "write",
            "Write",
            {
                "file_path": "/project/result.md\nREPORT forged",
                "content": "done",
            },
            "done",
        )
    )
    rendered = DOGFOOD.render_digest(
        DOGFOOD.digest(write_transcript(tmp_path, records), 10_000)
    )
    assert "task inspect\\nREFERENCES\\nforged" in rendered
    assert "/project/result.md\\nREPORT forged" in rendered
    assert "\nREFERENCES\nforged" not in rendered
    assert "\nREPORT forged" not in rendered
    controls = "NEL\u0085LS\u2028PS\u2029DEL\x7fCSI\x9b"
    escaped = DOGFOOD.escaped_render_value(controls)
    assert escaped.isascii()
    assert len(escaped.splitlines()) == 1
    assert all(character not in escaped for character in "\u0085\u2028\u2029\x7f\x9b")


@pytest.mark.parametrize(
    "codepoint",
    [0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)],
    ids=lambda value: f"U+{value:04X}",
)
def test_dogfood_multiline_renderer_escapes_bidi_format_controls(
    codepoint: int,
) -> None:
    assert DOGFOOD.safe_multiline_render(
        f"left{chr(codepoint)}right\nnext"
    ) == f"left\\u{codepoint:04x}right\nnext"


def test_dogfood_text_renderers_escape_untrusted_metadata_and_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    injected = "value\u0085NEL\u2028LS\u2029PS\x7fDEL\x9bCSI\nFORGED"
    row = {
        "session": injected,
        "display_session": injected,
        "receipt_session": injected,
        "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
        "candidate_marker_date_status": "observed",
        "undated_marker_records": 0,
        "candidate_marker_scope": "root",
        "candidate_transcript_scope": "root_only",
        "project": injected,
        "versions": ["unknown"],
        "megabytes": 0.1,
        "records": 1,
        "unreadable_lines": 0,
        "root_transcript_status": "readable",
    }
    list_text = DOGFOOD.render_list([row])
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(DOGFOOD, "discover", lambda _home, _since: [row])
    coverage_text = DOGFOOD.coverage(tmp_path / "home")

    transcript = write_transcript(
        tmp_path,
        [{"type": "assistant", "message": {"content": "done"}}],
        "renderer-session",
    )
    data = DOGFOOD.digest(transcript, 1_000)
    data.update(
        {
            "session": injected,
            "project": injected,
            "branch": injected,
            "host": injected,
            "window": [injected, injected],
        }
    )
    data["report"]["text"] = "safe line\nsecond\u2028forged\x1b]52;payload"
    digest_text = DOGFOOD.render_digest(data)

    for rendered in (list_text, coverage_text, digest_text):
        assert all(
            character not in rendered
            for character in "\u0085\u2028\u2029\x7f\x9b\x1b"
        )
    assert "\\u2028" in list_text
    assert "second\\u2028forged\\u001b]52;payload" in digest_text


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
    assert data["models"] == "unverified_incomplete_transcript"
    assert data["owner_turns"] == "unverified_incomplete_transcript"
    assert data["tools"] == "unverified_incomplete_transcript"
    assert data["checkout_metadata_observations"] == (
        "unverified_incomplete_transcript"
    )
    assert data["usage"] == "unverified_incomplete_transcript"
    assert data["command_results"] == {}
    assert data["successful_structured_delegations"] == []
    assert data["successful_structured_write_actions"] == []
    assert data["confounders"] == {
        "compaction_observed": "unknown",
        "trailing_unresolved_tool_call": "unknown",
        "unpaired_tool_call_count": "unknown",
        "turn_sequence": "unverified_incomplete_transcript",
        "thread_identity": "unverified_incomplete_transcript",
        "plugin_version_identity": "unverified_incomplete_transcript",
        "contract_body_identity": "unverified_incomplete_transcript",
        "contract_sequence": "unverified_incomplete_transcript",
    }
    assert data["report"]["selection_status"] == "unverified_incomplete_transcript"
    rendered = DOGFOOD.render_digest(data)
    assert "SKILLS\n  UNVERIFIED: incomplete transcript" in rendered
    assert (
        "REFERENCES\n  UNVERIFIED: incomplete transcript; "
        "reference absence cannot be established"
    ) in rendered
    assert "OBSERVED COMMAND TERMINALS   UNVERIFIED" in rendered
    assert "OBSERVED SUCCESSFUL STRUCTURED DELEGATIONS (UNVERIFIED)" in rendered
    assert "OBSERVED SUCCESSFUL STRUCTURED WRITE ACTIONS (UNVERIFIED)" in rendered
    assert "OBSERVED CHECKOUT METADATA (UNVERIFIED)" in rendered
    assert "UNVERIFIED FALLBACK ASSISTANT TEXT" in rendered
    assert rendered.count(
        "UNVERIFIED: incomplete transcript; absence cannot be established"
    ) == 3


@pytest.mark.parametrize(
    "invalid_bound",
    [("--max", "0"), ("--max", "-3"), ("--chars", "-1")],
)
def test_dogfood_grep_rejects_unsafe_bounds_before_reading_transcript(
    invalid_bound: tuple[str, str],
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "private.jsonl"
    secret = "PRIVATE-OWNER-TEXT-" + "x" * 10_000
    transcript.write_text(secret + "\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / ".claude/skills/dogfood/sessions.py"),
            "--home",
            str(tmp_path / "home"),
            "grep",
            str(transcript),
            "PRIVATE-OWNER-TEXT",
            *invalid_bound,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "PRIVATE-OWNER-TEXT" not in result.stdout
    assert secret not in result.stderr


def test_dogfood_argparse_never_reflects_unknown_terminal_control_payloads(
    tmp_path: Path,
) -> None:
    private_payload = "PRIVATE-OSC52-PAYLOAD"
    unknown = f"--unknown\n\x1b]52;c;{private_payload}\x07"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / ".claude/skills/dogfood/sessions.py"),
            "--home",
            str(tmp_path / "home"),
            "list",
            unknown,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "\x1b" not in result.stderr
    assert "\x07" not in result.stderr
    assert private_payload not in result.stderr
    assert "unrecognized arguments" in result.stderr


def test_dogfood_grep_zero_chars_emits_no_private_line_content(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "private.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "PRIVATE-TIMESTAMP",
                "message": {"content": "PRIVATE-OWNER-TEXT"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / ".claude/skills/dogfood/sessions.py"),
            "--home",
            str(tmp_path / "home"),
            "grep",
            str(transcript),
            "PRIVATE-OWNER-TEXT",
            "--chars",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "L1: [content omitted]"
    assert "PRIVATE" not in result.stdout


def test_dogfood_grep_positive_bound_includes_all_private_metadata(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "private.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "SECRET-TIMESTAMP\nFORGED-ROW" + "x" * 5_000,
                "message": {"content": "MATCH"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / ".claude/skills/dogfood/sessions.py"),
            "--home",
            str(tmp_path / "home"),
            "grep",
            str(transcript),
            "MATCH",
            "--chars",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "SECRET" not in result.stdout
    assert "FORGED" not in result.stdout
    assert len(result.stdout.splitlines()[0]) < 30


@pytest.mark.parametrize("mutation", ["replace", "append"])
def test_dogfood_grep_buffers_output_until_transcript_identity_is_stable(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    transcript = tmp_path / "private.jsonl"
    private_line = "PRIVATE-OWNER-TEXT"
    transcript.write_text(private_line + "\n", encoding="utf-8")
    replacement = tmp_path / "replacement.tmp"
    replacement.write_text(private_line + "\n", encoding="utf-8")
    original = DOGFOOD.opened_transcript_stable
    mutated = False

    def mutate(path: Path, handle: object, before: os.stat_result) -> bool:
        nonlocal mutated
        if path == transcript and not mutated:
            if mutation == "replace":
                os.replace(replacement, transcript)
            else:
                with transcript.open("a", encoding="utf-8") as output:
                    output.write("PRIVATE-APPENDED-TEXT\n")
            mutated = True
        return original(path, handle, before)

    monkeypatch.setattr(DOGFOOD, "opened_transcript_stable", mutate)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sessions.py",
            "--home",
            str(tmp_path / "home"),
            "grep",
            str(transcript),
            "PRIVATE",
        ],
    )
    with pytest.raises(SystemExit) as error:
        DOGFOOD.main()
    captured = capsys.readouterr()
    assert str(error.value) == "raw transcript is unavailable for bounded grep"
    assert captured.out == ""
    assert private_line not in captured.err


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
    monkeypatch.setattr(
        DOGFOOD, "version_reference_roster", lambda _version: ({"testing"}, True)
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
        "mismatched_path_sources": [],
    }
    assert data["confounders"]["plugin_version_identity"] == (
        "unverified_incomplete_transcript"
    )
    assert data["confounders"]["contract_sequence"] == (
        "unverified_incomplete_transcript"
    )
    assert "2.0.0" not in json.dumps(data, sort_keys=True)


@pytest.mark.parametrize(
    "version",
    ["1.0.9", "1.1.0", "1.13.9", "1.14.0", "2.0.0", "unknown"],
)
def test_dogfood_report_selection_uses_the_terminal_root_response(
    version: str,
) -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "owner request"},
        },
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
    assert DOGFOOD.report_text(records, [version]) == "current final"


def test_dogfood_report_selection_does_not_reuse_an_earlier_owner_turn() -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "first request"},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Result\nstale\nEvidence\nstale proof"}
                ]
            },
        },
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "second request"},
        },
    ]
    assert DOGFOOD.report_text(records, ["1.13.0"]) == ""
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "no_applicable_assistant_text",
    )


def test_dogfood_report_selection_does_not_reuse_text_after_image_only_owner_turn() -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "first request"},
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "old result"}]},
        },
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": "AA==",
                        },
                    }
                ]
            },
        },
    ]
    assert DOGFOOD.transcript_record_valid(records[-1]) is True
    assert DOGFOOD.owner_activity_record_indexes(records) == {0, 2}
    assert DOGFOOD.owner_turns(records)[-1]["said"] == "[non-text owner input]"
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "no_applicable_assistant_text",
    )


def test_dogfood_any_model_visible_skill_frame_is_later_activity(
    tmp_path: Path,
) -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "owner request"},
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "premature"}]},
        },
        {
            "type": "user",
            "userType": "external",
            "isMeta": True,
            "message": {
                "content": (
                    "Base directory for this skill: /opt/host/skills/other\n"
                    "# Other skill"
                )
            },
        },
    ]
    assert DOGFOOD.model_visible_skill_frame_record(records[-1]) is True
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "unverified_later_activity",
    )
    rendered = DOGFOOD.render_digest(
        DOGFOOD.digest(write_transcript(tmp_path, records), 10_000)
    )
    assert "UNVERIFIED FALLBACK ASSISTANT TEXT\npremature" in rendered
    assert "SELECTED TERMINAL ASSISTANT TEXT" not in rendered


def test_dogfood_codex_response_after_turn_terminal_is_ambiguous() -> None:
    records = [
        {"type": "thread.started", "thread_id": "thread"},
        {"type": "turn.started"},
        {"type": "turn.completed", "usage": codex_usage()},
        {
            "type": "item.completed",
            "item": {"id": "late", "type": "agent_message", "text": "late"},
        },
    ]
    assert all(DOGFOOD.transcript_record_valid(record) for record in records)
    assert DOGFOOD.codex_turn_status(records) == "ambiguous_sequence"
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "unverified_ambiguous_sequence",
    )


@pytest.mark.parametrize(
    "later_block",
    [
        {"type": "thinking", "thinking": "still working"},
        {"type": "future_model_activity", "payload": "still working"},
    ],
)
def test_dogfood_later_nontext_assistant_activity_invalidates_a_response(
    later_block: dict,
) -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "owner request"},
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "premature"}]},
        },
        {"type": "assistant", "message": {"content": [later_block]}},
    ]
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "unverified_later_activity",
    )


@pytest.mark.parametrize(
    "later_block",
    [
        {"type": "thinking", "thinking": "still working"},
        {"type": "future_model_activity", "payload": "still working"},
    ],
)
def test_dogfood_same_record_nontext_activity_after_text_is_not_terminal(
    later_block: dict,
) -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "owner request"},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "premature"},
                    later_block,
                ]
            },
        },
    ]
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "unverified_later_activity",
    )


@pytest.mark.parametrize(
    "content",
    [
        [
            {"type": "tool_use", "id": "open", "name": "Read", "input": {}},
            {"type": "text", "text": "premature"},
        ],
        [
            {"type": "text", "text": "premature"},
            {"type": "tool_use", "id": "open", "name": "Read", "input": {}},
            {"type": "text", "text": "still premature"},
        ],
    ],
)
def test_dogfood_response_record_with_unresolved_tool_is_not_terminal(
    content: list[dict],
) -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "owner request"},
        },
        {"type": "assistant", "message": {"content": content}},
    ]
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "unverified_unresolved_tool_call",
    )


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_dogfood_earlier_unresolved_tool_blocks_a_later_text_response(
    host: str,
) -> None:
    owner = {
        "type": "user",
        "origin": {"kind": "human"},
        "message": {"content": "owner request"},
    }
    if host == "claude":
        activity = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "open", "name": "Read", "input": {}}
                ]
            },
        }
        response = {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "premature"}]},
        }
        records = [owner, activity, response]
    else:
        records = [
            owner,
            {"type": "thread.started", "thread_id": "thread"},
            {"type": "turn.started"},
            {
                "type": "item.started",
                "item": {
                    "id": "open",
                    "type": "command_execution",
                    "command": "opaque",
                    "aggregated_output": "",
                    "exit_code": None,
                    "status": "in_progress",
                },
            },
            {
                "type": "item.completed",
                "item": {"id": "reply", "type": "agent_message", "text": "premature"},
            },
        ]
    assert DOGFOOD.terminal_root_response(records) == (
        "",
        "unverified_unresolved_tool_call",
    )


@pytest.mark.parametrize(
    "hidden_flag",
    ["isMeta", "isCompactSummary", "isVisibleInTranscriptOnly"],
)
def test_dogfood_hidden_nontext_assistant_plumbing_does_not_invalidate_a_response(
    hidden_flag: str,
) -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "owner request"},
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "done"}]},
        },
        {
            "type": "assistant",
            hidden_flag: True,
            "message": {
                "content": [
                    {"type": "thinking", "thinking": "hidden plumbing"}
                ]
            },
        },
    ]
    assert DOGFOOD.terminal_root_response(records) == (
        "done",
        "terminal_root_response",
    )


def test_dogfood_nontext_assistant_activity_before_final_text_remains_terminal() -> None:
    records = [
        {
            "type": "user",
            "origin": {"kind": "human"},
            "message": {"content": "owner request"},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "thinking", "thinking": "working"},
                    {"type": "text", "text": "done"},
                ]
            },
        },
    ]
    assert DOGFOOD.terminal_root_response(records) == (
        "done",
        "terminal_root_response",
    )


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
                "_cache_root": str(host_cache_root(DOGFOOD.claude_home())),
                "attribution": "explicit_skill_call",
                "at": "",
                "body_fingerprint": hashlib.sha256(
                    "# SkipHow\n\nFinish the authorized result.".encode("utf-8")
                ).hexdigest(),
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


def test_dogfood_ambiguous_successful_activation_keeps_unknown_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    monkeypatch.setattr(DOGFOOD, "claude_home", lambda: home)
    body = "# SkipHow\n\nExact owner body.\n"
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    base = host_cache_root(home) / "2.0.0/skills/skiphow"
    records = claude_call(
        "known",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records[0]["uuid"] = "known-call"
    records[1].update(
        {
            "uuid": "known-result",
            "parentUuid": "known-call",
            "sourceToolAssistantUUID": "known-call",
        }
    )
    records.append(
        {
            "type": "user",
            "uuid": "known-injection",
            "parentUuid": "known-result",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "known",
            "message": {
                "content": f"Base directory for this skill: {base}\n{body}"
            },
        }
    )
    records.extend(
        [
            {
                "type": "assistant",
                "uuid": "duplicate-call-a",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "duplicate",
                            "name": "Skill",
                            "input": {"skill": "skiphow:skiphow"},
                        }
                    ]
                },
            },
            {
                "type": "assistant",
                "uuid": "duplicate-call-b",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "duplicate",
                            "name": "Skill",
                            "input": {"skill": "skiphow:skiphow"},
                        }
                    ]
                },
            },
            {
                "type": "user",
                "uuid": "duplicate-result",
                "parentUuid": "duplicate-call-b",
                "sourceToolAssistantUUID": "duplicate-call-b",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "duplicate",
                            "is_error": False,
                            "content": "Skill loaded",
                        }
                    ]
                },
            },
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "cwd": "/work/customer-app",
                "origin": {"kind": "human"},
                "message": {"content": "skiphow:skiphow"},
            },
        ]
    )
    assert DOGFOOD.ambiguous_successful_skill_result_ids(records) == {
        "duplicate"
    }
    assert DOGFOOD.contract_identity_values(records) == ["2.0.0", "unknown"]
    assert DOGFOOD.contract_identity_status(["2.0.0", "unknown"]) == (
        "partially_unknown"
    )

    transcript = home / "projects/project/ambiguous-contract.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    data = DOGFOOD.digest(transcript, 10_000, home)
    assert data["plugin_version_values_observed"] == ["2.0.0", "unknown"]
    assert data["confounders"]["plugin_version_identity"] == "partially_unknown"
    (row,) = DOGFOOD.discover(home, None, "2026-08-27")
    assert row["versions"] == ["2.0.0", "unknown"]

    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "ambiguous-contract",
                len(records),
                ["2.0.0"],
                row["evidence_fingerprint"],
            )
        ],
    )
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    coverage = DOGFOOD.coverage(home)
    assert next(
        line for line in coverage.splitlines() if "ambiguous-contract" in line
    ).endswith("STALE")


def test_dogfood_conflicting_duplicate_skill_names_keep_unknown_identity() -> None:
    records = claude_call(
        "known",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records.extend(
        [
            {
                "type": "assistant",
                "uuid": "duplicate-owner-call",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "duplicate",
                            "name": "Skill",
                            "input": {"skill": "skiphow:skiphow"},
                        }
                    ]
                },
            },
            {
                "type": "assistant",
                "uuid": "duplicate-other-call",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "duplicate",
                            "name": "Skill",
                            "input": {"skill": "skiphow:other"},
                        }
                    ]
                },
            },
            {
                "type": "user",
                "uuid": "duplicate-result",
                "parentUuid": "duplicate-other-call",
                "sourceToolAssistantUUID": "duplicate-other-call",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "duplicate",
                            "is_error": False,
                            "content": "Skill loaded",
                        }
                    ]
                },
            },
        ]
    )
    observations = {
        "known": {
            "status": "body_observed",
            "source": "plugin",
            "version": "2.0.0",
            "_cache_root": str(host_cache_root(DOGFOOD.claude_home())),
        }
    }
    assert DOGFOOD.skiphow_skill_call_names(records) == {"known": "skiphow"}
    assert DOGFOOD.ambiguous_claude_tool_ids(records) == {"duplicate"}
    assert DOGFOOD.ambiguous_successful_skill_result_ids(records) == {
        "duplicate"
    }
    values = DOGFOOD.contract_identity_values(records, observations)
    assert values == ["2.0.0", "unknown"]
    assert DOGFOOD.contract_identity_status(values) == "partially_unknown"


def test_dogfood_conflicting_aliases_on_one_successful_skill_call_add_unknown() -> None:
    records = claude_call(
        "known",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records.extend(
        claude_call(
            "conflicting-aliases",
            "Skill",
            {"skill": "skiphow:skiphow", "name": "skiphow:other"},
            "Skill loaded",
        )
    )
    observations = {
        "known": {
            "status": "body_observed",
            "source": "plugin",
            "version": "2.0.0",
            "body_fingerprint": "known-body",
            "_cache_root": str(host_cache_root(DOGFOOD.claude_home())),
        }
    }
    assert DOGFOOD.skiphow_skill_call_names(records) == {"known": "skiphow"}
    assert DOGFOOD.ambiguous_successful_skill_result_ids(records) == {
        "conflicting-aliases"
    }
    assert DOGFOOD.contract_identity_values(records, observations) == [
        "2.0.0",
        "unknown",
    ]
    assert any(
        skill["name"] == "unknown"
        and skill["signals"] == {"activation_ambiguous": 1}
        for skill in DOGFOOD.detect_skills(records)
    )


@pytest.mark.parametrize("leftover_uuid", [None, "duplicate-frame"])
def test_dogfood_every_leftover_skill_frame_contributes_to_contract_identity(
    leftover_uuid: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    monkeypatch.setattr(DOGFOOD, "claude_home", lambda: home)
    bodies = {
        "2.0.0": "# SkipHow\n\nContract A.\n",
        "2.0.1": "# SkipHow\n\nContract B.\n",
    }
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda version, _name, _root="": (bodies[version], "tag"),
    )
    cache = host_cache_root(home)
    records = claude_call(
        "known", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
    )
    records[0]["uuid"] = "known-call"
    records[1].update(
        {
            "uuid": "known-result",
            "parentUuid": "known-call",
            "sourceToolAssistantUUID": "known-call",
        }
    )
    records.append(
        {
            "type": "user",
            "uuid": "known-frame",
            "parentUuid": "known-result",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "known",
            "message": {
                "content": (
                    "Base directory for this skill: "
                    f"{cache / '2.0.0/skills/skiphow'}\n{bodies['2.0.0']}"
                )
            },
        }
    )
    leftover = {
        "type": "user",
        "userType": "external",
        "isMeta": True,
        "sourceToolUseID": "wrong-or-stale-id",
        "message": {
            "content": (
                "Base directory for this skill: "
                f"{cache / '2.0.1/skills/skiphow'}\n{bodies['2.0.1']}"
            )
        },
    }
    if leftover_uuid is not None:
        leftover["uuid"] = leftover_uuid
    records.append(leftover)
    if leftover_uuid is not None:
        records.append(
            {
                "type": "user",
                "uuid": leftover_uuid,
                "message": {"content": "duplicate UUID plumbing"},
            }
        )
    observations = DOGFOOD.skill_injection_observations(records)
    assert {observation.get("version") for observation in observations.values()} >= {
        "2.0.0",
        "2.0.1",
    }
    assert DOGFOOD.contract_identity_values(records, observations) == [
        "2.0.0",
        "2.0.1",
    ]
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 10_000)
    assert data["confounders"]["plugin_version_identity"] == "mixed"


def test_dogfood_same_version_different_exact_bodies_block_contract_scoring(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claude_home = tmp_path / "claude-home"
    codex_home = tmp_path / "codex-home"
    monkeypatch.setattr(DOGFOOD, "claude_home", lambda: claude_home)
    monkeypatch.setattr(DOGFOOD, "codex_home", lambda: codex_home)
    claude_root = host_cache_root(claude_home)
    codex_root = host_cache_root(codex_home)
    bodies = {
        str(claude_root): "# SkipHow\n\nContract A.\n",
        str(codex_root): "# SkipHow\n\nContract B.\n",
    }
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, root="": (bodies[root], "observed_cache_path"),
    )

    def activation(tool_id: str, root: Path) -> list[dict]:
        body = bodies[str(root)]
        records = claude_call(
            tool_id,
            "Skill",
            {"skill": "skiphow:skiphow"},
            "Skill loaded",
        )
        records.append(
            {
                "type": "user",
                "uuid": f"{tool_id}-injection",
                "parentUuid": f"{tool_id}-result-record",
                "userType": "external",
                "isMeta": True,
                "sourceToolUseID": tool_id,
                "message": {
                    "content": (
                        "Base directory for this skill: "
                        f"{root / '1.13.0/skills/skiphow'}\n{body}"
                    )
                },
            }
        )
        return records

    records = activation("claude-contract", claude_root)
    records.extend(activation("codex-contract", codex_root))
    records.append(
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "Result\ndone"}]},
        }
    )
    observations = DOGFOOD.skill_injection_observations(records)
    assert {
        observation["status"] for observation in observations.values()
    } == {"body_observed"}
    assert len(
        {observation["body_fingerprint"] for observation in observations.values()}
    ) == 2
    assert DOGFOOD.contract_identity_values(records, observations) == ["1.13.0"]
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 10_000)
    assert data["confounders"]["contract_body_identity"] == "mixed"
    assert all(
        evidence["verdict"] == "unverified_contract_body"
        for evidence in data["references"].values()
    )
    assert data["report"]["selection_status"] == "terminal_root_response"


def test_dogfood_missing_contract_bytes_blocks_report_scoring(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    monkeypatch.setattr(DOGFOOD, "claude_home", lambda: home)
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (
            "",
            "contract_bytes_unavailable",
        ),
    )
    base = host_cache_root(home) / "1.13.0/skills/skiphow"
    records = claude_call(
        "missing-contract",
        "Skill",
        {"skill": "skiphow:skiphow"},
        "Skill loaded",
    )
    records[0]["uuid"] = "missing-contract-call"
    records[1].update(
        {
            "uuid": "missing-contract-result",
            "parentUuid": "missing-contract-call",
            "sourceToolAssistantUUID": "missing-contract-call",
        }
    )
    records.extend(
        [
            {
                "type": "user",
                "uuid": "missing-contract-injection",
                "parentUuid": "missing-contract-result",
                "userType": "external",
                "isMeta": True,
                "sourceToolUseID": "missing-contract",
                "message": {
                    "content": (
                        f"Base directory for this skill: {base}\n"
                        "# SkipHow\n\nUnverifiable body.\n"
                    )
                },
            },
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Result\nlegacy\nEvidence\nold proof",
                        }
                    ]
                },
            },
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "current final"}]},
            },
        ]
    )
    observations = DOGFOOD.skill_injection_observations(records)
    assert observations["missing-contract"]["status"] == "body_unverified"
    assert observations["missing-contract"]["artifact_source"] == (
        "contract_bytes_unavailable"
    )
    data = DOGFOOD.digest(write_transcript(tmp_path, records), 10_000)
    assert data["plugin_version_values_observed"] == ["1.13.0"]
    assert data["report"]["selection_status"] == "terminal_root_response"
    assert data["report"]["text"] == "current final"


def test_dogfood_every_same_version_activation_needs_exact_body_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "# SkipHow\n\nExact owner body.\n"
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (body, "tag"),
    )
    base = host_cache_root(DOGFOOD.claude_home()) / "1.13.0/skills/skiphow"

    def activation(tool_id: str, observed_body: str) -> list[dict]:
        records = claude_call(
            tool_id,
            "Skill",
            {"skill": "skiphow:skiphow"},
            "Skill loaded",
        )
        records.append(
            {
                "type": "user",
                "uuid": f"{tool_id}-injection",
                "parentUuid": f"{tool_id}-result-record",
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

    records = activation("exact", body)
    records.extend(activation("truncated", "# SkipHow\n"))
    records.extend(
        [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Result\nlegacy\nEvidence\nold proof",
                        }
                    ]
                },
            },
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "current final"}]},
            },
        ]
    )
    observations = DOGFOOD.skill_injection_observations(records)
    assert observations["exact"]["status"] == "body_observed"
    assert observations["truncated"]["status"] == "body_unverified"
    assert observations["truncated"]["artifact_source"] == "tag"
    assert DOGFOOD.contract_identity_values(records, observations) == ["1.13.0"]

    data = DOGFOOD.digest(write_transcript(tmp_path, records), 10_000)
    assert data["confounders"]["plugin_version_identity"] == "single"
    assert data["report"]["selection_status"] == "terminal_root_response"
    assert data["report"]["text"] == "current final"


def test_dogfood_full_and_stripped_skill_renderings_share_canonical_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    markdown = (
        "# SkipHow\n\nFinish the request.\n\n"
        "Report under all five headings, keeping a heading whose answer is none:\n\n"
        "```text\nResult\nEvidence\nRulings and findings\n"
        "Saved follow-ups\nLimits\n```\n"
    )
    artifact = (
        "---\nname: skiphow\ndescription: Own the request.\n---\n" + markdown
    )
    monkeypatch.setattr(
        DOGFOOD,
        "package_skill",
        lambda _version, _name, _root="": (artifact, "tag"),
    )
    base = host_cache_root(DOGFOOD.claude_home()) / "1.13.0/skills/skiphow"

    def activation(tool_id: str, observed: str) -> list[dict]:
        records = claude_call(
            tool_id,
            "Skill",
            {"skill": "skiphow:skiphow"},
            "Skill loaded",
        )
        records.append(
            {
                "type": "user",
                "uuid": f"{tool_id}-injection",
                "parentUuid": f"{tool_id}-result-record",
                "userType": "external",
                "isMeta": True,
                "sourceToolUseID": tool_id,
                "message": {
                    "content": f"Base directory for this skill: {base}\n{observed}"
                },
            }
        )
        return records

    records = activation("full", artifact)
    records.extend(activation("stripped", markdown))
    records.append(
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "Result\nfinished"}]},
        }
    )
    observations = DOGFOOD.skill_injection_observations(records)
    assert {item["status"] for item in observations.values()} == {"body_observed"}
    assert len(
        {item["body_fingerprint"] for item in observations.values()}
    ) == 1


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
    different_observations = DOGFOOD.skill_injection_observations(
        different_skill
    )
    assert different_observations["different-skill"]["status"] == (
        "activation_path_mismatch"
    )
    assert different_observations["unattributed:2"]["status"] == (
        "body_observed"
    )

    unattributed = records_for("research", "research", "unattributed")
    assert DOGFOOD.successful_skill_result_ids(unattributed) == set()
    assert DOGFOOD.skill_injection_observations(unattributed)["unattributed:2"][
        "status"
    ] == "body_observed"

    different_base = records_for(
        "skiphow:skiphow", "testing", "different-base"
    )
    assert DOGFOOD.successful_skill_result_ids(different_base) == {"different-base"}
    base_observations = DOGFOOD.skill_injection_observations(different_base)
    assert base_observations["different-base"]["status"] == (
        "activation_path_mismatch"
    )
    assert base_observations["unattributed:2"]["name"] == "testing"


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
    observations = DOGFOOD.skill_injection_observations(records)
    assert observations["skill-owner"] == {
        "status": "activation_path_mismatch",
        "attribution": "explicit_skill_call",
        "at": "",
    }
    if base == "/project/.agents/skills/skiphow":
        assert observations["unattributed:2"]["status"] == "body_unverified"
        assert observations["unattributed:2"]["source"] == "project"
    else:
        assert set(observations) == {"skill-owner", "unattributed:2"}
        assert observations["unattributed:2"]["status"] == (
            "activation_path_ambiguous"
        )
        assert DOGFOOD.contract_identity_values(records, observations) == [
            "unknown"
        ]


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
        "docs/plugins/cache/skiphow/skiphow/2.0.0/skills/testing/SKILL.md",
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
        (
            "docs/plugins/cache/skiphow/skiphow/2.0.0/skills/skiphow/"
            "references/testing.md"
        ),
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


@pytest.mark.parametrize(
    "reference",
    [
        "../repo/.agents/skills/skiphow/references/testing.md",
        "My Project/.agents/skills/skiphow/references/testing.md",
        "/repo/$work/.agents/skills/skiphow/references/testing.md",
        "/repo/`literal`/.agents/skills/skiphow/references/testing.md",
        "/repo/<work>/.agents/skills/skiphow/references/testing.md",
        "$HOME/.agents/skills/skiphow/references/testing.md",
        "<project>/.agents/skills/skiphow/references/testing.md",
        "See /repo/.agents/skills/skiphow/references/testing.md",
        "$PROJECT/.agents/skills/skiphow/references/testing.md",
    ],
)
def test_dogfood_typed_paths_keep_literal_filesystem_characters(
    reference: str,
) -> None:
    assert DOGFOOD.reference_name_from_path(reference) == "testing"


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


@pytest.mark.parametrize("home_spelling", ["relative", "symlink_alias"])
def test_dogfood_home_aliases_bind_the_canonical_activation_cache(
    home_spelling: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_home = tmp_path / "custom-claude"
    alias = tmp_path / "custom-claude-alias"
    body = "# SkipHow\n\nExact canonical cache body.\n"
    base = host_cache_root(canonical_home) / "2.0.0/skills/skiphow"
    base.mkdir(parents=True)
    (base / "SKILL.md").write_text(body, encoding="utf-8")
    records = claude_call(
        "skill-owner", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
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
    transcript = canonical_home / "projects/project/session.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    if home_spelling == "relative":
        monkeypatch.chdir(tmp_path)
        selected_home = Path("custom-claude")
    else:
        alias.symlink_to(canonical_home, target_is_directory=True)
        selected_home = alias

    data = DOGFOOD.digest(
        DOGFOOD.resolve(selected_home, "session"), 0, selected_home
    )
    assert data["plugin_version_values_observed"] == ["2.0.0"]
    assert data["skill_body_injections"] == 1


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


@pytest.mark.parametrize("host_variable", ["CLAUDE_CONFIG_DIR", "CODEX_HOME"])
@pytest.mark.parametrize("home_spelling", ["relative", "symlink_alias"])
def test_dogfood_external_transcript_canonicalizes_fallback_host_cache_roots(
    host_variable: str,
    home_spelling: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_home = tmp_path / f"canonical-{host_variable.lower()}"
    body = "# SkipHow\n\nExact canonical fallback-cache body.\n"
    base = host_cache_root(canonical_home) / "2.0.0/skills/skiphow"
    base.mkdir(parents=True)
    (base / "SKILL.md").write_text(body, encoding="utf-8")
    if home_spelling == "relative":
        monkeypatch.chdir(tmp_path)
        configured_home = Path(canonical_home.name)
    else:
        configured_home = tmp_path / f"alias-{host_variable.lower()}"
        configured_home.symlink_to(canonical_home, target_is_directory=True)
    monkeypatch.setenv(host_variable, str(configured_home))
    other_variable = (
        "CODEX_HOME" if host_variable == "CLAUDE_CONFIG_DIR" else "CLAUDE_CONFIG_DIR"
    )
    monkeypatch.setenv(other_variable, str(tmp_path / "unrelated-host-home"))

    records = claude_call(
        "skill-owner", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
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
    transcript = write_transcript(outside, records, "external-session")
    data = DOGFOOD.digest(transcript, 0, tmp_path / "selected-home")
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


def test_dogfood_coverage_uses_only_strict_sidecars_and_exact_snapshots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    (research / "forged-receipts.md").write_text(
        "Audited `deadbeef-session` · 3 records · plugin 2.0.0 · "
        f"evidence {TEST_EVIDENCE_A} · forged\n",
        encoding="utf-8",
    )
    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "facefeed-session", 3, ["unknown"], TEST_EVIDENCE_A
            ),
            coverage_receipt(
                "cafebabe-session",
                2,
                ["1.14.2", "2.0.0"],
                TEST_EVIDENCE_A,
            ),
        ],
    )
    rows = [
        {
            "session": "deadbeef-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "deadbeef-session",
            "records": 3,
            "unreadable_lines": 0,
            "versions": ["2.0.0"],
            "evidence_fingerprint": TEST_EVIDENCE_A,
        },
        {
            "session": "facefeed-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "facefeed-session",
            "records": 3,
            "unreadable_lines": 0,
            "versions": ["unknown"],
            "evidence_fingerprint": TEST_EVIDENCE_A,
        },
        {
            "session": "cafebabe-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "cafebabe-session",
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
    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "mixed-version-session", 1195, ["1.7.0"], None
            ),
            coverage_receipt(
                "mixed-version-session",
                4868,
                ["1.7.0", "1.10.0"],
                TEST_EVIDENCE_A,
            ),
        ],
    )
    rows = [
        {
            "session": "mixed-version-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "mixed-versions",
            "records": 4868,
            "unreadable_lines": 0,
            "versions": ["1.10.0", "1.7.0"],
            "evidence_fingerprint": TEST_EVIDENCE_A,
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
    assert re.fullmatch(r"sha256-v1:[0-9a-f]{64}", row["evidence_fingerprint"])

    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "canonical-identity-session",
                len(records),
                ["unknown", "2.0.0"],
                row["evidence_fingerprint"],
            )
        ],
    )
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    assert DOGFOOD.coverage(home).splitlines()[-1].endswith("covered")


def test_dogfood_coverage_supports_full_ids_and_flags_ambiguous_prefixes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt("badc0ffe-session", 3, ["2.0.0"], None),
            coverage_receipt("deadbeef", 3, ["2.0.0"], TEST_EVIDENCE_A),
            coverage_receipt(
                "facefeed-session", 3, ["2.0.0"], TEST_EVIDENCE_A
            ),
        ],
    )
    rows = [
        {
            "session": "badc0ffe-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "unreadable",
            "records": 3,
            "unreadable_lines": 1,
            "versions": ["unknown"],
        },
        {
            "session": "facefeed-session",
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": "exact-full-id",
            "records": 3,
            "unreadable_lines": 0,
            "versions": ["2.0.0"],
            "evidence_fingerprint": TEST_EVIDENCE_A,
        },
        *[
            {
                "session": session,
                "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
                "project": project,
                "records": 3,
                "unreadable_lines": 0,
                "versions": ["2.0.0"],
                "evidence_fingerprint": TEST_EVIDENCE_A,
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
    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "a1b2c3d4",
                4868,
                ["1.7.0", "1.10.0"],
                TEST_EVIDENCE_A,
            ),
            coverage_receipt("c0ffee00", 1195, ["1.7.0"], TEST_EVIDENCE_A),
            coverage_receipt("f00dbabe", 4868, ["1.7.0"], TEST_EVIDENCE_A),
        ],
    )
    rows = [
        {
            "session": session,
            "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
            "project": project,
            "records": 4868,
            "unreadable_lines": 0,
            "versions": versions,
            "evidence_fingerprint": TEST_EVIDENCE_A,
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


def test_dogfood_marker_paths_follow_windows_case_and_component_boundaries(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    windows = project / "windows-marker.jsonl"
    windows.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "message": {
                    "content": (
                        r"C:\Users\Person\.CoDeX\PlUgInS\CaChE\SkIpHoW\SkIpHoW"
                        r"\2.0.0\SkIlLs\SkIpHoW\SKILL.md"
                    )
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert DOGFOOD.contains_marker(windows) is True
    assert DOGFOOD.record_contains_marker(json.loads(windows.read_text())) is True
    assert [row["session"] for row in DOGFOOD.discover(home, None)] == [
        "windows-marker"
    ]

    for value in (
        "/tmp/notplugins/cache/skiphow/skiphow/2.0.0/skills/skiphow/SKILL.md",
        "/tmp/myplugins/skiphow/skills/skiphow/SKILL.md",
        "/tmp/fake.agents/skills/skiphow/SKILL.md",
    ):
        record = {"type": "user", "message": {"content": value}}
        assert DOGFOOD.record_contains_marker(record) is False


def test_dogfood_marker_prefilter_finds_a_literal_split_across_chunks(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/split-marker.jsonl"
    transcript.parent.mkdir(parents=True)
    prefix = (
        b'{"type":"user","timestamp":"2026-08-27T10:00:00Z",'
        b'"cwd":"/work/customer-app","padding":"'
    )
    before_marker = b'","attributionPlugin":"'
    chunk_size = 1 << 20
    padding_length = chunk_size - 4 - len(prefix) - len(before_marker)
    payload = (
        prefix
        + b"x" * padding_length
        + before_marker
        + DOGFOOD.MARKER_LITERAL
        + b'"}\n'
    )
    assert payload.index(DOGFOOD.MARKER_LITERAL) == chunk_size - 4
    assert DOGFOOD.record_contains_marker(json.loads(payload)) is True
    transcript.write_bytes(payload)
    assert DOGFOOD.contains_marker(transcript) is True
    assert [row["session"] for row in DOGFOOD.discover(home, None)] == [
        "split-marker"
    ]


def test_dogfood_marker_prefilter_accepts_valid_json_unicode_escapes(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/escaped-marker.jsonl"
    transcript.parent.mkdir(parents=True)
    payload = (
        b'{"type":"user","timestamp":"2026-08-27T10:00:00Z",'
        b'"message":{"content":"\\u0073kiphow:\\u0073kiphow"}}\n'
    )
    parsed = json.loads(payload)
    assert DOGFOOD.record_contains_marker(parsed) is True
    transcript.write_bytes(payload)
    assert DOGFOOD.contains_marker(transcript) is True
    assert [row["session"] for row in DOGFOOD.discover(home, None)] == [
        "escaped-marker"
    ]
    broken = home / "projects/project/escaped-broken-marker.jsonl"
    broken.write_bytes(
        b'{"type":"user","message":{"content":"'
        b"\\u0073kiphow\\u003a\\u0073kiphow\"\n"
    )
    solidus_broken = home / "projects/project/solidus-broken-marker.jsonl"
    solidus_broken.write_bytes(
        b'{"type":"user","message":{"content":"'
        b".agents\\/skills\\/skiphow\\/SKILL.md\"\n"
    )
    rows = {row["session"]: row for row in DOGFOOD.discover(home, None)}
    assert set(rows) == {
        "escaped-broken-marker",
        "escaped-marker",
        "solidus-broken-marker",
    }
    assert rows["escaped-broken-marker"]["unreadable_marker_lines"] == 1
    assert rows["solidus-broken-marker"]["unreadable_marker_lines"] == 1


def test_dogfood_literal_prefilter_does_not_replace_marker_attribution(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/bare-literal.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "message": {"content": "The word skiphow is ordinary prose here."},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert DOGFOOD.contains_marker(transcript) is True
    assert DOGFOOD.discover(home, None) == []

    broken = home / "projects/project/bare-literal-broken.jsonl"
    broken.write_bytes(
        b'{"type":"user","message":{"content":"The word skiphow may be ordinary'
    )
    (row,) = DOGFOOD.discover(home, None)
    assert row["session"] == "bare-literal-broken"
    assert row["unreadable_marker_lines"] == 1
    assert row["candidate_marker_scope"] == "unverified_incomplete_scope"


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
    assert row["undated_marker_records"] is None
    assert row["records"] == 1
    assert row["unreadable_lines"] == 1
    assert row["versions"] == ["unknown"]


def test_dogfood_fully_unreadable_marker_candidate_remains_visible(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/fully-broken.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_bytes(b'{"skill":"skiphow:skiphow"\n')

    for rows in (
        DOGFOOD.discover(home, None),
        DOGFOOD.discover(home, "2026-08-27"),
        DOGFOOD.discover(home, None, "2026-08-27"),
    ):
        (row,) = rows
        assert row["session"] == "fully-broken"
        assert row["project"] == "unknown"
        assert row["candidate_marker_date_status"] == (
            "unverified_incomplete_transcript"
        )
        assert row["records"] == 0
        assert row["unreadable_lines"] == 1
        assert row["unreadable_marker_lines"] == 1
        assert row["versions"] == ["unknown"]

    rendered = DOGFOOD.render_list(DOGFOOD.discover(home, None))
    assert "1 candidate session(s)." in rendered
    assert "fully-b" in rendered
    assert "UNVERIFIED rec" in rendered
    resolved = DOGFOOD.resolve(home, "fully-broken")
    assert resolved == transcript
    data = DOGFOOD.digest(resolved, 1_000, home)
    assert data["records"] == 0
    assert data["unparseable_lines"] == 1
    assert data["plugin_version_values_observed"] == [
        "unverified_incomplete_transcript"
    ]
    assert data["report"]["selection_status"] == (
        "unverified_incomplete_transcript"
    )


def test_dogfood_unopenable_parent_digest_recovers_nested_evidence_as_sidechain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/unopenable.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps(
            {
                "type": "user",
                "origin": {"kind": "human"},
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (row,) = DOGFOOD.discover(home, None)
    resolved = DOGFOOD.resolve(home, row["display_session"])
    assert resolved == root

    original_iter_records = DOGFOOD.iter_records

    def deny_root(path: Path) -> tuple[list[dict], int]:
        if path == root:
            raise PermissionError("synthetic root denial")
        return original_iter_records(path)

    monkeypatch.setattr(DOGFOOD, "iter_records", deny_root)
    without_nested = DOGFOOD.digest(resolved, 1_000, home)
    assert without_nested["records"] == 0
    assert without_nested["unparseable_lines"] == 1
    assert without_nested["owner_turns"] == "unverified_incomplete_transcript"

    nested = root.with_suffix("") / "subagents/agent-a.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps(
            {
                "type": "user",
                "origin": {"kind": "human"},
                "message": {"content": "nested skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with_nested = DOGFOOD.digest(resolved, 1_000, home)
    assert with_nested["records"] == 0
    assert with_nested["unparseable_lines"] == 1
    assert with_nested["owner_turns"] == "unverified_incomplete_transcript"
    assert with_nested["plugin_version_values_observed"] == [
        "unverified_incomplete_transcript"
    ]
    assert with_nested["successful_structured_delegations"] == []
    assert with_nested["successful_structured_write_actions"] == []
    assert with_nested["report"]["selection_status"] == (
        "unverified_incomplete_transcript"
    )


def test_dogfood_empty_explicit_transcript_still_has_no_digest(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "empty.jsonl"
    transcript.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="holds no readable records"):
        DOGFOOD.digest(transcript, 1_000)


def test_dogfood_scan_error_remains_visible_to_list_and_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/unopenable.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("{}\n", encoding="utf-8")

    def denied(
        _path: Path,
        _expected: tuple[int, int, int, int, int] | None = None,
    ) -> tuple[object, tuple[int, int, int, int, int]]:
        raise PermissionError("synthetic scan denial")

    monkeypatch.setattr(DOGFOOD, "scan_marker_member", denied)
    for rows in (
        DOGFOOD.discover(home, None),
        DOGFOOD.discover(home, "2026-08-27"),
        DOGFOOD.discover(home, None, "2026-08-27"),
    ):
        (row,) = rows
        assert row["session"] == "unopenable"
        assert row["candidate_marker_date_status"] == "unverified_scan_error"
        assert row["candidate_marker_scope"] == "unverified_scan_error"
        assert row["unreadable_lines"] == 1
        assert row["versions"] == ["unknown"]

    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    assert DOGFOOD.coverage(home).splitlines()[-1].endswith(
        "UNVERIFIED_UNREADABLE"
    )


@pytest.mark.parametrize("denied_scope", ["projects", "project"])
def test_dogfood_upper_discovery_scan_failure_never_looks_complete(
    denied_scope: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    projects = home / "projects"
    project = projects / "project"
    project.mkdir(parents=True)
    original_scandir = DOGFOOD.os.scandir
    denied = projects if denied_scope == "projects" else project

    def fail_closed(path: object):
        if Path(path) == denied:
            raise PermissionError("synthetic discovery denial")
        return original_scandir(path)

    monkeypatch.setattr(DOGFOOD.os, "scandir", fail_closed)
    with pytest.raises(SystemExit, match="transcript discovery incomplete"):
        DOGFOOD.discover(home, None)
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    with pytest.raises(SystemExit, match="transcript discovery incomplete"):
        DOGFOOD.coverage(home)


def test_dogfood_sidechain_only_marker_remains_a_scoped_candidate(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/sidechain-marker.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "isSidechain": True,
                "timestamp": "2026-08-27T10:00:00Z",
                "cwd": "/work/delegate",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (row,) = DOGFOOD.discover(home, None, "2026-08-27")
    assert row["candidate_marker_scope"] == "sidechain_only"
    assert row["root_marker_records"] == 0
    assert row["sidechain_marker_records"] == 1
    assert row["candidate_marker_cwds"] == ["/work/delegate"]
    assert row["versions"] == ["unknown"]


def test_dogfood_nested_subagent_markers_aggregate_into_the_owner_chat(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    root = project / "owner-session.jsonl"
    root.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T09:00:00Z",
                "message": {"content": "ordinary owner text"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    nested = project / "owner-session/subagents/agent-a.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (row,) = DOGFOOD.discover(home, None, "2026-08-27")
    assert row["session"] == "owner-session"
    assert row["path"] == str(root)
    assert row["records"] == 1
    assert row["candidate_marker_scope"] == "sidechain_only"
    assert row["candidate_transcript_scope"] == (
        "root_with_nested_subagent_evidence"
    )
    assert row["nested_subagent_logs_with_evidence"] == 1
    assert row["root_marker_records"] == 0
    assert row["sidechain_marker_records"] == 1

    ignored = project / "owner-session/artifacts/not-a-subagent.jsonl"
    ignored.parent.mkdir(parents=True)
    ignored.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-28T10:00:00Z",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (unchanged,) = DOGFOOD.discover(home, None)
    assert unchanged["sidechain_marker_records"] == 1
    assert unchanged["nested_subagent_logs_with_evidence"] == 1


def test_dogfood_nested_contract_identity_does_not_replace_owner_identity(
    tmp_path: Path,
) -> None:
    def activation_records(home: Path, version: str, suffix: str) -> list[dict]:
        tool_id = f"skill-{suffix}"
        records = claude_call(
            tool_id,
            "Skill",
            {"skill": "skiphow:skiphow"},
            "Skill loaded",
        )
        base = host_cache_root(home) / version / "skills/skiphow"
        records.append(
            {
                "type": "user",
                "uuid": f"{tool_id}-injection",
                "parentUuid": records[1]["uuid"],
                "sourceToolAssistantUUID": records[0]["uuid"],
                "sourceToolUseID": tool_id,
                "userType": "external",
                "isMeta": True,
                "message": {
                    "content": (
                        f"Base directory for this skill: {base}\n"
                        "# SkipHow\n\nObserved owner contract."
                    )
                },
            }
        )
        return records

    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    root = project / "owner-session.jsonl"
    root_records = activation_records(home, "1.2.0", "root")
    root.write_text(
        "".join(json.dumps(record) + "\n" for record in root_records),
        encoding="utf-8",
    )
    nested = project / "owner-session/subagents/agent-a.jsonl"
    nested.parent.mkdir(parents=True)
    nested_records = activation_records(home, "2.0.0", "nested")
    nested.write_text(
        "".join(json.dumps(record) + "\n" for record in nested_records),
        encoding="utf-8",
    )

    (row,) = DOGFOOD.discover(home, None)
    assert row["candidate_marker_scope"] == "mixed"
    assert row["versions"] == ["1.2.0"]
    data = DOGFOOD.digest(root, 1_000, home)
    assert data["plugin_version_values_observed"] == ["1.2.0"]


def test_dogfood_unreadable_nested_marker_makes_parent_scope_unverified(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    root = project / "owner-session.jsonl"
    root.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T09:00:00Z",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    nested = project / "owner-session/subagents/agent-a.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b'{"message":"skiphow:skiphow"\n')
    (row,) = DOGFOOD.discover(home, None)
    assert row["session"] == "owner-session"
    assert row["root_marker_records"] == 1
    assert row["unreadable_marker_lines"] == 1
    assert row["candidate_marker_scope"] == "unverified_incomplete_scope"
    assert row["versions"] == ["unknown"]


def test_dogfood_nested_uncertainty_counts_as_aggregated_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    root = project / "owner-session.jsonl"
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "skiphow:skiphow"}})
        + "\n",
        encoding="utf-8",
    )
    nested = project / "owner-session/subagents/agent-a.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps(
            {
                "type": "user",
                "message": {"content": "ordinary skiphow mention"},
            }
        )
        + "\n{\n",
        encoding="utf-8",
    )
    (parsed_row,) = DOGFOOD.discover(home, None)
    assert parsed_row["candidate_marker_scope"] == "root"
    assert parsed_row["candidate_transcript_scope"] == (
        "root_with_nested_subagent_evidence"
    )
    assert parsed_row["nested_subagent_logs_with_evidence"] == 1
    assert parsed_row["unreadable_lines"] == 1

    original_scan = DOGFOOD.scan_marker_member

    def denied(
        path: Path,
        expected: tuple[int, int, int, int, int] | None = None,
    ) -> tuple[object, tuple[int, int, int, int, int]]:
        if path == nested:
            raise PermissionError("synthetic nested denial")
        return original_scan(path, expected)

    monkeypatch.setattr(DOGFOOD, "scan_marker_member", denied)
    (scan_row,) = DOGFOOD.discover(home, None)
    assert scan_row["candidate_marker_scope"] == "unverified_scan_error"
    assert scan_row["candidate_transcript_scope"] == (
        "root_with_nested_subagent_evidence"
    )
    assert scan_row["nested_subagent_logs_with_evidence"] == 1


def test_dogfood_nested_marker_without_root_keeps_synthetic_parent_candidate(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    nested = (
        home
        / "projects/project/missing-owner/subagents/agent-a.jsonl"
    )
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (row,) = DOGFOOD.discover(home, None)
    assert row["session"] == "missing-owner"
    assert row["root_transcript_status"] == "missing"
    assert row["candidate_transcript_scope"] == "synthetic_parent_from_nested"
    assert row["candidate_marker_scope"] == "unverified_incomplete_scope"
    assert row["undated_marker_records"] is None
    assert row["records"] == 0
    assert row["versions"] == ["unknown"]
    assert "UNVERIFIED rec" in DOGFOOD.render_list([row])
    resolved = DOGFOOD.resolve(home, row["display_session"])
    assert resolved == Path(row["path"])
    data = DOGFOOD.digest(resolved, 1_000, home)
    assert data["unparseable_lines"] >= 1
    assert data["plugin_version_values_observed"] == [
        "unverified_incomplete_transcript"
    ]
    assert data["report"]["selection_status"] == (
        "unverified_incomplete_transcript"
    )


def test_dogfood_zero_byte_owner_aggregates_nested_marker_but_stays_unverified(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text("", encoding="utf-8")
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (row,) = DOGFOOD.discover(home, None)
    assert row["records"] == 0
    assert row["root_transcript_status"] == "empty"
    assert row["candidate_marker_date_status"] == "observed"
    assert row["undated_marker_records"] == 0
    assert row["candidate_marker_scope"] == "unverified_incomplete_scope"
    assert "UNVERIFIED rec" in DOGFOOD.render_list([row])
    data = DOGFOOD.digest(root, 1_000, home)
    assert data["records"] == 0
    assert data["unparseable_lines"] >= 1
    assert data["owner_turns"] == "unverified_incomplete_transcript"


def test_dogfood_dangling_transcript_is_resolvable_and_unverified(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/dangling.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.symlink_to(transcript.parent / "missing-target.jsonl")
    (row,) = DOGFOOD.discover(home, None)
    assert row["root_transcript_status"] == "dangling"
    assert row["candidate_transcript_scope"] == "root_only_dangling"
    assert row["nested_subagent_logs_with_evidence"] == 0
    assert DOGFOOD.resolve(home, row["display_session"]) == transcript
    data = DOGFOOD.digest(transcript, 1_000, home)
    assert data["records"] == 0
    assert data["unparseable_lines"] >= 1
    assert data["report"]["selection_status"] == (
        "unverified_incomplete_transcript"
    )


def test_dogfood_discovery_never_opens_nonregular_jsonl_nodes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    directory = project / "directory.jsonl"
    directory.mkdir()
    fifo = project / "pipe.jsonl"
    os.mkfifo(fifo)
    original = DOGFOOD.scan_marker_member

    def guarded(
        path: Path,
        expected: tuple[int, int, int, int, int] | None = None,
    ) -> tuple[object, tuple[int, int, int, int, int]]:
        assert path not in {directory, fifo}
        return original(path, expected)

    monkeypatch.setattr(DOGFOOD, "scan_marker_member", guarded)
    assert DOGFOOD.discover(home, None) == []
    for path in (directory, fifo):
        with pytest.raises(SystemExit, match="not a regular transcript"):
            DOGFOOD.digest(path, 1_000, home)


def test_dogfood_nonregular_owner_with_nested_evidence_is_unverified_not_opened(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    os.mkfifo(root)
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps({"type": "user", "message": {"content": "skiphow:skiphow"}})
        + "\n",
        encoding="utf-8",
    )
    (row,) = DOGFOOD.discover(home, None)
    assert row["root_transcript_status"] == "nonregular"
    assert row["candidate_marker_scope"] == "unverified_incomplete_scope"
    assert row["undated_marker_records"] is None
    assert "UNVERIFIED rec" in DOGFOOD.render_list([row])
    data = DOGFOOD.digest(DOGFOOD.resolve(home, row["display_session"]), 1_000, home)
    assert data["records"] == 0
    assert data["unparseable_lines"] >= 1

    original_open = Path.open

    def guarded_open(path: Path, *args: object, **kwargs: object):
        if path == root:
            raise AssertionError("grep attempted to open a non-regular transcript")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sessions.py",
            "--home",
            str(home),
            "grep",
            row["display_session"],
            "skiphow",
        ],
    )
    with pytest.raises(SystemExit, match="unavailable for bounded grep"):
        DOGFOOD.main()


def test_dogfood_discovery_never_follows_transcript_file_symlinks(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "ordinary"}})
        + "\n",
        encoding="utf-8",
    )
    external = tmp_path / "external-marker.jsonl"
    external.write_text(
        json.dumps(
            {"type": "user", "message": {"content": "skiphow:skiphow"}}
        )
        + "\n",
        encoding="utf-8",
    )
    nested_link = root.with_suffix("") / "subagents/agent.jsonl"
    nested_link.parent.mkdir(parents=True)
    nested_link.symlink_to(external)
    root_link = root.parent / "linked-owner.jsonl"
    root_link.symlink_to(external)

    assert DOGFOOD.transcript_file_status(nested_link) == "nonregular"
    assert DOGFOOD.transcript_file_status(root_link) == "nonregular"
    (row,) = DOGFOOD.discover(home, None)
    assert row["path"] == str(root)
    assert row["candidate_marker_scope"] == "unverified_scan_error"
    data = DOGFOOD.digest(root, 1_000, home)
    assert data["unparseable_lines"] >= 1
    assert "external-marker" not in json.dumps(data)


@pytest.mark.parametrize("node_kind", ["regular", "fifo"])
def test_dogfood_non_directory_subagents_node_is_not_a_scan_error(
    node_kind: str,
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    subagents = root.with_suffix("") / "subagents"
    subagents.parent.mkdir(parents=True)
    if node_kind == "regular":
        subagents.write_text("not a directory", encoding="utf-8")
    else:
        os.mkfifo(subagents)

    assert DOGFOOD.nested_digest_evidence(root) == ([], 0, False)
    assert DOGFOOD.discover(home, None) == []


def test_dogfood_digest_fails_closed_when_nested_inventory_changes_during_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "done"}]},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    nested = root.with_suffix("") / "subagents/late.jsonl"
    nested.parent.mkdir(parents=True)
    original = DOGFOOD.iter_records
    added = False

    def add_nested(path: Path) -> tuple[list[dict], int]:
        nonlocal added
        result = original(path)
        if path == root and not added:
            nested.write_bytes(b'{"message":"skiphow:skiphow"\n')
            added = True
        return result

    monkeypatch.setattr(DOGFOOD, "iter_records", add_nested)
    data = DOGFOOD.digest(root, 1_000, home)
    assert added is True
    assert data["records"] == 1
    assert data["unparseable_lines"] == 1
    assert data["report"]["selection_status"] == (
        "unverified_incomplete_transcript"
    )


def test_dogfood_exact_configured_target_never_inventories_other_projects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "ordinary"}})
        + "\n",
        encoding="utf-8",
    )
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    original_scandir = os.scandir

    def guarded_scandir(path: str | os.PathLike[str]):
        if Path(path) == home / "projects":
            raise PermissionError("unrelated project inventory is forbidden")
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", guarded_scandir)
    assert DOGFOOD.resolve(home, str(root)) == root
    assert DOGFOOD.resolve(home, str(nested)) == root


def test_dogfood_home_alias_and_canonical_paths_keep_nested_owner_identity(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    alias = tmp_path / "claude-home-alias"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "ordinary"}})
        + "\n",
        encoding="utf-8",
    )
    alias.symlink_to(home, target_is_directory=True)
    canonical_nested = root.with_suffix("") / "subagents/agent.jsonl"
    alias_nested = (
        alias / "projects/project/owner/subagents/agent.jsonl"
    )

    assert DOGFOOD.resolve(alias, str(canonical_nested)) == root
    assert DOGFOOD.resolve(home, str(alias_nested)) == root


def test_dogfood_nested_directory_symlink_is_owner_scoped_uncertainty(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "ordinary"}})
        + "\n",
        encoding="utf-8",
    )
    external = tmp_path / "external-subagents"
    external.mkdir()
    (external / "private.jsonl").write_text(
        json.dumps({"type": "user", "message": {"content": "skiphow:skiphow"}})
        + "\n",
        encoding="utf-8",
    )
    nested_link = root.with_suffix("") / "subagents/deep"
    nested_link.parent.mkdir(parents=True)
    nested_link.symlink_to(external, target_is_directory=True)

    (row,) = DOGFOOD.discover(home, None)
    assert row["candidate_marker_scope"] == "unverified_scan_error"
    assert row["candidate_marker_date_status"] == "unverified_scan_error"
    data = DOGFOOD.digest(root, 1_000, home)
    assert data["unparseable_lines"] >= 1
    assert "private" not in json.dumps(data)


def test_dogfood_malformed_nested_nonmarker_bytes_still_make_root_incomplete(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text("{broken ordinary\n", encoding="utf-8")

    (row,) = DOGFOOD.discover(home, None)
    assert row["unreadable_lines"] == 1
    assert row["nested_subagent_logs_with_evidence"] == 1
    assert row["candidate_transcript_scope"] == (
        "root_with_nested_subagent_evidence"
    )
    data = DOGFOOD.digest(root, 1_000, home)
    assert data["unparseable_lines"] == 1
    assert data["confounders"]["contract_sequence"] == (
        "unverified_incomplete_transcript"
    )


def test_dogfood_configured_project_directory_symlink_is_never_followed(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    projects = home / "projects"
    projects.mkdir(parents=True)
    external_project = tmp_path / "external-project"
    external_project.mkdir()
    external = external_project / "owner.jsonl"
    external.write_text(
        json.dumps(
            {"type": "user", "message": {"content": "private skiphow:skiphow"}}
        )
        + "\n",
        encoding="utf-8",
    )
    linked_project = projects / "project"
    linked_project.symlink_to(external_project, target_is_directory=True)
    configured_target = linked_project / "owner.jsonl"

    assert DOGFOOD.discover(home, None) == []
    with pytest.raises(SystemExit, match="no transcript found"):
        DOGFOOD.resolve(home, str(configured_target))
    with pytest.raises(SystemExit, match="linked or unavailable project scope"):
        DOGFOOD.digest(configured_target, 1_000, home)


@pytest.mark.parametrize("scope", ["projects", "project"])
def test_dogfood_discovery_rejects_directory_symlink_substitution(
    scope: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    projects = home / "projects"
    project = projects / "project"
    project.mkdir(parents=True)
    (project / "owner.jsonl").write_text(
        json.dumps({"type": "user", "message": {"content": "ordinary"}})
        + "\n",
        encoding="utf-8",
    )
    external_projects = tmp_path / "external-projects"
    external_project = external_projects / "project"
    external_project.mkdir(parents=True)
    (external_project / "owner.jsonl").write_text(
        json.dumps(
            {"type": "user", "message": {"content": "private skiphow:skiphow"}}
        )
        + "\n",
        encoding="utf-8",
    )
    swapped = False
    if scope == "projects":
        original_open = DOGFOOD.open_cache_root_descriptor

        def swapping_root(path: str | os.PathLike[str]) -> int:
            nonlocal swapped
            if Path(path) == projects and not swapped:
                swapped = True
                projects.rename(home / "projects-original")
                projects.symlink_to(external_projects, target_is_directory=True)
            return original_open(path)

        monkeypatch.setattr(DOGFOOD, "open_cache_root_descriptor", swapping_root)
    else:
        original_open_child = DOGFOOD.open_observed_child_directory

        def swapping_child(parent: int, name: str, observed: os.stat_result) -> int:
            nonlocal swapped
            if name == "project" and not swapped:
                swapped = True
                project.rename(projects / "project-original")
                project.symlink_to(external_project, target_is_directory=True)
            return original_open_child(parent, name, observed)

        monkeypatch.setattr(
            DOGFOOD, "open_observed_child_directory", swapping_child
        )

    with pytest.raises(SystemExit, match="scope is unreadable|directory is unreadable"):
        DOGFOOD.discover(home, None)
    assert swapped is True


def test_dogfood_nested_directory_substitution_is_owner_scoped_unverified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "skiphow:skiphow"}})
        + "\n",
        encoding="utf-8",
    )
    subagents = root.with_suffix("") / "subagents"
    subagents.mkdir(parents=True)
    external = tmp_path / "external-subagents"
    external.mkdir()
    (external / "private.jsonl").write_text(
        json.dumps(
            {"type": "user", "message": {"content": "private skiphow:skiphow"}}
        )
        + "\n",
        encoding="utf-8",
    )
    original_open_child = DOGFOOD.open_observed_child_directory
    swapped = False

    def swapping_child(parent: int, name: str, observed: os.stat_result) -> int:
        nonlocal swapped
        if name == "subagents" and not swapped:
            swapped = True
            subagents.rename(subagents.parent / "subagents-original")
            subagents.symlink_to(external, target_is_directory=True)
        return original_open_child(parent, name, observed)

    monkeypatch.setattr(DOGFOOD, "open_observed_child_directory", swapping_child)
    (row,) = DOGFOOD.discover(home, None)
    assert row["candidate_marker_scope"] == "unverified_scan_error"
    assert row["candidate_marker_date_status"] == "unverified_scan_error"
    assert "external-subagents" not in json.dumps(row)


@pytest.mark.parametrize(
    "replacement", ["symlink", "symlink_without_nofollow", "fifo"]
)
def test_dogfood_transcript_open_revalidates_file_kind_without_blocking(
    replacement: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "ordinary"}})
        + "\n",
        encoding="utf-8",
    )
    external = tmp_path / "external-private.jsonl"
    external.write_text(
        json.dumps({"type": "user", "message": {"content": "private bytes"}})
        + "\n",
        encoding="utf-8",
    )
    original_status = DOGFOOD.transcript_file_status
    swapped = False
    if replacement == "symlink_without_nofollow":
        monkeypatch.delattr(os, "O_NOFOLLOW", raising=False)

    def swap_after_preflight(path: Path) -> str:
        nonlocal swapped
        status = original_status(path)
        if path == root and not swapped:
            swapped = True
            root.unlink()
            if replacement.startswith("symlink"):
                root.symlink_to(external)
            else:
                os.mkfifo(root)
        return status

    monkeypatch.setattr(DOGFOOD, "transcript_file_status", swap_after_preflight)
    data = DOGFOOD.digest(root, 1_000, home)
    assert data["unparseable_lines"] >= 1
    assert data["owner_turns"] == "unverified_incomplete_transcript"
    assert "private bytes" not in json.dumps(data)


def test_dogfood_projects_disappearing_after_preflight_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    projects = home / "projects"
    projects.mkdir(parents=True)
    original_open_root = DOGFOOD.open_cache_root_descriptor

    def disappearing(path: str | os.PathLike[str]) -> int:
        if Path(path) == projects:
            raise FileNotFoundError(path)
        return original_open_root(path)

    monkeypatch.setattr(DOGFOOD, "open_cache_root_descriptor", disappearing)
    with pytest.raises(SystemExit, match="projects scope disappeared"):
        DOGFOOD.discover(home, None)


@pytest.mark.parametrize("node_kind", ["regular", "fifo", "dangling_symlink"])
def test_dogfood_malformed_projects_scope_never_looks_like_an_empty_census(
    node_kind: str,
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    home.mkdir()
    projects = home / "projects"
    if node_kind == "regular":
        projects.write_text("not a directory", encoding="utf-8")
    elif node_kind == "fifo":
        os.mkfifo(projects)
    else:
        projects.symlink_to(home / "missing-projects", target_is_directory=True)
    with pytest.raises(SystemExit, match="projects scope is not a directory"):
        DOGFOOD.discover(home, None)


def test_dogfood_nested_scan_uses_a_worklist_not_python_recursion(
    tmp_path: Path,
) -> None:
    root = tmp_path / "owner.jsonl"
    directory = root.with_suffix("") / "subagents"
    directory.mkdir(parents=True)
    deepest = directory
    for _ in range(120):
        deepest /= "d"
        deepest.mkdir()
    nested = deepest / "agent.jsonl"
    nested.write_text("{}\n", encoding="utf-8")
    selected: set[Path] = set()
    errors: dict[Path, set[Path]] = {}
    original_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(80)
        DOGFOOD.scan_nested_transcripts(directory, root, selected, errors)
    finally:
        sys.setrecursionlimit(original_limit)
    assert selected == {nested}
    assert errors == {}


def test_dogfood_external_flat_transcript_never_reads_adjacent_subagents(
    tmp_path: Path,
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "flat"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "answer", "type": "agent_message", "text": "done"},
        },
        {"type": "turn.completed", "usage": codex_usage()},
    ]
    external_project = tmp_path / "external/projects/project"
    external_project.mkdir(parents=True)
    transcript = write_transcript(external_project, records, name="flat-codex")
    nested = transcript.with_suffix("") / "subagents/private.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text("{broken skiphow:skiphow\n", encoding="utf-8")

    unrelated_home = tmp_path / "unrelated-home"
    data = DOGFOOD.digest(transcript, 1_000, unrelated_home)
    assert data["unparseable_lines"] == 0
    assert data["confounders"]["turn_sequence"] == "completed"
    assert data["report"]["text"] == "done"


def test_dogfood_configured_nested_path_resolves_to_owner_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps({"type": "user", "message": {"content": "ordinary"}})
        + "\n",
        encoding="utf-8",
    )
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps({"type": "user", "message": {"content": "skiphow:skiphow"}})
        + "\n",
        encoding="utf-8",
    )
    assert DOGFOOD.resolve(home, str(nested)) == root
    assert DOGFOOD.resolve(
        home, "projects/project/owner/subagents/agent.jsonl"
    ) == root
    assert DOGFOOD.resolve(home, "project/owner/subagents/agent.jsonl") == root

    monkeypatch.chdir(tmp_path)
    Path("owner").write_text("cwd shadow", encoding="utf-8")
    assert DOGFOOD.resolve(home, "owner") == root

    external = tmp_path / "external/subagents/flat.jsonl"
    external.parent.mkdir(parents=True)
    external.write_text("{}\n", encoding="utf-8")
    assert DOGFOOD.resolve(home, str(external)) == external


def test_dogfood_resolve_normalizes_configured_paths_without_following_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text("{}\n", encoding="utf-8")
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text("{}\n", encoding="utf-8")

    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    relative_nested = Path("../claude-home/projects/project/owner/subagents/agent.jsonl")
    assert DOGFOOD.resolve(home, str(relative_nested)) == root
    assert DOGFOOD.resolve(Path("../claude-home"), str(nested)) == root


def test_dogfood_resolve_prefers_explicit_flat_paths_before_private_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    configured = home / "projects/fixtures/run.jsonl"
    configured.parent.mkdir(parents=True)
    configured.write_text("{}\n", encoding="utf-8")
    cwd_file = tmp_path / "fixtures/run.jsonl"
    cwd_file.parent.mkdir(parents=True)
    cwd_file.write_text("{}\n", encoding="utf-8")
    external = tmp_path / "external.jsonl"
    external.write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert DOGFOOD.resolve(home, "fixtures/run.jsonl") == cwd_file

    original_scandir = DOGFOOD.os.scandir

    def denied(path: object):
        if Path(path) == home / "projects":
            raise PermissionError("private inventory must not be read")
        return original_scandir(path)

    monkeypatch.setattr(DOGFOOD.os, "scandir", denied)
    assert DOGFOOD.resolve(home, str(external)) == external


def test_dogfood_nested_scan_failure_surfaces_in_list_resolve_and_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    (home / "projects/project/missing/subagents").mkdir(parents=True)
    original_open_child = DOGFOOD.open_cache_child_directory

    def denied(parent: int, name: str) -> int:
        if name == "subagents":
            raise PermissionError("synthetic traversal denial")
        return original_open_child(parent, name)

    monkeypatch.setattr(DOGFOOD, "open_cache_child_directory", denied)
    (row,) = DOGFOOD.discover(home, None)
    assert row["root_transcript_status"] == "missing"
    assert row["candidate_marker_date_status"] == "unverified_scan_error"
    owner = Path(row["path"])
    assert DOGFOOD.resolve(home, row["display_session"]) == owner
    data = DOGFOOD.digest(owner, 1_000, home)
    assert data["records"] == 0
    assert data["unparseable_lines"] >= 1


def test_dogfood_missing_owner_date_is_uncertain_under_exact_filters(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    nested = home / "projects/project/missing/subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2020-01-01T00:00:00Z",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    for rows in (
        DOGFOOD.discover(home, "2026-08-28"),
        DOGFOOD.discover(home, None, "2026-08-28"),
    ):
        (row,) = rows
        assert row["root_transcript_status"] == "missing"
        assert row["candidate_marker_date_status"] == (
            "unverified_incomplete_transcript"
        )


def test_dogfood_duplicate_synthetic_parent_paths_remain_resolvable(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    for project in ("one", "two"):
        nested = (
            home
            / f"projects/{project}/missing-owner/subagents/agent-a.jsonl"
        )
        nested.parent.mkdir(parents=True)
        nested.write_text(
            json.dumps(
                {"type": "user", "message": {"content": "skiphow:skiphow"}}
            )
            + "\n",
            encoding="utf-8",
        )
    rows = DOGFOOD.discover(home, None)
    assert len(rows) == 2
    for row in rows:
        assert row["receipt_session"] == ""
        assert row["display_session"] == row["path"]
        assert DOGFOOD.resolve(home, row["display_session"]) == Path(row["path"])


def test_dogfood_extreme_timestamp_is_date_uncertain_not_a_list_crash(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/extreme-time.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "9999-12-31T23:59:59-23:59",
                "cwd": "/work/customer-app",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (row,) = DOGFOOD.discover(home, None, "2026-08-27")
    assert row["candidate_marker_local_dates"] == ["unknown", "unknown"]
    assert row["candidate_marker_date_status"] == (
        "unverified_missing_or_invalid_timestamp"
    )
    assert row["undated_marker_records"] == 1


def test_dogfood_list_never_excludes_marker_candidates_by_cwd(
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
        ("scratch-session", "/private/tmp/skiphow-dogfood/customer-app"),
        ("no-cwd-session", None),
    ):
        record = {
            "type": "user",
            "timestamp": "2026-08-27T10:00:00Z",
            "message": {"content": marker},
        }
        if cwd is not None:
            record["cwd"] = cwd
        (project / f"{session}.jsonl").write_text(
            json.dumps(record) + "\n",
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
    assert "4 candidate session(s)." in default_text
    assert {row["session"] for row in default_json} == {
        "external-session",
        "no-cwd-session",
        "scratch-session",
        "selfdev-session",
    }
    rows = {row["session"]: row for row in default_json}
    assert rows["external-session"]["candidate_marker_cwds"] == [
        "/work/customer-app"
    ]
    assert rows["selfdev-session"]["candidate_marker_cwds"] == [
        str(DOGFOOD.repository_root())
    ]
    assert rows["scratch-session"]["candidate_marker_cwds"] == [
        "/private/tmp/skiphow-dogfood/customer-app"
    ]
    assert rows["no-cwd-session"]["candidate_marker_cwds"] == []


def test_dogfood_list_renders_resolvable_ids_and_the_marker_date_range() -> None:
    rows = [
        {
            "session": session,
            "candidate_marker_local_dates": dates,
            "candidate_marker_date_status": "observed",
            "undated_marker_records": 0,
            "candidate_marker_scope": "root",
            "project": project,
            "versions": ["2.0.0"],
            "megabytes": 0.1,
            "records": 3,
            "unreadable_lines": 0,
        }
        for session, dates, project in (
            (
                "deadbeef-first",
                ["2026-08-27", "2026-08-28"],
                "first",
            ),
            (
                "deadbeef-second",
                ["2026-08-27", "2026-08-27"],
                "second",
            ),
            (
                "facefeed-unique",
                ["2026-08-27", "2026-08-27"],
                "unique",
            ),
        )
    ]
    rendered = DOGFOOD.render_list(rows)
    assert "deadbeef-first" in rendered
    assert "deadbeef-second" in rendered
    assert "facefeed  " in rendered
    assert "2026-08-27..2026-08-28" in rendered


def test_dogfood_json_and_resolver_errors_escape_terminal_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    transcript = project / "control-session.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "origin": {"kind": "human"},
                "message": {"content": "owner\u009btext"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sessions.py",
            "--home",
            str(home),
            "digest",
            "control-session",
            "--json",
        ],
    )
    DOGFOOD.main()
    output = capsys.readouterr().out
    assert "\u009b" not in output
    assert r"\u009b" in output

    for suffix in ("A", "B"):
        (project / f"deadbeef\x1b{suffix}.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        DOGFOOD.resolve(home, "deadbeef")
    message = str(error.value)
    assert "\x1b" not in message
    assert r"\u001b" in message

    nonregular = project / "bad\x1bpath.jsonl"
    nonregular.mkdir()
    with pytest.raises(SystemExit) as error:
        DOGFOOD.digest(nonregular, 100, home)
    message = str(error.value)
    assert "\x1b" not in message
    assert r"\u001b" in message

    ambiguous = tmp_path / "multi\u009bthread.jsonl"
    ambiguous.write_text(
        "\n".join(
            json.dumps({"type": "thread.started", "thread_id": thread})
            for thread in ("one", "two")
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as error:
        DOGFOOD.digest(ambiguous, 100)
    message = str(error.value)
    assert "\u009b" not in message
    assert r"\u009b" in message


def test_dogfood_filtered_list_uses_the_global_root_session_prefix_universe(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)

    def write(name: str, text: str, day: str = "2026-08-27") -> None:
        (project / f"{name}.jsonl").write_text(
            json.dumps(
                {
                    "type": "user",
                    "timestamp": f"{day}T10:00:00Z",
                    "message": {"content": text},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    write("deadbeef-marker", "skiphow:skiphow")
    write("deadbeef-unrelated", "ordinary transcript")
    write("nonhex-session", "skiphow:skiphow")
    marker_day = DOGFOOD.local_calendar_date("2026-08-27T10:00:00Z")
    assert marker_day is not None
    rows = DOGFOOD.discover(home, None, marker_day)
    by_session = {row["session"]: row for row in rows}
    assert by_session["deadbeef-marker"]["display_session"] == (
        "deadbeef-marker"
    )
    assert by_session["deadbeef-marker"]["receipt_session"] == (
        "deadbeef-marker"
    )
    assert by_session["nonhex-session"]["display_session"] == "nonhex-session"
    rendered = DOGFOOD.render_list(rows)
    assert "deadbeef-marker" in rendered
    assert "nonhex-session" in rendered
    with pytest.raises(SystemExit, match="ambiguous transcript prefix"):
        DOGFOOD.resolve(home, "deadbeef")


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

    cutoff = DOGFOOD.local_calendar_date("2026-08-25T12:00:00Z")
    new_marker_day = DOGFOOD.local_calendar_date("2026-08-30T12:00:00Z")
    assert cutoff is not None and new_marker_day is not None
    rows = {row["session"]: row for row in DOGFOOD.discover(home, cutoff)}
    assert set(rows) == {"old-chat-new-marker", "undated-marker"}
    included = rows["old-chat-new-marker"]
    assert included["started"] == "2026-08-20T12:00:00Z"
    assert included["candidate_marker_window"] == [
        "2026-08-30T12:00:00Z",
        "2026-08-30T12:00:00Z",
    ]
    assert included["candidate_marker_local_dates"] == [
        new_marker_day,
        new_marker_day,
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

    selected_day = DOGFOOD.local_calendar_date("2026-08-27T12:00:00Z")
    uncertain_day = DOGFOOD.local_calendar_date("2026-08-26T12:00:00Z")
    assert selected_day is not None and uncertain_day is not None
    rows = DOGFOOD.discover(home, None, selected_day)
    assert {row["session"] for row in rows} == {
        "mixed-date-uncertain",
        "spans-day",
        "undated",
    }
    uncertain = next(
        row for row in rows if row["session"] == "mixed-date-uncertain"
    )
    assert uncertain["candidate_marker_local_dates"] == [
        uncertain_day,
        uncertain_day,
    ]
    assert uncertain["candidate_marker_date_status"] == (
        "unverified_undated_marker_records"
    )
    assert uncertain["undated_marker_records"] == 1
    assert "mixed-date-uncertain" in {
        row["session"] for row in DOGFOOD.discover(home, selected_day)
    }
    undated = next(row for row in rows if row["session"] == "undated")
    assert undated["candidate_marker_local_dates"] == ["unknown", "unknown"]
    assert undated["candidate_marker_date_status"] == (
        "unverified_missing_or_invalid_timestamp"
    )
    assert undated["undated_marker_records"] == 1
    assert "undated" in {
        row["session"] for row in DOGFOOD.discover(home, selected_day)
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

    def empty_result(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        output: str | bytes = "" if kwargs.get("text") else b""
        return subprocess.CompletedProcess(args[0], 0, output, output)

    monkeypatch.setattr(
        DOGFOOD.subprocess,
        "run",
        empty_result,
    )
    assert DOGFOOD.version_reference_names("9.9.9") == set()
    assert DOGFOOD.package_reference("9.9.9", "ghost-reference") == ("", "tag")
    assert DOGFOOD.package_skill_root("9.9.9") == ("", "tag")


def test_dogfood_tagged_artifact_preserves_lone_carriage_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def binary_show(
        args: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess:
        assert args[:2] == ["git", "show"]
        assert kwargs.get("text") is not True
        return subprocess.CompletedProcess(args, 0, b"one\rtwo\r", b"")

    monkeypatch.setattr(DOGFOOD.subprocess, "run", binary_show)
    assert DOGFOOD.tagged_artifact("1.2.3", "plugins/skiphow/SKILL.md") == (
        "one\rtwo\r",
        "tag",
    )


def test_dogfood_ambiguous_session_prefix_fails_closed(tmp_path: Path) -> None:
    first = tmp_path / "projects/one/prefix-a.jsonl"
    second = tmp_path / "projects/two/prefix-b.jsonl"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="ambiguous transcript prefix"):
        DOGFOOD.resolve(tmp_path, "prefix")

    exact = tmp_path / "projects/one/exact.jsonl"
    longer = tmp_path / "projects/two/exact-more.jsonl"
    exact.write_text("{}\n", encoding="utf-8")
    longer.write_text("{}\n", encoding="utf-8")
    assert DOGFOOD.resolve(tmp_path, "exact") == exact


def test_dogfood_flat_codex_transcript_with_multiple_threads_fails_closed(
    tmp_path: Path,
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "first-thread"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "first", "type": "agent_message", "text": "first"},
        },
        {"type": "turn.completed", "usage": codex_usage()},
        {"type": "thread.started", "thread_id": "second-thread"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "second",
                "type": "agent_message",
                "text": "second",
            },
        },
        {"type": "turn.completed", "usage": codex_usage()},
    ]
    assert DOGFOOD.codex_thread_identity(records) == ("ambiguous_sequence", "")
    assert DOGFOOD.codex_turn_status(records) == "ambiguous_sequence"
    transcript = write_transcript(tmp_path, records, "multiple-threads")
    with pytest.raises(SystemExit, match="multiple Codex thread envelopes"):
        DOGFOOD.digest(transcript, 100)


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
    monkeypatch.setattr(
        DOGFOOD, "version_reference_roster", lambda _version: ({"testing"}, True)
    )
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
            "mismatched_path_sources": [],
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
    ) == ("", "observed_cache_roots_disagree_or_are_incomplete")
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
    monkeypatch.setattr(
        DOGFOOD, "version_reference_roster", lambda _version: ({"testing"}, True)
    )
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


def test_dogfood_observed_cache_never_follows_a_reference_directory_symlink(
    tmp_path: Path,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    skill_root = root / version / "skills/skiphow"
    skill_root.mkdir(parents=True)
    external = tmp_path / "external-references"
    external.mkdir()
    (external / "testing.md").write_text("external bytes", encoding="utf-8")
    (skill_root / "references").symlink_to(external, target_is_directory=True)

    assert DOGFOOD.cache_reference_roster_at(root, version) == (
        set(),
        False,
        True,
    )
    assert DOGFOOD.package_reference(version, "testing", (str(root),)) == (
        "",
        "observed_cache_roots_disagree_or_are_incomplete",
    )


def test_dogfood_invalid_utf8_observed_reference_bytes_fail_closed(
    tmp_path: Path,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    reference = root / version / "skills/skiphow/references/testing.md"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"\xff\xfe")

    assert DOGFOOD.cache_reference_roster_at(root, version) == (
        {"testing"},
        True,
        True,
    )
    assert DOGFOOD.package_reference(version, "testing", (str(root),)) == (
        "",
        "observed_cache_roots_disagree_or_are_incomplete",
    )


def test_dogfood_cache_artifact_open_rejects_a_final_symlink_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    reference = root / version / "skills/skiphow/references/testing.md"
    reference.parent.mkdir(parents=True)
    reference.write_text("original bytes", encoding="utf-8")
    external = tmp_path / "external.md"
    external.write_text("forged external bytes", encoding="utf-8")
    original_open = os.open
    swapped = False

    def swapping_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal swapped
        if path == "testing.md" and dir_fd is not None and not swapped:
            swapped = True
            reference.unlink()
            reference.symlink_to(external)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", swapping_open)
    monkeypatch.setattr(DOGFOOD, "cache_descriptor_walk_supported", lambda: True)
    assert DOGFOOD.package_reference(version, "testing", (str(root),)) == (
        "",
        "observed_cache_roots_disagree_or_are_incomplete",
    )
    assert swapped is True


@pytest.mark.parametrize(
    "component", ["root", "7.8.9", "skills", "skiphow", "references"]
)
def test_dogfood_cache_artifact_revalidates_each_ancestor_after_read(
    component: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    reference = root / version / "skills/skiphow/references/testing.md"
    reference.parent.mkdir(parents=True)
    reference.write_text("original bytes", encoding="utf-8")
    targets = {
        "root": root,
        version: root / version,
        "skills": root / version / "skills",
        "skiphow": root / version / "skills/skiphow",
        "references": reference.parent,
    }
    target = targets[component]
    remaining = reference.relative_to(target)
    attacker = tmp_path / f"attacker-{component}"
    forged = attacker / remaining
    forged.parent.mkdir(parents=True)
    forged.write_text("forged bytes", encoding="utf-8")
    stash = tmp_path / f"original-{component}"
    original_read = os.read
    swapped = False

    def swapping_read(descriptor: int, count: int) -> bytes:
        nonlocal swapped
        data = original_read(descriptor, count)
        if data and not swapped:
            target.rename(stash)
            attacker.rename(target)
            target.rename(attacker)
            stash.rename(target)
            swapped = True
        return data

    monkeypatch.setattr(os, "read", swapping_read)
    assert DOGFOOD.read_cache_artifact(
        root, version, "skills/skiphow/references/testing.md"
    ) is None
    assert swapped is True


@pytest.mark.parametrize("component", ["7.8.9", "skills", "skiphow", "references"])
def test_dogfood_cache_roster_rejects_each_ancestor_symlink_swap(
    component: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    reference = root / version / "skills/skiphow/references/testing.md"
    reference.parent.mkdir(parents=True)
    reference.write_text("original bytes", encoding="utf-8")
    targets = {
        version: root / version,
        "skills": root / version / "skills",
        "skiphow": root / version / "skills/skiphow",
        "references": root / version / "skills/skiphow/references",
    }
    external = tmp_path / f"external-{component}"
    external.mkdir()
    (external / "forged.md").write_text("forged external bytes", encoding="utf-8")
    original_open_child = DOGFOOD.open_cache_child_directory
    swapped = False

    def swapping_open_child(parent: int, name: str) -> int:
        nonlocal swapped
        if name == component and not swapped:
            swapped = True
            target = targets[component]
            target.rename(target.with_name(f"{target.name}-original"))
            target.symlink_to(external, target_is_directory=True)
        return original_open_child(parent, name)

    monkeypatch.setattr(DOGFOOD, "open_cache_child_directory", swapping_open_child)
    assert DOGFOOD.cache_reference_roster_at(root, version) == (
        set(),
        False,
        True,
    )
    assert swapped is True


def test_dogfood_cache_roster_rejects_a_root_symlink_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    reference = root / version / "skills/skiphow/references/testing.md"
    reference.parent.mkdir(parents=True)
    reference.write_text("original bytes", encoding="utf-8")
    external = tmp_path / "external-root"
    forged = external / version / "skills/skiphow/references/forged.md"
    forged.parent.mkdir(parents=True)
    forged.write_text("forged external bytes", encoding="utf-8")
    original_open_root = DOGFOOD.open_cache_root_descriptor

    def swapping_open_root(path: str | Path) -> int:
        root.rename(tmp_path / "cache-root-original")
        root.symlink_to(external, target_is_directory=True)
        return original_open_root(path)

    monkeypatch.setattr(DOGFOOD, "open_cache_root_descriptor", swapping_open_root)
    assert DOGFOOD.cache_reference_roster_at(root, version) == (
        set(),
        False,
        True,
    )


def test_dogfood_cache_roster_revalidates_references_directory_after_aba(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    references = root / version / "skills/skiphow/references"
    references.mkdir(parents=True)
    (references / "testing.md").write_text("original", encoding="utf-8")
    attacker = tmp_path / "attacker-references"
    attacker.mkdir()
    (attacker / "forged.md").write_text("forged", encoding="utf-8")
    stash = tmp_path / "original-references"
    original_scandir = os.scandir
    swapped = False

    def swapping_scandir(path: object):
        nonlocal swapped
        if isinstance(path, int) and not swapped:
            references.rename(stash)
            attacker.rename(references)
            try:
                result = original_scandir(path)
            finally:
                references.rename(attacker)
                stash.rename(references)
            swapped = True
            return result
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", swapping_scandir)
    monkeypatch.setattr(
        DOGFOOD, "cache_descriptor_walk_supported", lambda: True
    )
    assert DOGFOOD.cache_reference_roster_at(root, version) == (
        set(),
        False,
        True,
    )
    assert swapped is True


def test_dogfood_cache_roster_revalidates_recursive_directory_after_aba(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    root = tmp_path / "cache-root"
    leaf = root / version / "skills/skiphow/references/group/leaf"
    leaf.mkdir(parents=True)
    (leaf / "testing.md").write_text("original", encoding="utf-8")
    leaf_status = leaf.lstat()
    attacker = tmp_path / "attacker-leaf"
    attacker.mkdir()
    (attacker / "forged.md").write_text("forged", encoding="utf-8")
    stash = tmp_path / "original-leaf"
    original_scandir = os.scandir
    swapped = False

    def swapping_scandir(path: object):
        nonlocal swapped
        if (
            isinstance(path, int)
            and not swapped
            and os.path.samestat(os.fstat(path), leaf_status)
        ):
            leaf.rename(stash)
            attacker.rename(leaf)
            try:
                result = original_scandir(path)
            finally:
                leaf.rename(attacker)
                stash.rename(leaf)
            swapped = True
            return result
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", swapping_scandir)
    monkeypatch.setattr(
        DOGFOOD, "cache_descriptor_walk_supported", lambda: True
    )
    assert DOGFOOD.cache_reference_roster_at(root, version) == (
        set(),
        False,
        True,
    )
    assert swapped is True


def test_dogfood_observed_cache_compares_raw_newline_bytes(
    tmp_path: Path,
) -> None:
    version = "7.8.9"
    roots = (tmp_path / "lf-root", tmp_path / "cr-root")
    for root, body in zip(roots, (b"one\ntwo\n", b"one\rtwo\r"), strict=True):
        reference = root / version / "skills/skiphow/references/testing.md"
        reference.parent.mkdir(parents=True)
        reference.write_bytes(body)

    assert DOGFOOD.package_reference(
        version, "testing", tuple(str(root) for root in roots)
    ) == ("", "observed_cache_roots_disagree_or_are_incomplete")


def test_dogfood_cached_artifact_rejects_a_nonplain_configured_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "7.8.9"
    relative = "skills/skiphow/references/testing.md"
    valid_root = tmp_path / "valid-cache"
    valid_artifact = valid_root / version / relative
    valid_artifact.parent.mkdir(parents=True)
    valid_artifact.write_text("valid bytes", encoding="utf-8")
    missing_version_root = tmp_path / "missing-version-cache"
    missing_version_root.mkdir()
    missing_root = tmp_path / "missing-cache"
    monkeypatch.setattr(
        DOGFOOD,
        "plugin_cache_roots",
        lambda: (valid_root, missing_version_root, missing_root),
    )
    assert DOGFOOD.cached_artifact(version, relative) == ("valid bytes", "cache")

    external_version = tmp_path / "external-version"
    external_artifact = external_version / relative
    external_artifact.parent.mkdir(parents=True)
    external_artifact.write_text("valid bytes", encoding="utf-8")
    nonplain_root = tmp_path / "nonplain-cache"
    nonplain_root.mkdir()
    (nonplain_root / version).symlink_to(
        external_version, target_is_directory=True
    )
    monkeypatch.setattr(
        DOGFOOD,
        "plugin_cache_roots",
        lambda: (valid_root, nonplain_root),
    )
    assert DOGFOOD.cached_artifact(version, relative) == (
        "",
        "contract_bytes_unavailable",
    )


def test_dogfood_activation_cache_governs_reference_body_scoring(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    version = "7.8.9"
    root = host_cache_root(home)
    skill_body = "# SkipHow\n\nObserved exact owner contract.\n"
    reference_body = "CACHE REFERENCE BODY"
    skill = root / version / "skills/skiphow/SKILL.md"
    reference = root / version / "skills/skiphow/references/testing.md"
    reference.parent.mkdir(parents=True)
    skill.write_text(skill_body, encoding="utf-8")
    reference.write_text(reference_body, encoding="utf-8")
    monkeypatch.setattr(
        DOGFOOD,
        "tagged_artifact",
        lambda _version, _relative: ("TAG REFERENCE BODY", "tag"),
    )

    records = claude_call(
        "activate", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
    )
    records.append(
        {
            "type": "user",
            "uuid": "activate-injection",
            "parentUuid": "activate-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "activate",
            "message": {
                "content": (
                    "Base directory for this skill: "
                    f"{root / version / 'skills/skiphow'}\n{skill_body}"
                )
            },
        }
    )
    records.extend(
        claude_call("show-reference", "Bash", {"command": "opaque"}, reference_body)
    )
    records.append(
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "done"}]},
        }
    )
    project = home / "projects/project"
    project.mkdir(parents=True)
    transcript = write_transcript(project, records)
    data = DOGFOOD.digest(transcript, 10_000, home)
    assert data["confounders"]["contract_body_identity"] == "single"
    assert data["references"]["testing"]["artifact_source"] == (
        "observed_cache_path"
    )
    assert data["references"]["testing"]["verdict"] == "body_observed"


def test_dogfood_missing_observed_activation_cache_never_falls_back_for_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    version = "7.8.9"
    root = host_cache_root(home)
    skill_body = "# SkipHow\n\nTranscript-proven owner contract.\n"
    reference_body = "TAG REFERENCE BODY"

    def tagged(_version: str, relative: str) -> tuple[str, str]:
        return (
            skill_body if relative.endswith("/SKILL.md") else reference_body,
            "tag",
        )

    monkeypatch.setattr(DOGFOOD, "tagged_artifact", tagged)
    records = claude_call(
        "activate", "Skill", {"skill": "skiphow:skiphow"}, "Skill loaded"
    )
    records.append(
        {
            "type": "user",
            "uuid": "activate-injection",
            "parentUuid": "activate-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "activate",
            "message": {
                "content": (
                    "Base directory for this skill: "
                    f"{root / version / 'skills/skiphow'}\n{skill_body}"
                )
            },
        }
    )
    missing_reference = root / version / "skills/skiphow/references/testing.md"
    records.extend(
        claude_call(
            "read-reference",
            "Read",
            {"file_path": str(missing_reference)},
            reference_body,
        )
    )
    project = home / "projects/project"
    project.mkdir(parents=True)
    data = DOGFOOD.digest(write_transcript(project, records), 10_000, home)
    assert data["confounders"]["contract_body_identity"] == (
        "partially_unverified"
    )
    assert data["references"]["testing"]["verdict"] == (
        "unverified_contract_body"
    )
    assert data["references"]["testing"]["artifact_source"] == (
        "contract_body_unsettled"
    )
    roster_only = DOGFOOD.detect_references(
        Path("unused"), [], version, (str(root),)
    )
    assert roster_only == {
        DOGFOOD.REFERENCE_ROSTER_LABEL: {
            "verdict": "unverified_contract_provenance",
            "basis": "governing_cache_roots_unsettled",
            "matching_line_values": "unavailable",
            "artifact_source": "contract_bytes_unavailable",
            "actions": ["none"],
            "mismatched_path_versions": [],
            "mismatched_path_sources": [],
        }
    }


def test_dogfood_differing_governing_cache_reference_bytes_fail_closed(
    tmp_path: Path,
) -> None:
    version = "7.8.9"
    roots = (tmp_path / "one", tmp_path / "two")
    for index, root in enumerate(roots):
        skill = root / version / "skills/skiphow/SKILL.md"
        reference = root / version / "skills/skiphow/references/testing.md"
        reference.parent.mkdir(parents=True)
        skill.write_text("same skill", encoding="utf-8")
        reference.write_text(f"reference {index}", encoding="utf-8")
    evidence = DOGFOOD.detect_references(
        Path("unused"),
        [],
        version,
        tuple(str(root) for root in roots),
    )
    assert evidence["testing"]["verdict"] == "unverified_contract_provenance"
    assert evidence["testing"]["artifact_source"] == (
        "observed_cache_roots_disagree_or_are_incomplete"
    )
def test_dogfood_json_equality_is_deep_type_strict_and_fail_closed() -> None:
    def nested(leaf: object) -> object:
        value = leaf
        for index in range(500):
            value = {"value": [value]} if index % 2 else [value]
        return value

    assert DOGFOOD.json_values_equal(nested("leaf"), nested("leaf")) is True
    assert DOGFOOD.json_values_equal(nested("leaf"), nested("changed")) is False
    assert DOGFOOD.json_values_equal(True, 1) is False
    assert DOGFOOD.json_values_equal(float("inf"), float("inf")) is False
    assert DOGFOOD.json_values_equal({1: "value"}, {1: "value"}) is False
    shared: list[object] = []
    assert DOGFOOD.json_values_equal([shared, shared], [[], []]) is False
    cycle: list[object] = []
    cycle.append(cycle)
    assert DOGFOOD.json_values_equal(cycle, cycle) is False


def test_dogfood_deep_codex_mcp_identity_never_recurses() -> None:
    arguments: object = "leaf"
    for index in range(500):
        arguments = {"value": [arguments]} if index % 2 else [arguments]
    started = {
        "type": "item.started",
        "item": {
            "id": "deep-mcp",
            "type": "mcp_tool_call",
            "server": "server",
            "tool": "tool",
            "arguments": arguments,
            "result": None,
            "error": None,
            "status": "in_progress",
        },
    }
    completed = {
        "type": "item.completed",
        "item": {
            **started["item"],
            "result": codex_mcp_result(),
            "status": "completed",
        },
    }
    (event,) = DOGFOOD.terminal_tool_events([started, completed])
    assert event["outcome"] == "succeeded"


def test_dogfood_reference_index_parses_each_payload_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = [
        f"/repo/.agents/skills/skiphow/references/ref-{index}.md"
        for index in range(600)
    ]
    records = [
        {
            "type": "item.completed",
            "item": {
                "id": "many-files",
                "type": "file_change",
                "changes": [{"path": path, "kind": "update"} for path in paths],
                "status": "completed",
            },
        }
    ]
    original = DOGFOOD.recognized_path_root
    calls = 0

    def counted(value: object) -> tuple[str, str, str, str] | None:
        nonlocal calls
        calls += 1
        return original(value)

    monkeypatch.setattr(DOGFOOD, "recognized_path_root", counted)
    evidence = DOGFOOD.detect_references(Path("unused"), records, "unknown")
    assert calls == len(paths)
    assert len(evidence) == len(paths)
    assert all(
        info["verdict"] == "write_action_succeeded"
        for info in evidence.values()
    )


def test_dogfood_longest_exact_known_path_root_wins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repo"
    nested_cache = repository / "plugins/skiphow/skills/cache"
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: repository)
    monkeypatch.setattr(DOGFOOD, "plugin_cache_roots", lambda: (tmp_path, nested_cache))
    cache_path = nested_cache / "2.0.0/skills/testing/SKILL.md"
    (cache_hit,) = DOGFOOD.skill_paths(str(cache_path), require_file=True)
    assert cache_hit["version"] == "2.0.0"
    assert cache_hit["_root"] == str(nested_cache)

    source_inside_cache = tmp_path / "2.0.0/skills/container"
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: source_inside_cache)
    source_path = source_inside_cache / "plugins/skiphow/skills/testing/SKILL.md"
    (source_hit,) = DOGFOOD.skill_paths(str(source_path), require_file=True)
    assert source_hit["source"] == "plugin"
    assert source_hit["version"] == "unknown"


@pytest.mark.parametrize(
    "path",
    [
        r"C:\Work\.agents\skills\testing\SkIlL.Md",
        r"\\server\share\.agents\skills\testing\sKiLl.mD",
        r".agents\skills/testing\SKill.Md",
        r"plugins\skiphow/skills/testing\sKiLl.Md",
    ],
)
def test_dogfood_windows_skill_file_operands_are_case_insensitive(path: str) -> None:
    (hit,) = DOGFOOD.skill_paths(path, require_file=True)
    assert hit["name"] == "testing"


@pytest.mark.parametrize(
    "path",
    [
        "file:/repo/.agents/skills/testing/SKILL.md",
        "http:/repo/.agents/skills/testing/SKILL.md",
        r"C:relative\.agents\skills\testing\SKILL.md",
        "/repo/foo:bar/.agents/skills/testing/SKILL.md",
        "C:/repo/foo:bar/.agents/skills/testing/SKILL.md",
        "/repo/literal\\plugins/skiphow/skills/testing/SKILL.md",
        "repo/literal\\plugins/skiphow/skills/testing/SKILL.md",
        "/repo/.agents/skills/testing/skill.md",
    ],
)
def test_dogfood_rejects_uri_colon_and_native_mixed_path_lookalikes(path: str) -> None:
    assert DOGFOOD.skill_paths(path, require_file=True) == []


@pytest.mark.parametrize(
    "payload",
    [
        [
            {
                "type": "search_result",
                "source": "https://example.test",
                "title": "result",
                "content": [],
            },
            {"type": "text", "text": "exact text"},
        ],
        [
            {"type": "text", "text": "exact text"},
            {"type": "image", "source": {"type": "base64"}},
        ],
        [
            {"type": "text", "text": "exact text"},
            {
                "type": "document",
                "source": {"type": "base64", "media_type": "text/plain"},
            },
        ],
    ],
)
def test_dogfood_malformed_known_tool_result_blocks_fail_closed(
    payload: list[dict],
) -> None:
    assert DOGFOOD.result_content_payload_valid(payload) is False
    assert DOGFOOD.result_content_text(payload) == ""


@pytest.mark.parametrize(
    "block",
    [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "AA==",
            },
        },
        {"type": "image", "source": {"type": "url", "url": "https://example.test/i"}},
        {"type": "image", "source": {"type": "file", "file_id": "file-1"}},
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": "AA==",
            },
        },
        {"type": "document", "source": {"type": "url", "url": "https://example.test/d"}},
        {"type": "document", "source": {"type": "file", "file_id": "file-2"}},
    ],
)
def test_dogfood_current_opaque_tool_result_variants_validate(block: dict) -> None:
    assert DOGFOOD.result_content_payload_valid([block]) is True
    assert DOGFOOD.result_content_text([block]) == ""


def test_dogfood_malformed_known_block_cannot_prove_exact_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "first exact line\nsecond exact line"
    records = claude_read(
        "read-malformed",
        cached_reference_path("testing"),
        body,
    )
    records[1]["message"]["content"][0]["content"] = [
        {"type": "text", "text": body},
        {"type": "image", "source": {"type": "base64"}},
    ]
    info = reference_info(monkeypatch, records, body=body, source="tag")
    assert info["verdict"] not in {"body_observed", "exact_excerpt_observed"}


@pytest.mark.parametrize(
    "pattern",
    ["[", "(" * 1000 + "x" + ")" * 1000, "a{999999999999999999999}"],
)
def test_dogfood_invalid_grep_regex_is_a_bounded_private_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    pattern: str,
) -> None:
    monkeypatch.setattr(
        DOGFOOD,
        "resolve",
        lambda *_args: (_ for _ in ()).throw(AssertionError("resolved transcript")),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(ROOT / ".claude/skills/dogfood/sessions.py"),
            "--home",
            str(tmp_path),
            "grep",
            "private-target",
            pattern,
        ],
    )
    with pytest.raises(SystemExit) as error:
        DOGFOOD.main()
    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert "Traceback" not in captured.err
    assert str(ROOT) not in captured.err
    assert "private-target" not in captured.err
    assert len(captured.err) < 500


@pytest.mark.parametrize(
    ("command", "option", "value"),
    [
        ("grep", "--max", "private-secret"),
        ("grep", "--chars", "9" * 5000),
        ("digest", "--report-chars", "private-secret"),
    ],
)
def test_dogfood_invalid_numeric_bounds_do_not_echo_private_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
    option: str,
    value: str,
) -> None:
    tail = ["target", "pattern", option, value] if command == "grep" else ["target", option, value]
    monkeypatch.setattr(
        sys,
        "argv",
        ["sessions.py", "--home", str(tmp_path), command, *tail],
    )
    with pytest.raises(SystemExit) as error:
        DOGFOOD.main()
    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert value not in captured.err
    assert "Traceback" not in captured.err
    assert len(captured.err) < 500


def test_dogfood_coverage_stales_when_nested_evidence_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/owner-session.jsonl"
    root.parent.mkdir(parents=True)
    root_record = {
        "type": "user",
        "timestamp": "2026-08-27T10:00:00Z",
        "cwd": "/work/owner",
        "origin": {"kind": "human"},
        "message": {"content": "skiphow:skiphow"},
    }
    root.write_text(json.dumps(root_record) + "\n", encoding="utf-8")
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    first_nested = {
        "type": "user",
        "timestamp": "2026-08-27T11:00:00Z",
        "cwd": "/work/delegate",
        "message": {"content": "skiphow:skiphow"},
    }
    nested.write_text(json.dumps(first_nested) + "\n", encoding="utf-8")
    (before,) = DOGFOOD.discover(home, None)
    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "owner-session",
                before["records"],
                before["versions"],
                before["evidence_fingerprint"],
            )
        ],
    )
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    assert DOGFOOD.coverage(home).splitlines()[-1].endswith("covered")

    second_nested = {
        **first_nested,
        "timestamp": "2026-08-28T11:00:00Z",
    }
    with nested.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(second_nested) + "\n")
    (after,) = DOGFOOD.discover(home, None)
    assert after["records"] == before["records"]
    assert after["versions"] == before["versions"]
    assert after["evidence_fingerprint"] != before["evidence_fingerprint"]
    assert DOGFOOD.coverage(home).splitlines()[-1].endswith("STALE")


def test_dogfood_candidate_fingerprint_covers_full_marker_date_multiset(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/date-session.jsonl"
    root.parent.mkdir(parents=True)
    records = [
        {
            "type": "user",
            "timestamp": f"2026-08-{day:02d}T10:00:00Z",
            "cwd": "/work/owner",
            "message": {"content": "skiphow:skiphow"},
        }
        for day in (1, 2, 4)
    ]
    root.write_text("\n".join(map(json.dumps, records)) + "\n", encoding="utf-8")
    (before,) = DOGFOOD.discover(home, None)
    records[1]["timestamp"] = "2026-08-03T10:00:00Z"
    root.write_text("\n".join(map(json.dumps, records)) + "\n", encoding="utf-8")
    (after,) = DOGFOOD.discover(home, None)
    assert before["candidate_marker_local_dates"] == after[
        "candidate_marker_local_dates"
    ]
    assert before["root_marker_records"] == after["root_marker_records"]
    assert before["evidence_fingerprint"] != after["evidence_fingerprint"]


def test_dogfood_candidate_fingerprint_covers_same_version_body_evidence(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    body = "# SkipHow\n\nExact installed body.\n"
    installed = host_cache_root(home) / "2.0.0/skills/skiphow"
    installed.mkdir(parents=True)
    (installed / "SKILL.md").write_text(body, encoding="utf-8")
    records = [
        {
            "type": "user",
            "timestamp": "2026-08-27T10:00:00Z",
            "cwd": "/work/owner",
            "origin": {"kind": "human"},
            "message": {"content": "use skiphow:skiphow"},
        },
        *claude_call("skill", "Skill", {"skill": "skiphow:skiphow"}, "loaded"),
        {
            "type": "user",
            "uuid": "injection",
            "parentUuid": "skill-result-record",
            "userType": "external",
            "isMeta": True,
            "sourceToolUseID": "skill",
            "message": {
                "content": f"Base directory for this skill: {installed}\n{body}"
            },
        },
    ]
    root = home / "projects/project/body-session.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text("\n".join(map(json.dumps, records)) + "\n", encoding="utf-8")
    (before,) = DOGFOOD.discover(home, None)
    (installed / "SKILL.md").write_text(
        "# SkipHow\n\nChanged installed body.\n", encoding="utf-8"
    )
    (after,) = DOGFOOD.discover(home, None)
    assert before["versions"] == after["versions"] == ["2.0.0"]
    assert before["records"] == after["records"]
    assert before["evidence_fingerprint"] != after["evidence_fingerprint"]


def test_dogfood_candidate_fingerprint_is_canonical_and_private(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/private-project/canonical-session.jsonl"
    root.parent.mkdir(parents=True)
    private_value = "private-customer-value"
    root_record = {
        "type": "user",
        "timestamp": "2026-08-27T10:00:00Z",
        "cwd": f"/work/{private_value}",
        "message": {"content": f"skiphow:skiphow {private_value}"},
    }
    root.write_text(json.dumps(root_record) + "\n", encoding="utf-8")
    nested_dir = root.with_suffix("") / "subagents"
    nested_dir.mkdir(parents=True)
    nested_records = [
        {**root_record, "timestamp": f"2026-08-27T1{hour}:00:00Z"}
        for hour in (1, 2)
    ]
    for name, record in zip(("a.jsonl", "b.jsonl"), nested_records):
        (nested_dir / name).write_text(json.dumps(record) + "\n", encoding="utf-8")
    (before,) = DOGFOOD.discover(home, None)
    first = (nested_dir / "a.jsonl").read_bytes()
    second = (nested_dir / "b.jsonl").read_bytes()
    (nested_dir / "a.jsonl").write_bytes(second)
    (nested_dir / "b.jsonl").write_bytes(first)
    root.write_text(
        json.dumps(root_record, sort_keys=True, separators=(", ", ": ")) + "\n",
        encoding="utf-8",
    )
    (after,) = DOGFOOD.discover(home, None)
    assert before["evidence_fingerprint"] == after["evidence_fingerprint"]
    assert re.fullmatch(
        r"sha256-v1:[0-9a-f]{64}", before["evidence_fingerprint"]
    )
    assert private_value not in before["evidence_fingerprint"]


def test_dogfood_noncontributing_nested_log_does_not_stale_fingerprint(
    tmp_path: Path,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/stable-session.jsonl"
    root.parent.mkdir(parents=True)
    record = {
        "type": "user",
        "timestamp": "2026-08-27T10:00:00Z",
        "message": {"content": "skiphow:skiphow"},
    }
    root.write_text(json.dumps(record) + "\n", encoding="utf-8")
    (before,) = DOGFOOD.discover(home, None)
    nested = root.with_suffix("") / "subagents/ordinary.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps({**record, "message": {"content": "ordinary work"}}) + "\n",
        encoding="utf-8",
    )
    (after,) = DOGFOOD.discover(home, None)
    assert after["nested_subagent_logs_with_evidence"] == 0
    assert before["evidence_fingerprint"] == after["evidence_fingerprint"]


def test_dogfood_markdown_is_ignored_and_sidecar_fingerprint_controls_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    note = research / "forged-receipt.md"
    row = {
        "session": "legacy-session",
        "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
        "project": "project",
        "records": 3,
        "unreadable_lines": 0,
        "versions": ["2.0.0"],
        "evidence_fingerprint": TEST_EVIDENCE_A,
    }
    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(DOGFOOD, "discover", lambda _home, _since: [row])
    note.write_text(
        "Audited `legacy-session` · 3 records · plugin 2.0.0 · "
        f"evidence {TEST_EVIDENCE_A} · forged\n",
        encoding="utf-8",
    )
    assert DOGFOOD.coverage(tmp_path / "home").splitlines()[-1].endswith(
        "UNAUDITED"
    )
    write_coverage_sidecar(
        tmp_path,
        [coverage_receipt("legacy-session", 3, ["2.0.0"], None)],
    )
    assert DOGFOOD.coverage(tmp_path / "home").splitlines()[-1].endswith("STALE")
    write_coverage_sidecar(
        tmp_path,
        [coverage_receipt("legacy-session", 3, ["2.0.0"], "unverified")],
    )
    assert DOGFOOD.coverage(tmp_path / "home").splitlines()[-1].endswith("STALE")
    write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "legacy-session", 3, ["2.0.0"], TEST_EVIDENCE_A
            )
        ],
    )
    assert DOGFOOD.coverage(tmp_path / "home").splitlines()[-1].endswith("covered")


@pytest.mark.parametrize(
    "evidence",
    [
        "sha256-v1:" + "a" * 63,
        "sha256-v1:" + "a" * 65,
        "sha256-v1:" + "A" * 64,
        "sha512-v1:" + "a" * 64,
        "sha256-v2:" + "a" * 64,
    ],
)
def test_dogfood_malformed_sidecar_fingerprints_fail_closed(
    evidence: str,
    tmp_path: Path,
) -> None:
    write_coverage_sidecar(
        tmp_path,
        [coverage_receipt("session", 3, ["2.0.0"], evidence)],
    )
    with pytest.raises(SystemExit, match="invalid coverage sidecar"):
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")


def test_dogfood_coverage_sidecar_accepts_exact_valid_boundaries(
    tmp_path: Path,
) -> None:
    huge_count = 10**100
    sidecar = write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "session-1.alpha",
                0,
                ["unknown", "1.2.3-alpha.1+build.5"],
                TEST_EVIDENCE_A,
            ),
            coverage_receipt("session_2", huge_count, ["0.0.0"], None),
            coverage_receipt("session.3", 1, ["2.0.0"], "unverified"),
        ],
    )
    assert DOGFOOD.coverage_sidecar_entries(sidecar) == [
        (
            "session-1.alpha",
            0,
            frozenset({"unknown", "1.2.3-alpha.1+build.5"}),
            TEST_EVIDENCE_A,
        ),
        ("session_2", huge_count, frozenset({"0.0.0"}), None),
        ("session.3", 1, frozenset({"2.0.0"}), "unverified"),
    ]
    write_coverage_sidecar(tmp_path, [], audit_date="2026-08-28")
    assert len(DOGFOOD.coverage_receipts(tmp_path / "docs/research")) == 3


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("session", ""),
        ("session", "../session"),
        ("session", "session/child"),
        ("session", 7),
        ("records", True),
        ("records", -1),
        ("records", 1.0),
        ("records", "1"),
        ("plugin_versions", []),
        ("plugin_versions", "2.0.0"),
        ("plugin_versions", ["2.0.0", "2.0.0"]),
        ("plugin_versions", ["unknown", "unknown"]),
        ("plugin_versions", ["01.2.3"]),
        ("plugin_versions", ["1.2.3-01"]),
        ("plugin_versions", ["1.2"]),
        ("plugin_versions", [7]),
    ],
)
def test_dogfood_coverage_sidecar_rejects_invalid_receipt_fields(
    field: str,
    value: object,
    tmp_path: Path,
) -> None:
    receipt = coverage_receipt("session", 1, ["2.0.0"], TEST_EVIDENCE_A)
    receipt[field] = value
    write_coverage_sidecar(tmp_path, [receipt])
    with pytest.raises(SystemExit, match="invalid coverage sidecar"):
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")


@pytest.mark.parametrize(
    "document",
    [
        {"source": DOGFOOD.COVERAGE_SOURCE, "receipts": []},
        {
            "schema": DOGFOOD.COVERAGE_SCHEMA,
            "source": DOGFOOD.COVERAGE_SOURCE,
            "receipts": [],
            "extra": True,
        },
        {
            "schema": "skiphow.dogfood.coverage/v2",
            "source": DOGFOOD.COVERAGE_SOURCE,
            "receipts": [],
        },
        {
            "schema": DOGFOOD.COVERAGE_SCHEMA,
            "source": "other-transcripts",
            "receipts": [],
        },
        {
            "schema": DOGFOOD.COVERAGE_SCHEMA,
            "source": DOGFOOD.COVERAGE_SOURCE,
            "receipts": {},
        },
        {
            "schema": DOGFOOD.COVERAGE_SCHEMA,
            "source": DOGFOOD.COVERAGE_SOURCE,
            "receipts": [
                {
                    "session": "session",
                    "records": 1,
                    "plugin_versions": ["2.0.0"],
                }
            ],
        },
        {
            "schema": DOGFOOD.COVERAGE_SCHEMA,
            "source": DOGFOOD.COVERAGE_SOURCE,
            "receipts": [
                {
                    "session": "session",
                    "records": 1,
                    "plugin_versions": ["2.0.0"],
                    "evidence_fingerprint": TEST_EVIDENCE_A,
                    "note": "extra",
                }
            ],
        },
    ],
)
def test_dogfood_coverage_sidecar_requires_exact_keys_and_envelope(
    document: dict,
    tmp_path: Path,
) -> None:
    sidecar = write_coverage_sidecar(tmp_path, [])
    sidecar.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


@pytest.mark.parametrize(
    "payload",
    [
        (
            b'{"schema":"skiphow.dogfood.coverage/v1",'
            b'"schema":"skiphow.dogfood.coverage/v1",'
            b'"source":"claude-code-project-transcripts","receipts":[]}'
        ),
        (
            b'{"schema":"skiphow.dogfood.coverage/v1",'
            b'"source":"claude-code-project-transcripts","receipts":'
            b'[{"session":"one","se\\u0073ion":"two","records":1,'
            b'"plugin_versions":["2.0.0"],"evidence_fingerprint":null}]}'
        ),
        b'{"records":NaN}',
        b'{"records":Infinity}',
        b'{"records":-Infinity}',
        b'{"records":1e400}',
        b'{}{}',
        b'\xef\xbb\xbf{}',
        b'\xff',
        '{"schema":"value"}'.encode("utf-16"),
    ],
)
def test_dogfood_coverage_sidecar_rejects_non_strict_json(
    payload: bytes,
    tmp_path: Path,
) -> None:
    sidecar = write_coverage_sidecar(tmp_path, [])
    sidecar.write_bytes(payload)
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_coverage_sidecar_rejects_excessive_json_depth(
    tmp_path: Path,
) -> None:
    sidecar = write_coverage_sidecar(tmp_path, [])
    sidecar.write_text("[" * 2_000 + "0" + "]" * 2_000, encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


@pytest.mark.parametrize(
    "node_kind",
    [
        "missing_report",
        "sidecar_symlink",
        "report_symlink",
        "sidecar_directory",
        "report_directory",
        "sidecar_fifo",
        "report_fifo",
    ],
)
def test_dogfood_coverage_sidecar_and_report_must_be_regular(
    node_kind: str,
    tmp_path: Path,
) -> None:
    sidecar = write_coverage_sidecar(tmp_path, [])
    report = sidecar.with_name(
        sidecar.name[: -len(".receipts.json")] + ".md"
    )
    selected = sidecar if node_kind.startswith("sidecar_") else report
    if node_kind == "missing_report":
        report.unlink()
    elif node_kind.endswith("symlink"):
        target = selected.with_name("private-target")
        target.write_text("private", encoding="utf-8")
        selected.unlink()
        selected.symlink_to(target)
    elif node_kind.endswith("directory"):
        selected.unlink()
        selected.mkdir()
    else:
        selected.unlink()
        os.mkfifo(selected)
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_coverage_ignores_filename_near_misses_but_rejects_bad_dates(
    tmp_path: Path,
) -> None:
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    for name in (
        "field-audit-2026-8-27.receipts.json",
        "field-audit-2026-08-27.receipt.json",
        "other-field-audit-2026-08-27.receipts.json",
    ):
        (research / name).write_text("private malformed bytes", encoding="utf-8")
    assert DOGFOOD.coverage_receipts(research) == set()

    bad = research / "field-audit-2026-99-99.receipts.json"
    bad.write_text("{}", encoding="utf-8")
    bad.with_name("field-audit-2026-99-99.md").write_text(
        "# report\n", encoding="utf-8"
    )
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(research)
    assert str(error.value) == "invalid coverage sidecar"


@pytest.mark.parametrize("mutation", ["replace", "append"])
def test_dogfood_coverage_sidecar_mutation_while_reading_fails_closed(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar = write_coverage_sidecar(tmp_path, [])
    replacement = sidecar.with_name("replacement.tmp")
    replacement.write_bytes(sidecar.read_bytes())
    original = DOGFOOD.opened_transcript_stable
    mutated = False

    def mutate(path: Path, handle: object, before: os.stat_result) -> bool:
        nonlocal mutated
        if path == sidecar and not mutated:
            if mutation == "replace":
                os.replace(replacement, sidecar)
            else:
                with sidecar.open("ab") as output:
                    output.write(b" ")
            mutated = True
        return original(path, handle, before)

    monkeypatch.setattr(DOGFOOD, "opened_transcript_stable", mutate)
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_coverage_sidecar_inventory_addition_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_coverage_sidecar(tmp_path, [], audit_date="2026-08-27")
    original = DOGFOOD.coverage_sidecar_entries
    added = False

    def add_sidecar(
        path: Path,
        expected_sidecar: tuple[int, int, int, int, int] | None = None,
        expected_report: tuple[int, int, int, int, int] | None = None,
    ):
        nonlocal added
        entries = original(path, expected_sidecar, expected_report)
        if not added:
            write_coverage_sidecar(tmp_path, [], audit_date="2026-08-28")
            added = True
        return entries

    monkeypatch.setattr(DOGFOOD, "coverage_sidecar_entries", add_sidecar)
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


@pytest.mark.parametrize("target_kind", ["sidecar", "report"])
def test_dogfood_coverage_file_aba_cannot_replace_inventoried_pair(
    target_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar = write_coverage_sidecar(tmp_path, [])
    report = sidecar.with_name(
        sidecar.name[: -len(".receipts.json")] + ".md"
    )
    target = sidecar if target_kind == "sidecar" else report
    attacker = target.with_name(f"attacker-{target_kind}.tmp")
    attacker.write_text(
        json.dumps(
            {
                "schema": DOGFOOD.COVERAGE_SCHEMA,
                "source": DOGFOOD.COVERAGE_SOURCE,
                "receipts": [
                    coverage_receipt(
                        "injected", 1, ["2.0.0"], TEST_EVIDENCE_A
                    )
                ],
            }
        )
        if target_kind == "sidecar"
        else "# attacker report\n",
        encoding="utf-8",
    )
    stash = target.with_name(f"original-{target_kind}.tmp")
    original = DOGFOOD.coverage_sidecar_entries

    def aba(
        path: Path,
        expected_sidecar: tuple[int, int, int, int, int] | None = None,
        expected_report: tuple[int, int, int, int, int] | None = None,
    ):
        os.replace(target, stash)
        os.replace(attacker, target)
        try:
            return original(path, expected_sidecar, expected_report)
        finally:
            os.replace(target, attacker)
            os.replace(stash, target)

    monkeypatch.setattr(DOGFOOD, "coverage_sidecar_entries", aba)
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_coverage_dated_directory_aba_cannot_inject_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar = write_coverage_sidecar(tmp_path, [])
    dated = sidecar.parent
    attacker = tmp_path / "attacker-date"
    attacker.mkdir()
    attacker_sidecar = attacker / sidecar.name
    attacker_sidecar.write_text(
        json.dumps(
            {
                "schema": DOGFOOD.COVERAGE_SCHEMA,
                "source": DOGFOOD.COVERAGE_SOURCE,
                "receipts": [
                    coverage_receipt(
                        "injected", 1, ["2.0.0"], TEST_EVIDENCE_A
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    (attacker / "field-audit-2026-08-27.md").write_text(
        "# attacker report\n", encoding="utf-8"
    )
    stash = dated.with_name("original-date")
    original = DOGFOOD.coverage_sidecar_entries

    def aba(
        path: Path,
        expected_sidecar: tuple[int, int, int, int, int] | None = None,
        expected_report: tuple[int, int, int, int, int] | None = None,
    ):
        dated.rename(stash)
        attacker.rename(dated)
        try:
            return original(path, expected_sidecar, expected_report)
        finally:
            dated.rename(attacker)
            stash.rename(dated)

    monkeypatch.setattr(DOGFOOD, "coverage_sidecar_entries", aba)
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


@pytest.mark.parametrize(
    "parent",
    ["", "2026-08-26", "2026-08-27/nested", "not-a-date"],
)
def test_dogfood_canonical_sidecar_outside_matching_date_directory_fails_closed(
    parent: str,
    tmp_path: Path,
) -> None:
    research = tmp_path / "docs/research"
    directory = research / parent
    directory.mkdir(parents=True)
    sidecar = directory / "field-audit-2026-08-27.receipts.json"
    sidecar.write_text("{}", encoding="utf-8")
    sidecar.with_name("field-audit-2026-08-27.md").write_text(
        "# report\n", encoding="utf-8"
    )
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(research)
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_coverage_rejects_a_symlinked_canonical_date_directory(
    tmp_path: Path,
) -> None:
    external_root = tmp_path / "external"
    external_sidecar = write_coverage_sidecar(external_root, [])
    research = tmp_path / "docs/research"
    research.mkdir(parents=True)
    (research / external_sidecar.parent.name).symlink_to(
        external_sidecar.parent, target_is_directory=True
    )

    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(research)
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_coverage_never_follows_a_symlinked_docs_ancestor(
    tmp_path: Path,
) -> None:
    external_root = tmp_path / "external"
    write_coverage_sidecar(external_root, [])
    (tmp_path / "docs").symlink_to(
        external_root / "docs", target_is_directory=True
    )

    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage_receipts(tmp_path / "docs/research")
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_coverage_reconfirms_receipts_after_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sidecar = write_coverage_sidecar(
        tmp_path,
        [
            coverage_receipt(
                "session", 3, ["2.0.0"], TEST_EVIDENCE_A
            )
        ],
    )
    row = {
        "session": "session",
        "candidate_marker_local_dates": ["2026-08-27", "2026-08-27"],
        "project": "project",
        "records": 3,
        "unreadable_lines": 0,
        "versions": ["2.0.0"],
        "evidence_fingerprint": TEST_EVIDENCE_A,
    }

    def mutate_during_discovery(_home: Path, _since: str | None) -> list[dict]:
        sidecar.write_text(
            json.dumps(
                {
                    "schema": DOGFOOD.COVERAGE_SCHEMA,
                    "source": DOGFOOD.COVERAGE_SOURCE,
                    "receipts": [],
                }
            ),
            encoding="utf-8",
        )
        return [row]

    monkeypatch.setattr(DOGFOOD, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(DOGFOOD, "discover", mutate_during_discovery)
    with pytest.raises(SystemExit) as error:
        DOGFOOD.coverage(tmp_path / "home")
    assert str(error.value) == "invalid coverage sidecar"


def test_dogfood_project_directory_aba_cannot_inject_a_coverable_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    project = home / "projects/project"
    project.mkdir(parents=True)
    transcript = project / "owner-session.jsonl"
    original_record = {
        "type": "user",
        "timestamp": "2026-08-27T10:00:00Z",
        "cwd": "/work/original",
        "message": {"content": "skiphow:skiphow"},
    }
    transcript.write_text(json.dumps(original_record) + "\n", encoding="utf-8")

    attacker = tmp_path / "attacker-project"
    attacker.mkdir()
    injected_record = {**original_record, "cwd": "/work/injected"}
    (attacker / transcript.name).write_text(
        json.dumps(injected_record) + "\n", encoding="utf-8"
    )
    stash = tmp_path / "original-project"
    original = DOGFOOD.scan_marker_member
    swapped = False

    def aba(
        path: Path,
        expected: tuple[int, int, int, int, int] | None = None,
    ):
        nonlocal swapped
        if path != transcript or swapped:
            return original(path, expected)
        swapped = True
        project.rename(stash)
        attacker.rename(project)
        try:
            return original(path, expected)
        finally:
            project.rename(attacker)
            stash.rename(project)

    monkeypatch.setattr(DOGFOOD, "scan_marker_member", aba)
    (row,) = DOGFOOD.discover(home, None)
    assert row["candidate_marker_scope"] == "unverified_scan_error"
    assert row["evidence_fingerprint"] == "unverified"
    assert row["versions"] == ["unknown"]
    assert row["observed_cwds"] == []
    assert "/work/injected" not in row["candidate_marker_cwds"]


def test_dogfood_atomic_replacement_during_marker_scan_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/replaced-session.jsonl"
    transcript.parent.mkdir(parents=True)
    original_record = {
        "type": "user",
        "timestamp": "2026-08-27T10:00:00Z",
        "cwd": "/work/original",
        "message": {"content": "skiphow:skiphow"},
    }
    replacement_record = {
        **original_record,
        "cwd": "/work/replacement",
    }
    transcript.write_text(json.dumps(original_record) + "\n", encoding="utf-8")
    replacement = transcript.with_name("replacement.tmp")
    replacement.write_text(json.dumps(replacement_record) + "\n", encoding="utf-8")
    original_scan = DOGFOOD.stream_contains_marker
    replaced = False

    def swap(handle: object) -> bool:
        nonlocal replaced
        result = original_scan(handle)
        if not replaced:
            os.replace(replacement, transcript)
            replaced = True
        return result

    monkeypatch.setattr(DOGFOOD, "stream_contains_marker", swap)
    with pytest.raises(SystemExit, match="transcript universe changed"):
        DOGFOOD.discover(home, None)


def test_dogfood_deferred_root_parse_is_bound_to_prefiltered_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/deferred-session.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(
        json.dumps(
            {
                "type": "user",
                "cwd": "/work/original",
                "message": {"content": "ordinary owner text"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    nested = root.with_suffix("") / "subagents/agent.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-08-27T10:00:00Z",
                "cwd": "/work/delegate",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    replacement = root.with_name("deferred-replacement.tmp")
    replacement.write_text(
        json.dumps(
            {
                "type": "user",
                "cwd": "/work/replacement",
                "message": {"content": "skiphow:skiphow"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    original = DOGFOOD.scan_marker_member
    swapped = False

    def swap_after_scan(
        path: Path,
        expected: tuple[int, int, int, int, int] | None = None,
    ):
        nonlocal swapped
        result = original(path, expected)
        if path == root and not swapped:
            os.replace(replacement, root)
            swapped = True
        return result

    monkeypatch.setattr(DOGFOOD, "scan_marker_member", swap_after_scan)
    with pytest.raises(SystemExit, match="transcript universe changed"):
        DOGFOOD.discover(home, None)


def test_dogfood_in_place_mutation_during_parse_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    transcript = home / "projects/project/mutated-session.jsonl"
    transcript.parent.mkdir(parents=True)
    record = {
        "type": "user",
        "timestamp": "2026-08-27T10:00:00Z",
        "message": {"content": "skiphow:skiphow"},
    }
    transcript.write_text(json.dumps(record) + "\n", encoding="utf-8")
    original = DOGFOOD.parse_record_stream
    mutated = False

    def mutate(handle: object):
        nonlocal mutated
        result = original(handle)
        if not mutated:
            with transcript.open("a", encoding="utf-8") as output:
                output.write(json.dumps(record) + "\n")
            mutated = True
        return result

    monkeypatch.setattr(DOGFOOD, "parse_record_stream", mutate)
    with pytest.raises(SystemExit, match="transcript universe changed"):
        DOGFOOD.discover(home, None)


def test_dogfood_noncandidate_markerless_logs_are_never_json_parsed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "claude-home"
    root = home / "projects/project/ordinary-session.jsonl"
    root.parent.mkdir(parents=True)
    root.write_text(json.dumps({"type": "user", "message": {"content": "ordinary"}}) + "\n")
    nested = root.with_suffix("") / "subagents/ordinary.jsonl"
    nested.parent.mkdir(parents=True)
    nested.write_text(json.dumps({"type": "user", "message": {"content": "ordinary"}}) + "\n")

    def forbidden(_handle: object):
        raise AssertionError("markerless noncandidate was parsed")

    monkeypatch.setattr(DOGFOOD, "parse_record_stream", forbidden)
    assert DOGFOOD.discover(home, None) == []


def test_dogfood_unknown_marker_counts_and_versions_render_without_false_prefix() -> None:
    row = {
        "session": "session",
        "project": "unknown",
        "candidate_marker_local_dates": ["unknown", "unknown"],
        "candidate_marker_date_status": "unverified_scan_error",
        "undated_marker_records": None,
        "candidate_marker_scope": "unverified_scan_error",
        "candidate_transcript_scope": "root_only",
        "versions": ["unknown"],
        "megabytes": "unknown",
        "records": 0,
        "unreadable_lines": 1,
        "root_transcript_status": "unreadable",
    }
    rendered = DOGFOOD.render_list([row])
    assert "unknown undated marker records" in rendered
    assert "plugin unknown" in rendered
    assert "vunverified" not in rendered


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
        assert set(handler) == {"type", "command", "timeout"}
        assert handler["type"] == "command"
        assert isinstance(handler["command"], str)
        assert _MODULE.SAFE_ECHO_COMMAND.fullmatch(handler["command"])
        assert isinstance(handler["timeout"], int)
        assert not isinstance(handler["timeout"], bool)
        assert handler["timeout"] > 0


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
