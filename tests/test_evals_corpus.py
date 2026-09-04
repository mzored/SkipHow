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
import hashlib
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
HOST_CHECKS = importlib.util.spec_from_file_location(
    "skiphow_check_hosts_corpus", ROOT / "scripts/check_hosts.py"
)
assert HOST_CHECKS and HOST_CHECKS.loader
host_checks = importlib.util.module_from_spec(HOST_CHECKS)
HOST_CHECKS.loader.exec_module(host_checks)

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
        "trial",
        "package_version",
        "package_commit",
        "package_tree",
        "package_payload_sha256",
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
        "end_state_artifacts",
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
        "receipt_complete",
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


def fixture_source_sha256(name: str) -> str:
    """Hash the retained source layers that define a synthetic fixture."""
    layers: list[str] = []

    def add_layer(layer: str) -> None:
        record = fixture_record(layer)
        base = record.get("derives_from")
        if base is not None:
            add_layer(base)
        layers.append(layer)

    add_layer(name)
    payload: dict[str, dict[str, object]] = {}
    for layer in layers:
        root = FIXTURES / layer
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            payload[f"{layer}/{path.relative_to(root).as_posix()}"] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "executable": bool(path.stat().st_mode & 0o111),
            }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_fixture_snapshot(snapshot: object, name: str) -> bool:
    """Validate fixture provenance and return whether built content has a manifest."""
    assert isinstance(snapshot, dict), "fixture snapshot must be an object"
    assert set(snapshot) == {
        "id",
        "setup",
        "fixture_revision_sha256",
        "built_content",
    }, "fixture snapshot has unknown or missing fields"
    assert snapshot["id"] == name, "fixture snapshot mismatch"
    assert snapshot["setup"] == fixture_record(name)["setup"], "fixture snapshot setup mismatch"
    assert snapshot["fixture_revision_sha256"] == fixture_source_sha256(name), "fixture revision mismatch"
    built = snapshot["built_content"]
    assert isinstance(built, dict) and set(built) == {
        "verification",
        "sha256",
        "manifest",
    }, "fixture built-content proof is malformed"
    assert re.fullmatch(r"[0-9a-f]{64}", str(built["sha256"])), "invalid built fixture hash"
    assert built["sha256"] != "0" * 64, "invalid built fixture hash"
    if built["verification"] == "attested":
        assert built["manifest"] is None, "attested fixture build cannot claim a manifest"
        return False
    assert built["verification"] == "manifest", "unknown fixture verification"
    manifest = built["manifest"]
    assert isinstance(manifest, dict) and set(manifest) == {"schema", "scope", "files"}, "fixture manifest is malformed"
    assert manifest["schema"] == 1
    assert manifest["scope"] == "pre-session worktree regular files excluding .git"
    assert isinstance(manifest["files"], list) and manifest["files"], "fixture manifest files are empty"
    paths: list[str] = []
    for entry in manifest["files"]:
        assert isinstance(entry, dict) and set(entry) == {"path", "mode", "sha256"}, "fixture manifest entry is malformed"
        path = entry["path"]
        assert isinstance(path, str) and path and not path.startswith("/")
        assert ".." not in Path(path).parts and "\\" not in path, "unsafe fixture manifest path"
        assert entry["mode"] in {"100644", "100755"}, "invalid fixture manifest mode"
        assert re.fullmatch(r"[0-9a-f]{64}", str(entry["sha256"])), "invalid fixture manifest hash"
        paths.append(path)
    assert paths == sorted(set(paths)), "fixture manifest paths must be unique and sorted"
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == built["sha256"], "built fixture manifest hash mismatch"
    return True


def validate_end_state_artifacts(value: object) -> bool:
    """Validate retained end-state evidence and return whether any is present."""
    assert isinstance(value, list), "end-state artifacts must be a list"
    for artifact in value:
        assert isinstance(artifact, dict) and set(artifact) == {
            "kind",
            "sha256",
            "description",
            "content",
        }, "end-state artifact is malformed"
        assert artifact["kind"] in {"tree", "diff", "manifest", "file", "marker"}
        assert re.fullmatch(r"[0-9a-f]{64}", str(artifact["sha256"])), "invalid end-state artifact hash"
        assert artifact["sha256"] != "0" * 64, "invalid end-state artifact hash"
        assert isinstance(artifact["description"], str) and artifact["description"].strip()
        assert isinstance(artifact["content"], str) and artifact["content"].strip()
        assert hashlib.sha256(artifact["content"].encode()).hexdigest() == artifact["sha256"], "end-state artifact hash mismatch"
    return bool(value)


