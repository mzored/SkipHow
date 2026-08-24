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
        long_low_risk = next(item for item in scenarios if item["id"] == "durability-not-risk")
        self.assertTrue(long_low_risk["assertions"]["durable"])
        acceptance_mismatch = next(item for item in scenarios if item["id"] == "acceptance-mismatch")
        self.assertEqual("cto", acceptance_mismatch["assertions"]["route"])

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
