"""A diagnostic driver must retain evidence before optional analysis can fail."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "host_pilot_capture_tests", ROOT / "evals/receipts/host-pilot-20260905/run.py"
)
assert spec and spec.loader
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def prepare_fixture(scratch):
    """Copy ordinary files only; no host session or Git repository is created."""
    fixture = scratch / "fixture"
    driver.capture.materialize("orders-service", fixture)
    record, _ = driver.capture.source("orders-service")
    config = {field: "synthetic offline test" for field in (
        "run_id", "case_id", "arm", "host", "host_version", "model", "effort",
        "permission", "sandbox", "activation", "instructions", "isolation", "control_run",
        "prompt", "observable", "host_command", "permitted_command_evidence",
    )}
    config.update({
        "synthetic_test": True,
        "setup_note": "Source layers copied; Git setup and all model calls deliberately omitted.",
        "setup_performed": record["setup"],
        "limits": {"session_usd": 1, "receipt_usd": 1, "sessions_in_flight": 1, "wall_seconds": 30},
        "baseline": {"argv": [sys.executable, "-B", "-c", "import orders.totals; print('synthetic baseline')"],
                     "returncode": 0, "contains": "synthetic baseline"},
    })
    prepared = scratch / "prepared.json"
    driver.capture.prepare(fixture, "orders-service", config, prepared)
    trace = scratch / "trace.jsonl"
    trace.write_text(json.dumps({"type": "assistant", "message": "forwarded /private/operator text"}) + "\n")
    return fixture, prepared, trace


def test_mixed_jsonl_shapes_are_preserved_and_sanitized_without_dict_assumptions():
    events = [
        {"type": "assistant", "message": {"content": [
            {"type": "thinking", "signature": "private-signature-a", "thinking": "invented thought"},
            "string content", 42, None,
        ]}},
        {"type": "assistant", "message": "forwarded /private/operator text"},
        {"type": "assistant", "message": [{"signature": ["private-signature-b"]}]},
        {"type": "assistant", "message": None},
        ["array event", {"signature": {"nested": "private-signature-c"}}],
        "string event", 42, False, None,
        {"type": "result", "result": "done"},
    ]
    text = "\n".join(json.dumps(event) for event in events) + "\nplain /private/operator log\n"
    assert driver.parse_events(text) == [event for event in events if isinstance(event, dict)]
    sanitized = driver.sanitized_trace(text, {"/private/operator": "<operator>"})
    assert "private-signature" not in sanitized
    assert "/private/operator" not in sanitized
    lines = sanitized.splitlines()
    retained = [json.loads(line) for line in lines[:-1]]
    assert len(retained) == len(events)
    assert retained[1]["message"] == "forwarded <operator> text"
    assert retained[5:9] == events[5:9]
    assert retained[-1] == events[-1]
    assert lines[-1] == "plain <operator> log"


def test_optional_enrichment_failure_keeps_complete_capture_before_cleanup(tmp_path):
    destination = tmp_path / "capture.json"
    with pytest.raises(RuntimeError, match="optional grading failed"):
        with driver.owned_workspace(tmp_path) as workspace:
            scratch = workspace["path"]
            fixture, prepared, trace = prepare_fixture(scratch)
            workspace["model_started"] = True  # Synthetic lifecycle state; no model is called.
            (fixture / "result.txt").write_text("Retain this partial result\n")

            def fail_after_capture(receipt):
                assert destination.is_file()
                assert workspace["evidence_retained"] is True
                assert receipt["end_state_artifacts"]
                raise RuntimeError("optional grading failed")

            driver.retain_before_enrichment(
                fixture, prepared, trace, destination, {"/private/operator": "<operator>"},
                "interrupted", enrich=fail_after_capture, workspace=workspace,
            )
    assert not scratch.exists()
    retained = json.loads(destination.read_text())
    assert "<operator>" in retained["trace"]["content"]
    assert "/private/operator" not in destination.read_text()
    assert any(artifact["description"] == "result.txt" for artifact in retained["end_state_artifacts"])
    assert destination.with_suffix(".trace.jsonl").is_file()


def test_capture_failure_retains_safe_trace_and_raw_workspace(tmp_path, monkeypatch, capsys):
    destination = tmp_path / "capture.json"

    def capture_failure(*_args, **_kwargs):
        raise ValueError("injected capture failure")

    with pytest.raises(ValueError, match="injected capture failure"):
        with driver.owned_workspace(tmp_path) as workspace:
            scratch = workspace["path"]
            fixture, prepared, trace = prepare_fixture(scratch)
            workspace["model_started"] = True
            monkeypatch.setattr(driver.capture, "capture", capture_failure)
            driver.retain_before_enrichment(
                fixture, prepared, trace, destination, {"/private/operator": "<operator>"},
                "interrupted", workspace=workspace,
            )
    assert scratch.is_dir()
    assert prepared.is_file() and trace.is_file()
    assert (fixture / "orders/totals.py").is_file()
    assert workspace["evidence_retained"] is False
    safe_trace = destination.with_suffix(".trace.jsonl").read_text()
    assert "<operator>" in safe_trace and "/private/operator" not in safe_trace
    assert not destination.exists()
    assert str(scratch) in capsys.readouterr().err


def test_setup_failure_cleans_workspace_when_no_session_started(tmp_path):
    with pytest.raises(RuntimeError, match="setup failed"):
        with driver.owned_workspace(tmp_path) as workspace:
            scratch = workspace["path"]
            (scratch / "partial-setup.txt").write_text("No paid run began")
            raise RuntimeError("setup failed")
    assert not scratch.exists()


@pytest.mark.parametrize("suffix", [".json", ".trace.jsonl", ".destination.json"])
def test_existing_retained_evidence_blocks_repeat_before_setup(tmp_path, monkeypatch, suffix):
    (tmp_path / f"coordination{suffix}").write_text("Retained prior evidence")
    monkeypatch.setattr(driver, "__file__", str(tmp_path / "run.py"))
    monkeypatch.setattr(driver.sys, "argv", ["run.py", "coordination"])

    def unexpected_setup(_root):
        pytest.fail("run setup started despite retained evidence")

    monkeypatch.setattr(driver, "owned_workspace", unexpected_setup)
    with pytest.raises(RuntimeError, match="existing"):
        driver.main()
