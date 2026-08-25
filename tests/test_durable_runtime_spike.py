"""Fault-injection proofs for the durable runtime comparison."""

import json
import sqlite3
from pathlib import Path

from scripts.durable_runtime_spike import compare, run


def test_embedded_spike_recovers_without_duplicate_actions(tmp_path: Path) -> None:
    database = tmp_path / "runtime.db"
    assert run(database, "campaign", crash_after_provider=True) == 75
    assert run(database, "campaign", crash_after_provider=False) == 0
    assert run(database, "campaign", crash_after_provider=False) == 0

    connection = sqlite3.connect(database)
    assert connection.execute(
        "SELECT state FROM run_state WHERE run_id = 'campaign'"
    ).fetchone() == ("COMPLETED",)
    assert connection.execute(
        "SELECT action_key, COUNT(*) FROM receipts GROUP BY action_key ORDER BY action_key"
    ).fetchall() == [("external-action", 1), ("provider-turn", 1)]


def test_comparison_runs_process_fault_and_provider_restart(tmp_path: Path) -> None:
    fake = tmp_path / "fake-app-server.py"
    fake.write_text(
        """#!/usr/bin/env python3
import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    if 'id' not in request:
        continue
    method = request['method']
    if method == 'initialize':
        result = {'serverInfo': {'name': 'fake', 'version': '1'}}
    elif method == 'thread/start':
        result = {'thread': {'id': 'thread-from-durable-storage'}}
    elif method == 'thread/resume':
        result = {'thread': {'id': request['params']['threadId']}}
    else:
        result = {}
    print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
""",
        encoding="utf-8",
    )
    fake.chmod(0o755)

    receipt = compare(tmp_path / "state", [str(fake)])

    assert receipt["constraints"] == {
        "model_calls": 0,
        "cloud_accounts_created": 0,
        "heavy_services_installed": 0,
    }
    candidates = {item["candidate"]: item for item in receipt["candidates"]}
    assert candidates["embedded-sqlite"]["status"] == "VERIFIED"
    assert candidates["embedded-sqlite"]["checks"]["external_actions_exactly_once"]
    assert candidates["provider-native-codex-app-server"]["status"] == "VERIFIED"
    assert candidates["provider-native-codex-app-server"]["checks"]["model_turns_started"] == 0
    assert candidates["restate"]["status"] == "UNVERIFIED"
    assert candidates["temporal"]["status"] == "UNVERIFIED"

    serialized = json.dumps(receipt, sort_keys=True)
    assert "BUILD embedded SQLite controller" in serialized
