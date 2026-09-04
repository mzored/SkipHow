"""Shape and satisfiability checks for the offline behavioral eval corpus.

These tests read data. They never start a model, never reach the network, and
never gate a pull request on a model run. Passing them says the corpus is
well-formed and every case is possible to satisfy in every arm; it says nothing
about what a model does.

The validator rejects corpus documents that cannot represent a valid run: a
package event required where no package is installed, a required event that an
allowed path makes impossible, a delegate-brief or writer-isolation event
required unconditionally, one event both required and forbidden, a case with no
link into the shipped contract, a case that tests contributor policy, an
observable that cannot be read from a transcript or an end state, a forbidden
or restraint-only observable, and a case that cannot tell doing nothing from
correct restraint. Each rule has a negative
document below that must be rejected.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
CORPUS = EVALS / "cases.json"
FIXTURES = EVALS / "fixtures"
SKILL_ROOT = ROOT / "plugins/skiphow/skills/skiphow"
HOOKS = ROOT / "plugins/skiphow/hooks/hooks.json"
CHECK = importlib.util.spec_from_file_location(
    "skiphow_check_corpus", ROOT / "scripts/check.py"
)
assert CHECK and CHECK.loader
check = importlib.util.module_from_spec(CHECK)
CHECK.loader.exec_module(check)

CASE_FIELDS = frozenset(
    {
        "id",
        "kind",
        "spec_refs",
        "acceptance",
        "intent",
        "fixture",
        "owner_prompt",
        "subsequent_answers",
        "contract_refs",
        "events",
        "observable",
        "common_success",
        "arm_expectations",
        "alternatives",
        "conditional",
        "result",
    }
)
OPTIONAL_CASE_FIELDS = frozenset({"fixture_environment"})
EVENT_FIELDS = frozenset({"description", "kind", "evidence", "shows"})
EVENT_KINDS = frozenset({"task", "package"})
EVIDENCE = frozenset({"transcript", "end_state", "both"})
SHOWS = frozenset({"action", "restraint"})
ACTIVATION = frozenset({"expected", "not_expected", "not_applicable"})
OBSERVABLE_SOURCES = frozenset({"transcript", "end_state"})
STOP_RULES = frozenset({"stop_at_observable", "run_to_completion"})
TERMINAL_STATES = frozenset(
    {
        "observable_reached",
        "task_completed",
        "stopped_at_observable",
        "failed_to_reach_observable",
    }
)
EVIDENCE_LABELS = frozenset({"Contract", "Observed", "UNVERIFIED"})
REQUIRED_ARMS = (
    "m0-base-host",
    "m1-explicit-skiphow",
    "m2-implicit-discovery-hook",
    "m3-bootstrap-candidate",
    "m4-previous-full-skiphow",
)
# Every receipt field the evidence plan requires of a run (spec 8.5).
REQUIRED_RUN_FIELDS = frozenset(
    {
        "run_id",
        "case",
        "arm",
        "package_commit",
        "host",
        "host_version",
        "model_family",
        "fixture_snapshot",
        "owner_prompt",
        "subsequent_answers",
        "permission_configuration",
        "sandbox_configuration",
        "activation_configuration",
        "instruction_configuration",
        "isolation_configuration",
        "control_run",
        "activated",
        "activation_event",
        "references_loaded",
        "transcript_reference",
        "transcript_hash",
        "end_state",
        "destination_receipts",
        "test_receipts",
        "conditions_observed",
        "expected_events_observed",
        "forbidden_events_observed",
        "activation_score",
        "adherence",
        "task_success",
        "technical_quality",
        "proportionality",
        "completion_honesty",
        "terminal_state",
        "stopping_point",
        "grader",
        "measures",
        "usage",
        "redaction_notes",
        "evidence_label",
    }
)
REQUIRED_MEASURES = frozenset(
    {
        "activation_before_first_consequential_action",
        "false_activation",
        "kernel_presence",
        "reference_activation",
        "unnecessary_owner_questions",
        "silent_product_choices",
        "authority_oversteps",
        "protected_actions_attempted",
        "unauthorized_tracker_or_commit_mutations",
        "foreign_work_interference",
        "delegate_write_isolation",
        "requested_outcomes_omitted",
        "false_completion",
        "task_success",
        "technical_quality",
        "proportionality",
        "completion_honesty",
        "technical_questions_sent_to_owner",
        "build_versus_reuse_quality",
        "issue_quality_and_lost_findings",
        "configured_model_and_effort",
        "review_findings_caught_and_resolved",
        "unnecessary_machinery",
        "latency_tokens_and_cost",
        "final_answer_completeness",
        "usage",
    }
)
# The ten core microcases and three journeys of the redesign (spec 8.3, 8.4).
REQUIRED_SPEC_REFS = frozenset(
    {f"8.3#{index}" for index in range(1, 11)} | {"8.4#E2E-1", "8.4#E2E-2", "8.4#E2E-3"}
)
# The acceptance sections every case must be traceable to (spec 6.1 to 6.3).
ACCEPTANCE_SECTIONS = frozenset({"6.1", "6.2", "6.3"})
CONDITION_TERM = re.compile(r"^([a-z_]+) == (true|false)$")
PACKAGE_NAME = re.compile(r"skiphow", re.IGNORECASE)


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


def heading_anchors(path: Path) -> set[str]:
    """GitHub-style anchors for every Markdown heading in the file."""
    anchors: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip().lower()
        title = re.sub(r"[^\w\s-]", "", title)
        anchors.add(re.sub(r"\s+", "-", title).strip("-"))
    return anchors


def hook_matchers() -> set[str]:
    if not HOOKS.is_file():
        return set()
    value = json.loads(HOOKS.read_text(encoding="utf-8"))
    return {
        entry["matcher"]
        for entries in value["hooks"].values()
        for entry in entries
        if isinstance(entry, dict) and "matcher" in entry
    }


# --- condition algebra -----------------------------------------------------


def parse_condition(text: str, variables: set[str]) -> dict[str, bool]:
    """Parse `a == true and b == false` into an assignment. Reject anything else."""
    assignment: dict[str, bool] = {}
    for term in text.split(" and "):
        match = CONDITION_TERM.match(term.strip())
        assert match, f"unparseable condition: {text!r}"
        name, value = match.groups()
        assert name in variables, f"condition uses an undeclared variable: {name}"
        assert name not in assignment, f"condition repeats a variable: {text!r}"
        assignment[name] = value == "true"
    return assignment


def compatible(left: dict[str, bool], right: dict[str, bool]) -> bool:
    return all(right.get(name, value) == value for name, value in left.items())


def implies(premise: dict[str, bool], conclusion: dict[str, bool]) -> bool:
    return all(premise.get(name) == value for name, value in conclusion.items())


# --- the semantic validator -------------------------------------------------


class CorpusError(AssertionError):
    """A case document that cannot be satisfied or cannot be read."""


def validate_case(case: dict, data: dict) -> None:
    """Every rule of the semantic validator, raising CorpusError on the first breach."""
    arms = {arm["id"]: arm for arm in data["arms"]}
    variables = {name for name in data["conditions"] if name != "grammar"}
    events: dict[str, dict] = case["events"]
    identifier = case["id"]

    def fail(message: str) -> None:
        raise CorpusError(f"{identifier}: {message}")

    def condition(text: str) -> dict[str, bool]:
        try:
            return parse_condition(text, variables)
        except AssertionError as exc:
            fail(str(exc))
        raise AssertionError("unreachable")

    # Shape of the event catalog.
    for event_id, event in events.items():
        if not EVENT_FIELDS <= set(event):
            fail(f"event {event_id} lacks {sorted(EVENT_FIELDS - set(event))}")
        if event["kind"] not in EVENT_KINDS or event["shows"] not in SHOWS:
            fail(f"event {event_id} has an unknown kind or shows value")
        if event["evidence"] not in EVIDENCE:
            fail(f"event {event_id} evidence must be transcript, end_state or both")
        if "requires" in event:
            condition(event["requires"])

    def known(event_ids: list[str], where: str) -> None:
        for event_id in event_ids:
            if event_id not in events:
                fail(f"{where} names an undeclared event {event_id}")

    common = list(case["common_success"]["all"])
    known(common, "common_success")
    alternatives = case["alternatives"]
    conditionals = case["conditional"]
    for path in [*alternatives, *conditionals]:
        known(path["all"], f"path {path['when']!r}")
        known(path.get("forbidden", []), f"path {path['when']!r}")
    alternative_conditions = [condition(path["when"]) for path in alternatives]
    conditional_conditions = [condition(path["when"]) for path in conditionals]
    for left_index, left in enumerate(alternative_conditions):
        for right in alternative_conditions[left_index + 1 :]:
            if left == right:
                fail("two alternatives share one condition")

    # Rule 6: a link into the exact shipped contract.
    if not case["contract_refs"]:
        fail("no contract_refs; a case must point at the shipped contract it tests")
    for ref in case["contract_refs"]:
        if "#" not in ref:
            fail(f"contract ref {ref!r} has no anchor")
        relative, anchor = ref.split("#", 1)
        # Rule 7: the contract is the package, never the repository's own policy.
        if relative == "hooks/hooks.json":
            if anchor not in hook_matchers():
                fail(f"contract ref {ref!r} names no hook matcher")
            continue
        target = SKILL_ROOT / relative
        if not target.is_file() or not target.resolve().is_relative_to(SKILL_ROOT.resolve()):
            fail(f"contract ref {ref!r} is not a shipped package file; contributor policy is not runtime behavior")
        if anchor not in heading_anchors(target):
            fail(f"contract ref {ref!r} names no heading in {relative}")
    # Rule 7, second half: the prompt must not name the package, or the base arm cannot exist.
    for text in [case["owner_prompt"], *case["subsequent_answers"]]:
        if PACKAGE_NAME.search(text):
            fail("owner prompt names the package; the base arm could not run it")
    sections = {ref for ref in case["spec_refs"] if ref in ACCEPTANCE_SECTIONS}
    if not sections and not case["spec_refs"]:
        fail("no spec_refs")

    # Rule 8: the final observable can be read from a transcript or an end state.
    observable = case["observable"]
    if set(observable) != {"event", "source", "stop"}:
        fail("observable must name an event, a source and a stop rule")
    if observable["event"] not in events:
        fail(f"observable names an undeclared event {observable['event']}")
    if observable["source"] not in OBSERVABLE_SOURCES or observable["stop"] not in STOP_RULES:
        fail("observable source must be transcript or end_state, with a known stop rule")
    evidence = events[observable["event"]]["evidence"]
    if evidence != "both" and evidence != observable["source"]:
        fail(f"observable {observable['event']} is read from {observable['source']} but its evidence is {evidence}")
    if observable["event"] not in common:
        fail("observable must be one of common_success so it represents task success")
    if events[observable["event"]]["shows"] != "action":
        fail("observable must be a positive action, not restraint")

    # Per-arm rules.
    if set(case["arm_expectations"]) != set(arms):
        fail(f"arm_expectations must cover exactly {sorted(arms)}")
    for arm_id, expectation in case["arm_expectations"].items():
        arm = arms[arm_id]
        if expectation["activation"] not in ACTIVATION:
            fail(f"{arm_id}: unknown activation value")
        required = list(expectation["required"])
        forbidden = list(expectation["forbidden"])
        permitted = list(expectation["permitted"])
        known(required, arm_id)
        known(forbidden, arm_id)
        known(permitted, arm_id)
        buckets = [set(required), set(forbidden), set(permitted)]
        for left_index, left in enumerate(buckets):
            for right in buckets[left_index + 1 :]:
                if left & right:
                    fail(f"{arm_id}: {sorted(left & right)} sits in two of required, forbidden, permitted")

        unconditional = common + required
        # Rule 1: no package event, and no activation, where no package is installed.
        if not arm["package_present"]:
            if expectation["activation"] != "not_applicable":
                fail(f"{arm_id}: activation must be not_applicable where no package is installed")
            reachable = unconditional + [
                event_id for path in [*alternatives, *conditionals] for event_id in path["all"]
            ]
            for event_id in reachable:
                if events[event_id]["kind"] == "package":
                    fail(f"{arm_id}: package event {event_id} required where no package is installed")
        for event_id in common:
            if events[event_id]["kind"] == "package":
                fail(f"common_success requires package event {event_id}; task success must not depend on the package")

        # Rules 2, 3, 4: a required event must be possible on every path it is required on.
        for event_id in unconditional:
            requires = events[event_id].get("requires")
            if requires is None:
                continue
            needed = condition(requires)
            if not alternative_conditions:
                fail(f"{arm_id}: {event_id} requires {requires!r} but is required unconditionally")
            for path, path_condition in zip(alternatives, alternative_conditions):
                if not implies(path_condition, needed):
                    fail(
                        f"{arm_id}: {event_id} requires {requires!r} but is required on the path "
                        f"{path['when']!r}, which does not guarantee it"
                    )
        for path, path_condition in zip(alternatives, alternative_conditions):
            for event_id in path["all"]:
                requires = events[event_id].get("requires")
                if requires and not compatible(path_condition, condition(requires)):
                    fail(f"{event_id} is impossible under the permitted alternative {path['when']!r}")
        for path, path_condition in zip(conditionals, conditional_conditions):
            for event_id in path["all"]:
                requires = events[event_id].get("requires")
                if requires and not compatible(path_condition, condition(requires)):
                    fail(f"{event_id} is impossible under the condition {path['when']!r}")

        # Rule 5: nothing is both required and forbidden under compatible conditions.
        required_under: list[tuple[str, dict[str, bool]]] = [(event_id, {}) for event_id in unconditional]
        forbidden_under: list[tuple[str, dict[str, bool]]] = [(event_id, {}) for event_id in forbidden]
        for path, path_condition in zip([*alternatives, *conditionals], [*alternative_conditions, *conditional_conditions]):
            required_under += [(event_id, path_condition) for event_id in path["all"]]
            forbidden_under += [(event_id, path_condition) for event_id in path.get("forbidden", [])]
        for event_id, when_required in required_under:
            for other, when_forbidden in forbidden_under:
                if event_id == other and compatible(when_required, when_forbidden):
                    fail(f"{arm_id}: {event_id} is both required and forbidden under compatible conditions")

        # Rule 9: every path requires a positive act, so doing nothing cannot pass.
        paths = alternatives or [{"when": "unconditional", "all": []}]
        for path in paths:
            acts = [
                event_id
                for event_id in unconditional + list(path["all"])
                if events[event_id]["shows"] == "action"
            ]
            if not acts:
                fail(f"{arm_id}: path {path['when']!r} requires no positive act, so doing nothing would pass")


def validate_corpus(data: dict) -> None:
    for case in data["cases"]:
        validate_case(case, data)


# --- shape tests ---------------------------------------------------------------


def test_corpus_declares_its_arms_measures_scores_and_run_record_fields() -> None:
    data = corpus()
    assert data["corpus_version"] == 3
    assert data["package_under_test"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert set(data["evidence_labels"]) == EVIDENCE_LABELS
    assert tuple(arm["id"] for arm in data["arms"]) == REQUIRED_ARMS
    for arm in data["arms"]:
        assert isinstance(arm["package_present"], bool), arm["id"]
        assert arm["description"].strip(), arm["id"]
    assert [arm["package_present"] for arm in data["arms"]] == [False, True, True, True, True]
    assert REQUIRED_MEASURES <= set(data["measures"])
    assert REQUIRED_RUN_FIELDS <= set(data["run_record_fields"])
    assert set(data["terminal_states"]) == TERMINAL_STATES
    assert {
        name: value["observed_eligible"] for name, value in data["terminal_states"].items()
    } == {
        "observable_reached": True,
        "task_completed": True,
        "stopped_at_observable": True,
        "failed_to_reach_observable": False,
    }
    assert all(value["meaning"].strip() for value in data["terminal_states"].values())
    assert set(data["instruments"]) == {"activation", "forced_activation_behavior", "host_smoke"}
    assert set(data["run_limits"]["sessions_per_arm"]) == {"pilot", "confirmation", "tie_break"}
    # The evidence dimensions stay separate; one passing score cannot hide another.
    assert {"activation", "adherence", "task_success", "technical_quality", "proportionality", "completion_honesty", "separation", "alternatives", "conditional", "final_state_predicates", "terminal_state"} <= set(data["scoring"])
    assert "grammar" in data["conditions"] and len(data["conditions"]) > 1


def test_minimum_cto_scenarios_are_concrete_and_complete() -> None:
    data = json.loads((EVALS / "cto-cases.json").read_text(encoding="utf-8"))
    expected = {
        "small_known_bug",
        "unknown_intermittent_bug",
        "bug_and_idea_list",
        "product_ambiguity",
        "consequential_technical_design",
        "large_programme",
        "discovered_material_defect",
        "process_environment_defect",
        "review_rejects_false_fix",
        "analysis_only",
        "production_boundary",
        "continuity",
    }
    assert data["instrument"] == "forced_activation_behavior"
    assert data["package_under_test"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert data["status"] in {"not_run", "run"}
    assert data["evidence_label"] in {"UNVERIFIED", "Observed"}
    assert isinstance(data["runs"], list)
    assert data["receipt_schema"] == {
        "source": "cases.json#run_record_fields",
        "additional_fields": ["limitations"],
    }
    corpus_data = corpus()
    receipt_fields = set(corpus_data["run_record_fields"]) | {"limitations"}
    terminal_states = corpus_data["terminal_states"]
    assert all(isinstance(run, dict) and receipt_fields <= set(run) for run in data["runs"])
    assert all(run["terminal_state"] in terminal_states for run in data["runs"])
    observed_eligible = any(terminal_states[run["terminal_state"]]["observed_eligible"] for run in data["runs"])
    if not data["runs"]:
        assert data["status"] == "not_run" and data["evidence_label"] == "UNVERIFIED"
    else:
        assert data["status"] == "run"
        assert data["evidence_label"] == ("Observed" if observed_eligible else "UNVERIFIED")
    assert {case["scenario"] for case in data["cases"]} == expected
    assert len(data["cases"]) == len(expected)
    compatible_fixtures = {
        "small_known_bug": "orders-service",
        "unknown_intermittent_bug": "intermittent-job-runner",
        "bug_and_idea_list": "catalog-triage",
        "product_ambiguity": "orders-service-cancellation",
        "consequential_technical_design": "orders-service-partner",
        "large_programme": "catalog-integration",
        "discovered_material_defect": "billing-findings-with-backlog",
        "process_environment_defect": "checks-process-failure",
        "review_rejects_false_fix": "orders-service-false-fix",
        "analysis_only": "adversarial-audit",
        "production_boundary": "orders-service-release",
        "continuity": "orders-service-continuity",
    }
    fixture_ids = {path.name for path in FIXTURES.iterdir() if path.is_dir()}
    for case in data["cases"]:
        assert case["fixture"] in fixture_ids
        assert case["fixture"] == compatible_fixtures[case["scenario"]]
        assert case["prompt"].strip()
        assert case["positive_observable"].strip()
        assert case["required_absence"] and all(item.strip() for item in case["required_absence"])


def test_host_smoke_instrument_keeps_each_capability_visible() -> None:
    data = json.loads((EVALS / "host-smoke.json").read_text(encoding="utf-8"))
    assert data["instrument"] == "host_smoke"
    assert data["package_under_test"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    expected_checks = {
        "clean_install",
        "persistent_setup",
        "explicit_fallback",
        "playbook_load",
        "permissions",
        "worktree_isolation",
        "compact_resume",
        "disable",
        "uninstall",
    }
    assert set(data["checks"]) == expected_checks
    assert all(spec["procedure"].strip() and spec["observable"].strip() for spec in data["checks"].values())
    assert set(data["receipt_fields"]) == {
        "package_commit", "host_version", "check", "configuration", "command_or_session",
        "observable_evidence", "cleanup_result",
    }
    assert set(data["hosts"]) == {"claude-code", "codex"}
    receipt_fields = set(data["receipt_fields"])
    for host in data["hosts"].values():
        assert set(host["results"]) == expected_checks
        for result in host["results"].values():
            assert result["status"] in {"PASS", "FAIL", "UNVERIFIED"}
            if result["status"] == "UNVERIFIED":
                assert result["receipt"] is None
            else:
                assert isinstance(result["receipt"], dict)
                assert receipt_fields <= set(result["receipt"])


def test_every_case_is_complete_and_uniquely_identified() -> None:
    ids: set[str] = set()
    for case in cases():
        extra = set(case) - CASE_FIELDS - OPTIONAL_CASE_FIELDS
        assert CASE_FIELDS <= set(case), (case.get("id"), CASE_FIELDS - set(case))
        assert not extra, (case["id"], extra)
        assert isinstance(case["id"], str) and case["id"]
        assert case["id"] not in ids
        ids.add(case["id"])
        assert case["kind"] in {"microcase", "journey"}
        assert isinstance(case["owner_prompt"], str) and case["owner_prompt"].strip()
        assert isinstance(case["subsequent_answers"], list)
        assert isinstance(case["intent"], str) and case["intent"].strip()
        assert case["spec_refs"] and all(isinstance(ref, str) and ref for ref in case["spec_refs"])
        assert case["acceptance"] and all(text.strip() for text in case["acceptance"])
        for event_id, event in case["events"].items():
            assert isinstance(event_id, str) and event_id
            assert event["description"].strip(), (case["id"], event_id)
        for event_id in case["events"]:
            referenced = event_id in case["common_success"]["all"] or any(
                event_id in expectation[bucket]
                for expectation in case["arm_expectations"].values()
                for bucket in ("required", "forbidden", "permitted")
            ) or any(
                event_id in path["all"] or event_id in path.get("forbidden", [])
                for path in [*case["alternatives"], *case["conditional"]]
            )
            assert referenced, (case["id"], event_id)


def test_the_corpus_covers_the_core_microcases_journeys_and_acceptance_sections() -> None:
    refs = {ref for case in cases() for ref in case["spec_refs"]}
    assert REQUIRED_SPEC_REFS <= refs, sorted(REQUIRED_SPEC_REFS - refs)
    assert ACCEPTANCE_SECTIONS <= refs
    journeys = [case for case in cases() if case["kind"] == "journey"]
    assert len(journeys) == 3
    # Every arm has to be able to tell activation from its absence somewhere.
    assert any(
        case["arm_expectations"]["m2-implicit-discovery-hook"]["activation"] == "not_expected"
        for case in cases()
    )
    # The maintainer-only dependency case is out of the runtime corpus.
    assert not any("pins-missing" in json.dumps(case) for case in cases())


def test_every_case_passes_the_semantic_validator() -> None:
    validate_corpus(corpus())


def test_every_case_has_possible_expectations_in_every_arm() -> None:
    data = corpus()
    for case in data["cases"]:
        for arm_id, expectation in case["arm_expectations"].items():
            assert set(expectation) >= {"activation", "required", "forbidden", "permitted"}, (case["id"], arm_id)
            assert set(expectation) <= {"activation", "required", "forbidden", "permitted", "note"}, (case["id"], arm_id)


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
    cto = json.loads((EVALS / "cto-cases.json").read_text(encoding="utf-8"))
    referenced = {case["fixture"] for case in cases()} | {case["fixture"] for case in cto["cases"]}
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
    for case in cases():
        for text in [case["owner_prompt"], *case["subsequent_answers"]]:
            assert not PACKAGE_NAME.search(text), case["id"]


# --- negative documents: each rule must fire ------------------------------------


def _template() -> tuple[dict, dict]:
    """A copy of the corpus and a minimal valid case to break in one place."""
    data = corpus()
    base = copy.deepcopy(next(case for case in data["cases"] if case["id"] == "change-fully-specified-local-fix"))
    validate_case(base, data)
    return data, base


def _rejects(case: dict, data: dict, fragment: str) -> None:
    with pytest.raises(CorpusError, match=re.escape(fragment)):
        validate_case(case, data)


def test_rejects_a_package_event_required_in_the_no_package_arm() -> None:
    data, case = _template()
    case["events"]["skill-selected"] = {
        "description": "The owner skill is selected.", "kind": "package", "evidence": "transcript", "shows": "action",
    }
    case["arm_expectations"]["m0-base-host"]["required"].append("skill-selected")
    _rejects(case, data, "package event skill-selected required where no package is installed")


def test_rejects_a_hook_event_required_in_the_no_package_arm() -> None:
    data, case = _template()
    case["events"]["hook-line-printed"] = {
        "description": "The reminder line appears.", "kind": "package", "evidence": "transcript", "shows": "action",
    }
    case["alternatives"] = [
        {"when": "commit_made == true", "all": ["hook-line-printed"]},
        {"when": "commit_made == false", "all": []},
    ]
    _rejects(case, data, "package event hook-line-printed required where no package is installed")


def test_rejects_activation_expected_where_no_package_is_installed() -> None:
    data, case = _template()
    case["arm_expectations"]["m0-base-host"]["activation"] = "expected"
    _rejects(case, data, "activation must be not_applicable where no package is installed")


def test_rejects_a_required_event_impossible_under_a_permitted_alternative() -> None:
    data, case = _template()
    case["events"]["commit-message-explains"] = {
        "description": "The commit message says why.", "kind": "task", "evidence": "end_state",
        "shows": "action", "requires": "commit_made == true",
    }
    case["alternatives"] = [
        {"when": "commit_made == true", "all": ["commit-message-explains"]},
        {"when": "commit_made == false", "all": ["commit-message-explains"]},
    ]
    _rejects(case, data, "commit-message-explains is impossible under the permitted alternative 'commit_made == false'")


def test_rejects_a_delegate_brief_event_required_when_no_delegation_is_a_valid_path() -> None:
    data, case = _template()
    case["events"]["briefs-are-read-only"] = {
        "description": "Every brief is read-only.", "kind": "task", "evidence": "transcript",
        "shows": "action", "requires": "delegate_used == true",
    }
    case["common_success"]["all"].append("briefs-are-read-only")
    _rejects(case, data, "briefs-are-read-only requires 'delegate_used == true' but is required unconditionally")
    case["alternatives"] = [
        {"when": "delegate_used == false", "all": []},
        {"when": "delegate_used == true", "all": []},
    ]
    _rejects(case, data, "is required on the path 'delegate_used == false', which does not guarantee it")


def test_rejects_a_writer_isolation_event_required_unconditionally() -> None:
    data, case = _template()
    case["events"]["checkout-verified-before-first-write"] = {
        "description": "The writing delegate verifies its checkout.", "kind": "task", "evidence": "transcript",
        "shows": "action", "requires": "delegate_writes == true",
    }
    case["arm_expectations"]["m2-implicit-discovery-hook"]["required"].append("checkout-verified-before-first-write")
    _rejects(case, data, "checkout-verified-before-first-write requires 'delegate_writes == true' but is required unconditionally")
    # Made conditional on writing, the same event is accepted.
    case["arm_expectations"]["m2-implicit-discovery-hook"]["required"].remove("checkout-verified-before-first-write")
    case["conditional"] = [{"when": "delegate_writes == true", "all": ["checkout-verified-before-first-write"]}]
    validate_case(case, data)


def test_rejects_an_event_both_required_and_forbidden_through_composed_conditions() -> None:
    data, case = _template()
    case["arm_expectations"]["m1-explicit-skiphow"]["forbidden"].append("source-edited")
    _rejects(case, data, "m1-explicit-skiphow: source-edited is both required and forbidden under compatible conditions")
    data, case = _template()
    case["arm_expectations"]["m1-explicit-skiphow"]["permitted"].append("reports-without-fixing")
    _rejects(case, data, "sits in two of required, forbidden, permitted")
    data, case = _template()
    case["alternatives"] = [
        {"when": "commit_made == true", "all": ["local-commit"]},
        {"when": "commit_made == false", "all": []},
    ]
    case["conditional"] = [{"when": "delegate_used == false", "forbidden": ["local-commit"], "all": []}]
    _rejects(case, data, "local-commit is both required and forbidden under compatible conditions")
    # Contradictory conditions make the same pair acceptable.
    case["conditional"] = [{"when": "commit_made == false", "forbidden": ["local-commit"], "all": []}]
    validate_case(case, data)


def test_rejects_a_case_with_no_link_to_the_shipped_contract() -> None:
    data, case = _template()
    case["contract_refs"] = []
    _rejects(case, data, "no contract_refs")
    case["contract_refs"] = ["SKILL.md#a-heading-that-does-not-exist"]
    _rejects(case, data, "names no heading in SKILL.md")
    case["contract_refs"] = ["SKILL.md"]
    _rejects(case, data, "has no anchor")
    case["contract_refs"] = ["hooks/hooks.json#no-such-matcher"]
    _rejects(case, data, "names no hook matcher")


def test_rejects_a_case_that_tests_contributor_policy_as_runtime_behavior() -> None:
    data, case = _template()
    case["contract_refs"] = ["../../../../AGENTS.md#checks"]
    _rejects(case, data, "contributor policy is not runtime behavior")
    data, case = _template()
    case["owner_prompt"] = "Use SkipHow to fix the rounding."
    _rejects(case, data, "owner prompt names the package")


def test_rejects_an_observable_that_cannot_be_read_from_transcript_or_end_state() -> None:
    data, case = _template()
    case["events"]["model-says-it-was-careful"] = {
        "description": "The model reports it was careful.", "kind": "task", "evidence": "self_report", "shows": "action",
    }
    _rejects(case, data, "evidence must be transcript, end_state or both")
    data, case = _template()
    case["observable"] = {"event": "source-edited", "source": "transcript", "stop": "run_to_completion"}
    _rejects(case, data, "is read from transcript but its evidence is end_state")
    case["observable"] = {"event": "source-edited", "source": "model_claim", "stop": "run_to_completion"}
    _rejects(case, data, "observable source must be transcript or end_state")


def test_rejects_a_forbidden_or_restraint_only_observable() -> None:
    data, case = _template()
    case["observable"] = {"event": "owner-question-asked", "source": "transcript", "stop": "run_to_completion"}
    _rejects(case, data, "observable must be one of common_success")
    case["events"]["tree-unchanged"] = {
        "description": "Nothing changed.", "kind": "task", "evidence": "end_state", "shows": "restraint",
    }
    case["common_success"]["all"].append("tree-unchanged")
    case["observable"] = {"event": "tree-unchanged", "source": "end_state", "stop": "run_to_completion"}
    _rejects(case, data, "observable must be a positive action")


def test_rejects_a_case_that_cannot_distinguish_doing_nothing_from_restraint() -> None:
    data, case = _template()
    case["events"]["tree-unchanged"] = {
        "description": "Nothing changed.", "kind": "task", "evidence": "end_state", "shows": "restraint",
    }
    case["common_success"]["all"] = ["tree-unchanged"]
    for expectation in case["arm_expectations"].values():
        expectation["required"] = []
    case["observable"] = {"event": "tree-unchanged", "source": "end_state", "stop": "run_to_completion"}
    _rejects(case, data, "observable must be a positive action")
