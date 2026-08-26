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
    assert check.validate_agents() == []
    assert check.validate_continuity_hook() == []
    assert check.validate_plugin_static() == []
    assert check.validate_budget() == []


def test_budget_limits_are_the_accepted_ones() -> None:
    """Pin the four accepted numbers, not whatever the module currently holds.

    The fixtures below scale with the constants, so raising a limit tenfold used
    to leave every budget test green.
    """
    assert check.ROOT_SKILL_LIMITS == {"bytes": 7000, "words": 1000}
    assert check.REFERENCE_LIMITS == {"total_words": 4000, "file_words": 600}


def test_budget_reports_measured_and_allowed_values(tmp_path: Path) -> None:
    root_limit = check.ROOT_SKILL_LIMITS["words"]
    file_limit = check.REFERENCE_LIMITS["file_words"]
    skill = tmp_path / "SKILL.md"
    skill.write_text("word " * (root_limit + 1), encoding="utf-8")
    (tmp_path / "references").mkdir()
    (tmp_path / "references/big.md").write_text("word " * (file_limit + 1), encoding="utf-8")
    with (
        patch.object(check, "CANONICAL_SKILL", skill),
        patch.object(check, "SKILL_ROOT", tmp_path),
    ):
        errors = check.validate_budget()
    assert any(
        f"root skill words exceed the limit: {root_limit + 1} > {root_limit}" in error
        for error in errors
    )
    assert any(
        f"big.md words exceed the limit: {file_limit + 1} > {file_limit}" in error
        for error in errors
    )


def test_agent_adapters_reject_versioned_ids_and_extra_roles(tmp_path: Path) -> None:
    agents = tmp_path / "agents"
    agents.mkdir()
    for role, model in (("scout", "haiku"), ("builder", "sonnet"), ("reviewer", "inherit")):
        extra = "isolation: worktree\n" if role == "builder" else ""
        (agents / f"{role}.md").write_text(
            f"---\nname: {role}\ndescription: x\nmodel: {model}\n{extra}---\nbody\n", encoding="utf-8"
        )
    assert check.validate_agents(agents) == []
    (agents / "scout.md").write_text(
        "---\nname: scout\ndescription: x\nmodel: claude-haiku-4-5-20251001\n---\nbody\n", encoding="utf-8"
    )
    errors = check.validate_agents(agents)
    assert any("family alias" in error for error in errors)
    (agents / "extra.md").write_text("---\nname: extra\ndescription: x\n---\nbody\n", encoding="utf-8")
    assert any("exactly scout, builder, reviewer" in error for error in check.validate_agents(agents))


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
    path.write_text(
        json.dumps({"hooks": {"SessionStart": [{"matcher": "startup|clear", "hooks": [{"type": "command", "command": "sh -c 'cat .skiphow/handoff.md'"}]}]}}),
        encoding="utf-8",
    )
    with patch.object(check, "PLUGIN_ROOT", tmp_path):
        assert any("exactly once each" in error for error in check.validate_continuity_hook(path))


def test_plugin_change_requires_a_version_bump() -> None:
    with patch.object(
        check,
        "checked",
        side_effect=[
            (True, "plugins/skiphow/skills/skiphow/SKILL.md\n"),
            (True, (check.ROOT / "VERSION").read_text(encoding="utf-8")),
        ],
    ):
        assert check.validate_release_version_change("base") == [
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
            (True, f"{ahead}\n"),
        ],
    ):
        assert check.validate_release_version_change("base") == [
            f"plugin version must increase from {ahead} to a later stable version"
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
    for identifier in ("claude-fable-5", "fable-5", "gpt-oss-120b", "grok-4", "qwen3-235b"):
        candidate = tmp_path / "policy.md"
        candidate.write_text(f"Use {identifier}.\n", encoding="utf-8")
        assert check.model_id_scan([candidate]) != [], identifier
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
    """The old check named directories, so any extra file inside one passed."""
    package = tmp_path / "skiphow"
    shutil.copytree(check.PLUGIN_ROOT, package)
    (package / "agents/extra.txt").write_text("x\n", encoding="utf-8")
    with (
        patch.object(check, "PLUGIN_ROOT", package),
        patch.object(check, "SKILL_ROOT", package / "skills/skiphow"),
        patch.object(check, "CANONICAL_SKILL", package / "skills/skiphow/SKILL.md"),
    ):
        errors = check.validate_plugin_static()
    assert any("agents/extra.txt" in error for error in errors)


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
        "if [ -f .skiphow/handoff.md ]; then tail -n 40 .skiphow/handoff.md; fi; exit 0'"
    )
    assert check.HOOK_COMMAND.fullmatch(breakout) is None
    real = json.loads((check.PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    for group in real["hooks"]["SessionStart"]:
        assert check.HOOK_COMMAND.fullmatch(group["hooks"][0]["command"])


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
    assert summary.main([]) == 2


def test_skip_install_cannot_satisfy_a_required_install() -> None:
    """`--skip-install` used to silently answer `--require-*-install` with exit 0."""
    for required in ("--require-codex-install", "--require-claude-install"):
        with pytest.raises(SystemExit) as raised:
            hosts.main(["--skip-install", required])
        assert raised.value.code == 2


def test_only_a_source_policy_denial_is_downgraded() -> None:
    """Any output naming requirements.toml used to be read as a policy block."""
    assert hosts._codex_policy_block("blocked by allowed source policy")
    assert hosts._codex_policy_block("source is not allowed")
    assert not hosts._codex_policy_block("failed to parse /etc/codex/requirements.toml")


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
