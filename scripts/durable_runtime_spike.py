#!/usr/bin/env python3
"""Executable crash and resume spike for the embedded runtime candidate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys


SCHEMA = """
CREATE TABLE IF NOT EXISTS run_state (
    run_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    revision INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS receipts (
    run_id TEXT NOT NULL,
    action_key TEXT NOT NULL,
    result TEXT NOT NULL,
    PRIMARY KEY (run_id, action_key)
);
"""


def transition(connection: sqlite3.Connection, run_id: str, state: str) -> None:
    """Commit one monotonic run revision."""
    with connection:
        connection.execute(
            """
            INSERT INTO run_state(run_id, state, revision) VALUES (?, ?, 1)
            ON CONFLICT(run_id) DO UPDATE SET
                state = excluded.state,
                revision = run_state.revision + 1
            """,
            (run_id, state),
        )


def receipt(
    connection: sqlite3.Connection, run_id: str, action_key: str, result: str
) -> bool:
    """Record an external action once and return whether this call claimed it."""
    with connection:
        cursor = connection.execute(
            "INSERT OR IGNORE INTO receipts(run_id, action_key, result) VALUES (?, ?, ?)",
            (run_id, action_key, result),
        )
    return cursor.rowcount == 1


def run(database: Path, run_id: str, crash_after_provider: bool) -> int:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.executescript(SCHEMA)

    row = connection.execute(
        "SELECT state FROM run_state WHERE run_id = ?", (run_id,)
    ).fetchone()
    if row is None:
        transition(connection, run_id, "RUNNING")

    provider_claimed = receipt(connection, run_id, "provider-turn", "completed")
    if provider_claimed and crash_after_provider:
        print("simulated crash after committed provider receipt")
        return 75

    external_claimed = receipt(connection, run_id, "external-action", "completed")
    transition(connection, run_id, "COMPLETED")
    receipts = connection.execute(
        "SELECT action_key, COUNT(*) FROM receipts WHERE run_id = ? GROUP BY action_key",
        (run_id,),
    ).fetchall()
    state = connection.execute(
        "SELECT state, revision FROM run_state WHERE run_id = ?", (run_id,)
    ).fetchone()
    print(
        f"state={state[0]} revision={state[1]} "
        f"provider_executed={provider_claimed} external_executed={external_claimed} "
        f"receipts={dict(receipts)}"
    )
    connection.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--run-id", default="spike-run")
    parser.add_argument("--crash-after-provider", action="store_true")
    args = parser.parse_args()
    return run(args.db, args.run_id, args.crash_after_provider)


if __name__ == "__main__":
    sys.exit(main())
