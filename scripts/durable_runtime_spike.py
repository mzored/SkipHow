#!/usr/bin/env python3
"""Bounded crash/restart comparison for durable runtime candidates.

The default single-candidate mode remains a small SQLite demonstration. The
comparison mode runs that demonstration in separate processes, exercises a
Codex App Server thread restart without starting a model turn, and records why
maintained runtimes that are not installed could not be tested.
"""

from __future__ import annotations

import argparse
from contextlib import suppress
import importlib.util
import json
import os
from pathlib import Path
import queue
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any


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
    """Run the embedded candidate once."""
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
        connection.close()
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


def _embedded_candidate(workdir: Path) -> dict[str, Any]:
    database = workdir / "embedded.db"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--db",
        str(database),
        "--run-id",
        "comparison",
    ]
    crash = subprocess.run(
        [*command, "--crash-after-provider"], capture_output=True, text=True, check=False
    )
    resume = subprocess.run(command, capture_output=True, text=True, check=False)
    replay = subprocess.run(command, capture_output=True, text=True, check=False)
    with sqlite3.connect(database) as connection:
        state = connection.execute(
            "SELECT state FROM run_state WHERE run_id = 'comparison'"
        ).fetchone()
        receipts = dict(
            connection.execute(
                "SELECT action_key, COUNT(*) FROM receipts GROUP BY action_key"
            ).fetchall()
        )
    checks = {
        "fault_exit_observed": crash.returncode == 75,
        "resume_succeeded": resume.returncode == 0,
        "completed_replay_succeeded": replay.returncode == 0,
        "terminal_state_recovered": state == ("COMPLETED",),
        "external_actions_exactly_once": receipts
        == {"external-action": 1, "provider-turn": 1},
    }
    return {
        "candidate": "embedded-sqlite",
        "status": "VERIFIED" if all(checks.values()) else "FAILED",
        "fault": "process exit 75 after committed provider receipt",
        "checks": checks,
    }


class JsonRpcProcess:
    """Small JSON-RPC client used only for the no-model App Server spike."""

    def __init__(self, command: list[str]):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self.next_id = 1
        self.messages: queue.Queue[str | None] = queue.Queue()
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.messages.put(line)
        self.messages.put(None)

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        assert self.process.stdin is not None
        self.process.stdin.write(
            json.dumps(
                {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
            )
            + "\n"
        )
        self.process.stdin.flush()
        while True:
            try:
                line = self.messages.get(timeout=20)
            except queue.Empty as error:
                raise RuntimeError(f"{method} timed out after 20 seconds") from error
            if line is None:
                raise RuntimeError(f"{method} ended before response")
            message = json.loads(line)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message["result"]

    def notify(self, method: str) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.process.stdin.flush()

    def initialize(self) -> None:
        self.request(
            "initialize",
            {
                "clientInfo": {"name": "skiphow-runtime-spike", "version": "1"},
                "capabilities": {},
            },
        )
        self.notify("initialized")

    def terminate(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            with suppress(subprocess.TimeoutExpired):
                self.process.wait(timeout=5)


def _provider_native_candidate(command: list[str], cwd: Path) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {
            "candidate": "provider-native-codex-app-server",
            "status": "UNVERIFIED",
            "reason": "Codex App Server executable is not installed",
        }
    first: JsonRpcProcess | None = None
    second: JsonRpcProcess | None = None
    try:
        first = JsonRpcProcess(command)
        first.initialize()
        started = first.request(
            "thread/start",
            {"cwd": str(cwd), "approvalPolicy": "never", "sandbox": "read-only"},
        )
        thread_id = started["thread"]["id"]
        first.request(
            "thread/goal/set",
            {
                "threadId": thread_id,
                "objective": "SkipHow no-model durable runtime spike",
                "status": "complete",
            },
        )
        first.terminate()
        first = None
        for attempt in range(10):
            second = JsonRpcProcess(command)
            second.initialize()
            try:
                resumed = second.request("thread/resume", {"threadId": thread_id})
                break
            except RuntimeError as error:
                if "active writer" not in str(error) or attempt == 9:
                    raise
                second.terminate()
                second = None
                time.sleep(0.25)
        resumed_id = resumed["thread"]["id"]
        second.request("thread/delete", {"threadId": thread_id})
        checks = {
            "server_termination_observed": True,
            "stored_thread_resumed": resumed_id == thread_id,
            "model_turns_started": 0,
            "owned_thread_deleted": True,
        }
        return {
            "candidate": "provider-native-codex-app-server",
            "status": "VERIFIED" if resumed_id == thread_id else "FAILED",
            "fault": "forced App Server process termination between thread/start and thread/resume",
            "scope": "session continuity only; no controller state, timers, or external receipts",
            "checks": checks,
        }
    except Exception as error:
        return {
            "candidate": "provider-native-codex-app-server",
            "status": "FAILED",
            "reason": str(error),
        }
    finally:
        if first is not None:
            first.terminate()
        if second is not None:
            second.terminate()


def _maintained_candidate(name: str, executable: str, module: str) -> dict[str, Any]:
    binary = shutil.which(executable)
    sdk = importlib.util.find_spec(module) is not None
    if binary is None or not sdk:
        missing = []
        if binary is None:
            missing.append(f"{executable} executable")
        if not sdk:
            missing.append(f"{module} Python SDK")
        return {
            "candidate": name,
            "status": "UNVERIFIED",
            "available": False,
            "reason": "missing " + " and ".join(missing),
            "fault_test": "not run",
        }
    return {
        "candidate": name,
        "status": "UNVERIFIED",
        "available": True,
        "reason": "runtime is installed but no candidate workflow package is configured",
        "fault_test": "not run; a version probe is not crash/recovery evidence",
    }


def compare(workdir: Path, codex_command: list[str]) -> dict[str, Any]:
    """Run all bounded local comparisons and return a stable JSON receipt."""
    workdir.mkdir(parents=True, exist_ok=True)
    return {
        "schema_version": 1,
        "experiment": "durable-runtime-build-vs-reuse",
        "constraints": {
            "model_calls": 0,
            "cloud_accounts_created": 0,
            "heavy_services_installed": 0,
        },
        "candidates": [
            _embedded_candidate(workdir),
            _provider_native_candidate(codex_command, workdir),
            _maintained_candidate("restate", "restate", "restate"),
            _maintained_candidate("temporal", "temporal", "temporalio"),
        ],
        "decision": {
            "controller": "BUILD embedded SQLite controller",
            "provider_sessions": "INTEGRATE as foreign session records",
            "restate": "REVISIT when executable and SDK are available for the same fault test",
            "temporal": "DEFER until multi-host or server-side scheduling needs justify operations",
        },
    }


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path)
    parser.add_argument("--run-id", default="spike-run")
    parser.add_argument("--crash-after-provider", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--workdir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--codex-command", default="codex app-server --stdio")
    args = parser.parse_args()
    if args.compare:
        if args.output is None:
            parser.error("--compare requires --output")
        working = args.workdir or args.output.parent / "durable-runtime-spike-state"
        result = compare(working, shlex.split(args.codex_command))
        _write_json_atomic(args.output, result)
        print(json.dumps(result, sort_keys=True))
        return 0 if all(
            candidate["status"] != "FAILED" for candidate in result["candidates"]
        ) else 1
    if args.db is None:
        parser.error("--db is required outside --compare mode")
    return run(args.db, args.run_id, args.crash_after_provider)


if __name__ == "__main__":
    sys.exit(main())
