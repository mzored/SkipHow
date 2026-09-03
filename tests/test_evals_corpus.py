"""Shape contracts for the offline behavioral eval corpus.

These tests read data. They never start a model, never reach the network, and
never gate a pull request on a model run.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
CORPUS = EVALS / "cases.json"
FIXTURES = EVALS / "fixtures"
CHECK = importlib.util.spec_from_file_location(
    "skiphow_check_corpus", ROOT / "scripts/check.py"
)
assert CHECK and CHECK.loader
check = importlib.util.module_from_spec(CHECK)
CHECK.loader.exec_module(check)

CASE_FIELDS = frozenset(
    {
        "id",
        "matrix_rows",
        "behavior",
        "polarity",
        "intent",
        "fixture",
        "owner_prompt",
        "subsequent_answers",
        "activation_expected",
        "expected_events",
        "forbidden_events",
        "permitted_events",
        "result",
    }
)
# Every record field the evidence plan requires of a run.
REQUIRED_RUN_FIELDS = frozenset(
    {
        "arm",
        "fixture_snapshot",
        "owner_prompt",
        "subsequent_answers",
        "package_commit",
        "host",
        "host_version",
        "permission_configuration",
        "isolation_configuration",
        "hook_configuration",
        "activated",
        "references_loaded",
        "expected_events_observed",
        "forbidden_events_observed",
        "adherence",
        "end_state",
        "measures",
        "usage",
        "evidence_label",
        "transcript_reference",
    }
)
REQUIRED_MEASURES = frozenset(
    {
        "unnecessary_owner_questions",
        "silent_product_choices",
        "protected_actions_attempted",
        "unauthorized_tracker_or_commit_mutations",
        "requested_outcomes_omitted",
        "false_completion",
        "foreign_work_interference",
        "delegate_write_isolation",
        "reference_activation",
        "task_success",
        "final_answer_completeness",
        "usage",
    }
)
REQUIRED_ARMS = ("base-host-no-skiphow", "compact-candidate", "previous-full-skiphow")
# The acceptance rows 3.0.0 changed and this corpus must be able to observe.
REQUIRED_MATRIX_ROWS = frozenset({"A1", "A2", "A3", "A4", "G1", "H1", "T1"})
EVIDENCE_LABELS = frozenset({"Contract", "Observed", "UNVERIFIED"})


def corpus() -> dict:
    value = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def cases() -> list[dict]:
    value = corpus()["cases"]
    assert isinstance(value, list) and value
    return value


def fixture_record(name: str) -> dict:
    value = json.loads((FIXTURES / name / "fixture.json").read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_corpus_declares_its_arms_measures_and_run_record_fields() -> None:
    data = corpus()
    assert data["package_under_test"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert set(data["evidence_labels"]) == EVIDENCE_LABELS
    assert tuple(arm["id"] for arm in data["arms"]) == REQUIRED_ARMS
    assert REQUIRED_MEASURES <= set(data["measures"])
    assert REQUIRED_RUN_FIELDS <= set(data["run_record_fields"])
    assert set(data["run_limits"]["sessions_per_arm"]) == {"pilot", "confirmation", "tie_break"}
    # Activation and adherence are scored separately, and the corpus says so.
    assert {"activation", "adherence", "separation"} <= set(data["scoring"])


def test_every_case_is_complete_and_uniquely_identified() -> None:
    ids: set[str] = set()
    for case in cases():
        assert CASE_FIELDS <= set(case), case.get("id")
        assert isinstance(case["id"], str) and case["id"]
        assert case["id"] not in ids
        ids.add(case["id"])
        assert case["polarity"] in {"positive", "negative"}
        assert isinstance(case["activation_expected"], bool)
        assert isinstance(case["owner_prompt"], str) and case["owner_prompt"].strip()
        assert isinstance(case["subsequent_answers"], list)
        assert isinstance(case["intent"], str) and case["intent"].strip()
        assert case["matrix_rows"] and all(
            isinstance(row, str) and row for row in case["matrix_rows"]
        )
    for case in cases():
        for sibling in case.get("scored_together_with", []):
            assert sibling in ids


def test_every_case_names_expected_and_forbidden_events() -> None:
    for case in cases():
        expected = case["expected_events"]
        forbidden = case["forbidden_events"]
        assert expected, case["id"]
        assert forbidden, case["id"]
        seen: set[str] = set()
        for event in [*expected, *forbidden, *case["permitted_events"]]:
            assert set(event) == {"id", "description"}, case["id"]
            assert event["description"].strip()
            # One event id cannot be required and forbidden in the same case.
            assert event["id"] not in seen, (case["id"], event["id"])
            seen.add(event["id"])


def test_the_changed_rows_are_covered_in_both_directions() -> None:
    rows = {row for case in cases() for row in case["matrix_rows"]}
    assert REQUIRED_MATRIX_ROWS <= rows
    polarities: dict[str, set[str]] = {}
    for case in cases():
        polarities.setdefault(case["behavior"], set()).add(case["polarity"])
    assert polarities
    for behavior, seen in polarities.items():
        assert seen == {"positive", "negative"}, behavior
    # A behavior must be forbidden somewhere it is expected elsewhere.
    assert any(not case["activation_expected"] for case in cases())


def test_every_referenced_fixture_exists_and_describes_itself() -> None:
    directories = {path.name for path in FIXTURES.iterdir() if path.is_dir()}
    assert directories
    for name in directories:
        record = fixture_record(name)
        assert record["id"] == name
        assert record["synthetic"] is True
        assert record["summary"].strip()
        assert record["planted"] and record["setup"] and record["privacy"].strip()
        base = record.get("derives_from")
        assert base is None or base in directories
    referenced = {case["fixture"] for case in cases()}
    assert referenced <= directories
    # A fixture nothing points at is dead weight in a corpus this small.
    assert directories - referenced == set()
    for case in cases():
        environment = case.get("fixture_environment")
        if environment is not None:
            assert environment in fixture_record(case["fixture"])["environments"]


def test_no_case_claims_a_result_it_has_not_earned() -> None:
    for case in cases():
        result = case["result"]
        assert set(result) == {"status", "evidence_label", "arms_pending", "runs"}
        assert result["status"] == "not_run", case["id"]
        assert result["evidence_label"] == "UNVERIFIED", case["id"]
        assert result["runs"] == [], case["id"]
        assert tuple(result["arms_pending"]) == REQUIRED_ARMS, case["id"]


def test_the_corpus_stays_offline_privacy_safe_and_uncollected() -> None:
    for path in sorted(EVALS.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        assert path.name != "conftest.py", relative
        assert not path.name.startswith("test_"), relative
        assert not path.name.endswith("_test.py"), relative
        assert not path.stat().st_mode & 0o111, relative
        text = path.read_text(encoding="utf-8")
        assert not check.PERSONAL_PATH.search(text), relative
        assert not check.CONCRETE_MODEL_ID.search(text), relative
