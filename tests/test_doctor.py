"""Tests for non-blocking read-only diagnostics."""

import importlib.util
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/skiphow/scripts/doctor.py"
SPEC = importlib.util.spec_from_file_location("skiphow_doctor", SCRIPT)
assert SPEC and SPEC.loader
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


def test_no_optional_tools_still_reports_core_ready() -> None:
    with (
        patch.object(doctor.shutil, "which", return_value=None),
        patch.object(doctor, "succeeds", return_value=False),
    ):
        lines = doctor.report()
    assert "Core: READY" in lines
    assert "Repository: LIMITED" in lines
    assert "GitHub Issues: NOT AVAILABLE" in lines
    assert "GitHub Project: NOT CONFIGURED" in lines
    assert "Host checks: UNVERIFIED" in lines


def test_project_is_read_only_and_only_explicit_config_is_used(tmp_path: Path) -> None:
    config = tmp_path / ".skiphow" / "config.yml"
    config.parent.mkdir()
    config.write_text("project: owner/9\n", encoding="utf-8")
    assert doctor.configured_project(str(tmp_path)) == "owner/9"
    config.write_text("project: disabled\n", encoding="utf-8")
    assert doctor.configured_project(str(tmp_path)) is None


def test_nonzero_status_is_reserved_for_required_workflow() -> None:
    with patch.object(doctor, "report", return_value=["Core: READY", "Repository: LIMITED"]):
        assert doctor.main([]) == 0
        assert doctor.main(["--require", "repository"]) == 1
