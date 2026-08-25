"""End-to-end CLI controls use the durable store, not process memory."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def invoke(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = {"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    import os

    return subprocess.run(
        [sys.executable, "-m", "skiphow", "--project-root", str(project), *args],
        cwd=ROOT,
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def test_cli_start_status_pause_resume_cancel_survive_processes(tmp_path: Path) -> None:
    started = invoke(
        tmp_path,
        "start",
        "Work through the backlog overnight",
        "--run-id",
        "run-1",
        "--task",
        "Deliver the first slice",
    )
    assert started.returncode == 0, started.stderr
    assert json.loads(started.stdout)["status"] == "RUNNING"

    assert invoke(tmp_path, "pause", "run-1").returncode == 0
    status = invoke(tmp_path, "status", "run-1")
    assert json.loads(status.stdout)["status"] == "PAUSED"
    assert invoke(tmp_path, "resume", "run-1").returncode == 0
    cancelled = invoke(tmp_path, "cancel", "run-1")
    assert json.loads(cancelled.stdout)["status"] == "CANCELLED"

    exported = invoke(tmp_path, "export", "run-1")
    receipt = json.loads(exported.stdout)
    assert receipt["run"]["original_request"] == "Work through the backlog overnight"
    assert receipt["events"][0]["kind"] == "run_created"


def test_cli_rejects_database_outside_project(tmp_path: Path) -> None:
    result = invoke(
        tmp_path,
        "--database",
        str(tmp_path.parent / "outside.sqlite3"),
        "status",
        "missing",
    )
    assert result.returncode == 2
    assert "database must remain inside" in result.stderr


def test_cli_intake_dry_run_and_explicit_local_persistence(tmp_path: Path) -> None:
    source = tmp_path / "signals.json"
    source.write_text(json.dumps(["Idea: add reports", "Checkout might fail"]), encoding="utf-8")
    dry = invoke(tmp_path, "intake", str(source))
    assert dry.returncode == 0
    assert json.loads(dry.stdout)["persisted"] is False
    assert not (tmp_path / ".skiphow/intake").exists()

    persisted = invoke(tmp_path, "intake", str(source), "--persist")
    assert persisted.returncode == 0
    assert json.loads(persisted.stdout)["store"]["signals_added"] == 2


def test_cli_setup_migrates_v1_with_backup(tmp_path: Path) -> None:
    config = tmp_path / ".skiphow/config.json"
    config.parent.mkdir()
    config.write_text('{"tracker":"local"}\n', encoding="utf-8")
    result = invoke(tmp_path, "setup", "--tracker", "github", "--project", "owner/7")
    assert result.returncode == 0, result.stderr
    value = json.loads(config.read_text(encoding="utf-8"))
    assert value["schema_version"] == 2
    assert value["tracker"] == {"type": "github", "project": "owner/7"}
    assert config.with_suffix(".json.v1.bak").read_text() == '{"tracker":"local"}\n'
