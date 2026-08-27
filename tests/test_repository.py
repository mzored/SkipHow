"""Structural contracts for the plugin-only package.

These tests check package shape and the few semantic invariants whose absence
caused a field failure. Other prose remains free to change.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re

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


def test_dogfood_auditor_tracks_shipped_references_and_identity_transitions() -> None:
    reference_root = SKILL.parent / "references"
    current_references = {
        path.stem for path in reference_root.glob("*.md")
    } if reference_root.is_dir() else set()
    assert set(DOGFOOD.REFERENCES) == current_references | set(DOGFOOD.LEGACY_REFERENCES)
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


def test_dogfood_observes_dynamic_top_level_skill_activation_and_reads() -> None:
    records = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Skill",
                        "input": {"skill": "skiphow:future-specialist"},
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
                        "name": "Skill",
                        "input": {"skill": "attributed-specialist"},
                        "caller": {"attributionPlugin": "skiphow"},
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
                        "content": (
                            "Base directory for this skill: "
                            "/private/cache/plugins/cache/skiphow/skiphow/2.0.0/"
                            "skills/future-specialist\n\n# Future specialist"
                        ),
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
                        "name": "Read",
                        "input": {
                            "file_path": (
                                "/private/cache/plugins/cache/skiphow/skiphow/2.0.0/"
                                "skills/future-specialist/SKILL.md"
                            )
                        },
                    },
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {
                            "file_path": (
                                "/private/project/.agents/skills/"
                                "product-decisions/SKILL.md"
                            )
                        },
                    },
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {
                            "command": (
                                "sed -n '1,80p' /checkout/plugins/skiphow/skills/"
                                "research/SKILL.md"
                            )
                        },
                    },
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {
                            "command": (
                                "rg -n hypothesis /private/project/.agents/skills/"
                                "research/SKILL.md"
                            )
                        },
                    },
                ]
            },
        },
    ]

    assert DOGFOOD.detect_skills(records) == [
        {
            "name": "attributed-specialist",
            "source": "plugin",
            "version": "unknown",
            "signals": {"activated": 1},
        },
        {
            "name": "future-specialist",
            "source": "plugin",
            "version": "2.0.0",
            "signals": {"activated": 1, "read": 1},
        },
        {
            "name": "product-decisions",
            "source": "project",
            "version": "unknown",
            "signals": {"read": 1},
        },
        {
            "name": "research",
            "source": "plugin",
            "version": "unknown",
            "signals": {"read": 1},
        },
        {
            "name": "research",
            "source": "project",
            "version": "unknown",
            "signals": {"searched": 1},
        },
    ]


def test_dogfood_keeps_sidechains_and_neighboring_attribution_separate() -> None:
    sidechain = {
        "type": "user",
        "isSidechain": True,
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "content": (
                        "Base directory for this skill: "
                        "/cache/skiphow/skiphow/2.0.0/skills/skiphow"
                    ),
                }
            ]
        },
    }
    neighboring_calls = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "Skill",
                    "input": {"skill": "unattributed-skill"},
                },
                {
                    "type": "tool_use",
                    "name": "Skill",
                    "input": {"skill": "attributed-skill"},
                    "caller": {"attributionPlugin": "skiphow"},
                },
            ]
        },
    }

    assert DOGFOOD.skill_injection_texts(sidechain) == []
    assert DOGFOOD.detect_skills([sidechain, neighboring_calls]) == [
        {
            "name": "attributed-skill",
            "source": "plugin",
            "version": "unknown",
            "signals": {"activated": 1},
        }
    ]


def test_dogfood_keeps_unversioned_activation_separate_from_a_search() -> None:
    records = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Skill",
                        "input": {"skill": "skiphow:research"},
                    }
                ]
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "search-1",
                "type": "command_execution",
                "command": (
                    "rg -n sources /cache/skiphow/skiphow/2.0.0/"
                    "skills/research/SKILL.md"
                ),
                "status": "completed",
                "exit_code": 0,
            },
        },
    ]

    assert DOGFOOD.detect_skills(records) == [
        {
            "name": "research",
            "source": "plugin",
            "version": "2.0.0",
            "signals": {"searched": 1},
        },
        {
            "name": "research",
            "source": "plugin",
            "version": "unknown",
            "signals": {"activated": 1},
        },
    ]


def test_dogfood_uses_a_versioned_codex_read_for_the_digest_version(
    tmp_path: Path,
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "versioned-read"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "read-1",
                "type": "command_execution",
                "command": (
                    "sed -n '1,120p' /cache/skiphow/skiphow/2.0.0/"
                    "skills/skiphow/SKILL.md"
                ),
                "status": "completed",
                "exit_code": 0,
            },
        },
        {"type": "turn.completed", "usage": {}},
    ]
    transcript = tmp_path / "versioned.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    data = DOGFOOD.digest(transcript, 100)
    assert data["plugin_versions"] == ["2.0.0"]
    assert data["skills"] == [
        {
            "name": "skiphow",
            "source": "plugin",
            "version": "2.0.0",
            "signals": {"read": 1},
        }
    ]


def test_dogfood_does_not_treat_failed_codex_access_as_loaded_or_authored(
    tmp_path: Path,
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "failed-access"},
        {"type": "turn.started"},
        {
            "type": "item.started",
            "item": {
                "id": "read-1",
                "type": "command_execution",
                "command": (
                    "sed -n '1,120p' /cache/skiphow/skiphow/2.0.0/"
                    "skills/skiphow/SKILL.md"
                ),
                "status": "in_progress",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "read-1",
                "type": "command_execution",
                "command": (
                    "sed -n '1,120p' /cache/skiphow/skiphow/2.0.0/"
                    "skills/skiphow/SKILL.md"
                ),
                "status": "failed",
                "exit_code": 1,
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "write-1",
                "type": "file_change",
                "changes": [
                    {
                        "path": "/private/project/.agents/skills/testing/SKILL.md",
                        "kind": "update",
                    }
                ],
                "status": "failed",
            },
        },
        {"type": "turn.failed", "error": {"message": "fixture failure"}},
    ]
    transcript = tmp_path / "failed-access.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    data = DOGFOOD.digest(transcript, 100)
    assert data["plugin_versions"] == ["unknown"]
    assert data["skills"] == [
        {
            "name": "skiphow",
            "source": "plugin",
            "version": "2.0.0",
            "signals": {"attempted": 1},
        },
        {
            "name": "testing",
            "source": "project",
            "version": "unknown",
            "signals": {"attempted": 1},
        },
    ]
    assert data["command_results"] == {"failed:1": 1}
    assert data["structured_writes"] == []
    assert data["confounders"]["turn_failed"] is True
    assert data["confounders"]["unfinished_turn"] is False
    assert data["confounders"]["in_flight"] is False


def test_dogfood_surfaces_mixed_plugin_versions_without_picking_reference_bytes(
    tmp_path: Path,
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "mixed-versions"},
        {"type": "turn.started"},
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "content": (
                            "Base directory for this skill: "
                            "/cache/skiphow/skiphow/1.14.2/skills/skiphow"
                        ),
                    }
                ]
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "read-1",
                "type": "command_execution",
                "command": (
                    "sed -n '1,120p' /cache/skiphow/skiphow/2.0.0/"
                    "skills/skiphow/SKILL.md"
                ),
                "status": "completed",
                "exit_code": 0,
            },
        },
        {"type": "turn.completed", "usage": {}},
    ]
    transcript = tmp_path / "mixed.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    data = DOGFOOD.digest(transcript, 100)
    assert data["plugin_versions"] == ["1.14.2", "2.0.0"]
    assert data["confounders"]["mixed_plugin_versions"] is True
    assert {
        (info["verdict"], info["probe_source"])
        for info in data["references"].values()
    } == {("unverified_mixed_version", "mixed_versions")}


def test_dogfood_observes_codex_skill_reads_without_returning_private_paths(
    tmp_path: Path,
) -> None:
    private_path = "/private/project/.agents/skills/skiphow/SKILL.md"
    records = [
        {"type": "thread.started", "thread_id": "codex-thread-id"},
        {"type": "turn.started"},
        {
            "type": "item.started",
            "item": {
                "id": "item-1",
                "type": "command_execution",
                "command": f"sed -n '1,120p' {private_path}",
                "status": "in_progress",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "item-1",
                "type": "command_execution",
                "command": f"sed -n '1,120p' {private_path}",
                "status": "completed",
                "exit_code": 0,
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "item-2",
                "type": "command_execution",
                "command": (
                    "sed -n '1,120p' .agents/skills/testing/SKILL.md && "
                    "sed -n '1,120p' plugins/skiphow/skills/research/SKILL.md"
                ),
                "status": "completed",
                "exit_code": 0,
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "item-3",
                "type": "file_change",
                "changes": [
                    {
                        "path": "/private/project/.agents/skills/testing/SKILL.md",
                        "kind": "update",
                    }
                ],
                "status": "completed",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "item-4",
                "type": "agent_message",
                "text": "Codex final result",
            },
        },
        {
            "type": "turn.completed",
            "usage": {"input_tokens": 100, "output_tokens": 20},
        },
    ]
    transcript = tmp_path / "codex.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    assert DOGFOOD.contains_marker(transcript)
    assert DOGFOOD.detect_skills(records) == [
        {
            "name": "research",
            "source": "plugin",
            "version": "unknown",
            "signals": {"read": 1},
        },
        {
            "name": "skiphow",
            "source": "project",
            "version": "unknown",
            "signals": {"read": 1},
        },
        {
            "name": "testing",
            "source": "project",
            "version": "unknown",
            "signals": {"read": 1, "authored": 1},
        },
    ]
    data = DOGFOOD.digest(transcript, 100)
    rendered = DOGFOOD.render_digest(data)
    assert data["session"] == "codex-thread-id"
    assert data["skills"] == DOGFOOD.detect_skills(records)
    assert data["tools"] == {"command_execution": 2, "file_change": 1}
    assert data["command_results"] == {"completed:0": 2}
    assert data["usage"] == {"input_tokens": 100, "output_tokens": 20}
    assert data["confounders"]["compaction"] == "unknown"
    assert data["confounders"]["in_flight"] is False
    assert data["confounders"]["unfinished_turn"] is False
    assert data["confounders"]["turn_failed"] is False
    assert data["report"]["text"] == "Codex final result"
    assert data["structured_writes"] == [
        {
            "at": "",
            "tool": "file_change",
            "path": "/private/project/.agents/skills/testing/SKILL.md",
        }
    ]
    assert private_path not in json.dumps(data)
    assert private_path not in rendered
    assert "SKILLS" in rendered
    assert "\n  skiphow" in rendered


def test_dogfood_marks_an_unfinished_codex_turn_in_flight(tmp_path: Path) -> None:
    records = [
        {"type": "thread.started", "thread_id": "unfinished"},
        {"type": "turn.started"},
        {
            "type": "item.started",
            "item": {
                "id": "command-1",
                "type": "command_execution",
                "command": "git status --short",
                "status": "in_progress",
            },
        },
    ]
    transcript = tmp_path / "unfinished.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    data = DOGFOOD.digest(transcript, 100)
    assert data["session"] == "unfinished"
    assert data["confounders"]["in_flight"] is True
    assert data["confounders"]["ended_mid_tool"] is True
    assert data["confounders"]["unfinished_turn"] is True
    assert data["confounders"]["turn_failed"] is False
    assert data["confounders"]["compaction"] == "unknown"


def test_dogfood_keeps_a_stale_interrupted_codex_turn_unfinished(
    tmp_path: Path,
    monkeypatch,
) -> None:
    records = [
        {"type": "thread.started", "thread_id": "interrupted"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "command-1",
                "type": "command_execution",
                "command": "git status --short",
                "status": "completed",
                "exit_code": 0,
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "message-1",
                "type": "agent_message",
                "text": "Still working",
            },
        },
    ]
    transcript = tmp_path / "interrupted.jsonl"
    transcript.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        DOGFOOD.time,
        "time",
        lambda: transcript.stat().st_mtime + 16 * 60,
    )

    data = DOGFOOD.digest(transcript, 100)
    assert data["confounders"]["in_flight"] is False
    assert data["confounders"]["ended_mid_tool"] is False
    assert data["confounders"]["unfinished_turn"] is True
    assert data["confounders"]["turn_failed"] is False


def test_dogfood_tracks_pending_codex_web_and_collaboration_tools() -> None:
    for item_type in ("web_search", "collab_tool_call"):
        records = [
            {"type": "turn.started"},
            {
                "type": "item.started",
                "item": {"id": f"{item_type}-1", "type": item_type},
            },
        ]
        assert DOGFOOD.ended_mid_tool(records) is True

        records.append(
            {
                "type": "item.completed",
                "item": {"id": f"{item_type}-1", "type": item_type},
            }
        )
        assert DOGFOOD.ended_mid_tool(records) is False


def test_dogfood_uses_the_actual_final_answer_without_requiring_headings(tmp_path: Path) -> None:
    records = [
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "Result\nold\nEvidence\nstale"}]},
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "Fixed and verified with the full suite."}]},
        },
    ]
    assert DOGFOOD.final_assistant_text(records) == "Fixed and verified with the full suite."
    assert DOGFOOD.report_text(records, ["1.13.0"]) == "Result\nold\nEvidence\nstale"
    assert DOGFOOD.report_text(records, ["1.14.0"]) == "Fixed and verified with the full suite."
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        "\n".join(
            json.dumps(record)
            for record in [
                {
                    "type": "assistant",
                    "timestamp": "2026-08-27T10:00:00Z",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/repo/a.py"}}
                        ]
                    },
                },
                {
                    "type": "assistant",
                    "timestamp": "2026-08-27T10:00:01Z",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": "Bash", "input": {"command": "git status"}}
                        ]
                    },
                },
            ]
        ),
        encoding="utf-8",
    )
    assert DOGFOOD.digest(transcript, 100)["structured_writes"] == [
        {"at": "2026-08-27T10:00:00Z", "tool": "Edit", "path": "/repo/a.py"}
    ]


def test_dogfood_marks_references_absent_from_an_older_package() -> None:
    body, source = DOGFOOD.package_reference("1.6.1", "worktrees")
    assert body == ""
    assert source == "absent_in_version"


def test_dogfood_prefers_exact_version_cache_over_head(
    tmp_path: Path,
    monkeypatch,
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


def test_dogfood_downgrades_negative_evidence_from_nonexact_reference_bytes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    body = (
        "This sentence is intentionally long enough to provide a unique reference "
        "fingerprint for the test."
    )
    transcript = tmp_path / "empty.jsonl"
    transcript.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(DOGFOOD, "REFERENCES", ("future-reference",))
    monkeypatch.setattr(
        DOGFOOD,
        "package_reference",
        lambda version, name: (body, "HEAD"),
    )

    info = DOGFOOD.detect_references(transcript, [], "unknown")["future-reference"]
    assert info["verdict"] == "not_loaded"
    assert info["confidence"] == "medium"
    assert info["probe_source"] == "HEAD"


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
