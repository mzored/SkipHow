"""Contract tests for routing, activation, and outcome evals."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile


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


def missing_load_bearing_rules(text: str) -> list[str]:
    rules = (
        "Analysis, research, review, diagnosis-only, and planning requests are read-only",
        "For an ordinary clear change, create an ephemeral brief",
        "`CAMPAIGN` is an internal execution shape, not an intent",
        "Inspect a tracker only after persistence is requested",
    )
    return [rule for rule in rules if rule not in text]


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
    assert by_id["authorization-small-fix"]["execution_shape"] == "execute"
    assert by_id["optional-validator"]["testing"] == "UNVERIFIED"
    assert by_id["scoped-rereview"]["review"] == "scoped-rereview"


def test_activation_and_outcome_corpora_are_representative() -> None:
    activation, outcome = outcomes.validate_corpora()
    categories = {row["category"] for row in activation["scenarios"]}
    assert categories == {"direct", "indirect", "follow-up", "negative", "boundary"}
    assert any(not row["activate"] for row in activation["scenarios"])
    by_id = {row["id"]: row for row in outcome["scenarios"]}
    assert by_id["analysis-only"]["graders"]["changed"] == []
    assert ".skiphow/runs" in by_id["tiny-fix"]["graders"]["absent"]
    assert by_id["local-capture"]["graders"]["changed"] == [".skiphow/inbox.md"]


def test_policy_mutations_break_the_load_bearing_rule_check() -> None:
    skill = (ROOT / "plugins/skiphow/skills/skiphow/SKILL.md").read_text(encoding="utf-8")
    assert missing_load_bearing_rules(skill) == []
    for rule in (
        "Analysis, research, review, diagnosis-only, and planning requests are read-only",
        "For an ordinary clear change, create an ephemeral brief",
        "`CAMPAIGN` is an internal execution shape, not an intent",
        "Inspect a tracker only after persistence is requested",
    ):
        assert rule in missing_load_bearing_rules(skill.replace(rule, ""))


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
        evals.stage_runtime(candidate, runtime)
        assert (runtime / "plugins/skiphow/skills/skiphow/SKILL.md").is_file()
        assert not any(runtime.rglob("behavioral_scenarios.json"))


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
