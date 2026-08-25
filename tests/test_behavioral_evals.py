"""Contract tests for routing, activation, and outcome evals."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evals = load_module("run_codex_evals", ROOT / "scripts/run_codex_evals.py")
claude_evals = load_module("run_claude_evals", ROOT / "scripts/run_claude_evals.py")
outcomes = load_module("run_outcome_evals", ROOT / "scripts/run_outcome_evals.py")


def test_routing_corpus_covers_the_product_contract() -> None:
    scenarios = evals.load_corpus(evals.DEFAULT_CORPUS)["scenarios"]
    assert len(scenarios) >= 20
    intents = {row["assertions"]["intent"] for row in scenarios}
    assert intents == {"ANSWER", "CAPTURE", "DECIDE", "CHANGE", "REPAIR", "CONTINUE"}
    by_id = {row["id"]: row["assertions"] for row in scenarios}
    assert by_id["clear-feature-direct"]["execution_shape"] == "execute"
    assert not by_id["clear-feature-direct"]["tracker_touched"]
    assert not by_id["clear-feature-direct"]["product_acceptance"]
    assert by_id["analysis-read-only"]["tracker_touched"] is False
    assert by_id["unclear-defect"]["execution_shape"] == "diagnose-then-execute"
    assert by_id["campaign-migration"]["execution_shape"] == "campaign"
    assert by_id["bounded-parallel-execute"]["execution_shape"] == "execute"
    assert not by_id["bounded-parallel-execute"]["durable"]
    assert by_id["authorization-small-fix"]["execution_shape"] == "execute"
    assert by_id["optional-validator"]["testing"] == "UNVERIFIED"
    assert by_id["scoped-rereview"]["review"] == "scoped-rereview"


def test_activation_and_outcome_corpora_are_representative() -> None:
    activation, outcome = outcomes.validate_corpora()
    categories = {row["category"] for row in activation["scenarios"]}
    assert categories == {"direct", "indirect", "follow-up", "negative", "boundary"}
    assert any(not row["activate"] for row in activation["scenarios"])
    by_id = {row["id"]: row for row in outcome["scenarios"]}
    assert len(by_id) >= 24
    assert {row.get("host_profile") for row in outcome["scenarios"] if row.get("host_profile")} >= {
        "no_delegation", "no_optional_verifier", "no_protected_action", "local_only"
    }
    analysis = by_id["analysis-only"]["graders"]
    assert analysis["files"] == [{"path": "app.txt", "unchanged": True}]
    assert ".skiphow/runs" in by_id["trivial-fix"]["graders"]["side_effects"]["forbidden_paths"]
    assert by_id["optional-verifier-unavailable"]["graders"]["final"]["contains_any"] == [
        "unverified",
        "unavailable",
    ]
    assert by_id["local-capture"]["graders"]["files"][0]["path"] == ".skiphow/inbox.md"
    assert "--limit 10000" in by_id["project-over-100-no-duplicate"]["graders"]["side_effects"]["required_commands"]
    assert "gh issue develop" in by_id["record-delivery-provenance"]["graders"]["side_effects"]["forbidden_commands"]
    assert by_id["doctor-proof-separation"]["graders"]["files"][0]["json_equals"]["value"] == "UNVERIFIED"
    assert "fully supported" in by_id["host-receipt-support-claims"]["graders"]["files"][0]["not_contains"]
    side_effect_keys = {
        key
        for scenario in outcome["scenarios"]
        for key in scenario["graders"]["side_effects"]
    }
    assert {
        "forbidden_paths", "forbidden_commands", "max_owner_questions",
        "max_tracker_touches", "max_campaign_starts", "max_durable_documents",
        "max_subagents", "full_reviews", "rereviews",
    } <= side_effect_keys


def test_policy_mutations_break_the_load_bearing_rule_check() -> None:
    document = json.loads(outcomes.MUTATIONS.read_text(encoding="utf-8"))
    mutations = document["mutations"]
    assert len(mutations) >= 5
    assert outcomes.runtime_policy_failures(ROOT) == []
    for mutation in mutations:
        with tempfile.TemporaryDirectory() as temporary:
            mutant_root = Path(temporary)
            for row in mutations:
                source = Path(row["source"])
                target = mutant_root / source
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / source, target)
            outcomes.apply_policy_mutation(mutant_root, mutation)
            assert outcomes.runtime_policy_failures(mutant_root) == [mutation["rule"]]


def test_outcome_grader_hard_gates_semantics_commands_and_side_effects(tmp_path: Path) -> None:
    fixture = {"app.py": "old\n"}
    (tmp_path / "app.py").write_text("new behavior\n", encoding="utf-8")
    graders = {
        "files": [{"path": "app.py", "changed": True, "contains": ["behavior"]}],
        "behavior": [{"command": [sys.executable, "-c", "print('works')"], "stdout": "works"}],
        "commands": [{"matches": "pytest", "passed": True}],
        "final": {"contains": ["verified"]},
        "side_effects": {"forbidden_paths": [".skiphow"], "max_owner_questions": 0},
    }
    observation = {
        "commands": [{"command": "pytest -q", "returncode": 0}],
        "final_response": "Change verified.",
        "metrics": {"owner_questions": 0},
    }
    assert outcomes.grade(tmp_path, fixture, graders, observation) == []
    observation["commands"][0]["returncode"] = 1
    observation["metrics"]["owner_questions"] = 1
    failures = outcomes.grade(tmp_path, fixture, graders, observation)
    assert "required command did not pass: pytest" in failures
    assert "expected owner_questions<=0, got 1" in failures


def test_unavailable_is_a_semantic_limitation(tmp_path: Path) -> None:
    graders = {
        "files": [],
        "final": {"contains_any": ["unavailable"], "required_limitation": True},
        "side_effects": {},
    }
    observation = {"final_response": "The optional verifier is unavailable.", "metrics": {}}
    assert outcomes.grade(tmp_path, {}, graders, observation) == []


def test_outcome_grader_rejects_unaccounted_scope(tmp_path: Path) -> None:
    outcomes.write_fixture(tmp_path, {"app.py": "old\n", "unrelated.py": "keep\n"})
    (tmp_path / "app.py").write_text("new\n", encoding="utf-8")
    (tmp_path / "unrelated.py").write_text("changed too\n", encoding="utf-8")
    graders = {"files": [{"path": "app.py", "changed": True}], "side_effects": {}}
    assert outcomes.grade(tmp_path, {"app.py": "old\n", "unrelated.py": "keep\n"}, graders) == [
        "unexpected out-of-scope change unrelated.py"
    ]


def test_empty_outcome_fixture_has_a_clean_initial_commit(tmp_path: Path) -> None:
    outcomes.write_fixture(tmp_path, {})
    identity = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert identity.returncode == 0
    assert subprocess.run(
        ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True, check=False
    ).stdout == ""


def test_structural_and_negative_content_graders(tmp_path: Path) -> None:
    (tmp_path / "receipt.json").write_text('{"status":"UNVERIFIED"}\n', encoding="utf-8")
    (tmp_path / "SUPPORT.md").write_text("Package proof is UNVERIFIED.\n", encoding="utf-8")
    fixture = {
        "receipt.json": '{"status":"UNVERIFIED"}\n',
        "SUPPORT.md": "old claim\n",
    }
    graders = {
        "files": [
            {"path": "receipt.json", "unchanged": True, "json_equals": {"path": "status", "value": "UNVERIFIED"}},
            {"path": "SUPPORT.md", "changed": True, "not_contains": ["fully supported"]},
        ],
        "side_effects": {},
    }
    assert outcomes.grade(tmp_path, fixture, graders) == []
    (tmp_path / "SUPPORT.md").write_text("fully supported\n", encoding="utf-8")
    assert "SUPPORT.md contains forbidden text 'fully supported'" in outcomes.grade(tmp_path, fixture, graders)


def test_multi_trial_aggregation_uses_pass_rate_and_medians() -> None:
    records = [
        {"id": "case", "returncode": 0, "failures": [], "metrics": {"elapsed_seconds": 9, "cost": 0.9}},
        {"id": "case", "returncode": 1, "failures": ["bad"], "metrics": {"elapsed_seconds": 1, "cost": 0.1}},
        {"id": "case", "returncode": 0, "failures": [], "metrics": {"elapsed_seconds": 5, "cost": 0.5}},
    ]
    aggregate = outcomes.aggregate_trials(records)["case"]
    assert aggregate == {"trials": 3, "passed": 2, "pass_rate": 2 / 3, "median_elapsed_seconds": 5, "median_cost": 0.5}


def test_live_command_timeout_becomes_a_recordable_failure(tmp_path: Path) -> None:
    error = subprocess.TimeoutExpired(["host"], 7, output=b"partial output")
    with patch.object(outcomes.subprocess, "run", side_effect=error):
        completed = outcomes.run(["host"], cwd=tmp_path, env={}, timeout=7)
    assert completed.returncode == 124
    assert completed.stdout == "partial output"
    assert completed.stderr == "timed out after 7 seconds"


def test_release_receipt_binds_candidate_host_version_model_and_profile() -> None:
    records = [{"id": "case", "returncode": 0, "failures": [], "metrics": {"elapsed_seconds": 1}}]
    receipt = outcomes.build_receipt(
        commit="abc", tree="def", host="codex", cli_version="codex-cli 9.9",
        executable="/opt/bin/codex", installation_source="isolated staged candidate",
        model="gpt-eval", host_profile="release-ci",
        eval_profile="release", trials=1, records=records,
    )
    assert receipt["candidate"] == {"commit": "abc", "tree": "def"}
    assert receipt["execution"] == {
        "host": "codex", "cli_version": "codex-cli 9.9", "executable": "/opt/bin/codex",
        "installation_source": "isolated staged candidate",
        "model": "gpt-eval", "host_profile": "release-ci", "eval_profile": "release",
    }


def test_paid_outcomes_are_opt_in_and_release_requires_three_trials() -> None:
    offline = subprocess.run([sys.executable, str(ROOT / "scripts/run_outcome_evals.py")], capture_output=True, text=True, check=False)
    assert offline.returncode == 0
    assert "24 outcome scenarios offline" in offline.stdout
    invalid = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_outcome_evals.py"), "--execute", "--host", "codex", "--model", "eval-model", "--host-profile-label", "ci", "--profile", "release", "--trials", "2", "--output", "/tmp/unused-eval-receipt.json"],
        capture_output=True, text=True, check=False,
    )
    assert invalid.returncode == 2
    assert "release requires at least three" in invalid.stderr
    missing_receipt = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_outcome_evals.py"), "--execute", "--host", "codex", "--model", "eval-model", "--host-profile-label", "ci", "--profile", "release", "--trials", "3"],
        capture_output=True, text=True, check=False,
    )
    assert missing_receipt.returncode == 2
    assert "requires --output" in missing_receipt.stderr


def test_claude_command_evidence_is_captured_and_tool_counts_are_unavailable(tmp_path: Path) -> None:
    command_log = tmp_path / "commands"
    command_log.write_text("0\tpytest -q\n", encoding="utf-8")
    completed = subprocess.CompletedProcess([], 0, json.dumps({"result": "done", "usage": {"input_tokens": 3}}), "")
    observation = outcomes._observation("claude", completed, 1.0, command_log, tmp_path / "gh", tmp_path)
    assert observation["commands"] == [{"command": "pytest -q", "returncode": 0}]
    assert observation["metrics"]["command_evidence"] == "SHIMMED_COMMANDS_ONLY"
    assert observation["metrics"]["tool_evidence"] == "UNAVAILABLE"
    assert observation["metrics"]["subagents"] is None
    graders = {"files": [], "commands": [{"matches": "pytest", "passed": True}], "side_effects": {"max_subagents": 0}}
    assert outcomes.grade(tmp_path, {}, graders, observation) == [
        "required metric unavailable: subagents"
    ]


def test_structured_evaluation_reports_only_mismatches() -> None:
    expected = {
        name: False if expected_type is bool else "none" if name == "escalation" else name
        for name, expected_type in evals.REQUIRED_ASSERTIONS.items()
    }
    assert evals.evaluate(expected, expected) == []
    assert evals.evaluate(dict(expected, intent="wrong"), expected) == ["intent"]


def test_escalation_requires_a_complete_brief() -> None:
    expected = {
        name: False if expected_type is bool else "owner-decision" if name == "escalation" else name
        for name, expected_type in evals.REQUIRED_ASSERTIONS.items()
    }
    assert evals.evaluate(expected, expected) == list(evals.ESCALATION_BRIEF_FIELDS)
    complete = dict(
        expected,
        recommendation="Choose the safer retention policy.",
        evidence="The current decision does not choose one.",
        consequence_of_waiting="Implementation cannot finalize the data flow.",
        decision_or_action_needed="Choose whether customer data is hidden or deleted.",
    )
    assert evals.evaluate(complete, expected) == []


def test_response_schema_uses_public_intents() -> None:
    schema = json.loads(evals.RESPONSE_SCHEMA.read_text(encoding="utf-8"))
    assert "intent" in schema["required"]
    assert set(schema["properties"]["intent"]["enum"]) == {
        "ANSWER", "CAPTURE", "DECIDE", "CHANGE", "REPAIR", "CONTINUE"
    }
    assert set(schema["properties"]["escalation"]["enum"]) == evals.ESCALATION_CLASSES


def test_claude_adapter_extracts_schema_validated_output() -> None:
    response = {"intent": "REPAIR", "reason": "bounded repair"}
    payload = '{"type":"result","structured_output":' + json.dumps(response) + "}"
    assert claude_evals.structured_response(payload) == response


def test_efficiency_metrics_remain_secondary() -> None:
    codex_output = "\n".join(
        (
            '{"type":"item.completed","item":{"type":"command_execution"}}',
            '{"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":3}}',
        )
    )
    assert evals.codex_metrics(codex_output) == {
        "tool_calls": 1,
        "usage": {"input_tokens": 12, "output_tokens": 3},
    }
    claude_output = json.dumps(
        {"structured_output": {}, "usage": {"input_tokens": 7}, "num_turns": 1}
    )
    assert claude_evals.claude_metrics(claude_output) == {
        "usage": {"input_tokens": 7},
        "num_turns": 1,
    }


def test_runtime_staging_excludes_eval_oracles() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        candidate = root / "candidate"
        runtime = root / "runtime"
        for relative in (".agents", ".claude-plugin", "adapters"):
            directory = candidate / relative
            directory.mkdir(parents=True)
            (directory / "marker.txt").write_text("runtime\n", encoding="utf-8")
        plugin = candidate / "plugins" / "skiphow"
        (plugin / "skills" / "skiphow").mkdir(parents=True)
        (plugin / "skills" / "skiphow" / "SKILL.md").write_text(
            "---\nname: skiphow\ndescription: route\n---\n", encoding="utf-8"
        )
        (plugin / "evals").mkdir()
        (plugin / "evals" / "behavioral_scenarios.json").write_text("{}\n", encoding="utf-8")
        (plugin / "evals" / "outcome_scenarios.json").write_text("{}\n", encoding="utf-8")
        (plugin / "evals" / "policy_mutations.json").write_text("{}\n", encoding="utf-8")
        (plugin / "evals" / "host_profiles.json").write_text("{}\n", encoding="utf-8")
        evals.stage_runtime(candidate, runtime)
        assert (runtime / "plugins/skiphow/skills/skiphow/SKILL.md").is_file()
        assert not any(runtime.rglob("*_scenarios.json"))
        assert not any(runtime.rglob("policy_mutations.json"))
        assert not any(runtime.rglob("host_profiles.json"))


def test_outcome_prompts_do_not_disclose_policy_oracles() -> None:
    prompts = "\n".join(row["prompt"] for row in outcomes.validate_corpora()[1]["scenarios"])
    for leaked in (
        "do not create a replacement verifier",
        "without restarting review",
        "must not narrow this request",
        "do not turn speculation into follow-up",
        "start a campaign",
    ):
        assert leaked not in prompts.lower()


def test_live_prompts_do_not_repeat_the_routing_oracle_and_claude_keeps_tools() -> None:
    codex_source = (ROOT / "scripts/run_codex_evals.py").read_text(encoding="utf-8")
    claude_source = (ROOT / "scripts/run_claude_evals.py").read_text(encoding="utf-8")
    leaked = "Use execute as the normal technical shape"
    assert leaked not in codex_source
    assert leaked not in claude_source
    assert '"--tools",\n                    ""' not in claude_source
    for source in (codex_source, claude_source):
        assert "candidate_commit" in source
        assert "candidate_tree" in source
