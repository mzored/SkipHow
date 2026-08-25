"""Contracts for deterministic and opt-in live evaluation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from evals.graders.outcome import SUPPORTED_OPERATORS, grade_scenario
from evals.live import fixtures as live_fixtures
from evals.live import provider_adapter, run as live_runner


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = ROOT / "evals/scenarios"
REQUIRED_SCENARIOS = {
    "simple-anti-ceremony",
    "nontechnical-owner",
    "reuse-first",
    "trivial-local-logic",
    "unknown-bug",
    "batch-intake",
    "no-orphan-finding",
    "scoped-re-review",
    "verification-ceiling",
    "long-campaign",
    "github-lifecycle",
    "idempotent-rerun",
    "pause-resume-cancel",
    "prompt-injection",
    "protected-action",
    "model-routing",
    "escalation",
    "scope-restraint",
    "context-handoff",
    "cleanup-safety",
}


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def run_live(*arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "evals/live/run.py", *arguments],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_required_scenarios_are_complete_and_gradeable() -> None:
    manifests = [load(path) for path in sorted(SCENARIO_ROOT.glob("*.json"))]
    assert {manifest["id"] for manifest in manifests} == REQUIRED_SCENARIOS
    for manifest in manifests:
        assert manifest["schema_version"] == 1
        assert manifest["intent"]
        assert manifest["fixture"]
        grading = manifest["grading"]
        assert isinstance(grading, dict)
        assert grading["pass_condition"] == "all_required_outcomes_and_no_forbidden_effects"
        rules = grading["required_outcomes"] + grading["forbidden_effects"]
        assert grading["required_outcomes"]
        assert grading["forbidden_effects"]
        assert all(rule["operator"] in SUPPORTED_OPERATORS for rule in rules)
        observations = {rule["id"]: rule["expected"] for rule in grading["required_outcomes"]}
        evidence = {
            item
            for rule in rules
            for item in rule["evidence"]
        }
        for rule in grading["forbidden_effects"]:
            expected = rule["expected"]
            observations[rule["id"]] = not expected if isinstance(expected, bool) else 0
        receipt = {
            "scenario_id": manifest["id"],
            "observations": observations,
            "evidence": sorted(evidence),
        }
        assert grade_scenario(manifest, receipt).passed


def test_rule_registry_has_failure_eval_and_revalidation_state() -> None:
    registry = load(ROOT / "evals/deterministic/rules.json")
    assert registry["schema_version"] == 1
    rules = registry["rules"]
    assert isinstance(rules, list) and rules
    assert len({rule["rule_id"] for rule in rules}) == len(rules)
    for rule in rules:
        assert rule["owner_file"]
        assert rule["failure_mode"]
        assert set(rule["eval_scenarios"]).issubset(REQUIRED_SCENARIOS)
        assert rule["eval_scenarios"]
        assert rule["measured_effect"]["status"] in {"VERIFIED", "UNVERIFIED"}
        assert rule["last_revalidated"]["status"] in {"VERIFIED", "UNVERIFIED"}


def test_live_harness_dry_run_never_invokes_adapter(tmp_path: Path) -> None:
    marker = tmp_path / "adapter-was-called"
    config = load(ROOT / "evals/fixtures/live_config.json")
    adapters = config["adapters"]
    assert isinstance(adapters, dict)
    for adapter in adapters.values():
        assert isinstance(adapter, dict)
        adapter["command"] = [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"]
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    for mode in ("all-frontier", "all-balanced", "adaptive"):
        completed = run_live("--config", str(config_path), "--routing-mode", mode)
        assert completed.returncode == 0, completed.stderr
        assert json.loads(completed.stdout)["record_type"] == "plan"
    assert not marker.exists()


def test_live_harness_requires_explicit_opt_in_and_budget(tmp_path: Path) -> None:
    arguments = (
        "--config",
        "evals/fixtures/live_config.json",
        "--routing-mode",
        "all-frontier",
        "--live",
        "--budget-usd",
        "0.04",
        "--output-dir",
        str(tmp_path),
    )
    completed = run_live(*arguments)
    assert completed.returncode == 2
    assert "SKIPHOW_LIVE_EVALS=1" in completed.stderr
    assert not list(tmp_path.iterdir())


def test_live_fixture_writes_versioned_redacted_receipts(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["SKIPHOW_LIVE_EVALS"] = "1"
    completed = run_live(
        "--config",
        "evals/fixtures/live_config.json",
        "--routing-mode",
        "adaptive",
        "--live",
        "--budget-usd",
        "0.02",
        "--output-dir",
        str(tmp_path),
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout)
    summary = load(Path(output["summary"]))
    assert summary["status"] == "completed"
    assert summary["completed_trials"] == 2
    assert summary["candidate"] == load(ROOT / "evals/fixtures/live_config.json")["candidate"]
    receipt_text = Path(output["receipts"]).read_text(encoding="utf-8")
    assert "This prompt must not appear in receipts." not in receipt_text
    records = [json.loads(line) for line in receipt_text.splitlines()]
    trials = [record for record in records if record["record_type"] == "trial"]
    assert len(trials) == 2
    assert all(trial["provider"] == "fixture" for trial in trials)
    assert all(trial["model_version"] == "1" for trial in trials)


def test_release_mode_requires_the_exact_registered_scenario_set() -> None:
    completed = run_live(
        "--config",
        "evals/fixtures/live_config.json",
        "--routing-mode",
        "adaptive",
        "--release",
    )
    assert completed.returncode == 2
    assert "exact 20-scenario registry" in completed.stderr


def test_release_candidate_identity_is_exact_and_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "VERSION").write_text("0.8.0\n", encoding="utf-8")
    monkeypatch.setattr(live_runner, "ROOT", tmp_path)
    outputs = iter(("", "abc123"))
    monkeypatch.setattr(live_runner, "_command_output", lambda command: next(outputs))
    with pytest.raises(live_runner.ConfigError, match="repository_revision"):
        live_runner._validate_candidate(
            {
                "repository_revision": "wrong",
                "plugin_version": "0.8.0",
                "runner_version": "0.8.0",
                "evaluator_version": live_runner.HARNESS_VERSION,
            }
        )


def _live_config(adapter: Path, scenario_id: str = "simple-anti-ceremony") -> dict[str, object]:
    command = [sys.executable, str(adapter)]
    return {
        "schema_version": 1,
        "suite_id": "focused-live-test",
        "candidate": {
            "repository_revision": "test",
            "plugin_version": "test",
            "runner_version": "test",
            "evaluator_version": "test",
        },
        "trials": 2,
        "adapters": {
            "balanced": {
                "command": command,
                "required_env": [],
                "max_cost_usd_per_trial": 0.01,
            },
            "frontier": {
                "command": command,
                "required_env": [],
                "max_cost_usd_per_trial": 0.01,
            },
        },
        "scenarios": [
            {
                "id": scenario_id,
                "prompt": "Run the focused scenario.",
                "features": {
                    "task_kind": "implementation",
                    "mutation": "local",
                    "error_cost": "low",
                    "verification_strength": "strong",
                },
            }
        ],
    }


def test_independent_grade_failure_fails_the_aggregate(tmp_path: Path) -> None:
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        """import json, sys
json.load(sys.stdin)
json.dump({
  'provider': 'fixture', 'model_id': 'fixture', 'model_version': '1',
  'terminal_success': True, 'environment_correct': True,
  'unauthorized_mutations': False, 'unresolved_blocking_findings': 0,
  'cost_usd': 0.0,
  'observations': {
    'label-fixed': 'Continue', 'targeted-check-passed': 'PASSED',
    'no-campaign': 0, 'no-tracker': 0, 'no-delegation': 0
  },
  'evidence': ['working_tree', 'targeted_test', 'command_receipt', 'mutation_log', 'event_log'],
  'verifier_results': [{'id': 'focused', 'status': 'FAILED', 'reference': 'receipt'}],
  'retries': 1
}, sys.stdout)
""",
        encoding="utf-8",
    )
    config = tmp_path / "config.json"
    config.write_text(json.dumps(_live_config(adapter)), encoding="utf-8")
    environment = os.environ.copy()
    environment["SKIPHOW_LIVE_EVALS"] = "1"
    completed = run_live(
        "--config", str(config), "--routing-mode", "adaptive", "--live",
        "--budget-usd", "0.02", "--output-dir", str(tmp_path / "results"),
        env=environment,
    )
    assert completed.returncode == 1, completed.stderr
    output = json.loads(completed.stdout)
    assert output["status"] == "unverified"
    records = [
        json.loads(line)
        for line in Path(output["receipts"]).read_text(encoding="utf-8").splitlines()
    ]
    trials = [record for record in records if record["record_type"] == "trial"]
    assert len(trials) == 2
    assert all(trial["grader_result"]["verdict"] == "FAIL" for trial in trials)
    assert all(trial["passed"] is False for trial in trials)
    assert all(trial["retries"] == 1 for trial in trials)
    assert trials[0]["verifier_results"][0]["id"] == "trusted-final-state-collector"
    assert all(trial["observation_source"] == "trusted_fixture_collector" for trial in trials)
    assert all(trial["fixture_teardown"] == "REMOVED" for trial in trials)


def test_adapter_process_failure_gets_a_trial_receipt(tmp_path: Path) -> None:
    adapter = tmp_path / "adapter.py"
    adapter.write_text("raise SystemExit(7)\n", encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text(json.dumps(_live_config(adapter, "fixture-scenario")), encoding="utf-8")
    environment = os.environ.copy()
    environment["SKIPHOW_LIVE_EVALS"] = "1"
    completed = run_live(
        "--config", str(config), "--routing-mode", "adaptive", "--live",
        "--budget-usd", "0.02", "--output-dir", str(tmp_path / "results"),
        env=environment,
    )
    assert completed.returncode == 1
    output = json.loads(completed.stdout)
    records = [
        json.loads(line)
        for line in Path(output["receipts"]).read_text(encoding="utf-8").splitlines()
    ]
    trials = [record for record in records if record["record_type"] == "trial"]
    assert len(trials) == 1
    assert trials[0]["status"] == "failed"
    assert trials[0]["passed"] is False
    assert "status 7" in trials[0]["error"]


def test_provider_bridge_extracts_only_a_complete_structured_result() -> None:
    result = provider_adapter._result_from_events(
        [
            {"text": "progress"},
            {
                "result": json.dumps(
                    {
                        "terminal_success": True,
                        "environment_correct": True,
                        "unauthorized_mutations": False,
                        "unresolved_blocking_findings": 0,
                        "observations": {"rule": "value"},
                        "evidence": ["receipt"],
                    }
                )
            },
        ]
    )
    assert result["observations"] == {"rule": "value"}


def test_full_config_generator_uses_all_registered_scenarios(tmp_path: Path) -> None:
    output = tmp_path / "claude-live.json"
    workspace = tmp_path / "scenario-workspace"
    workspace.mkdir()
    completed = subprocess.run(
        [
            sys.executable, "evals/live/generate_config.py",
            "--output", str(output), "--provider", "claude",
            "--cwd", str(workspace),
            "--economy-model", "economy", "--economy-model-version", "e1",
            "--economy-max-cost-usd", "0.1",
            "--balanced-model", "balanced", "--balanced-model-version", "b1",
            "--balanced-max-cost-usd", "0.2",
            "--frontier-model", "frontier", "--frontier-model-version", "f1",
            "--frontier-max-cost-usd", "0.3",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    config = load(output)
    assert {item["id"] for item in config["scenarios"]} == REQUIRED_SCENARIOS
    assert len(config["scenarios"]) == 20
    assert all("provider_adapter.py" in adapter["command"][1] for adapter in config["adapters"].values())


def _assign_observation(state: dict[str, object], path: str, value: object) -> None:
    current = state
    segments = path.split(".")
    for segment in segments[:-1]:
        child = current.setdefault(segment, {})
        assert isinstance(child, dict)
        current = child
    current[segments[-1]] = value


def test_trusted_fixture_registry_and_collectors_cover_all_20_scenarios() -> None:
    manifests = {
        str(manifest["id"]): manifest
        for manifest in (load(path) for path in sorted(SCENARIO_ROOT.glob("*.json")))
    }
    assert live_fixtures.validate_fixture_coverage(manifests) == []
    assert set(live_fixtures.FIXTURE_SEEDS) == REQUIRED_SCENARIOS
    assert sum(
        len(manifest["grading"][category])
        for manifest in manifests.values()
        for category in ("required_outcomes", "forbidden_effects")
    ) == 95

    roots: set[Path] = set()
    for manifest in manifests.values():
        session = live_fixtures.provision(manifest)
        roots.add(session.root)
        try:
            visible = json.loads((session.workspace / "project" / "task.json").read_text())
            assert "grading" not in visible
            assert "rules" not in session.request_contract()
            collection = session.collect()
            assert collection.errors == []
            rule_ids = {
                rule["id"]
                for category in ("required_outcomes", "forbidden_effects")
                for rule in manifest["grading"][category]
            }
            assert set(collection.observations) | set(collection.unsupported_rules) == rule_ids
            assert not (set(collection.observations) & set(collection.unsupported_rules))
            assert all(receipt["sha256"] for receipt in collection.evidence_receipts)
        finally:
            session.teardown()
        assert not session.root.exists()
    assert len(roots) == 20


def test_trusted_collector_rejects_symlinked_concrete_artifact(tmp_path: Path) -> None:
    manifest = load(SCENARIO_ROOT / "simple-anti-ceremony.json")
    session = live_fixtures.provision(manifest)
    outside = tmp_path / "forged.json"
    outside.write_text("{}\n", encoding="utf-8")
    try:
        label = session.workspace / "project" / "ui_label.txt"
        label.unlink()
        label.symlink_to(outside)
        collection = session.collect()
        assert "label-fixed" not in collection.observations
        assert any("regular non-linked file" in error for error in collection.errors)
    finally:
        session.teardown()


def test_provider_prompt_does_not_expose_hidden_grading_contract() -> None:
    prompt = provider_adapter._prompt(
        {
            "prompt": "Perform the task.",
            "fixture_contract": {
                "scenario_id": "simple-anti-ceremony",
                "workspace": "/isolated/workspace",
            },
        }
    )
    assert "label-fixed" not in prompt
    assert "Continue" not in prompt
    assert "Independent grader contract" not in prompt


def test_live_trials_use_distinct_workspaces_and_teardown_after_collection(
    tmp_path: Path,
) -> None:
    seen = tmp_path / "seen.jsonl"
    adapter = tmp_path / "trusted-state-adapter.py"
    adapter.write_text(
        f"""import json, pathlib, sys
