"""Contract tests for the portable behavioral eval corpus."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_codex_evals.py"
SPEC = importlib.util.spec_from_file_location("run_codex_evals", SCRIPT)
assert SPEC and SPEC.loader
evals = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evals)


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

    def test_structured_evaluation_reports_only_mismatches(self) -> None:
        expected = {
            name: False if expected_type is bool else name
            for name, expected_type in evals.REQUIRED_ASSERTIONS.items()
        }
        self.assertEqual([], evals.evaluate(expected, expected))
        changed = dict(expected, route="wrong")
        self.assertEqual(["route"], evals.evaluate(changed, expected))
