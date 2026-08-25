"""Tests for deterministic checks and optional host package checks."""

from __future__ import annotations

import importlib.util
from pathlib import Path
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
    assert check.pinned_requirements() == {
        "PyYAML": "6.0.3",
        "markdown-it-py": "4.2.0",
        "pytest": "9.1.1",
    }
    assert not check.MANAGED_ENV.is_relative_to(ROOT)
    assert check.MANAGED_ENV.name == f"python-{sys.version_info.major}.{sys.version_info.minor}"


def test_check_subprocesses_do_not_write_python_bytecode() -> None:
    with patch.object(check.subprocess, "run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = ""
        run.return_value.stderr = ""
        assert check.checked(["python", "example.py"])[0]
    assert run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


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
    assert check.validate_runtime_removal() == []
    assert check.model_id_scan() == []
    assert check.validate_plugin_static() == []


def test_portable_policy_rejects_provider_model_ids(tmp_path: Path) -> None:
    policy = tmp_path / "policy.md"
    policy.write_text("Use gpt-5.6-example for this lane.\n", encoding="utf-8")
    errors = check.model_id_scan([policy])
    assert len(errors) == 1
    assert "gpt-5.6-example" in errors[0]


def test_portability_scan_includes_untracked_package_files() -> None:
    untracked = check.PLUGIN_ROOT / "personal-path.txt"
    untracked.write_text("/" + "Users/person/secret\n", encoding="utf-8")
    try:
        assert any("personal-path.txt" in error for error in check.portability_scan())
    finally:
        untracked.unlink()


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


def test_codex_git_marketplace_rejects_a_ref_for_another_commit() -> None:
    with patch.object(
        hosts,
        "checked",
        side_effect=[
            (True, "candidate123"),
            (True, "other456\trefs/heads/release"),
        ],
    ):
        passed, output = hosts.verify_codex_marketplace_source(
            "https://example.invalid/project.git", "refs/heads/release"
        )
    assert not passed
    assert "not candidate candidate123" in output


def test_codex_git_marketplace_accepts_the_exact_ref() -> None:
    with patch.object(
        hosts,
        "checked",
        side_effect=[
            (True, "candidate123"),
            (True, "candidate123\trefs/heads/release"),
        ],
    ):
        assert hosts.verify_codex_marketplace_source(
            "https://example.invalid/project.git", "refs/heads/release"
        ) == (True, "Git marketplace ref 'refs/heads/release' at candidate123")


def test_codex_local_marketplace_must_be_the_candidate_checkout(tmp_path: Path) -> None:
    assert hosts.verify_codex_marketplace_source(str(ROOT))[0]
    passed, output = hosts.verify_codex_marketplace_source(str(tmp_path))
    assert not passed
    assert "candidate checkout" in output


def test_codex_install_passes_the_verified_ref_to_the_host() -> None:
    calls: list[list[str]] = []

    def checked(command, **kwargs):
        calls.append(list(command))
        return True, "skiphow"

    with (
        patch.object(
            hosts,
            "verify_codex_marketplace_source",
            return_value=(True, "exact candidate"),
        ),
        patch.object(hosts, "checked", side_effect=checked),
    ):
        assert hosts.isolated_install(
            "codex",
            "/bin/codex",
            codex_marketplace_source="https://example.invalid/project.git",
            codex_marketplace_ref="refs/heads/release",
        )[0]
    assert calls[0][-3:] == ["--ref", "refs/heads/release", "--json"]


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

    with patch.object(hosts, "checked", side_effect=checked):
        assert hosts.isolated_install(host, f"/bin/{host}")[0]
    assert str(ROOT) in calls[0][0]
    assert calls[0][1][home_variable]
    assert len({call[1][home_variable] for call in calls}) == 1


def test_available_host_install_failure_blocks_release() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", side_effect=["/bin/codex", None]),
        patch.object(hosts, "isolated_install", return_value=(False, "install failed")),
    ):
        assert hosts.main([]) == 1


def test_required_install_fails_when_host_is_missing() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--require-codex-install"]) == 1
        assert hosts.main(["--require-claude-install"]) == 1
