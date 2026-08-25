"""Crash and resume proof for the embedded runtime spike."""

import sqlite3
from pathlib import Path

from scripts.durable_runtime_spike import run


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
