"""Contract tests for the portable behavioral eval corpus."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_codex_evals.py"
SPEC = importlib.util.spec_from_file_location("run_codex_evals", SCRIPT)
assert SPEC and SPEC.loader
evals = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evals)
CLAUDE_SCRIPT = ROOT / "scripts/run_claude_evals.py"
CLAUDE_SPEC = importlib.util.spec_from_file_location("run_claude_evals", CLAUDE_SCRIPT)
assert CLAUDE_SPEC and CLAUDE_SPEC.loader
claude_evals = importlib.util.module_from_spec(CLAUDE_SPEC)
CLAUDE_SPEC.loader.exec_module(claude_evals)


class BehavioralEvalTests(unittest.TestCase):
    def test_corpus_is_machine_valid_and_representative(self) -> None:
        corpus = evals.load_corpus(evals.DEFAULT_CORPUS)
        scenarios = corpus["scenarios"]
        self.assertGreaterEqual(len(scenarios), 20)
        prompts = "\n".join(item["prompt"] for item in scenarios).lower()
        for topic in ("approved", "board", "product contract", "days"):
            self.assertIn(topic, prompts)
        reviews = {item["assertions"]["review"] for item in scenarios}
        self.assertIn("independent", reviews)
        self.assertTrue(any(item["assertions"]["owner_question"] for item in scenarios))
        escalations = {item["assertions"]["escalation"] for item in scenarios}
        self.assertIn("owner-decision", escalations)
        self.assertIn("protected-action", escalations)
        security = next(item for item in scenarios if item["id"] == "security-sensitive-change")
        self.assertFalse(security["assertions"]["durable"])
        self.assertEqual("execute", security["assertions"]["execution_shape"])
        long_low_risk = next(item for item in scenarios if item["id"] == "durability-not-risk")
        self.assertTrue(long_low_risk["assertions"]["durable"])
        self.assertEqual("campaign", long_low_risk["assertions"]["execution_shape"])
        acceptance_mismatch = next(item for item in scenarios if item["id"] == "acceptance-mismatch")
        self.assertEqual("cto", acceptance_mismatch["assertions"]["route"])
        by_id = {item["id"]: item["assertions"] for item in scenarios}
        self.assertEqual("persist-follow-up", by_id["independent-finding-persisted"]["ceremony"])
        self.assertEqual("link-duplicate", by_id["duplicate-finding-linked"]["ceremony"])
        self.assertEqual("scoped-rereview", by_id["review-fix-scoped-rereview"]["review"])
        self.assertEqual("independent", by_id["review-fix-material-redesign"]["review"])
        self.assertEqual("resolve-current", by_id["resolved-in-scope-finding"]["ceremony"])
        self.assertEqual("dismiss-finding", by_id["dismissed-speculative-finding"]["ceremony"])
        self.assertEqual("UNVERIFIED", by_id["optional-validator-unavailable"]["testing"])
        self.assertEqual(
            "external-prerequisite",
            by_id["required-validator-unavailable"]["escalation"],
        )
        self.assertFalse(by_id["acceptance-internal-delta"]["product_acceptance"])
        self.assertTrue(by_id["acceptance-semantic-delta"]["product_acceptance"])
        self.assertFalse(by_id["tiny-css-fix"]["tracker_touched"])
        self.assertFalse(by_id["untracked-coherent-feature"]["tracker_touched"])
        self.assertTrue(by_id["independent-finding-persisted"]["tracker_touched"])
        self.assertEqual("diagnose-only", by_id["diagnosis-only"]["execution_shape"])
        self.assertEqual("prototype", by_id["prototype-design-question"]["ceremony"])
        self.assertEqual("merge-conflict", by_id["merge-conflict-intent"]["ceremony"])
        self.assertEqual("human-action-handoff", by_id["human-action-handoff"]["ceremony"])
        self.assertEqual("setup", by_id["github-project-setup"]["route"])
        self.assertEqual("campaign", by_id["campaign-fog-of-war"]["execution_shape"])

    def test_structured_evaluation_reports_only_mismatches(self) -> None:
        expected = {
            name: False if expected_type is bool else "none" if name == "escalation" else name
            for name, expected_type in evals.REQUIRED_ASSERTIONS.items()
        }
        self.assertEqual([], evals.evaluate(expected, expected))
        changed = dict(expected, route="wrong")
        self.assertEqual(["route"], evals.evaluate(changed, expected))

    def test_non_none_escalation_requires_a_complete_brief(self) -> None:
        expected = {
            name: False if expected_type is bool else "owner-decision" if name == "escalation" else name
            for name, expected_type in evals.REQUIRED_ASSERTIONS.items()
        }
        mismatches = evals.evaluate(expected, expected)
        self.assertEqual(list(evals.ESCALATION_BRIEF_FIELDS), mismatches)

        complete = dict(
            expected,
            recommendation="Choose the safer retention policy.",
            evidence="The Product Contract does not choose a retention policy.",
            consequence_of_waiting="The implementation cannot finalize the data flow.",
            decision_or_action_needed="Approve hiding or deleting customer data.",
        )
        self.assertEqual([], evals.evaluate(complete, expected))

    def test_response_schema_requires_a_brief_only_for_escalations(self) -> None:
        schema = json.loads(evals.RESPONSE_SCHEMA.read_text(encoding="utf-8"))
        self.assertIn("escalation", schema["required"])
        self.assertEqual(
            evals.ESCALATION_CLASSES,
            set(schema["properties"]["escalation"]["enum"]),
        )
        self.assertEqual(
            list(evals.ESCALATION_BRIEF_FIELDS),
            schema["allOf"][0]["else"]["required"],
        )

    def test_claude_adapter_extracts_schema_validated_output(self) -> None:
        response = {"route": "fix", "reason": "bounded repair"}
        payload = '{"type":"result","structured_output":' + json.dumps(response) + "}"
        self.assertEqual(response, claude_evals.structured_response(payload))

    def test_live_metric_extractors_keep_efficiency_signals_secondary(self) -> None:
        codex_output = "\n".join(
            (
                '{"type":"item.completed","item":{"type":"command_execution"}}',
                '{"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":3}}',
            )
        )
        self.assertEqual(
            {"tool_calls": 1, "usage": {"input_tokens": 12, "output_tokens": 3}},
            evals.codex_metrics(codex_output),
        )
        claude_output = json.dumps(
            {"structured_output": {}, "usage": {"input_tokens": 7}, "num_turns": 1}
        )
        self.assertEqual(
            {"usage": {"input_tokens": 7}, "num_turns": 1},
            claude_evals.claude_metrics(claude_output),
        )

    def test_codex_live_runner_binds_evidence_to_a_clean_snapshot(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            '"status", "--porcelain"',
            '"HEAD^{tree}"',
            '"clone", "--quiet", "--shared", "--no-checkout"',
            '"candidate_commit": candidate_commit',
            '"candidate_tree": candidate_tree',
        ):
            self.assertIn(required, source)

    def test_staged_runtime_excludes_behavioral_oracle(self) -> None:
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
                "---\nname: skiphow\ndescription: route\n---\n",
                encoding="utf-8",
            )
            (plugin / "evals").mkdir()
            (plugin / "evals" / "behavioral_scenarios.json").write_text(
                "{}\n", encoding="utf-8"
            )
            evals.stage_runtime(candidate, runtime)
            self.assertTrue(
                (runtime / "plugins/skiphow/skills/skiphow/SKILL.md").is_file()
            )
            self.assertFalse(any(runtime.rglob("behavioral_scenarios.json")))

    def test_claude_live_runner_uses_snapshot_runtime_and_isolated_config(self) -> None:
        source = CLAUDE_SCRIPT.read_text(encoding="utf-8")
        for required in (
            "shared.snapshot_candidate(output_dir)",
            "shared.stage_runtime(candidate_dir, runtime_dir)",
            'environment["CLAUDE_CONFIG_DIR"]',
            "cwd=evaluation_dir",
            '"candidate_commit": candidate_commit',
            '"candidate_tree": candidate_tree',
        ):
            self.assertIn(required, source)
