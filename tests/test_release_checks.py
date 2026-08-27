"""Tests for deterministic checks and optional host package checks."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


check = load("skiphow_check", "scripts/check.py")
hosts = load("skiphow_check_hosts", "scripts/check_hosts.py")


def test_local_dependencies_are_pinned_and_kept_outside_the_repo() -> None:
    pins = check.pinned_requirements()
    assert {"pytest", "PyYAML", "markdown-it-py"} <= set(pins)
    assert all(re.fullmatch(r"\d+(?:\.\d+)*", value) for value in pins.values())
    assert not check.MANAGED_ENV.is_relative_to(ROOT)
    assert check.MANAGED_ENV.name == f"python-{sys.version_info.major}.{sys.version_info.minor}"



def test_offline_mode_never_bootstraps_missing_dependencies(capsys) -> None:
    with (
        patch.object(check, "requirements_satisfied", return_value=False),
        patch.object(check, "bootstrap_dependencies") as bootstrap,
    ):
        assert check.main(["--offline"]) == 2
    bootstrap.assert_not_called()
    assert "UNVERIFIED" in capsys.readouterr().err


def test_local_package_and_document_checks_pass() -> None:
    assert check.validate_json() == []
    assert check.validate_yaml() == []
    assert check.validate_markdown_links() == []
    assert check.portability_scan() == []
    assert check.validate_version() == []
    assert check.model_id_scan() == []
    assert check.validate_continuity_hook() == []
    assert check.validate_plugin_static() == []


def write_skill(root: Path, name: str, *, description: str = "Handle a focused task.") -> Path:
    skill = root / name
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nDo the task.\n",
        encoding="utf-8",
    )
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        f"  display_name: {name}\n"
        "  short_description: Handle one focused project task\n"
        f"  default_prompt: Use ${name} for this request.\n"
        "policy:\n"
        "  allow_implicit_invocation: true\n",
        encoding="utf-8",
    )
    return skill


def test_each_top_level_skill_has_spec_metadata_and_may_ship_resources(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "diagnosing-bugs")
    for directory in ("references", "scripts", "assets"):
        (skill / directory).mkdir()
        (skill / directory / "resource.txt").write_text("resource\n", encoding="utf-8")
    (skill / "examples").mkdir()
    (skill / "examples/scenario.txt").write_text("example\n", encoding="utf-8")
    (skill / "LICENSE.txt").write_text("local terms\n", encoding="utf-8")
    assert check.validate_skill_directory(skill) == []

    (skill / "SKILL.md").write_text(
        "---\nname: wrong-name\ndescription: x\n---\n\nBody.\n", encoding="utf-8"
    )
    assert any("name must match its directory" in error for error in check.validate_skill_directory(skill))


def test_openai_metadata_is_optional_but_cannot_disable_implicit_use(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "diagnosing-bugs")
    metadata_path = skill / "agents/openai.yaml"
    metadata_path.unlink()
    (skill / "agents/other-host.yaml").write_text("enabled: true\n", encoding="utf-8")
    assert check.validate_skill_directory(skill) == []

    metadata_path.write_text(
        "policy:\n  allow_implicit_invocation: true\n",
        encoding="utf-8",
    )
    assert check.validate_skill_directory(skill) == []

    metadata_path.write_text(
        "interface:\n"
        "  display_name: Investigate product failures\n"
        "  short_description: Handle one focused project task\n"
        "  default_prompt: Investigate this failure.\n"
        "policy:\n"
        "  allow_implicit_invocation: false\n",
        encoding="utf-8",
    )
    assert any(
        "must not disable implicit invocation" in error
        for error in check.validate_skill_directory(skill)
    )


@pytest.mark.parametrize(
    ("extra_frontmatter", "expected"),
    [
        ("license:\n  - MIT\n", "license must be a nonempty string"),
        ("license: null\n", "license must be a nonempty string"),
        (f"compatibility: {'x' * 501}\n", "compatibility must be"),
        ("metadata:\n  version: 2\n", "metadata must map strings to strings"),
        ("allowed-tools:\n  - Bash\n", "allowed-tools must be a nonempty string"),
        ("made-up-field: value\n", "unsupported Agent Skills fields"),
    ],
)
def test_skill_frontmatter_rejects_invalid_optional_fields(
    tmp_path: Path, extra_frontmatter: str, expected: str
) -> None:
    skill = write_skill(tmp_path, "research")
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: research\n"
        "description: Research one uncertain question.\n"
        f"{extra_frontmatter}"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    assert any(expected in error for error in check.validate_skill_directory(skill))


def test_skill_frontmatter_accepts_valid_optional_fields(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "research")
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: research\n"
        "description: Research one uncertain question.\n"
        "license: MIT\n"
        "compatibility: Requires access to current primary sources.\n"
        "metadata:\n"
        "  author: example\n"
        "allowed-tools: Read Bash\n"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    assert check.validate_skill_directory(skill) == []


def test_skill_description_uses_the_agent_skills_metadata_limit(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "research", description="x" * 1025)
    errors = check.validate_skill_directory(skill)
    assert any("at most 1024 characters" in error for error in errors)


def test_plugin_markdown_links_cannot_escape_the_package(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        "[outside](../../../outside.md)\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("escapes package" in error for error in errors)


def test_plugin_markdown_links_validate_image_destinations(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "skiphow")
    (skill / "SKILL.md").write_text(
        "---\nname: skiphow\ndescription: Owner entry.\n---\n\n"
        "![missing preview](assets/missing.png)\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", plugin):
        errors = check.validate_plugin_links()
    assert any("missing.png" in error for error in errors)


def test_markdown_references_must_be_reachable_from_their_skill(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, "research")
    references = skill / "references"
    (references / "nested").mkdir(parents=True)
    (references / "first.md").write_text("[Details](nested/details.md)\n", encoding="utf-8")
    (references / "nested/details.md").write_text("Details.\n", encoding="utf-8")
    (skill / "SKILL.md").write_text(
        "---\nname: research\ndescription: Research one uncertain question.\n---\n\n"
        "Read [the method](references/first.md) when needed.\n",
        encoding="utf-8",
    )
    assert check.validate_skill_directory(skill) == []

    (references / "orphan.md").write_text("Unreachable.\n", encoding="utf-8")
    errors = check.validate_skill_directory(skill)
    assert any("unreachable Markdown reference: references/orphan.md" in error for error in errors)


def test_adapted_source_manifest_validates_provenance_not_upstream_hashes(tmp_path: Path) -> None:
    plugin = tmp_path / "skiphow"
    skill = write_skill(plugin / "skills", "diagnosing-bugs")
    commit = "a" * 40
    repository = "https://example.test/upstream/skills"
    provenance = "Adapted for this package"
    (plugin / "THIRD_PARTY_NOTICES.md").write_text(
        f"Source: {repository}\nCommit: {commit}\nLicense: MIT\n{provenance}\n\n"
        f"{check.MIT_PERMISSION_PARAGRAPH}\n\n{check.MIT_WARRANTY_PARAGRAPH}\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "sources": [
            {
                "repository": repository,
                "commit": commit,
                "license": "MIT",
                "provenance": provenance,
                "adaptations": [
                    {
                        "skill": "diagnosing-bugs",
                        "source_paths": ["skills/engineering/diagnosing-bugs/SKILL.md"],
                        "files": ["SKILL.md"],
                    }
                ],
            }
        ],
    }
    (plugin / "SOURCES.json").write_text(json.dumps(manifest), encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", plugin):
        assert check.validate_third_party_sources({"diagnosing-bugs"}) == []
        (plugin / "THIRD_PARTY_NOTICES.md").write_text(
            f"{repository}\n{commit}\nMIT\n{provenance}\n{check.MIT_PERMISSION_PARAGRAPH}\n",
            encoding="utf-8",
        )
        errors = check.validate_third_party_sources({"diagnosing-bugs"})
        assert any("canonical MIT warranty paragraph" in error for error in errors)

        (plugin / "THIRD_PARTY_NOTICES.md").write_text(
            f"{repository}\n{commit}\nMIT\n{check.MIT_PERMISSION_PARAGRAPH}\n"
            f"{check.MIT_WARRANTY_PARAGRAPH}\n",
            encoding="utf-8",
        )
        errors = check.validate_third_party_sources({"diagnosing-bugs"})
        assert any("source provenance" in error for error in errors)

        manifest["sources"][0]["commit"] = "moving-main"
        (plugin / "SOURCES.json").write_text(json.dumps(manifest), encoding="utf-8")
        errors = check.validate_third_party_sources({"diagnosing-bugs"})
    assert any("40-character hexadecimal" in error for error in errors)


def test_current_package_cannot_drop_third_party_provenance(tmp_path: Path) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    (package / "SOURCES.json").unlink()
    (package / "THIRD_PARTY_NOTICES.md").unlink()
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("SOURCES.json" in error and "THIRD_PARTY_NOTICES.md" in error for error in errors)


def test_continuity_hook_rejects_other_events_and_network(tmp_path: Path) -> None:
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    path = hooks / "hooks.json"
    path.write_text(
        json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "sh -c 'true'"}]}]}}),
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", tmp_path):
        assert any("only SessionStart" in error for error in check.validate_continuity_hook(path))
    path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {"matcher": "startup|clear", "hooks": [{"type": "command", "command": "sh -c 'cat .skiphow/handoff.md'"}]},
                        {"matcher": "compact|resume", "hooks": [{"type": "command", "command": "sh -c 'curl http://x; cat .skiphow/handoff.md'"}]},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", tmp_path):
        errors = check.validate_continuity_hook(path)
    assert any("must not write, fetch, or run programs" in error for error in errors)
    mixed = json.loads(
        (check.PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8")
    )
    mixed["hooks"]["SessionStart"][0]["matcher"] = "startup|compact"
    mixed["hooks"]["SessionStart"][1]["matcher"] = "clear|resume"
    path.write_text(json.dumps(mixed), encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", tmp_path):
        errors = check.validate_continuity_hook(path)
    assert any(
        "exactly the startup|clear and compact|resume matcher groups" in error
        for error in errors
    )
    path.write_text(
        json.dumps({"hooks": {"SessionStart": [{"matcher": "startup|clear", "hooks": [{"type": "command", "command": "sh -c 'cat .skiphow/handoff.md'"}]}]}}),
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", tmp_path):
        assert any(
            "exactly the startup|clear and compact|resume matcher groups" in error
            for error in check.validate_continuity_hook(path)
        )


def test_plugin_change_requires_a_version_bump() -> None:
    with patch.object(
        check,
        "checked",
        side_effect=[
            (True, "plugins/skiphow/skills/skiphow/SKILL.md\n"),
            (True, ""),
            (True, ""),
            (True, (check.ROOT / "VERSION").read_text(encoding="utf-8")),
        ],
    ):
        assert check.validate_release_version_change("base") == [
            "plugins/skiphow changed without a VERSION bump"
        ]


@pytest.mark.parametrize(
    ("working_tree", "untracked"),
    [
        ("plugins/skiphow/skills/tracked/SKILL.md\n", ""),
        ("", "plugins/skiphow/skills/untracked/SKILL.md\n"),
    ],
)
def test_base_diff_cannot_hide_dirty_plugin_changes(
    working_tree: str, untracked: str
) -> None:
    with patch.object(
        check,
        "checked",
        side_effect=[
            (True, "docs/release-notes.md\n"),
            (True, working_tree),
            (True, untracked),
            (True, (check.ROOT / "VERSION").read_text(encoding="utf-8")),
        ],
    ) as checked:
        assert check.validate_release_version_change("base") == [
            "plugins/skiphow changed without a VERSION bump"
        ]
    assert [call.args[0] for call in checked.call_args_list[:3]] == [
        ["git", "diff", "--name-only", "base...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]


def test_working_tree_plugin_change_requires_a_version_bump_without_base() -> None:
    with patch.object(
        check,
        "checked",
        side_effect=[
            (True, "plugins/skiphow/skills/new-skill/SKILL.md\n"),
            (True, "plugins/skiphow/skills/untracked/SKILL.md\n"),
            (True, (check.ROOT / "VERSION").read_text(encoding="utf-8")),
        ],
    ):
        assert check.validate_release_version_change(None) == [
            "plugins/skiphow changed without a VERSION bump"
        ]


def test_non_plugin_change_does_not_require_a_version_bump() -> None:
    with patch.object(check, "checked", return_value=(True, "docs/README.md\n")):
        assert check.validate_release_version_change("base") == []


def test_plugin_version_cannot_move_backward() -> None:
    current = (check.ROOT / "VERSION").read_text(encoding="utf-8").strip()
    major, minor, patch_number = (int(part) for part in current.split("."))
    ahead = f"{major + 1}.{minor}.{patch_number}"
    with patch.object(
        check,
        "checked",
        side_effect=[
            (True, "plugins/skiphow/skills/skiphow/SKILL.md\n"),
            (True, ""),
            (True, ""),
            (True, f"{ahead}\n"),
        ],
    ):
        assert check.validate_release_version_change("base") == [
            f"plugin version must increase from {ahead} to a later stable version"
        ]


def test_diff_validation_checks_unstaged_staged_and_candidate_changes() -> None:
    commands: list[list[str]] = []

    def checked(command, **kwargs):
        commands.append(list(command))
        return True, ""

    with patch.object(check, "checked", side_effect=checked):
        assert check.validate_diff("origin/main") == []
    assert commands == [
        ["git", "diff", "--check"],
        ["git", "diff", "--cached", "--check"],
        ["git", "diff", "--check", "origin/main...HEAD"],
    ]


def test_portable_policy_rejects_provider_model_ids(tmp_path: Path) -> None:
    policy = tmp_path / "policy.md"
    policy.write_text("Use gpt-5.6-example for this lane.\n", encoding="utf-8")
    errors = check.model_id_scan([policy])
    assert len(errors) == 1
    assert "gpt-5.6-example" in errors[0]


def test_file_enumeration_asks_git_for_untracked_files() -> None:
    """The scan can only see a new file if the enumerator asks Git for one."""
    with patch.object(check.subprocess, "run") as run:
        run.return_value = check.subprocess.CompletedProcess(["git"], 0, b"", b"")
        list(check.repository_files())
    command = run.call_args.args[0]
    assert command[:2] == ["git", "ls-files"]
    assert {"--others", "--exclude-standard", "--cached"} <= set(command)
    assert run.call_args.kwargs["timeout"]


def test_portability_scan_flags_a_personal_path_in_a_package_file(tmp_path: Path) -> None:
    """The scan reports a file the enumerator yields -- proven off the real package."""
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    untracked = plugin / "personal-path.txt"
    untracked.write_text("/" + "Users/person/secret\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[untracked]),
    ):
        errors = check.portability_scan()
    assert any("personal-path.txt" in error for error in errors)


def test_portability_scan_catches_a_home_path_with_no_trailing_separator(tmp_path: Path) -> None:
    """`/Users/person` at the end of a sentence used to pass the scan."""
    plugin = tmp_path / "plugins/skiphow"
    plugin.mkdir(parents=True)
    candidate = plugin / "note.md"
    candidate.write_text("Run it from /" + "Users/person.\n", encoding="utf-8")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check, "PLUGIN_ROOT", plugin),
        patch.object(check, "repository_files", return_value=[candidate]),
    ):
        assert check.portability_scan() != []


def test_model_scan_covers_every_shipped_file_and_current_families(tmp_path: Path) -> None:
    """The default scan read the prose only, and named no current Claude family.

    A `claude-fable-5` in the Codex adapter or either manifest passed both gates.
    """
    # `claude-future-5` and `gemini-pro-3` name no family the pattern lists; the
    # invariant is no versioned ID, so enumerating the families of the day is not enough.
    for identifier in (
        "claude-fable-5", "fable-5", "gpt-oss-120b", "grok-4", "qwen3-235b",
        "claude-future-5", "gemini-pro-3", "mistral-large-2",
    ):
        candidate = tmp_path / "policy.md"
        candidate.write_text(f"Use {identifier}.\n", encoding="utf-8")
        assert check.model_id_scan([candidate]) != [], identifier
    for innocent in ("claude-code", "Claude Code 2.1.246", "a fabled release", "the opus of work"):
        candidate = tmp_path / "prose.md"
        candidate.write_text(f"{innocent}\n", encoding="utf-8")
        assert check.model_id_scan([candidate]) == [], innocent
    # Default mode, over a manifest -- the file kind the old candidate list skipped.
    package = tmp_path / "skiphow"
    (package / ".codex-plugin").mkdir(parents=True)
    (package / ".codex-plugin/plugin.json").write_text(
        '{"model": "claude-fable-5"}\n', encoding="utf-8"
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.model_id_scan()
    assert any("claude-fable-5" in error for error in errors)


def test_package_shape_rejects_an_extra_shipped_file(tmp_path: Path) -> None:
    """A universal agents directory is not part of the composable skill package."""
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    (package / "agents").mkdir(exist_ok=True)
    (package / "agents/extra.txt").write_text("x\n", encoding="utf-8")
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("agents/extra.txt" in error for error in errors)


def test_package_shape_rejects_a_nested_skill(tmp_path: Path) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    nested = package / "skills/skiphow/references/nested/SKILL.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text(
        "---\nname: nested\ndescription: Wrongly nested skill.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("nested SKILL.md" in error for error in errors)


def test_package_shape_rejects_a_second_owner_visible_skill(tmp_path: Path) -> None:
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    write_skill(package / "skills", "extra-entry")
    with patch.object(check, "PLUGIN_ROOT", package):
        errors = check.validate_plugin_static()
    assert any("exactly one owner entry" in error for error in errors)


def test_changelog_must_lead_with_the_released_version() -> None:
    """A newer section above the released one used to satisfy the heading search."""
    changelog = (check.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release = (check.ROOT / "VERSION").read_text(encoding="utf-8").strip()
    dated = re.findall(r"^## (\S+) \(\d{4}-\d{2}-\d{2}\)$", changelog, re.MULTILINE)
    assert dated[0] == release
    assert check.validate_version() == []


def test_hook_shape_rejects_a_quote_breakout() -> None:
    """A single quote in the message closes the outer `sh -c '...'`.

    The shape excluded `"`, `$`, backtick and backslash but not `'`, so a message
    could end the quoting and run a program the denylist never named.
    """
    breakout = (
        "sh -c 'printf \"%s\\n\" \"' ; touch f; echo '\"; "
        "if [ -f .skiphow/handoff.md ]; then cat .skiphow/handoff.md; fi; exit 0'"
    )
    assert check.HOOK_COMMAND.fullmatch(breakout) is None
    real = json.loads((check.PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    for group in real["hooks"]["SessionStart"]:
        command = group["hooks"][0]["command"]
        if {"compact", "resume"} & set(group["matcher"].split("|")):
            assert check.HOOK_COMMAND.fullmatch(command)
        else:
            assert check.HOOK_NOTICE_COMMAND.fullmatch(command)


def test_personal_path_scan_leaves_web_routes_alone() -> None:
    """Dropping the required trailing separator reached into URLs.

    A `/users/` route in a documented URL is not a home directory, and the gate
    scans public documentation, so a false positive blocks a release for nothing.
    """
    for innocent in (
        "https://example.com/Users/profile",
        "https://example.test/users/alice",
        "GET /users/me",
    ):
        assert check.PERSONAL_PATH.search(innocent) is None, innocent
    for personal in ("see /" + "Users/person", "/" + "home/person", "C:\\USERS\\person\\x"):
        assert check.PERSONAL_PATH.search(personal), personal


def test_run_summary_refuses_evidence_it_cannot_read(tmp_path: Path) -> None:
    """A corrupt or unfinished transcript produced a plausible zero-cost summary."""
    summary = load("skiphow_run_summary", "scripts/run_summary.py")
    broken = tmp_path / "broken.jsonl"
    broken.write_text("not json\n", encoding="utf-8")
    with pytest.raises(summary.TranscriptError):
        summary.summarize(broken)
    unfinished = tmp_path / "unfinished.jsonl"
    unfinished.write_text('{"type": "assistant", "message": {"model": "m", "content": []}}\n', encoding="utf-8")
    with pytest.raises(summary.TranscriptError):
        summary.summarize(unfinished)
    # `isinstance(False, int)` is True, so a boolean metric used to render as zero.
    boolean = tmp_path / "boolean.jsonl"
    boolean.write_text('{"type": "result", "num_turns": false}\n', encoding="utf-8")
    with pytest.raises(summary.TranscriptError):
        summary.summarize(boolean)
    # A streaming-input run emits one cumulative result per turn; the last one wins.
    multi = tmp_path / "multi.jsonl"
    multi.write_text(
        '{"type": "result", "num_turns": 2, "total_cost_usd": 0.1, "duration_ms": 1000}\n'
        '{"type": "result", "num_turns": 5, "total_cost_usd": 0.3, "duration_ms": 4000}\n',
        encoding="utf-8",
    )
    assert summary.summarize(multi)["turns"] == 5
    # A metric the host never reported stays absent rather than becoming a zero.
    partial = tmp_path / "partial.jsonl"
    partial.write_text('{"type": "result", "num_turns": 3}\n', encoding="utf-8")
    assert summary.summarize(partial)["cost_usd"] is None
    # `float("nan")` is an instance of float, and a negative count is not a count.
    for impossible in ('{"type": "result", "num_turns": NaN}', '{"type": "result", "num_turns": -1}'):
        broken_metric = tmp_path / "metric.jsonl"
        broken_metric.write_text(impossible + "\n", encoding="utf-8")
        with pytest.raises(summary.TranscriptError):
            summary.summarize(broken_metric)
    assert summary.main([]) == 2


def test_skip_install_cannot_satisfy_a_required_install() -> None:
    """`--skip-install` used to silently answer `--require-*-install` with exit 0."""
    for required in ("--require-codex-install", "--require-claude-install"):
        with pytest.raises(SystemExit) as raised:
            hosts.main(["--skip-install", required])
        assert raised.value.code == 2


def test_only_a_source_policy_denial_is_downgraded() -> None:
    """Any output naming requirements.toml used to be read as a policy block.

    The first string is the message a machine with a managed Codex policy actually
    prints; narrowing this match without it turned that machine's `UNVERIFIED` into
    a release-blocking `FAIL`.
    """
    observed = (
        "Error: marketplace source `/tmp/skiphow-codex-install-x/marketplace` is not "
        "allowed by requirements from /etc/codex/requirements.toml"
    )
    assert hosts._codex_policy_block(observed)
    assert hosts._codex_policy_block("blocked by allowed source policy")
    assert not hosts._codex_policy_block("failed to parse /etc/codex/requirements.toml")
    assert not hosts._codex_policy_block("network unreachable")
    # An unrelated refusal beside a parse error is not a source-policy denial.
    assert not hosts._codex_policy_block(
        "network setting is not allowed; failed to parse /etc/codex/requirements.toml"
    )


def test_file_enumeration_falls_back_without_git(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    expected = tmp_path / "docs/archive.md"
    expected.write_text("archive\n", encoding="utf-8")
    completed = check.subprocess.CompletedProcess(["git"], 128, b"", b"not a repository")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check.subprocess, "run", return_value=completed),
    ):
        assert list(check.repository_files({".md"})) == [expected]
        assert check.validate_diff(None) == []


def test_missing_hosts_are_unverified_unless_required(capsys) -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install"]) == 0
        assert hosts.main(["--require-codex-validator", "--skip-install"]) == 1
        assert hosts.main(["--require-claude", "--skip-install"]) == 1
    assert "UNVERIFIED" in capsys.readouterr().out


def test_configured_codex_validator_failure_blocks_release(tmp_path: Path) -> None:
    validator = tmp_path / "validate.py"
    validator.write_text("raise SystemExit(1)\n", encoding="utf-8")
    with (
        patch.object(hosts, "codex_validator", return_value=validator),
        patch.object(hosts, "validator_python", return_value=(sys.executable, "current Python")),
        patch.object(hosts.shutil, "which", return_value=None),
        patch.object(hosts, "checked", return_value=(False, "invalid plugin")),
    ):
        assert hosts.main(["--skip-install"]) == 1


def test_codex_validator_can_use_the_managed_python(tmp_path: Path) -> None:
    managed = tmp_path / "python"
    managed.write_text("", encoding="utf-8")
    with patch.object(
        hosts,
        "checked",
        side_effect=[(False, "missing yaml"), (True, str(managed))],
    ):
        assert hosts.validator_python() == (str(managed), "repository-managed Python")


def test_plain_marketplace_matches_exact_candidate_and_rejects_repositories(tmp_path: Path) -> None:
    source = hosts._plain_marketplace(tmp_path / "plain", "codex")
    assert hosts.verify_plain_marketplace_source(str(source), "codex")[0]
    (source / ".git").mkdir()
    passed, output = hosts.verify_plain_marketplace_source(str(source), "codex")
    assert not passed
    assert "repository" in output


def test_codex_install_uses_plain_source_without_a_git_ref(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    source = hosts._plain_marketplace(tmp_path / "plain", "codex")

    def checked(command, **kwargs):
        calls.append(list(command))
        return True, "skiphow"

    with (
        patch.object(hosts, "checked", side_effect=checked),
        patch.object(hosts, "_installed_path", return_value=hosts.PLUGIN_ROOT),
    ):
        assert hosts.isolated_install(
            "codex",
            "/bin/codex",
            codex_marketplace_source=str(source),
        )[0]
    assert calls[0][-2:] == [str(source), "--json"]
    assert "--ref" not in calls[0]


def test_claude_validation_targets_the_plugin_directory() -> None:
    commands: list[list[str]] = []

    def checked(command, **kwargs):
        commands.append(list(command))
        return True, "ok"

    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", side_effect=[None, "/bin/claude"]),
        patch.object(hosts, "checked", side_effect=checked),
    ):
        assert hosts.main(["--skip-install"]) == 0
    assert ["/bin/claude", "plugin", "validate", "--strict", str(hosts.PLUGIN_ROOT)] in commands


@pytest.mark.parametrize("host,home_variable", [("codex", "CODEX_HOME"), ("claude", "CLAUDE_CONFIG_DIR")])
def test_isolated_install_uses_local_marketplace_and_empty_host_home(
    host: str, home_variable: str
) -> None:
    calls: list[tuple[list[str], dict[str, str]]] = []

    def checked(command, **kwargs):
        calls.append((list(command), kwargs["env"]))
        return True, "skiphow"

    with (
        patch.object(hosts, "checked", side_effect=checked),
        patch.object(hosts, "_installed_path", return_value=hosts.PLUGIN_ROOT),
    ):
        assert hosts.isolated_install(host, f"/bin/{host}")[0]
    assert "marketplace" in " ".join(calls[0][0])
    assert calls[0][1][home_variable]
    assert len({call[1][home_variable] for call in calls}) == 1


def test_available_host_install_failure_blocks_release() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", side_effect=["/bin/codex", None]),
        patch.object(hosts, "isolated_install", return_value=(False, "install failed")),
    ):
        assert hosts.main([]) == 1


def test_managed_codex_policy_is_unverified_unless_install_is_required(capsys) -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", side_effect=["/bin/codex", None, "/bin/codex", None]),
        patch.object(hosts, "isolated_install", return_value=(False, "blocked by /etc/codex/requirements.toml allowed source policy")),
    ):
        assert hosts.main([]) == 0
        assert hosts.main(["--require-codex-install"]) == 1
    assert "Codex isolated install: UNVERIFIED" in capsys.readouterr().out


def test_required_install_fails_when_host_is_missing() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--require-codex-install"]) == 1
        assert hosts.main(["--require-claude-install"]) == 1
