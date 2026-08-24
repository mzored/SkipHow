"""Contract tests for the portable behavioral eval corpus."""

import importlib.util
import json
from pathlib import Path
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
        security = next(item for item in scenarios if item["id"] == "security-sensitive-change")
        self.assertFalse(security["assertions"]["durable"])
        long_low_risk = next(item for item in scenarios if item["id"] == "durability-not-risk")
        self.assertTrue(long_low_risk["assertions"]["durable"])

    def test_structured_evaluation_reports_only_mismatches(self) -> None:
        expected = {
            name: False if expected_type is bool else name
            for name, expected_type in evals.REQUIRED_ASSERTIONS.items()
        }
        self.assertEqual([], evals.evaluate(expected, expected))
        changed = dict(expected, route="wrong")
        self.assertEqual(["route"], evals.evaluate(changed, expected))

    def test_claude_adapter_extracts_schema_validated_output(self) -> None:
        response = {"route": "fix", "reason": "bounded repair"}
        payload = '{"type":"result","structured_output":' + json.dumps(response) + "}"
        self.assertEqual(response, claude_evals.structured_response(payload))

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
