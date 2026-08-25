"""Tests for non-blocking read-only diagnostics."""

import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/skiphow/scripts/doctor.py"
SPEC = importlib.util.spec_from_file_location("skiphow_doctor", SCRIPT)
assert SPEC and SPEC.loader
doctor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = doctor
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
    assert "Configuration: VALID" in lines
    assert "Host CLI: NOT AVAILABLE" in lines
    assert "Package proof: UNVERIFIED (no receipt supplied)" in lines


def test_project_is_read_only_and_only_explicit_config_is_used(tmp_path: Path) -> None:
    config = tmp_path / ".skiphow" / "config.json"
    config.parent.mkdir()
    config.write_text('{"project": "owner/9"}', encoding="utf-8")
    assert doctor.configured_project(str(tmp_path)) == "owner/9"
    config.write_text('{"project": null}', encoding="utf-8")
    assert doctor.configured_project(str(tmp_path)) is None


def test_host_cli_does_not_claim_package_proof(tmp_path: Path) -> None:
    with (
        patch.object(doctor.shutil, "which", return_value="/bin/host"),
        patch.object(doctor, "succeeds", return_value=True),
    ):
        lines = doctor.report(cwd=str(tmp_path))
    assert "Host CLI: AVAILABLE" in lines
    assert "Package proof: UNVERIFIED (no receipt supplied)" in lines


def test_package_proof_requires_explicit_receipt(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps({"status": "VERIFIED", "reference": "ci/run/123"}),
        encoding="utf-8",
    )
    assert doctor.package_proof(str(receipt)) == "VERIFIED (ci/run/123)"
    receipt.write_text(
        json.dumps({"status": "UNVERIFIED", "reference": "cli unavailable"}),
        encoding="utf-8",
    )
    assert doctor.package_proof(str(receipt)) == "UNVERIFIED (cli unavailable)"
    receipt.write_text('{"status": "VERIFIED"}', encoding="utf-8")
    assert doctor.package_proof(str(receipt)).startswith("FAILED (")


def test_require_package_accepts_only_verified_receipt(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    with (
        patch.object(doctor, "configured_project", return_value=None),
        patch.object(doctor.shutil, "which", return_value=None),
        patch.object(doctor, "succeeds", return_value=False),
    ):
        for status, expected in (("UNVERIFIED", 1), ("FAILED", 1), ("VERIFIED", 0)):
            receipt.write_text(
                json.dumps({"status": status, "reference": "test receipt"}),
                encoding="utf-8",
            )
            assert (
                doctor.main(
                    ["--require", "package", "--package-proof-receipt", str(receipt)]
                )
                == expected
            )


def test_nonzero_status_is_reserved_for_required_workflow() -> None:
    with patch.object(doctor, "report", return_value=["Core: READY", "Repository: LIMITED"]):
        assert doctor.main([]) == 0
        assert doctor.main(["--require", "repository"]) == 1
        assert doctor.main(["--require", "host"]) == 1
