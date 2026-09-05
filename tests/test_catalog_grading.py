"""The catalog grader states outcomes independently of the implementation under test."""

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_eval as capture
import grade_catalog as grader

RECEIPTS = ROOT / "evals/receipts"


def test_planted_base_fixture_fails_every_check(tmp_path):
    capture.materialize("catalog-audit", tmp_path / "fixture")
    checks = grader.probe_directory(tmp_path / "fixture")
    assert checks == {name: False for name in grader.CHECKS}


@pytest.mark.parametrize("receipt, source", [
    ("isolated-host-20260905/codex-delivery-verification.json", "destination"),
    ("host-pilot-20260905/candidate.json", "working copy"),
])
def test_known_correct_retained_end_states_pass(receipt, source):
    report = grader.grade_capture(RECEIPTS / receipt)
    assert report["checks"] == {name: True for name in grader.CHECKS}
    assert report["substantive_pass"] is True
    assert report["artifact_source"] == source
    assert report["evidence_label"] == "UNVERIFIED"


def test_a_working_copy_capture_does_not_establish_a_worktree_delivery():
    """The Codex bootstrap session delivered from a worktree; its checkout stayed unrepaired."""
    report = grader.grade_capture(RECEIPTS / "isolated-host-20260905/codex-bootstrap.json")
    assert report["checks"] == {name: False for name in grader.CHECKS}
    assert report["artifact_source"] == "working copy"


def test_retained_coordination_end_state_fails_only_shipping():
    report = grader.grade_capture(RECEIPTS / "host-pilot-20260905/coordination.json")
    assert report["checks"] == {
        "discount_over_100_rejected": True,
        "case_insensitive_search": True,
        "oversell_rejected_without_mutation": True,
        "two_lines_in_one_parcel": False,
    }
    assert report["substantive_pass"] is False


def test_grader_rejects_receipts_without_a_catalog_or_with_altered_content(tmp_path):
    with pytest.raises(ValueError, match="manual-evaluation-capture"):
        grader.catalog_files({"kind": "other"})
    path = RECEIPTS / "host-pilot-20260905/candidate.json"
    receipt = json.loads(path.read_text())
    for artifact in receipt["end_state_artifacts"]:
        if artifact["description"] == "catalog/shipping.py":
            item = json.loads(artifact["content"])
            item["content"] = item["content"].replace("PARCEL_RATE", "RATE")
            artifact["content"] = json.dumps(item)
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="hash mismatch"):
        grader.grade_capture(altered)


def test_cli_exit_code_follows_the_substantive_grade(capsys):
    assert grader.main([str(RECEIPTS / "isolated-host-20260905/codex-delivery-verification.json")]) == 0
    assert grader.main([str(RECEIPTS / "host-pilot-20260905/coordination.json")]) == 1
    lines = capsys.readouterr().out.strip().splitlines()
    assert json.loads(lines[-1])["checks"]["two_lines_in_one_parcel"] is False
