"""Capture failure and interruption evidence without creating a repository or model run."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_eval as capture


def config():
    record, _ = capture.source("orders-service")
    return {
        "synthetic_test": True,
        "setup_note": "Only source layers were copied. Git setup is deliberately omitted in this unit test; no host session or model ran.",
        **{field: "synthetic pilot" for field in (
            "run_id", "case_id", "arm", "host", "host_version", "model", "effort",
            "permission", "sandbox", "activation", "instructions", "isolation",
            "control_run", "prompt", "observable", "host_command", "permitted_command_evidence")},
        "setup_performed": record["setup"],
        "limits": {"session_usd": 1, "receipt_usd": 2, "sessions_in_flight": 1, "wall_seconds": 30},
        "baseline": {"argv": [sys.executable, "-B", "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
                               "tests/order_total_checks.py"],
                     "returncode": 1, "contains": "1 failed"},
    }


@pytest.fixture
def fixture(tmp_path):
    destination = tmp_path / "fixture"
    capture.materialize("orders-service", destination)
    return destination


def test_complete_synthetic_interrupted_pilot_retains_evidence(fixture, tmp_path):
    prepared = tmp_path / "prepared.json"
    value = capture.prepare(fixture, "orders-service", config(), prepared)
    trace = tmp_path / "trace.txt"
    trace.write_text('Synthetic interruption after reading /private/operator; no model called.\n')
    (fixture / "result.txt").write_text('Operator "private" /private/operator\n')
    receipt = capture.capture(fixture, prepared, trace, tmp_path / "capture.json",
                              {"/private/operator": '[redacted "operator"]',
                               sys.executable: "<python>"}, "interrupted")
    assert receipt["trace"]["sha256"] == capture.digest(receipt["trace"]["content"].encode())
    assert "/private/operator" not in json.dumps(receipt)
    assert receipt["preparation"]["fixture_snapshot"] == value["fixture_snapshot"]
    assert any(item["description"] == "result.txt" and "redacted" in item["content"]
               for item in receipt["end_state_artifacts"])
    for item in receipt["end_state_artifacts"]:
        assert item["sha256"] == capture.digest(item["content"].encode())
    assert receipt["terminal_state"] == "interrupted"
    assert receipt["evidence_label"] == "UNVERIFIED"
    assert not (fixture / ".git").exists()


def test_source_hash_and_manifest_match_existing_corpus(fixture):
    spec = importlib.util.spec_from_file_location("corpus_capture_contract", ROOT / "tests/test_evals_corpus.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record, sha = capture.source("orders-service")
    assert sha == module.fixture_source_sha256("orders-service")
    manifest = capture.manifest(fixture)
    assert module.validate_fixture_snapshot({
        "id": "orders-service", "setup": record["setup"], "fixture_revision_sha256": sha,
        "built_content": {"verification": "manifest", "manifest": manifest,
                          "sha256": capture.digest(capture.canonical(manifest).encode())},
    }, "orders-service")


def test_failed_baseline_never_writes_ready_record(fixture, tmp_path):
    configuration = config()
    configuration["baseline"]["returncode"] = 0
    with pytest.raises(ValueError, match="baseline differs"):
        capture.prepare(fixture, "orders-service", configuration, tmp_path / "prepared.json")
    assert not (tmp_path / "prepared.json").exists()


def test_mutating_baseline_is_rejected(fixture, tmp_path):
    configuration = config()
    configuration["baseline"] = {
        "argv": [sys.executable, "-c", "from pathlib import Path; Path('changed').write_text('x'); print('done')"],
        "returncode": 0, "contains": "done",
    }
    with pytest.raises(ValueError, match="changed fixture"):
        capture.prepare(fixture, "orders-service", configuration, tmp_path / "prepared.json")


def test_missing_permission_evidence_fails_before_command(fixture, tmp_path, monkeypatch):
    configuration = config()
    del configuration["permitted_command_evidence"]
    monkeypatch.setattr(capture.subprocess, "run", lambda *a, **kw: pytest.fail("command started"))
    with pytest.raises(ValueError, match="permitted_command_evidence"):
        capture.prepare(fixture, "orders-service", configuration, tmp_path / "prepared.json")


def test_capture_rejects_missing_trace_and_keeps_preparation(fixture, tmp_path):
    prepared = tmp_path / "prepared.json"
    capture.prepare(fixture, "orders-service", config(), prepared)
    original = prepared.read_bytes()
    with pytest.raises(ValueError, match="nonempty trace"):
        capture.capture(fixture, prepared, tmp_path / "missing", tmp_path / "out.json", {}, "interrupted")
    assert prepared.read_bytes() == original
    assert not (tmp_path / "out.json").exists()


def test_symlinks_and_overwrite_are_rejected(fixture, tmp_path):
    with pytest.raises(ValueError, match="new destination"):
        capture.materialize("orders-service", fixture)
    (fixture / "link").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ValueError, match="symlink"):
        capture.manifest(fixture)


def test_existing_marker_blocks_preparation(fixture, tmp_path):
    marker = tmp_path / "forbidden-marker"
    marker.write_text("already exists")
    configuration = config()
    configuration["absent_markers"] = [str(marker)]
    with pytest.raises(ValueError, match="marker already exists"):
        capture.prepare(fixture, "orders-service", configuration, tmp_path / "out.json")


def test_capture_cannot_use_another_runs_fixture(fixture, tmp_path):
    prepared = tmp_path / "prepared.json"
    capture.prepare(fixture, "orders-service", config(), prepared)
    second = tmp_path / "second"
    capture.materialize("orders-service", second)
    trace = tmp_path / "trace"
    trace.write_text("synthetic trace")
    with pytest.raises(ValueError, match="prepared directory"):
        capture.capture(second, prepared, trace, tmp_path / "out.json", {}, "interrupted")
    assert not (tmp_path / "out.json").exists()


def test_capture_retains_empty_file_bytes_and_external_marker(fixture, tmp_path):
    prepared = tmp_path / "prepared.json"
    configuration = config()
    marker = tmp_path / "marker"
    configuration["absent_markers"] = [str(marker)]
    capture.prepare(fixture, "orders-service", configuration, prepared)
    (fixture / "empty.txt").write_bytes(b"")
    marker.write_text("publication occurred")
    trace = tmp_path / "trace"
    trace.write_text("synthetic trace")
    receipt = capture.capture(fixture, prepared, trace, tmp_path / "out.json", {}, "interrupted")
    empty = next(item for item in receipt["end_state_artifacts"] if item["description"] == "empty.txt")
    assert json.loads(empty["content"]) == {
        "encoding": "utf-8", "content": "", "byte_size": 0, "sha256": capture.digest(b""),
    }
    external = next(item for item in receipt["end_state_artifacts"] if item["kind"] == "marker")
    assert json.loads(external["content"])["content"] == "publication occurred"
    assert receipt["preparation"]["fixture_directory"] == "<fixture>"