def synthetic_fixture_snapshot(name: str) -> dict:
    """Build a complete in-memory receipt for validator unit tests."""
    manifest = {
        "schema": 1,
        "scope": "pre-session worktree regular files excluding .git",
        "files": [
            {
                "path": "receipt.txt",
                "mode": "100644",
                "sha256": hashlib.sha256(b"synthetic fixture").hexdigest(),
            }
        ],
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return {
        "id": name,
        "setup": fixture_record(name)["setup"],
        "fixture_revision_sha256": fixture_source_sha256(name),
        "built_content": {
            "verification": "manifest",
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "manifest": manifest,
        },
    }


def synthetic_end_state_artifacts() -> list[dict]:
    return [
        {
            "kind": "manifest",
            "sha256": hashlib.sha256(b"synthetic end state").hexdigest(),
            "description": "Synthetic end-state manifest for validator tests.",
            "content": "synthetic end state",
        }
    ]


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
    assert data["corpus_version"] == 4
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


def validate_cto_instrument(
    data: dict,
    *,
    identity_validator=host_checks.validate_committed_package_identity,
    historical_identity_validator=host_checks.validate_committed_package_identity,
) -> None:
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
    assert "status" not in data and "evidence_label" not in data and "runs" not in data
    assert data["suite_status"] in {"not_run", "partial", "complete"}
    coverage = data["minimum_coverage"]
    assert set(coverage) == {"case_ids", "hosts", "arms", "trials", "prompt_style"}
    required_case_ids = {
        "cto-small-known-bug",
        "cto-product-ambiguity",
        "cto-consequential-design",
        "cto-large-programme",
        "cto-discovered-material-defect",
        "cto-process-environment-defect",
        "cto-analysis-only",
        "cto-production-boundary",
    }
    assert set(coverage["case_ids"]) == required_case_ids
    assert set(coverage["case_ids"]) <= {case["id"] for case in data["cases"]}
    assert len(coverage["case_ids"]) == len(set(coverage["case_ids"])), "duplicate coverage case id"
    assert set(coverage["hosts"]) == {"claude-code", "codex"}
    assert set(coverage["arms"]) == {"m1-explicit-skiphow"}
    assert set(coverage["trials"]) == {"pilot", "confirmation"}
    assert coverage["prompt_style"] == "autonomy"
    assert data["receipt_schema"] == {
        "source": "cases.json#run_record_fields",
        "additional_fields": [
            "limitations",
            "prompt_id",
            "fixture",
            "method_selection",
            "owner_boundary",
            "ceremony",
            "owner_questions",
        ],
    }
    corpus_data = corpus()
    arm_by_id = {arm["id"]: arm for arm in corpus_data["arms"]}
    receipt_fields = set(corpus_data["run_record_fields"]) | set(data["receipt_schema"]["additional_fields"])
    terminal_states = corpus_data["terminal_states"]
    assert {case["scenario"] for case in data["cases"]} == expected
    assert len(data["cases"]) == len(expected)
    case_ids = [case["id"] for case in data["cases"]]
    assert len(case_ids) == len(set(case_ids)), "duplicate CTO case id"
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
    prompt_ids: set[str] = set()
    run_ids: set[str] = set()
    transcript_hashes: set[str] = set()
    observed_scenarios = 0
    any_run = False
    all_cases_covered = True
    paired_styles = 0
    host_summary = {
        host: {
            "observed_scenarios": 0,
            "total_scenarios": len(data["cases"]),
            "covered_minimum_scenarios": 0,
            "total_minimum_scenarios": len(required_case_ids),
        }
        for host in coverage["hosts"]
    }
    for case in data["cases"]:
        assert case["fixture"] in fixture_ids
        assert case["fixture"] == compatible_fixtures[case["scenario"]]
        assert case["prompts"]
        prompt_by_id: dict[str, dict] = {}
        for prompt in case["prompts"]:
            assert set(prompt) == {"id", "style", "text"}
            assert prompt["style"] in {"adherence", "autonomy"}
            assert prompt["text"].strip()
            assert prompt["id"] not in prompt_ids, "duplicate CTO prompt id"
            prompt_ids.add(prompt["id"])
            prompt_by_id[prompt["id"]] = prompt
        assert any(prompt["style"] == "autonomy" for prompt in case["prompts"])
        if {prompt["style"] for prompt in case["prompts"]} == {"adherence", "autonomy"}:
            paired_styles += 1
        assert case["positive_observable"].strip()
        assert case["required_absence"] and all(item.strip() for item in case["required_absence"])
        result = case["result"]
        assert set(result) == {"status", "evidence_label", "runs"}
        assert result["status"] in {"not_run", "partial", "run"}
        assert result["evidence_label"] in {"UNVERIFIED", "Observed"}
        assert isinstance(result["runs"], list)
        observed_eligible = False
        observed_by_host = {host: False for host in coverage["hosts"]}
        covered_cells: set[tuple[str, str, str]] = set()
        for run in result["runs"]:
            any_run = True
            assert isinstance(run, dict) and receipt_fields <= set(run), "incomplete CTO receipt"
            assert run["run_id"] not in run_ids, "duplicate CTO run id"
            run_ids.add(run["run_id"])
            assert re.fullmatch(r"[0-9a-f]{64}", str(run["transcript_hash"])), "invalid CTO transcript hash"
            assert run["transcript_hash"] not in transcript_hashes, "duplicate CTO transcript hash"
            transcript_hashes.add(run["transcript_hash"])
            assert run["case"] == case["id"], "unknown or mismatched CTO case"
            assert run["prompt_id"] in prompt_by_id, "unknown CTO prompt"
            prompt = prompt_by_id[run["prompt_id"]]
            assert run["owner_prompt"] == prompt["text"], "CTO receipt prompt mismatch"
            assert run["fixture"] == case["fixture"], "CTO receipt fixture mismatch"
            manifest_verified = validate_fixture_snapshot(run["fixture_snapshot"], case["fixture"])
            assert run["host"] in coverage["hosts"], "unknown CTO host"
            assert run["arm"] in arm_by_id, "unknown CTO arm"
            assert run["trial"] in {"pilot", "confirmation", "tie_break"}, "unknown CTO trial"
            package_fields = (
                "package_version",
                "package_commit",
                "package_tree",
                "package_payload_sha256",
            )
            if arm_by_id[run["arm"]]["package_present"]:
                if run["arm"] == "m4-previous-full-skiphow":
                    historical_identity_validator(run, match_current=False)
                else:
                    identity_validator(run)
            else:
                assert all(run[field] == "not_applicable" for field in package_fields), "base arm carries package identity"
            assert run["terminal_state"] in terminal_states
            eligible_terminal = terminal_states[run["terminal_state"]]["observed_eligible"]
            artifacts_retained = validate_end_state_artifacts(run["end_state_artifacts"])
            receipt_complete = manifest_verified and artifacts_retained
            assert isinstance(run["receipt_complete"], bool), "CTO receipt_complete must be boolean"
            assert run["receipt_complete"] is receipt_complete, "CTO receipt completeness is not derived"
            eligible = eligible_terminal and receipt_complete
            expected_label = "Observed" if eligible else "UNVERIFIED"
            assert run["evidence_label"] == expected_label, "CTO run evidence label is not derived"
            assert run["method_selection"] in {"pass", "fail", "not_applicable"}
            assert run["owner_boundary"] in {"pass", "fail", "not_applicable"}
            assert run["ceremony"] in {"pass", "fail", "not_applicable"}
            assert run["owner_questions"] in {"pass", "fail", "not_applicable"}
            assert run["activation_score"] in {"pass", "fail", "not_applicable"}
            assert run["adherence"] in {"pass", "fail", "not_applicable"}
            for score in ("task_success", "technical_quality", "proportionality", "completion_honesty"):
                assert run[score] in {"pass", "fail"}, f"invalid CTO {score}"
            for field in (
                "host_version",
                "model_family",
                "permission_configuration",
                "sandbox_configuration",
                "activation_configuration",
                "instruction_configuration",
                "isolation_configuration",
                "control_run",
                "activation_event",
                "transcript_reference",
                "end_state",
                "test_receipts",
                "stopping_point",
                "grader",
                "redaction_notes",
                "limitations",
            ):
                assert isinstance(run[field], str) and run[field].strip(), f"empty CTO {field}"
            assert isinstance(run["activated"], bool), "CTO activated must be boolean"
            for field in (
                "subsequent_answers",
                "references_loaded",
                "expected_events_observed",
                "forbidden_events_observed",
            ):
                assert isinstance(run[field], list), f"CTO {field} must be a list"
            for field in ("conditions_observed", "measures", "usage", "destination_receipts"):
                assert isinstance(run[field], dict), f"CTO {field} must be an object"
            declared_candidate = (
                prompt["style"] == coverage["prompt_style"]
                and run["arm"] in coverage["arms"]
                and run["activated"] is True
                and run["activation_score"] == "pass"
            )
            observed_eligible = observed_eligible or (eligible and declared_candidate)
            if eligible and declared_candidate:
                observed_by_host[run["host"]] = True
            if (
                prompt["style"] == coverage["prompt_style"]
                and run["host"] in coverage["hosts"]
                and run["arm"] in coverage["arms"]
                and run["trial"] in coverage["trials"]
            ):
                if receipt_complete:
                    covered_cells.add((run["host"], run["arm"], run["trial"]))
        required_cells = {
            (host, arm, trial)
            for host in coverage["hosts"]
            for arm in coverage["arms"]
            for trial in coverage["trials"]
        }
        case_covered = required_cells <= covered_cells
        expected_status = "not_run" if not result["runs"] else "run" if case_covered else "partial"
        assert result["status"] == expected_status, "CTO scenario status is not derived"
        expected_label = "Observed" if observed_eligible else "UNVERIFIED"
        assert result["evidence_label"] == expected_label, "CTO scenario evidence label is not derived"
        observed_scenarios += int(observed_eligible)
        if case["id"] in required_case_ids:
            all_cases_covered = all_cases_covered and case_covered
            for host in coverage["hosts"]:
                host_cells = {
                    (host, arm, trial)
                    for arm in coverage["arms"]
                    for trial in coverage["trials"]
                }
                host_summary[host]["covered_minimum_scenarios"] += int(
                    host_cells <= covered_cells
                )
        for host, observed in observed_by_host.items():
            host_summary[host]["observed_scenarios"] += int(observed)
    assert paired_styles >= 8
    expected_suite_status = "not_run" if not any_run else "complete" if all_cases_covered else "partial"
    assert data["suite_status"] == expected_suite_status, "CTO suite coverage status is not derived"
    assert data["summary"] == {
        "prompt_style": coverage["prompt_style"],
        "observed_scenarios": observed_scenarios,
        "total_scenarios": len(data["cases"]),
        "by_host": host_summary,
    }, "stale CTO evidence summary"


def test_minimum_cto_scenarios_are_concrete_and_complete() -> None:
    data = json.loads((EVALS / "cto-cases.json").read_text(encoding="utf-8"))
    validate_cto_instrument(data)


def _cto_document() -> dict:
    data = json.loads((EVALS / "cto-cases.json").read_text(encoding="utf-8"))
    for case in data["cases"]:
        case["result"] = {"status": "not_run", "evidence_label": "UNVERIFIED", "runs": []}
    data["suite_status"] = "not_run"
    data["summary"]["observed_scenarios"] = 0
    for host in data["summary"]["by_host"].values():
        host["observed_scenarios"] = 0
        host["covered_minimum_scenarios"] = 0
    return data


def _validate_synthetic_cto(data: dict) -> None:
    validate_cto_instrument(
        data,
        identity_validator=lambda _: None,
        historical_identity_validator=lambda *_args, **_kwargs: None,
    )


def _add_cto_run(
    data: dict,
    case_index: int = 0,
    *,
    host: str = "claude-code",
    arm: str = "m1-explicit-skiphow",
    trial: str = "pilot",
    terminal_state: str = "task_completed",
    run_id: str | None = None,
) -> dict:
    case = data["cases"][case_index]
    prompt = next(prompt for prompt in case["prompts"] if prompt["style"] == "autonomy")
    run = {field: "recorded" for field in corpus()["run_record_fields"]}
    eligible = corpus()["terminal_states"][terminal_state]["observed_eligible"]
    receipt_run_id = run_id or f"{case['id']}-{host}-{trial}"
    run.update(
        {
            "run_id": receipt_run_id,
            "case": case["id"],
            "arm": arm,
            "package_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
            "package_commit": "a" * 40,
            "package_tree": "b" * 40,
            "package_payload_sha256": "c" * 64,
            "host": host,
            "owner_prompt": prompt["text"],
            "fixture_snapshot": synthetic_fixture_snapshot(case["fixture"]),
            "terminal_state": terminal_state,
            "evidence_label": "Observed" if eligible else "UNVERIFIED",
            "transcript_hash": hashlib.sha256(receipt_run_id.encode()).hexdigest(),
            "prompt_id": prompt["id"],
            "fixture": case["fixture"],
            "trial": trial,
            "limitations": "Synthetic validator receipt.",
            "method_selection": "pass",
            "owner_boundary": "pass",
            "ceremony": "pass",
            "owner_questions": "pass",
            "activation_score": "pass",
            "adherence": "pass",
            "task_success": "pass",
            "technical_quality": "pass",
            "proportionality": "pass",
            "completion_honesty": "pass",
            "receipt_complete": True,
            "activated": True,
            "subsequent_answers": [],
            "references_loaded": [],
            "expected_events_observed": [],
            "forbidden_events_observed": [],
            "conditions_observed": {},
            "measures": {},
            "usage": {},
            "destination_receipts": {},
            "end_state_artifacts": synthetic_end_state_artifacts(),
        }
    )
    if not next(arm_spec for arm_spec in corpus()["arms"] if arm_spec["id"] == arm)["package_present"]:
        for field in ("package_version", "package_commit", "package_tree", "package_payload_sha256"):
            run[field] = "not_applicable"
        run["activated"] = False
        run["activation_score"] = "not_applicable"
    case["result"]["runs"].append(run)
    case["result"]["status"] = "partial"
    if eligible and arm in data["minimum_coverage"]["arms"]:
        case["result"]["evidence_label"] = "Observed"
    data["suite_status"] = "partial"
    data["summary"]["observed_scenarios"] = sum(
        result_case["result"]["evidence_label"] == "Observed"
        for result_case in data["cases"]
    )
    data["summary"]["by_host"][host]["observed_scenarios"] = sum(
        any(
            recorded["host"] == host
            and recorded["evidence_label"] == "Observed"
            and recorded["arm"] in data["minimum_coverage"]["arms"]
            and next(
                prompt_item["style"]
                for prompt_item in result_case["prompts"]
                if prompt_item["id"] == recorded["prompt_id"]
            )
            == data["minimum_coverage"]["prompt_style"]
            for recorded in result_case["result"]["runs"]
        )
        for result_case in data["cases"]
    )
    if case["id"] in data["minimum_coverage"]["case_ids"]:
        required_host_cells = {
            (required_arm, required_trial)
            for required_arm in data["minimum_coverage"]["arms"]
            for required_trial in data["minimum_coverage"]["trials"]
        }
        covered_host_cells = {
            (recorded["arm"], recorded["trial"])
            for recorded in case["result"]["runs"]
            if recorded["host"] == host
            and next(
                prompt_item["style"]
                for prompt_item in case["prompts"]
                if prompt_item["id"] == recorded["prompt_id"]
            )
            == data["minimum_coverage"]["prompt_style"]
        }
        if required_host_cells <= covered_host_cells:
            data["summary"]["by_host"][host]["covered_minimum_scenarios"] = sum(
                all(
                    any(
                        recorded["host"] == host
                        and recorded["arm"] == required_arm
                        and recorded["trial"] == required_trial
                        and next(
                            prompt_item["style"]
                            for prompt_item in result_case["prompts"]
                            if prompt_item["id"] == recorded["prompt_id"]
                        )
                        == data["minimum_coverage"]["prompt_style"]
                        for recorded in result_case["result"]["runs"]
                    )
                    for required_arm, required_trial in required_host_cells
                )
                for result_case in data["cases"]
                if result_case["id"] in data["minimum_coverage"]["case_ids"]
            )
    return run


def test_one_cto_receipt_observes_only_its_own_scenario() -> None:
    data = _cto_document()
    _add_cto_run(data)
    _validate_synthetic_cto(data)
    assert data["summary"]["observed_scenarios"] == 1
    assert data["summary"]["total_scenarios"] == 12
    assert data["summary"]["by_host"]["claude-code"]["observed_scenarios"] == 1
    assert data["summary"]["by_host"]["codex"]["observed_scenarios"] == 0
    assert data["cases"][0]["result"]["evidence_label"] == "Observed"
    assert all(case["result"]["evidence_label"] == "UNVERIFIED" for case in data["cases"][1:])


def test_cto_instrument_rejects_unknown_or_mismatched_case() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    run["case"] = "not-a-cto-case"
    with pytest.raises(AssertionError, match="unknown or mismatched CTO case"):
        _validate_synthetic_cto(data)


def test_cto_instrument_rejects_duplicate_run_id_across_scenarios() -> None:
    data = _cto_document()
    _add_cto_run(data, run_id="duplicate")
    _add_cto_run(data, 1, run_id="duplicate")
    with pytest.raises(AssertionError, match="duplicate CTO run id"):
        _validate_synthetic_cto(data)


def test_cto_instrument_rejects_empty_coverage_and_reused_session() -> None:
    data = _cto_document()
    data["minimum_coverage"]["arms"] = []
    _add_cto_run(data)
    with pytest.raises(AssertionError):
        _validate_synthetic_cto(data)

    data = _cto_document()
    first = _add_cto_run(data)
    second = _add_cto_run(data, 1)
    second["transcript_hash"] = first["transcript_hash"]
    with pytest.raises(AssertionError, match="duplicate CTO transcript hash"):
        _validate_synthetic_cto(data)


def test_adherence_receipt_does_not_upgrade_the_autonomy_summary() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    case = data["cases"][0]
    adherence = next(prompt for prompt in case["prompts"] if prompt["style"] == "adherence")
    run["prompt_id"] = adherence["id"]
    run["owner_prompt"] = adherence["text"]
    case["result"]["evidence_label"] = "UNVERIFIED"
    data["summary"]["observed_scenarios"] = 0
    data["summary"]["by_host"]["claude-code"]["observed_scenarios"] = 0
    _validate_synthetic_cto(data)


def test_base_arm_receipt_does_not_upgrade_candidate_evidence() -> None:
    data = _cto_document()
    run = _add_cto_run(data, arm="m0-base-host")
    _validate_synthetic_cto(data)
    assert run["package_commit"] == "not_applicable"
    assert data["cases"][0]["result"]["evidence_label"] == "UNVERIFIED"
    assert data["summary"]["observed_scenarios"] == 0

    data = _cto_document()
    _add_cto_run(data, arm="m4-previous-full-skiphow")
    _validate_synthetic_cto(data)
    assert data["cases"][0]["result"]["evidence_label"] == "UNVERIFIED"


def test_cto_receipt_rejects_invalid_scores_and_empty_required_context() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    run["task_success"] = "recorded"
    with pytest.raises(AssertionError, match="invalid CTO task_success"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    run = _add_cto_run(data)
    run["grader"] = ""
    with pytest.raises(AssertionError, match="empty CTO grader"):
        _validate_synthetic_cto(data)


def test_cto_receipt_identity_is_checked_against_the_candidate() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    seen: list[str] = []

    def identity_validator(receipt: dict) -> None:
        seen.append(receipt["run_id"])
        assert receipt["package_commit"] == "a" * 40

    validate_cto_instrument(data, identity_validator=identity_validator)
    assert seen == [run["run_id"]]

    run["package_commit"] = "d" * 40
    with pytest.raises(AssertionError):
        validate_cto_instrument(data, identity_validator=identity_validator)


def test_cto_instrument_rejects_prompt_and_fixture_mismatches() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    run["owner_prompt"] = "A different prompt."
    with pytest.raises(AssertionError, match="prompt mismatch"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    run = _add_cto_run(data)
    run["fixture"] = "another-fixture"
    with pytest.raises(AssertionError, match="fixture mismatch"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    run = _add_cto_run(data)
    run["fixture_snapshot"]["id"] = "another-fixture"
    with pytest.raises(AssertionError, match="snapshot mismatch"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    run = _add_cto_run(data)
    run["fixture_snapshot"]["setup"] = list(reversed(run["fixture_snapshot"]["setup"]))
    with pytest.raises(AssertionError, match="setup mismatch"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    run = _add_cto_run(data)
    run["fixture_snapshot"]["fixture_revision_sha256"] = "f" * 64
    with pytest.raises(AssertionError, match="fixture revision mismatch"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    run = _add_cto_run(data)
    run["fixture_snapshot"]["built_content"]["sha256"] = "e" * 64
    with pytest.raises(AssertionError, match="manifest hash mismatch"):
        _validate_synthetic_cto(data)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("host", "other-host", "unknown CTO host"),
        ("arm", "other-arm", "unknown CTO arm"),
        ("trial", "fourth", "unknown CTO trial"),
    ],
)
def test_cto_instrument_rejects_unknown_coverage_dimension(field: str, value: str, message: str) -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    run[field] = value
    with pytest.raises(AssertionError, match=message):
        _validate_synthetic_cto(data)


def test_failed_cto_run_cannot_upgrade_run_or_scenario() -> None:
    data = _cto_document()
    run = _add_cto_run(data, terminal_state="failed_to_reach_observable")
    _validate_synthetic_cto(data)
    assert run["evidence_label"] == "UNVERIFIED"
    assert data["cases"][0]["result"]["evidence_label"] == "UNVERIFIED"

    run["evidence_label"] = "Observed"
    with pytest.raises(AssertionError, match="run evidence label"):
        _validate_synthetic_cto(data)

    run["evidence_label"] = "UNVERIFIED"
    data["cases"][0]["result"]["evidence_label"] = "Observed"
    data["summary"]["observed_scenarios"] = 1
    with pytest.raises(AssertionError, match="scenario evidence label"):
        _validate_synthetic_cto(data)


def test_incomplete_cto_receipt_preserves_outcome_but_cannot_upgrade() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    run["end_state_artifacts"] = []
    run["receipt_complete"] = False
    run["evidence_label"] = "UNVERIFIED"
    data["cases"][0]["result"]["evidence_label"] = "UNVERIFIED"
    data["summary"]["observed_scenarios"] = 0
    data["summary"]["by_host"]["claude-code"]["observed_scenarios"] = 0
    _validate_synthetic_cto(data)
    assert run["terminal_state"] == "task_completed"

    run["receipt_complete"] = True
    with pytest.raises(AssertionError, match="receipt completeness"):
        _validate_synthetic_cto(data)


def test_cto_receipt_rejects_malformed_end_state_artifact() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    run["end_state_artifacts"][0]["sha256"] = "0" * 64
    with pytest.raises(AssertionError, match="invalid end-state artifact hash"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    run = _add_cto_run(data)
    run["end_state_artifacts"][0]["content"] = "different bytes"
    with pytest.raises(AssertionError, match="end-state artifact hash mismatch"):
        _validate_synthetic_cto(data)


def test_task_success_without_activation_cannot_upgrade_cto_evidence() -> None:
    data = _cto_document()
    run = _add_cto_run(data)
    run["activated"] = False
    run["activation_score"] = "fail"
    run["adherence"] = "not_applicable"
    data["cases"][0]["result"]["evidence_label"] = "UNVERIFIED"
    data["summary"]["observed_scenarios"] = 0
    data["summary"]["by_host"]["claude-code"]["observed_scenarios"] = 0
    _validate_synthetic_cto(data)

    data["cases"][0]["result"]["evidence_label"] = "Observed"
    data["summary"]["observed_scenarios"] = 1
    data["summary"]["by_host"]["claude-code"]["observed_scenarios"] = 1
    with pytest.raises(AssertionError, match="scenario evidence label"):
        _validate_synthetic_cto(data)


def test_one_host_cannot_complete_the_cto_suite_or_imply_host_parity() -> None:
    data = _cto_document()
    for case_index in range(len(data["cases"])):
        _add_cto_run(data, case_index, host="claude-code", trial="pilot")
        _add_cto_run(data, case_index, host="claude-code", trial="confirmation")
    _validate_synthetic_cto(data)
    assert data["suite_status"] == "partial"
    assert all(case["result"]["status"] == "partial" for case in data["cases"])

    data["suite_status"] = "complete"
    with pytest.raises(AssertionError, match="suite coverage status"):
        _validate_synthetic_cto(data)


def test_cto_instrument_rejects_stale_summary_and_duplicate_case_ids() -> None:
    data = _cto_document()
    _add_cto_run(data)
    data["summary"]["observed_scenarios"] = 0
    with pytest.raises(AssertionError, match="stale CTO evidence summary"):
        _validate_synthetic_cto(data)

    data = _cto_document()
    data["cases"][1]["id"] = data["cases"][0]["id"]
    with pytest.raises(AssertionError):
        _validate_synthetic_cto(data)


def test_host_smoke_instrument_keeps_each_capability_visible() -> None:
    data = json.loads((EVALS / "host-smoke.json").read_text(encoding="utf-8"))
    assert data["instrument"] == "host_smoke"
    assert data["package_under_test"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert data["scope"] == "external_candidate_receipts"
    assert "evidence_label" not in data
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
    assert tuple(data["receipt_fields"]) == host_checks.HOST_RECEIPT_FIELDS
    assert set(data["hosts"]) == {"claude-code", "codex"}
    receipt_fields = set(data["receipt_fields"])
    for host_id, host in data["hosts"].items():
        assert set(host["results"]) == expected_checks
        for check, result in host["results"].items():
            assert result["status"] in {"PASS", "FAIL", "UNVERIFIED"}
            if result["status"] == "UNVERIFIED":
                assert result["receipt"] is None
            else:
                assert isinstance(result["receipt"], dict)
                assert receipt_fields <= set(result["receipt"])
                receipt = result["receipt"]
                assert receipt["package_version"] == data["package_under_test"]
                assert re.fullmatch(r"[0-9a-f]{40}", receipt["package_commit"])
                assert re.fullmatch(r"[0-9a-f]{40}", receipt["package_tree"])
                assert re.fullmatch(r"[0-9a-f]{64}", receipt["package_payload_sha256"])
                assert receipt["check"] == check
                assert all(str(receipt[field]).strip() for field in receipt_fields)
                host_checks.validate_host_receipt(
                    receipt,
                    host=host_id,
                    check=check,
                    status=result["status"],
                )


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


def validate_case_results(
    data: dict,
    *,
    identity_validator=host_checks.validate_committed_package_identity,
    historical_identity_validator=host_checks.validate_committed_package_identity,
) -> None:
    arm_by_id = {arm["id"]: arm for arm in data["arms"]}
    terminal_states = data["terminal_states"]
    receipt_fields = set(data["run_record_fields"])
    run_ids: set[str] = set()
    transcript_hashes: set[str] = set()
    for case in data["cases"]:
        result = case["result"]
        assert set(result) == {"status", "evidence_label", "observed_arms", "arms_pending", "runs"}
        assert result["status"] in {"not_run", "partial", "run"}
        assert result["evidence_label"] in {"UNVERIFIED", "Observed"}
        seen_arms: set[str] = set()
        observed_arms: set[str] = set()
        for run in result["runs"]:
            assert isinstance(run, dict) and receipt_fields <= set(run), "incomplete case receipt"
            assert run["run_id"] not in run_ids, "duplicate case run id"
            run_ids.add(run["run_id"])
            assert re.fullmatch(r"[0-9a-f]{64}", str(run["transcript_hash"])), "invalid case transcript hash"
            assert run["transcript_hash"] not in transcript_hashes, "duplicate case transcript hash"
            transcript_hashes.add(run["transcript_hash"])
            assert run["case"] == case["id"], "case receipt mismatch"
            assert run["arm"] in arm_by_id, "unknown case receipt arm"
            assert run["trial"] in {"pilot", "confirmation", "tie_break"}
            assert run["host"] in {"claude-code", "codex"}
            assert run["owner_prompt"] == case["owner_prompt"]
            manifest_verified = validate_fixture_snapshot(run["fixture_snapshot"], case["fixture"])
            arm = arm_by_id[run["arm"]]
            package_fields = (
                "package_version",
                "package_commit",
                "package_tree",
                "package_payload_sha256",
            )
            if not arm["package_present"]:
                assert all(run[field] == "not_applicable" for field in package_fields)
            elif run["arm"] == "m4-previous-full-skiphow":
                historical_identity_validator(run, match_current=False)
            else:
                identity_validator(run)
            assert run["terminal_state"] in terminal_states
            eligible_terminal = terminal_states[run["terminal_state"]]["observed_eligible"]
            artifacts_retained = validate_end_state_artifacts(run["end_state_artifacts"])
            receipt_complete = manifest_verified and artifacts_retained
            assert isinstance(run["receipt_complete"], bool)
            assert run["receipt_complete"] is receipt_complete
            eligible = eligible_terminal and receipt_complete
            assert run["evidence_label"] == ("Observed" if eligible else "UNVERIFIED")
            assert run["activation_score"] in {"pass", "fail", "not_applicable"}
            assert run["adherence"] in {"pass", "fail", "not_applicable"}
            for score in ("task_success", "technical_quality", "proportionality", "completion_honesty"):
                assert run[score] in {"pass", "fail"}
            for field in (
                "host_version",
                "model_family",
                "permission_configuration",
                "sandbox_configuration",
                "activation_configuration",
                "instruction_configuration",
                "isolation_configuration",
                "control_run",
                "activation_event",
                "transcript_reference",
                "end_state",
                "test_receipts",
                "stopping_point",
                "grader",
                "redaction_notes",
            ):
                assert isinstance(run[field], str) and run[field].strip(), f"empty case receipt {field}"
            if receipt_complete:
                seen_arms.add(run["arm"])
            if eligible:
                observed_arms.add(run["arm"])
        expected_pending = tuple(arm for arm in REQUIRED_ARMS if arm not in seen_arms)
        expected_observed = tuple(arm for arm in REQUIRED_ARMS if arm in observed_arms)
        assert tuple(result["arms_pending"]) == expected_pending
        assert tuple(result["observed_arms"]) == expected_observed
        expected_status = "not_run" if not result["runs"] else "run" if not expected_pending else "partial"
        assert result["status"] == expected_status
        assert result["evidence_label"] == ("Observed" if expected_observed else "UNVERIFIED")


def test_case_results_are_derived_without_claiming_unrun_arms() -> None:
    validate_case_results(corpus())


def _add_case_run(data: dict, *, arm: str = "m1-explicit-skiphow") -> dict:
    case = data["cases"][0]
    run_id = f"{case['id']}-{arm}-pilot"
    run = {field: "recorded" for field in data["run_record_fields"]}
    run.update(
        {
            "run_id": run_id,
            "case": case["id"],
            "arm": arm,
            "trial": "pilot",
            "package_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
            "package_commit": "a" * 40,
            "package_tree": "b" * 40,
            "package_payload_sha256": "c" * 64,
            "host": "claude-code",
            "owner_prompt": case["owner_prompt"],
            "fixture_snapshot": synthetic_fixture_snapshot(case["fixture"]),
            "subsequent_answers": case["subsequent_answers"],
            "activated": True,
            "references_loaded": [],
            "transcript_hash": hashlib.sha256(run_id.encode()).hexdigest(),
            "destination_receipts": {},
            "end_state_artifacts": synthetic_end_state_artifacts(),
            "conditions_observed": {},
            "expected_events_observed": [],
            "forbidden_events_observed": [],
            "activation_score": "pass",
            "adherence": "pass",
            "task_success": "pass",
            "technical_quality": "pass",
            "proportionality": "pass",
            "completion_honesty": "pass",
            "receipt_complete": True,
            "terminal_state": "task_completed",
            "measures": {},
            "usage": {},
            "evidence_label": "Observed",
        }
    )
    if arm == "m0-base-host":
        for field in ("package_version", "package_commit", "package_tree", "package_payload_sha256"):
            run[field] = "not_applicable"
        run["activated"] = False
        run["activation_score"] = "not_applicable"
    case["result"] = {
        "status": "partial",
        "evidence_label": "Observed",
        "observed_arms": [arm],
        "arms_pending": [candidate for candidate in REQUIRED_ARMS if candidate != arm],
        "runs": [run],
    }
    return run


def test_case_result_accepts_one_arm_without_claiming_full_coverage() -> None:
    data = corpus()
    _add_case_run(data)
    validate_case_results(
        data,
        identity_validator=lambda _: None,
        historical_identity_validator=lambda *_args, **_kwargs: None,
    )


def test_base_case_receipt_cannot_carry_candidate_identity() -> None:
    data = corpus()
    run = _add_case_run(data, arm="m0-base-host")
    run["package_commit"] = "a" * 40
    with pytest.raises(AssertionError):
        validate_case_results(
            data,
            identity_validator=lambda _: None,
            historical_identity_validator=lambda *_args, **_kwargs: None,
        )


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
