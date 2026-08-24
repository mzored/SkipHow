"""Tests for local and host release check separation."""

import importlib.util
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


def test_host_validator_absence_is_unverified_unless_required(capsys) -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install"]) == 0
        assert hosts.main(["--require-codex-validator", "--skip-install"]) == 1
    assert "UNVERIFIED" in capsys.readouterr().out


def test_configured_codex_validator_failure_is_blocking(tmp_path: Path) -> None:
    validator = tmp_path / "validate.py"
    validator.write_text("raise SystemExit(1)\n", encoding="utf-8")
    with (
        patch.object(hosts, "codex_validator", return_value=validator),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install"]) == 1


def test_isolated_install_failure_is_unverified_unless_required() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value="/bin/tool"),
        patch.object(hosts, "checked", return_value=(True, "ok")),
        patch.object(hosts, "isolated_install", return_value=(False, "blocked by host policy")),
    ):
        assert hosts.main([]) == 0
        assert hosts.main(["--require-codex-install"]) == 1
