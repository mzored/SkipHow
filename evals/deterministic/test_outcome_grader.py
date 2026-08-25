"""Contract tests for the model-free outcome grader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.graders.outcome import ManifestError, grade_files, grade_scenario


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/deterministic"


def load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_passing_receipt_proves_outcomes_and_forbidden_effect_absence() -> None:
    report = grade_files(FIXTURES / "scenario.json", FIXTURES / "pass.json")
    assert report.verdict == "PASS"
    assert report.passed
    assert len(report.checks) == 4


def test_forbidden_effect_and_wrong_outcome_fail() -> None:
    report = grade_files(FIXTURES / "scenario.json", FIXTURES / "fail.json")
    assert report.verdict == "FAIL"
    failures = {check.rule_id for check in report.checks if not check.passed}
    assert failures == {"bounded_files", "campaign_created"}


def test_missing_forbidden_effect_evidence_cannot_pass() -> None:
    report = grade_files(FIXTURES / "scenario.json", FIXTURES / "missing-evidence.json")
    assert report.verdict == "FAIL"
    failures = {check.rule_id for check in report.checks if not check.passed}
    assert failures == {"campaign_created", "engineering_question"}


def test_rule_id_observation_can_supply_a_human_readable_observation_label() -> None:
    manifest = load("scenario.json")
    grading = manifest["grading"]
    assert isinstance(grading, dict)
    required = grading["required_outcomes"]
    assert isinstance(required, list) and isinstance(required[0], dict)
    required[0]["observation"] = "human description"
    receipt = load("pass.json")
    receipt["observations"] = {"terminal_success": "success"}
    assert grade_scenario(manifest, receipt).checks[0].passed


def test_unknown_operator_is_invalid() -> None:
    manifest = load("scenario.json")
    grading = manifest["grading"]
    assert isinstance(grading, dict)
    required = grading["required_outcomes"]
    assert isinstance(required, list) and isinstance(required[0], dict)
    required[0]["operator"] = "approximately"
    with pytest.raises(ManifestError, match="unsupported operator"):
        grade_scenario(manifest, load("pass.json"))


def test_greater_than_marks_a_positive_forbidden_counter_as_a_violation() -> None:
    manifest = load("scenario.json")
    grading = manifest["grading"]
    assert isinstance(grading, dict)
    forbidden = grading["forbidden_effects"]
    assert isinstance(forbidden, list) and isinstance(forbidden[1], dict)
    forbidden[1]["operator"] = "greater_than"
    forbidden[1]["expected"] = 0
    receipt = load("pass.json")
    owner_questions = receipt["owner_questions"]
    assert isinstance(owner_questions, dict)
    owner_questions["engineering"] = 1
    report = grade_scenario(manifest, receipt)
    assert not next(check for check in report.checks if check.rule_id == "engineering_question").passed