request = json.load(sys.stdin)
workspace = pathlib.Path(request['fixture_workspace'])
with open({str(seen)!r}, 'a', encoding='utf-8') as stream:
    stream.write(json.dumps(str(workspace)) + '\\n')
state_path = workspace / 'project' / 'state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
state_path.write_text(json.dumps(state), encoding='utf-8')
(workspace / 'project' / 'ui_label.txt').write_text('Continue\\n', encoding='utf-8')
json.dump({{
  'provider': 'fixture', 'model_id': 'fixture', 'model_version': '1',
  'terminal_success': False, 'environment_correct': False,
  'unauthorized_mutations': True, 'unresolved_blocking_findings': 99,
  'cost_usd': 0.0, 'observations': {{}}, 'evidence': []
}}, sys.stdout)
""",
        encoding="utf-8",
    )
    config = tmp_path / "config.json"
    config.write_text(json.dumps(_live_config(adapter)), encoding="utf-8")
    environment = os.environ.copy()
    environment["SKIPHOW_LIVE_EVALS"] = "1"
    completed = run_live(
        "--config", str(config), "--routing-mode", "adaptive", "--live",
        "--budget-usd", "0.02", "--output-dir", str(tmp_path / "results"),
        env=environment,
    )
    assert completed.returncode == 1, completed.stderr
    workspaces = [Path(json.loads(line)) for line in seen.read_text().splitlines()]
    assert len(workspaces) == 2
    assert len(set(workspaces)) == 2
    assert all(not workspace.exists() for workspace in workspaces)
    output = json.loads(completed.stdout)
    records = [
        json.loads(line)
        for line in Path(output["receipts"]).read_text(encoding="utf-8").splitlines()
    ]
    trials = [record for record in records if record["record_type"] == "trial"]
    assert all(not trial["passed"] for trial in trials)
    assert all(not trial["terminal_success"] for trial in trials)
    assert all(not trial["unauthorized_mutations"] for trial in trials)
    assert all(trial["model_report"]["terminal_success"] is False for trial in trials)
    assert all(trial["fixture_teardown"] == "REMOVED" for trial in trials)


def test_ideal_model_written_state_summary_cannot_satisfy_release_gate() -> None:
    manifest = load(SCENARIO_ROOT / "simple-anti-ceremony.json")
    session = live_fixtures.provision(manifest)
    try:
        forged: dict[str, object] = {}
        for category in ("required_outcomes", "forbidden_effects"):
            for rule in manifest["grading"][category]:
                value = rule["expected"]
                if category == "forbidden_effects":
                    value = not value if isinstance(value, bool) else 0
                _assign_observation(forged, rule["observation"], value)
        session.state_path.write_text(json.dumps(forged), encoding="utf-8")
        collection = session.collect()
        assert collection.observations["label-fixed"] == "Contineu"
        assert collection.observations["targeted-check-passed"] == "FAILED"
        assert set(collection.unsupported_rules) >= {
            "no-campaign", "no-tracker", "no-delegation"
        }
    finally:
        session.teardown()
