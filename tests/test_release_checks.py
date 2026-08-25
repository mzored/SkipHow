"""Tests for local and host release check separation."""

import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch


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


def test_local_check_dependencies_are_pinned_and_repo_managed() -> None:
    assert check.pinned_requirements() == {
        "PyYAML": "6.0.3",
        "markdown-it-py": "4.2.0",
        "pytest": "9.1.1",
    }
    assert not check.MANAGED_ENV.is_relative_to(ROOT)
    assert check.MANAGED_ENV.name == f"python-{sys.version_info.major}.{sys.version_info.minor}"
    assert ".venv/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_check_subprocesses_do_not_write_python_caches() -> None:
    with patch.object(check.subprocess, "run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = ""
        run.return_value.stderr = ""
        assert check.checked(["python", "example.py"])[0]
    assert run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_offline_check_does_not_attempt_dependency_bootstrap(capsys) -> None:
    with (
        patch.object(check, "requirements_satisfied", return_value=False),
        patch.object(check, "bootstrap_dependencies") as bootstrap,
    ):
        assert check.main(["--offline"]) == 2
    bootstrap.assert_not_called()
    assert "UNVERIFIED" in capsys.readouterr().err


def test_local_metadata_links_and_version_validate() -> None:
    assert check.validate_json() == []
    assert check.validate_yaml() == []
    assert check.validate_markdown_links() == []
    assert check.validate_version() == []
    assert check.validate_plugin_static() == []


def test_source_scan_includes_untracked_distribution_files(tmp_path: Path) -> None:
    untracked = ROOT / "plugins/skiphow/untracked-personal-path.txt"
    untracked.write_text("/" + "Users/person/secret\n", encoding="utf-8")
    try:
        assert any("untracked-personal-path" in error for error in check.source_scan())
    finally:
        untracked.unlink()


def test_archive_file_enumeration_falls_back_without_git(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    expected = tmp_path / "docs" / "archive.md"
    expected.write_text("archive\n", encoding="utf-8")
    completed = check.subprocess.CompletedProcess(["git"], 128, b"", b"not a repository")
    with (
        patch.object(check, "ROOT", tmp_path),
        patch.object(check.subprocess, "run", return_value=completed),
    ):
        assert list(check.repository_files({".md"})) == [expected]
        assert check.validate_diff(None) == []


def test_host_validator_absence_is_unverified_unless_required(capsys) -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install", "--skip-runner-package"]) == 0
        assert hosts.main(
            ["--require-codex-validator", "--skip-install", "--skip-runner-package"]
        ) == 1
    assert "UNVERIFIED" in capsys.readouterr().out


def test_configured_codex_validator_failure_is_blocking(tmp_path: Path) -> None:
    validator = tmp_path / "validate.py"
    validator.write_text("raise SystemExit(1)\n", encoding="utf-8")
    with (
        patch.object(hosts, "codex_validator", return_value=validator),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install", "--skip-runner-package"]) == 1


def test_codex_validator_prepares_managed_python_when_yaml_is_missing(
    tmp_path: Path,
) -> None:
    managed = tmp_path / "python"
    managed.write_text("", encoding="utf-8")
    with (
        patch.object(
            hosts,
            "checked",
            side_effect=[
                (False, "missing yaml"),
                (True, str(managed)),
            ],
        ),
    ):
        assert hosts.validator_python() == (str(managed), "repository-managed Python")


def test_codex_marketplace_defaults_to_repository_origin() -> None:
    with patch.object(
        hosts,
        "checked",
        return_value=(True, "https://github.com/example/project.git"),
    ):
        assert hosts.default_codex_marketplace_source() == "https://github.com/example/project.git"


def test_codex_git_marketplace_must_match_the_candidate_commit() -> None:
    with patch.object(
        hosts,
        "checked",
        side_effect=[
            (True, "candidate123"),
            (True, "other456\tHEAD"),
        ],
    ):
        passed, output = hosts.verify_codex_marketplace_source(
            "https://github.com/example/project.git", "refs/heads/release"
        )
    assert not passed
    assert "not candidate candidate123" in output


def test_codex_git_marketplace_accepts_the_exact_candidate() -> None:
    with patch.object(
        hosts,
        "checked",
        side_effect=[
            (True, "candidate123"),
            (True, "candidate123\tHEAD"),
        ],
    ):
        assert hosts.verify_codex_marketplace_source(
            "https://github.com/example/project.git", "refs/heads/release"
        ) == (True, "Git marketplace ref 'refs/heads/release' at candidate123")


def test_codex_git_marketplace_accepts_an_advertised_exact_commit() -> None:
    commit = "a" * 40
    with patch.object(
        hosts,
        "checked",
        side_effect=[
            (True, commit),
            (True, f"{commit}\trefs/heads/release\n"),
        ],
    ) as checked:
        assert hosts.verify_codex_marketplace_source(
            "https://github.com/example/project.git", commit
        ) == (True, f"Git marketplace ref '{commit}' at {commit}")
    assert checked.call_args_list[-1].args[0] == [
        "git",
        "ls-remote",
        "https://github.com/example/project.git",
    ]


def test_codex_install_passes_exact_ref_to_marketplace_command(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def run(command, **kwargs):
        calls.append(list(command))
        return hosts.subprocess.CompletedProcess(command, 0, "skiphow", "")

    with (
        patch.object(hosts, "verify_codex_marketplace_source", return_value=(True, "ok")),
        patch.object(hosts.subprocess, "run", side_effect=run),
    ):
        assert hosts.isolated_install(
            "codex",
            "/bin/codex",
            codex_marketplace_source="https://example.invalid/repo.git",
            codex_marketplace_ref="refs/heads/release",
        )[0]
    assert calls[0][-3:] == ["--ref", "refs/heads/release", "--json"]


def test_runner_package_check_builds_installs_and_smokes(tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def checked(command, *, timeout=180):
        commands.append(list(command))
        if "wheel" in command:
            wheel_directory = Path(command[command.index("--wheel-dir") + 1])
            wheel_directory.mkdir(parents=True)
            (wheel_directory / "skiphow_runner-0.8.0-py3-none-any.whl").write_bytes(b"wheel")
        if command[-2:] == ["-c", "import skiphow; print(skiphow.__version__)"]:
            return True, (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        return True, "ok"

    with patch.object(hosts, "checked", side_effect=checked):
        passed, reference = hosts.runner_package_check()
    assert passed
    assert "skiphow_runner-0.8.0-py3-none-any.whl" in reference
    assert any("wheel" in command for command in commands)
    assert any("install" in command for command in commands)
    assert any(command[-1:] == ["--help"] for command in commands)


def test_runner_package_failure_is_blocking_only_when_required() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
        patch.object(hosts, "runner_package_check", return_value=(False, "bad wheel")),
    ):
        assert hosts.main(["--skip-install"]) == 0
        assert hosts.main(["--skip-install", "--require-runner-package"]) == 1


def test_isolated_install_failure_is_unverified_unless_required() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value="/bin/tool"),
        patch.object(hosts, "checked", return_value=(True, "ok")),
        patch.object(hosts, "isolated_install", return_value=(False, "blocked by host policy")),
        patch.object(hosts, "default_codex_marketplace_source", return_value="https://example.invalid/repo.git"),
        patch.object(hosts, "runner_package_check", return_value=(True, "ok")),
    ):
        assert hosts.main([]) == 0
        assert hosts.main(["--require-codex-install"]) == 1


def test_host_check_writes_machine_readable_unverified_receipt(tmp_path: Path) -> None:
    output = tmp_path / "host-proof.json"
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
        patch.object(hosts, "runner_package_check", return_value=(True, "ok")),
        patch.object(
            hosts,
            "candidate_identity",
            return_value={"commit": "abc123", "tree": "tree123", "dirty": False},
        ),
    ):
        assert hosts.main(["--skip-install", "--output", str(output)]) == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == 1
    assert receipt["status"] == "UNVERIFIED"
    assert receipt["candidate"] == {
        "commit": "abc123",
        "tree": "tree123",
        "dirty": False,
    }
    assert receipt["host_cli_versions"] == {"claude": None, "codex": None}
    assert receipt["checks"]["codex_validator"]["status"] == "UNVERIFIED"
    assert receipt["checks"]["claude_package"]["status"] == "UNVERIFIED"
    assert receipt["checks"]["runner_package"]["status"] == "VERIFIED"
    assert receipt["reference"]


def test_host_check_receipt_is_verified_only_for_clean_fully_proven_candidate(
    tmp_path: Path,
) -> None:
    output = tmp_path / "host-proof.json"
    validator = tmp_path / "validate.py"
    validator.write_text("", encoding="utf-8")
    with (
        patch.object(hosts, "codex_validator", return_value=validator),
        patch.object(hosts.shutil, "which", return_value="/bin/host"),
        patch.object(hosts, "checked", return_value=(True, "host 1.2.3")),
        patch.object(hosts, "isolated_install", return_value=(True, "skiphow")),
        patch.object(hosts, "runner_package_check", return_value=(True, "ok")),
        patch.object(
            hosts,
            "candidate_identity",
            return_value={"commit": "abc123", "tree": "tree123", "dirty": False},
        ),
    ):
        assert hosts.main(
            [
                "--codex-marketplace-source",
                "https://secret@example.invalid/repo.git",
                "--output",
                str(output),
            ]
        ) == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "VERIFIED"
    assert receipt["host_cli_versions"] == {
        "claude": "host 1.2.3",
        "codex": "host 1.2.3",
    }
    assert all(check["status"] == "VERIFIED" for check in receipt["checks"].values())
    assert "secret" not in json.dumps(receipt)


def test_host_check_rejects_receipt_inside_candidate_worktree(tmp_path: Path) -> None:
    output = ROOT / "host-proof.json"
    with patch.object(hosts, "runner_package_check") as package:
        assert hosts.main(["--skip-install", "--output", str(output)]) == 2
    package.assert_not_called()
    assert not output.exists()
