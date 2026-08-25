"""Transactional SQLite state and append-only journal for the runner."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Any, Iterator, Mapping, Sequence
from uuid import uuid4

from .schemas import (
    Event, Finding, RUN_TERMINAL, RUN_TRANSITIONS, SCHEMA_VERSION, TASK_TERMINAL,
    TASK_TRANSITIONS, Run, RunStatus, Task, TaskStatus,
    utc_now, validate_transition,
)
from .security import SecretRedactor


class ConflictError(RuntimeError):
    """Raised when a revision or lease changed before a write."""


class NotFoundError(KeyError):
    """Raised when a requested runner record does not exist."""


class StoreCorruptionError(RuntimeError):
    """Raised when startup cannot prove or restore store integrity."""


MAX_RECOVERY_SNAPSHOTS = 3


class RunnerStore:
    """Own runner state in SQLite and expose revision-checked operations."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.last_backup_path: Path | None = None
        self._redactor = SecretRedactor()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            has_runner_tables = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='runs'"
            ).fetchone() is not None
        if version > SCHEMA_VERSION:
            raise RuntimeError(f"database schema {version} is newer than supported {SCHEMA_VERSION}")
        if version == 0 and not has_runner_tables:
            with self._connect() as connection:
                connection.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, status TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
                    revision INTEGER NOT NULL, status TEXT NOT NULL, priority INTEGER NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
                    run_id TEXT NOT NULL REFERENCES runs(run_id), task_id TEXT,
                    kind TEXT NOT NULL, occurred_at TEXT NOT NULL, payload TEXT NOT NULL,
                    previous_hash TEXT NOT NULL DEFAULT '', event_hash TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS findings (
                    finding_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
                    task_id TEXT, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    idempotency_key TEXT UNIQUE NOT NULL, worker_id TEXT NOT NULL,
                    session_id TEXT, lease_expires_at REAL NOT NULL, last_progress_at TEXT NOT NULL,
                    owned_resources TEXT NOT NULL, base_identity TEXT, head_identity TEXT,
                    failure_signature TEXT, next_action TEXT NOT NULL, active INTEGER NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_attempt
                    ON attempts(task_id) WHERE active = 1;
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
                    task_id TEXT, reason TEXT NOT NULL, created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS external_waits (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
                    due_at REAL NOT NULL, reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    run_id TEXT NOT NULL REFERENCES runs(run_id), event_sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL, payload TEXT NOT NULL,
                    payload_hash TEXT NOT NULL, journal_hash TEXT NOT NULL,
                    PRIMARY KEY (run_id, event_sequence)
                );
                CREATE TABLE IF NOT EXISTS route_lanes (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    revision INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS route_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    attempt_id TEXT NOT NULL UNIQUE REFERENCES attempts(attempt_id),
                    recorded_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS security_audit (
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    sequence INTEGER NOT NULL, digest TEXT NOT NULL, task_id TEXT,
                    created_at TEXT NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY (run_id, sequence), UNIQUE (run_id, digest)
                );
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                PRAGMA user_version = 2;
                COMMIT;
                """
                )
        elif version in {0, 1}:
            self.last_backup_path = self._backup_before_migration(version)
            self._run_migrations(1 if version == 0 else version)
        self._startup_integrity_check()

    def _backup_before_migration(self, version: int) -> Path:
        """Create a consistent SQLite backup before changing a released schema."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = self.path.with_name(f"{self.path.name}.v{version}.{stamp}.bak")
        source = self._connect()
        destination = sqlite3.connect(backup_path)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
            source.close()
        descriptor = os.open(backup_path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return backup_path

    @staticmethod
    def _upgrade_record_version(payload: str) -> str:
        value = json.loads(payload)
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise StoreCorruptionError("schema 1 record has no schema 1 envelope")
        value["schema_version"] = 2
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @staticmethod
    def _upgrade_snapshot_version(payload: str) -> str:
        value = json.loads(payload)
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise StoreCorruptionError("schema 1 snapshot has no schema 1 envelope")
        value["schema_version"] = 2
        for field in ("run",):
            record = value.get(field)
            if isinstance(record, dict) and record.get("schema_version") == 1:
                record["schema_version"] = 2
        for field in ("tasks", "events", "findings"):
            records = value.get(field, [])
            if not isinstance(records, list):
                raise StoreCorruptionError(f"schema 1 snapshot {field} must be a list")
            for record in records:
                if isinstance(record, dict) and record.get("schema_version") == 1:
                    record["schema_version"] = 2
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @staticmethod
    def _event_digest(row: Mapping[str, Any], previous_hash: str) -> str:
        envelope = {
            "event_id": row["event_id"], "run_id": row["run_id"],
            "task_id": row["task_id"], "kind": row["kind"],
            "occurred_at": row["occurred_at"], "payload": row["payload"],
            "previous_hash": previous_hash,
        }
        encoded = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _run_migrations(self, version: int) -> None:
        migrations = {1: self._migrate_v1_to_v2}
        current = version
        while current < SCHEMA_VERSION:
            migration = migrations.get(current)
            if migration is None:
                raise RuntimeError(f"no database migration from schema {current}")
            migration()
            current += 1

    def _migrate_v1_to_v2(self) -> None:
        """Upgrade schema 1 atomically after the online backup succeeds."""
        with self._transaction() as connection:
            connection.execute("DROP TRIGGER IF EXISTS events_no_update")
            connection.execute("DROP TRIGGER IF EXISTS events_no_delete")
            event_columns = {row["name"] for row in connection.execute("PRAGMA table_info(events)")}
            if "previous_hash" not in event_columns:
                connection.execute("ALTER TABLE events ADD COLUMN previous_hash TEXT NOT NULL DEFAULT ''")
            if "event_hash" not in event_columns:
                connection.execute("ALTER TABLE events ADD COLUMN event_hash TEXT NOT NULL DEFAULT ''")
            snapshot_columns = {row["name"] for row in connection.execute("PRAGMA table_info(snapshots)")}
            if "payload_hash" not in snapshot_columns:
                connection.execute("ALTER TABLE snapshots ADD COLUMN payload_hash TEXT NOT NULL DEFAULT ''")
            if "journal_hash" not in snapshot_columns:
                connection.execute("ALTER TABLE snapshots ADD COLUMN journal_hash TEXT NOT NULL DEFAULT ''")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS route_lanes (task_id TEXT PRIMARY KEY REFERENCES tasks(task_id), run_id TEXT NOT NULL REFERENCES runs(run_id), revision INTEGER NOT NULL, updated_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS route_outcomes (outcome_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), task_id TEXT NOT NULL REFERENCES tasks(task_id), attempt_id TEXT NOT NULL UNIQUE REFERENCES attempts(attempt_id), recorded_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS security_audit (run_id TEXT NOT NULL REFERENCES runs(run_id), sequence INTEGER NOT NULL, digest TEXT NOT NULL, task_id TEXT, created_at TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY (run_id, sequence), UNIQUE (run_id, digest))"
            )
            for table in ("runs", "tasks", "events", "findings"):
                for row in connection.execute(f"SELECT rowid AS storage_rowid,payload FROM {table}").fetchall():
                    upgraded = self._upgrade_record_version(row["payload"])
                    connection.execute(f"UPDATE {table} SET payload=? WHERE rowid=?", (upgraded, row["storage_rowid"]))
            previous_by_run: dict[str, str] = {}
            for row in connection.execute("SELECT * FROM events ORDER BY sequence").fetchall():
                previous = previous_by_run.get(row["run_id"], "")
                digest = self._event_digest(row, previous)
                connection.execute(
                    "UPDATE events SET previous_hash=?,event_hash=? WHERE sequence=?",
                    (previous, digest, row["sequence"]),
                )
                previous_by_run[row["run_id"]] = digest
            for row in connection.execute("SELECT rowid AS storage_rowid,run_id,event_sequence,payload FROM snapshots").fetchall():
                payload = self._upgrade_snapshot_version(row["payload"])
                journal = connection.execute(
                    "SELECT event_hash FROM events WHERE run_id=? AND sequence=?",
                    (row["run_id"], row["event_sequence"]),
                ).fetchone()
                connection.execute(
                    "UPDATE snapshots SET payload=?,payload_hash=?,journal_hash=? WHERE rowid=?",
                    (payload, hashlib.sha256(payload.encode()).hexdigest(), journal[0] if journal else "", row["storage_rowid"]),
                )
            connection.execute(
                "CREATE TRIGGER events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END"
            )
            connection.execute(
                "CREATE TRIGGER events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END"
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _journal_valid(self, connection: sqlite3.Connection, run_id: str) -> bool:
        previous = ""
        first = True
        for row in connection.execute("SELECT * FROM events WHERE run_id=? ORDER BY sequence", (run_id,)):
            try:
                payload = Event.from_dict(json.loads(row["payload"]))
            except (ValueError, TypeError, json.JSONDecodeError):
                return False
            if first and row["kind"] != "run_created":
                return False
            if payload.event_id != row["event_id"] or payload.run_id != row["run_id"]:
                return False
            if payload.task_id != row["task_id"] or payload.kind != row["kind"] or payload.occurred_at != row["occurred_at"]:
                return False
            if row["previous_hash"] != previous or row["event_hash"] != self._event_digest(row, previous):
                return False
            previous = row["event_hash"]
            first = False
        return not first

    def _validate_run_state(self, connection: sqlite3.Connection, run_id: str) -> None:
        run_row = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if run_row is None:
            raise StoreCorruptionError(f"run {run_id} is missing")
        run = Run.from_dict(json.loads(run_row["payload"]))
        if run.run_id != run_id or run.revision != run_row["revision"] or run.status != run_row["status"]:
            raise StoreCorruptionError(f"run {run_id} columns disagree with its payload")
        for row in connection.execute("SELECT * FROM tasks WHERE run_id=?", (run_id,)):
            task = Task.from_dict(json.loads(row["payload"]))
            if task.task_id != row["task_id"] or task.run_id != run_id:
                raise StoreCorruptionError(f"task row {row['task_id']} disagrees with its payload")
            if task.revision != row["revision"] or task.status != row["status"] or task.priority != row["priority"]:
                raise StoreCorruptionError(f"task {task.task_id} columns disagree with its payload")
        for row in connection.execute("SELECT payload FROM findings WHERE run_id=?", (run_id,)):
            Finding.from_dict(json.loads(row["payload"]))
        for table in ("checkpoints", "route_lanes", "route_outcomes"):
            for row in connection.execute(f"SELECT payload FROM {table} WHERE run_id=?", (run_id,)):
                json.loads(row["payload"])
        for row in connection.execute(
            "SELECT owned_resources FROM attempts WHERE task_id IN (SELECT task_id FROM tasks WHERE run_id=?)",
            (run_id,),
        ):
            resources = json.loads(row["owned_resources"])
            if not (
                isinstance(resources, list)
                or isinstance(resources, dict) and isinstance(resources.get("paths"), list)
            ):
                raise StoreCorruptionError("attempt owned_resources must be a list or a paths record")
        events = [
            Event.from_dict(json.loads(row["payload"]))
            for row in connection.execute("SELECT payload FROM events WHERE run_id=? ORDER BY sequence", (run_id,))
        ]
        expected_tasks = {event.task_id for event in events if event.kind == "task_created"}
        actual_tasks = {row[0] for row in connection.execute("SELECT task_id FROM tasks WHERE run_id=?", (run_id,))}
        if expected_tasks != actual_tasks:
            raise StoreCorruptionError(f"run {run_id} task rows disagree with its journal")
        identity_checks = (
            ("finding_recorded", "finding_id", "findings", "finding_id"),
            ("checkpoint_saved", "checkpoint_id", "checkpoints", "checkpoint_id"),
            ("route_outcome_recorded", "outcome_id", "route_outcomes", "outcome_id"),
        )
        for kind, data_key, table, column in identity_checks:
            expected = {event.data[data_key] for event in events if event.kind == kind}
            actual = {row[0] for row in connection.execute(f"SELECT {column} FROM {table} WHERE run_id=?", (run_id,))}
            if expected != actual:
                raise StoreCorruptionError(f"run {run_id} {table} rows disagree with its journal")
        expected_lanes = {event.task_id for event in events if event.kind == "route_lane_created"}
        actual_lanes = {row[0] for row in connection.execute("SELECT task_id FROM route_lanes WHERE run_id=?", (run_id,))}
        if expected_lanes != actual_lanes:
            raise StoreCorruptionError(f"run {run_id} route lane rows disagree with its journal")
        expected_attempt_keys = {
            f"{event.task_id}:{event.data['revision']}"
            for event in events
            if event.kind == "task_transitioned" and event.data.get("to") == TaskStatus.CLAIMED
        }
        actual_attempt_keys = {row[0] for row in connection.execute(
            "SELECT idempotency_key FROM attempts WHERE task_id IN (SELECT task_id FROM tasks WHERE run_id=?)",
            (run_id,),
        )}
        if expected_attempt_keys != actual_attempt_keys:
            raise StoreCorruptionError(f"run {run_id} attempt rows disagree with its journal")
        waiting_tasks = {row[0] for row in connection.execute(
            "SELECT task_id FROM tasks WHERE run_id=? AND status=?", (run_id, TaskStatus.WAITING_EXTERNAL)
        )}
        wait_rows = {row[0] for row in connection.execute(
            "SELECT task_id FROM external_waits WHERE task_id IN (SELECT task_id FROM tasks WHERE run_id=?)",
            (run_id,),
        )}
        if waiting_tasks != wait_rows:
            raise StoreCorruptionError(f"run {run_id} external wait rows disagree with task state")
        audit_checkpoints: dict[int, str] = {}
        for row in connection.execute(
            "SELECT payload FROM checkpoints WHERE run_id=? AND reason='security_audit'", (run_id,)
        ):
            payload = json.loads(row["payload"])
            audit_checkpoints[int(payload["sequence"])] = str(payload["digest"])
        previous_digest: str | None = None
        audit_rows: dict[int, str] = {}
        for row in connection.execute("SELECT * FROM security_audit WHERE run_id=? ORDER BY sequence", (run_id,)):
            payload = json.loads(row["payload"])
            sequence = int(row["sequence"])
            if sequence != len(audit_rows) + 1:
                raise StoreCorruptionError(f"run {run_id} security audit sequence has a gap")
            if payload.get("sequence") != sequence or payload.get("digest") != row["digest"]:
                raise StoreCorruptionError(f"run {run_id} security audit row disagrees with its payload")
            if payload.get("previous_digest") != previous_digest:
                raise StoreCorruptionError(f"run {run_id} security audit chain is broken")
            audit_rows[sequence] = str(row["digest"])
            previous_digest = str(row["digest"])
        if audit_rows != audit_checkpoints:
            raise StoreCorruptionError(f"run {run_id} security audit rows disagree with its journal checkpoints")

    def _restore_matching_snapshot(self, run_id: str) -> bool:
        with self._connect() as connection:
            head = connection.execute(
                "SELECT sequence,event_hash FROM events WHERE run_id=? ORDER BY sequence DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            if head is None:
                return False
            candidates = connection.execute(
                "SELECT * FROM snapshots WHERE run_id=? ORDER BY event_sequence DESC LIMIT ?",
                (run_id, MAX_RECOVERY_SNAPSHOTS),
            ).fetchall()
        for row in candidates:
            if row["event_sequence"] != head["sequence"] or row["journal_hash"] != head["event_hash"]:
                continue
            if hashlib.sha256(row["payload"].encode()).hexdigest() != row["payload_hash"]:
                continue
            try:
                snapshot = json.loads(row["payload"])
                run = Run.from_dict(snapshot["run"])
                tasks = [Task.from_dict(item) for item in snapshot["tasks"]]
                findings = [Finding.from_dict(item) for item in snapshot["findings"]]
                recovery = snapshot["_recovery"]
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
            if run.run_id != run_id or any(task.run_id != run_id for task in tasks):
                continue
            with self._transaction() as connection:
                connection.execute("DELETE FROM security_audit WHERE run_id=?", (run_id,))
                connection.execute("DELETE FROM route_outcomes WHERE run_id=?", (run_id,))
                connection.execute("DELETE FROM route_lanes WHERE run_id=?", (run_id,))
                connection.execute("DELETE FROM external_waits WHERE task_id IN (SELECT task_id FROM tasks WHERE run_id=?)", (run_id,))
                connection.execute("DELETE FROM attempts WHERE task_id IN (SELECT task_id FROM tasks WHERE run_id=?)", (run_id,))
                connection.execute("DELETE FROM checkpoints WHERE run_id=?", (run_id,))
                connection.execute("DELETE FROM findings WHERE run_id=?", (run_id,))
                connection.execute("DELETE FROM tasks WHERE run_id=?", (run_id,))
                connection.execute(
                    "UPDATE runs SET revision=?,status=?,payload=? WHERE run_id=?",
                    (run.revision, run.status, self._dump(run.to_dict()), run_id),
                )
                for task in tasks:
                    connection.execute(
                        "INSERT INTO tasks VALUES(?,?,?,?,?,?)",
                        (task.task_id, task.run_id, task.revision, task.status, task.priority, self._dump(task.to_dict())),
                    )
                for finding in findings:
                    connection.execute(
                        "INSERT INTO findings VALUES(?,?,?,?)",
                        (finding.finding_id, finding.run_id, finding.task_id, self._dump(finding.to_dict())),
                    )
                for item in recovery.get("checkpoints", []):
                    connection.execute(
                        "INSERT INTO checkpoints VALUES(?,?,?,?,?,?)",
                        (item["checkpoint_id"], run_id, item["task_id"], item["reason"], item["created_at"], item["payload"]),
                    )
                for item in recovery.get("attempts", []):
                    connection.execute(
                        "INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        tuple(item[key] for key in (
                            "attempt_id", "task_id", "idempotency_key", "worker_id", "session_id",
                            "lease_expires_at", "last_progress_at", "owned_resources", "base_identity",
                            "head_identity", "failure_signature", "next_action", "active",
                        )),
                    )
                for item in recovery.get("external_waits", []):
                    connection.execute(
                        "INSERT INTO external_waits VALUES(?,?,?,?)",
                        (item["task_id"], item["due_at"], item["reason"], item["created_at"]),
                    )
                for item in recovery.get("route_lanes", []):
                    connection.execute(
                        "INSERT INTO route_lanes VALUES(?,?,?,?,?)",
                        (item["task_id"], run_id, item["revision"], item["updated_at"], item["payload"]),
                    )
                for item in recovery.get("route_outcomes", []):
                    connection.execute(
                        "INSERT INTO route_outcomes VALUES(?,?,?,?,?,?)",
                        (item["outcome_id"], run_id, item["task_id"], item["attempt_id"], item["recorded_at"], item["payload"]),
                    )
                for item in recovery.get("security_audit", []):
                    connection.execute(
                        "INSERT INTO security_audit VALUES(?,?,?,?,?,?)",
                        (run_id, item["sequence"], item["digest"], item["task_id"], item["created_at"], item["payload"]),
                    )
            return True
        return False

    def _startup_integrity_check(self) -> None:
        connection = self._connect()
        invalid: list[tuple[str, BaseException]] = []
        try:
            connection.execute("BEGIN")
            quick = connection.execute("PRAGMA quick_check(1)").fetchone()[0]
            if quick != "ok":
                raise StoreCorruptionError(f"SQLite quick_check failed: {quick}")
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchone()
            if foreign_keys is not None:
                raise StoreCorruptionError("SQLite foreign-key integrity check failed")
            run_ids = [row[0] for row in connection.execute("SELECT run_id FROM runs ORDER BY run_id")]
            for run_id in run_ids:
                if not self._journal_valid(connection, run_id):
                    raise StoreCorruptionError(f"event journal integrity check failed for run {run_id}")
                try:
                    self._validate_run_state(connection, run_id)
                except (StoreCorruptionError, ValueError, TypeError, json.JSONDecodeError) as error:
                    invalid.append((run_id, error))
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        for run_id, error in invalid:
            if not self._restore_matching_snapshot(run_id):
                raise StoreCorruptionError(
                    f"run {run_id} state is corrupt and no exact-head snapshot can restore it"
                ) from error
            with self._connect() as connection:
                connection.execute("BEGIN")
                try:
                    if not self._journal_valid(connection, run_id):
                        raise StoreCorruptionError(f"event journal integrity check failed for run {run_id}")
                    self._validate_run_state(connection, run_id)
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise

    def _dump(self, value: Mapping[str, Any]) -> str:
        safe = self._redactor.redact(value)
        return json.dumps(safe, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    def _safe_text(self, value: str) -> str:
        return self._redactor.redact_text(value)

    def _event(self, connection: sqlite3.Connection, event: Event) -> int:
        payload = event.to_dict()
        previous = connection.execute(
            "SELECT event_hash FROM events WHERE run_id=? ORDER BY sequence DESC LIMIT 1",
            (event.run_id,),
        ).fetchone()
        previous_hash = previous["event_hash"] if previous else ""
        serialized = self._dump(payload)
        values = {
            "event_id": event.event_id, "run_id": event.run_id,
            "task_id": event.task_id, "kind": self._safe_text(event.kind),
            "occurred_at": event.occurred_at, "payload": serialized,
        }
        event_hash = self._event_digest(values, previous_hash)
        cursor = connection.execute(
            "INSERT INTO events(event_id,run_id,task_id,kind,occurred_at,payload,previous_hash,event_hash) VALUES(?,?,?,?,?,?,?,?)",
            (event.event_id, event.run_id, event.task_id, values["kind"], event.occurred_at, serialized, previous_hash, event_hash),
        )
        return int(cursor.lastrowid)

    def append_event(self, event: Event) -> int:
        with self._transaction() as connection:
            return self._event(connection, event)

    def create_run(self, run: Run) -> Run:
        with self._transaction() as connection:
            connection.execute("INSERT INTO runs VALUES(?,?,?,?)", (run.run_id, run.revision, run.status, self._dump(run.to_dict())))
            self._event(connection, Event.create(run.run_id, "run_created", {"revision": 0, "status": run.status}))
        return run

    def get_run(self, run_id: str, connection: sqlite3.Connection | None = None) -> Run:
        owned = connection is None
        connection = connection or self._connect()
        try:
            row = connection.execute("SELECT payload FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if row is None:
                raise NotFoundError(run_id)
            return Run.from_dict(json.loads(row["payload"]))
        finally:
            if owned:
                connection.close()

    def transition_run(self, run_id: str, target: RunStatus, *, expected_revision: int, next_action: str | None = None) -> Run:
        with self._transaction() as connection:
            current = self.get_run(run_id, connection)
            if current.revision != expected_revision:
                raise ConflictError(f"stale run revision {expected_revision}")
            if current.status == target and (next_action is None or next_action == current.next_action):
                return current
            validate_transition(current.status, target, RUN_TRANSITIONS)
            updated = replace(current, status=target, revision=current.revision + 1, updated_at=utc_now(), next_action=current.next_action if next_action is None else next_action)
            cursor = connection.execute(
                "UPDATE runs SET revision=?,status=?,payload=? WHERE run_id=? AND revision=?",
                (updated.revision, updated.status, self._dump(updated.to_dict()), run_id, expected_revision),
            )
            if cursor.rowcount != 1:
                raise ConflictError(f"stale run revision {expected_revision}")
            self._event(connection, Event.create(run_id, "run_transitioned", {"from": current.status, "to": target, "revision": updated.revision}))
            return updated

    def add_task(self, task: Task) -> Task:
        with self._transaction() as connection:
            if task.task_id in task.dependencies:
                raise ValueError("task cannot depend on itself")
            dependency_rows = connection.execute(
                f"SELECT task_id,run_id FROM tasks WHERE task_id IN ({','.join('?' for _ in task.dependencies)})" if task.dependencies else "SELECT task_id,run_id FROM tasks WHERE 0",
                task.dependencies,
            ).fetchall()
            if len(dependency_rows) != len(task.dependencies) or any(row["run_id"] != task.run_id for row in dependency_rows):
                raise ValueError("dependencies must exist in the same run")
            connection.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?)", (task.task_id, task.run_id, task.revision, task.status, task.priority, self._dump(task.to_dict())))
            self._event(connection, Event.create(task.run_id, "task_created", {"status": task.status}, task_id=task.task_id))
        return task

    def get_task(self, task_id: str, connection: sqlite3.Connection | None = None) -> Task:
        owned = connection is None
        connection = connection or self._connect()
        try:
            row = connection.execute("SELECT payload FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise NotFoundError(task_id)
            return Task.from_dict(json.loads(row["payload"]))
        finally:
            if owned:
                connection.close()

    def list_tasks(self, run_id: str, connection: sqlite3.Connection | None = None) -> list[Task]:
        owned = connection is None
        connection = connection or self._connect()
        try:
            rows = connection.execute("SELECT payload FROM tasks WHERE run_id=? ORDER BY priority DESC, task_id", (run_id,)).fetchall()
            return [Task.from_dict(json.loads(row["payload"])) for row in rows]
        finally:
            if owned:
                connection.close()

    def transition_task(self, task_id: str, target: TaskStatus, *, expected_revision: int, next_action: str | None = None) -> Task:
        with self._transaction() as connection:
            return self._transition_task(connection, task_id, target, expected_revision, next_action=next_action)

    def _transition_task(self, connection: sqlite3.Connection, task_id: str, target: TaskStatus, expected_revision: int, *, next_action: str | None = None, failure_signature: str | None = None, failure_count: int | None = None) -> Task:
        current = self.get_task(task_id, connection)
        if current.revision != expected_revision:
            raise ConflictError(f"stale task revision {expected_revision}")
        if current.status == target and next_action in {None, current.next_action} and failure_signature in {None, current.failure_signature} and failure_count in {None, current.failure_count}:
            return current
        validate_transition(current.status, target, TASK_TRANSITIONS)
        updated = replace(
            current, status=target, revision=current.revision + 1, updated_at=utc_now(),
            next_action=current.next_action if next_action is None else next_action,
            failure_signature=current.failure_signature if failure_signature is None else failure_signature,
            failure_count=current.failure_count if failure_count is None else failure_count,
        )
        cursor = connection.execute(
            "UPDATE tasks SET revision=?,status=?,payload=? WHERE task_id=? AND revision=?",
            (updated.revision, updated.status, self._dump(updated.to_dict()), task_id, expected_revision),
        )
        if cursor.rowcount != 1:
            raise ConflictError(f"stale task revision {expected_revision}")
        if current.status == TaskStatus.WAITING_EXTERNAL and target != TaskStatus.WAITING_EXTERNAL:
            connection.execute("DELETE FROM external_waits WHERE task_id=?", (task_id,))
        self._event(connection, Event.create(current.run_id, "task_transitioned", {"from": current.status, "to": target, "revision": updated.revision}, task_id=task_id))
        return updated

    def promote_ready(self, run_id: str) -> list[Task]:
        """Move proposed tasks whose dependencies finished to READY."""
        promoted: list[Task] = []
        with self._transaction() as connection:
            tasks = self.list_tasks(run_id, connection)
            statuses = {task.task_id: task.status for task in tasks}
            for task in tasks:
                if task.status == TaskStatus.PROPOSED and all(statuses.get(dep) == TaskStatus.DONE for dep in task.dependencies):
                    promoted.append(self._transition_task(connection, task.task_id, TaskStatus.READY, task.revision))
        return promoted

    def claim_ready(self, run_id: str, worker_id: str, *, limit: int, lease_seconds: float, now: float | None = None) -> list[dict[str, Any]]:
        if limit < 1 or lease_seconds <= 0:
            raise ValueError("limit and lease_seconds must be positive")
        timestamp = datetime.now(timezone.utc).timestamp() if now is None else now
        claimed: list[dict[str, Any]] = []
        with self._transaction() as connection:
            run = self.get_run(run_id, connection)
            if run.status != RunStatus.RUNNING or run.cancel_requested:
                return []
            active = int(connection.execute(
                "SELECT COUNT(*) FROM attempts a JOIN tasks t ON t.task_id=a.task_id WHERE t.run_id=? AND a.active=1 AND a.lease_expires_at>?",
                (run_id, timestamp),
            ).fetchone()[0])
            available = max(0, limit - active)
            if available == 0:
                return []
            rows = connection.execute(
                "SELECT payload FROM tasks WHERE run_id=? AND status=? ORDER BY priority DESC, task_id LIMIT ?",
                (run_id, TaskStatus.READY, available),
            ).fetchall()
            for row in rows:
                task = Task.from_dict(json.loads(row["payload"]))
                updated = self._transition_task(connection, task.task_id, TaskStatus.CLAIMED, task.revision)
                attempt_id = uuid4().hex
                key = f"{task.task_id}:{updated.revision}"
                lease_expiry = timestamp + lease_seconds
                connection.execute(
                    "INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (attempt_id, task.task_id, key, worker_id, None, lease_expiry, utc_now(), "[]", None, None, None, self._safe_text(updated.next_action), 1),
                )
                claimed.append({"task": updated, "attempt_id": attempt_id, "idempotency_key": key, "lease_expires_at": lease_expiry})
        return claimed

    def transition_attempt(
        self,
        attempt_id: str,
        worker_id: str,
        target: TaskStatus,
        *,
        expected_task_revision: int,
        now: float | None = None,
        next_action: str | None = None,
    ) -> Task:
        """Transition a claimed task only while its worker owns a live lease."""
        timestamp = datetime.now(timezone.utc).timestamp() if now is None else now
        with self._transaction() as connection:
            attempt = connection.execute(
                "SELECT task_id FROM attempts WHERE attempt_id=? AND worker_id=? AND active=1 AND lease_expires_at>?",
                (attempt_id, worker_id, timestamp),
            ).fetchone()
            if attempt is None:
                raise ConflictError("attempt lease is stale, expired, or not owned by worker")
            updated = self._transition_task(
                connection,
                attempt["task_id"],
                target,
                expected_task_revision,
                next_action=next_action,
            )
            if target in TASK_TERMINAL or target in {TaskStatus.READY, TaskStatus.WAITING_EXTERNAL}:
                connection.execute("UPDATE attempts SET active=0 WHERE attempt_id=?", (attempt_id,))
            return updated

    def renew_lease(self, attempt_id: str, worker_id: str, *, lease_seconds: float, now: float | None = None, next_action: str | None = None) -> float:
        timestamp = datetime.now(timezone.utc).timestamp() if now is None else now
        expiry = timestamp + lease_seconds
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE attempts SET lease_expires_at=?,last_progress_at=?,next_action=COALESCE(?,next_action) WHERE attempt_id=? AND worker_id=? AND active=1 AND lease_expires_at>?",
                (expiry, utc_now(), self._safe_text(next_action) if next_action is not None else None, attempt_id, worker_id, timestamp),
            )
            if cursor.rowcount != 1:
                raise ConflictError("attempt lease is stale, expired, or not owned by worker")
        return expiry

    def wait_external(
        self,
        attempt_id: str,
        worker_id: str,
        *,
        expected_task_revision: int,
        due_at: float,
        reason: str,
        now: float | None = None,
    ) -> Task:
        """Park an owned task until a persisted recheck deadline."""
        timestamp = datetime.now(timezone.utc).timestamp() if now is None else now
        if due_at <= timestamp or not reason.strip():
            raise ValueError("external wait needs a future deadline and reason")
        with self._transaction() as connection:
            attempt = connection.execute(
                "SELECT task_id FROM attempts WHERE attempt_id=? AND worker_id=? AND active=1 AND lease_expires_at>?",
                (attempt_id, worker_id, timestamp),
            ).fetchone()
            if attempt is None:
                raise ConflictError("attempt lease is stale, expired, or not owned by worker")
            self._checkpoint(
                connection,
                self.get_task(attempt["task_id"], connection).run_id,
                "before_external_wait",
                {
                    "due_at": due_at,
                    "reason": reason,
                    "next_action": f"recheck external state: {reason}",
                },
                task_id=attempt["task_id"],
            )
            task = self._transition_task(
                connection,
                attempt["task_id"],
                TaskStatus.WAITING_EXTERNAL,
                expected_task_revision,
                next_action=f"recheck external state: {reason}",
            )
            connection.execute("UPDATE attempts SET active=0 WHERE attempt_id=?", (attempt_id,))
            connection.execute(
                "INSERT INTO external_waits(task_id,due_at,reason,created_at) VALUES(?,?,?,?) "
                "ON CONFLICT(task_id) DO UPDATE SET due_at=excluded.due_at,reason=excluded.reason",
                (task.task_id, due_at, self._safe_text(reason), utc_now()),
            )
            self._event(
                connection,
                Event.create(task.run_id, "external_wait_scheduled", {"due_at": due_at, "reason": reason}, task_id=task.task_id),
            )
            return task

    def release_due_waits(self, run_id: str, *, now: float | None = None) -> list[Task]:
        """Return due external waits to the ready frontier exactly once."""
        timestamp = datetime.now(timezone.utc).timestamp() if now is None else now
        released: list[Task] = []
        with self._transaction() as connection:
            rows = connection.execute(
                "SELECT w.task_id FROM external_waits w JOIN tasks t ON t.task_id=w.task_id "
                "WHERE t.run_id=? AND w.due_at<=? ORDER BY w.due_at,w.task_id",
                (run_id, timestamp),
            ).fetchall()
            for row in rows:
                task = self.get_task(row["task_id"], connection)
                if task.status == TaskStatus.WAITING_EXTERNAL:
                    released.append(
                        self._transition_task(
                            connection,
                            task.task_id,
                            TaskStatus.READY,
                            task.revision,
                            next_action="reconcile external state",
                        )
                    )
                connection.execute("DELETE FROM external_waits WHERE task_id=?", (task.task_id,))
        return released

    def update_attempt_context(
        self,
        attempt_id: str,
        worker_id: str,
        *,
        session_id: str | None = None,
        owned_resources: Sequence[str] = (),
        base_identity: str | None = None,
        head_identity: str | None = None,
        next_action: str = "",
        now: float | None = None,
    ) -> None:
        timestamp = datetime.now(timezone.utc).timestamp() if now is None else now
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE attempts SET session_id=?,owned_resources=?,base_identity=?,head_identity=?,next_action=?,last_progress_at=? WHERE attempt_id=? AND worker_id=? AND active=1 AND lease_expires_at>?",
                (session_id, self._dump({"paths": list(owned_resources)}), base_identity, head_identity, self._safe_text(next_action), utc_now(), attempt_id, worker_id, timestamp),
            )
            if cursor.rowcount != 1:
                raise ConflictError("attempt lease is stale, expired, or not owned by worker")

    def release_expired_leases(self, *, now: float | None = None) -> list[str]:
        timestamp = datetime.now(timezone.utc).timestamp() if now is None else now
        recovered: list[str] = []
        with self._transaction() as connection:
            rows = connection.execute("SELECT attempt_id,task_id FROM attempts WHERE active=1 AND lease_expires_at<=?", (timestamp,)).fetchall()
            for row in rows:
                task = self.get_task(row["task_id"], connection)
                connection.execute("UPDATE attempts SET active=0 WHERE attempt_id=?", (row["attempt_id"],))
                if task.status == TaskStatus.VERIFYING:
                    task = self._transition_task(
                        connection,
                        task.task_id,
                        TaskStatus.RUNNING,
                        task.revision,
                        next_action="recover verifier after expired lease",
                    )
                if task.status in {TaskStatus.CLAIMED, TaskStatus.RUNNING}:
                    self._transition_task(connection, task.task_id, TaskStatus.READY, task.revision, next_action="retry after expired lease")
                    recovered.append(task.task_id)
        return recovered

    def request_cancel(self, run_id: str, *, expected_revision: int) -> Run:
        with self._transaction() as connection:
            current = self.get_run(run_id, connection)
            if current.status in RUN_TERMINAL:
                return current
            updated = replace(current, cancel_requested=True, revision=current.revision + 1, updated_at=utc_now(), next_action="interrupt active work and reconcile")
            cursor = connection.execute("UPDATE runs SET revision=?,payload=? WHERE run_id=? AND revision=?", (updated.revision, self._dump(updated.to_dict()), run_id, expected_revision))
            if cursor.rowcount != 1:
                raise ConflictError(f"stale run revision {expected_revision}")
            connection.execute(
                "UPDATE attempts SET active=0 WHERE task_id IN (SELECT task_id FROM tasks WHERE run_id=?)",
                (run_id,),
            )
            self._event(connection, Event.create(run_id, "cancel_requested", {"revision": updated.revision}))
            return updated

    def record_failure(self, task_id: str, signature: str, *, expected_revision: int, threshold: int = 3) -> Task:
        if threshold < 1 or not signature:
            raise ValueError("threshold must be positive and signature non-empty")
        with self._transaction() as connection:
            task = self.get_task(task_id, connection)
            count = task.failure_count + 1 if task.failure_signature == signature else 1
            target = TaskStatus.CIRCUIT_BROKEN if count >= threshold else TaskStatus.READY
            updated = self._transition_task(connection, task_id, target, expected_revision, next_action="material course correction required" if target == TaskStatus.CIRCUIT_BROKEN else "bounded retry", failure_signature=signature, failure_count=count)
            connection.execute(
                "UPDATE attempts SET active=0,failure_signature=? WHERE task_id=? AND active=1",
                (self._safe_text(signature), task_id),
            )
            return updated

    def ensure_route_lane(
        self,
        run_id: str,
        task_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Persist the first route for a task and return the sticky stored route."""
        with self._transaction() as connection:
            task = self.get_task(task_id, connection)
            if task.run_id != run_id:
                raise ValueError("route lane task must belong to the run")
            row = connection.execute(
                "SELECT payload FROM route_lanes WHERE task_id=?", (task_id,)
            ).fetchone()
            if row is not None:
                return json.loads(row["payload"])
            stored = dict(payload)
            stored["revision"] = 0
            connection.execute(
                "INSERT INTO route_lanes VALUES(?,?,?,?,?)",
                (task_id, run_id, 0, utc_now(), self._dump(stored)),
            )
            self._event(
                connection,
                Event.create(
                    run_id,
                    "route_lane_created",
                    {
                        "profile": stored.get("profile"),
                        "model_version": stored.get("candidate", {}).get("version"),
                    },
                    task_id=task_id,
                ),
            )
            return json.loads(self._dump(stored))

    def get_route_lane(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM route_lanes WHERE task_id=?", (task_id,)
            ).fetchone()
        return None if row is None else json.loads(row["payload"])

    def update_route_lane(
        self,
        task_id: str,
        payload: Mapping[str, Any],
        *,
        expected_revision: int,
    ) -> dict[str, Any]:
        """Revision-check a profile/candidate switch at a checkpoint boundary."""
        with self._transaction() as connection:
            current_row = connection.execute(
                "SELECT run_id,revision,payload FROM route_lanes WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if current_row is None:
                raise NotFoundError(task_id)
            if int(current_row["revision"]) != expected_revision:
                raise ConflictError(f"stale route lane revision {expected_revision}")
            current = json.loads(current_row["payload"])
            updated = dict(payload)
            updated["revision"] = expected_revision + 1
            cursor = connection.execute(
                "UPDATE route_lanes SET revision=?,updated_at=?,payload=? WHERE task_id=? AND revision=?",
                (
                    updated["revision"],
                    utc_now(),
                    self._dump(updated),
                    task_id,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise ConflictError(f"stale route lane revision {expected_revision}")
            self._event(
                connection,
                Event.create(
                    current_row["run_id"],
                    "route_lane_promoted",
                    {
                        "from": current.get("profile"),
                        "to": updated.get("profile"),
                        "model_version": updated.get("candidate", {}).get("version"),
                        "revision": updated["revision"],
                    },
                    task_id=task_id,
                ),
            )
            return json.loads(self._dump(updated))

    def record_route_outcome(
        self,
        run_id: str,
        task_id: str,
        attempt_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Record one redacted, exact-version execution outcome per attempt."""
        outcome_id = uuid4().hex
        recorded_at = utc_now()
        stored = dict(payload)
        stored.update(
            {
                "outcome_id": outcome_id,
                "run_id": run_id,
                "task_id": task_id,
                "attempt_id": attempt_id,
                "recorded_at": recorded_at,
            }
        )
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT payload FROM route_outcomes WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if existing is not None:
                return json.loads(existing["payload"])
            connection.execute(
                "INSERT INTO route_outcomes VALUES(?,?,?,?,?,?)",
                (
                    outcome_id,
                    run_id,
                    task_id,
                    attempt_id,
                    recorded_at,
                    self._dump(stored),
                ),
            )
            self._event(
                connection,
                Event.create(
                    run_id,
                    "route_outcome_recorded",
                    {
                        "outcome_id": outcome_id,
                        "terminal_outcome": stored.get("terminal_outcome"),
                        "model_version": stored.get("model_version"),
                    },
                    task_id=task_id,
                ),
            )
        return json.loads(self._dump(stored))

    def latest_route_outcome(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM route_outcomes WHERE task_id=? ORDER BY recorded_at DESC,rowid DESC LIMIT 1",
                (task_id,),
            ).fetchone()
        return None if row is None else json.loads(row["payload"])

    def list_route_outcomes(self, run_id: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as connection:
            if run_id is None:
                rows = connection.execute(
                    "SELECT payload FROM route_outcomes ORDER BY recorded_at,outcome_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT payload FROM route_outcomes WHERE run_id=? ORDER BY recorded_at,outcome_id",
                    (run_id,),
                ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def add_finding(self, finding: Finding) -> Finding:
        with self._transaction() as connection:
            connection.execute("INSERT INTO findings VALUES(?,?,?,?)", (finding.finding_id, finding.run_id, finding.task_id, self._dump(finding.to_dict())))
            self._event(connection, Event.create(finding.run_id, "finding_recorded", {"finding_id": finding.finding_id, "disposition": finding.disposition}, task_id=finding.task_id))
        return finding

    def checkpoint(self, run_id: str, reason: str, payload: Mapping[str, Any], *, task_id: str | None = None) -> str:
        with self._transaction() as connection:
            return self._checkpoint(connection, run_id, reason, payload, task_id=task_id)

    def _checkpoint(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        reason: str,
        payload: Mapping[str, Any],
        *,
        task_id: str | None = None,
    ) -> str:
        checkpoint_id = uuid4().hex
        connection.execute(
            "INSERT INTO checkpoints VALUES(?,?,?,?,?,?)",
            (checkpoint_id, run_id, task_id, self._safe_text(reason), utc_now(), self._dump(dict(payload))),
        )
        self._event(
            connection,
            Event.create(
                run_id,
                "checkpoint_saved",
                {"checkpoint_id": checkpoint_id, "reason": reason},
                task_id=task_id,
            ),
        )
        return checkpoint_id

    def append_security_audit(
        self,
        run_id: str,
        payload: Mapping[str, Any],
        *,
        expected_sequence: int,
        expected_previous_digest: str | None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Compare-and-swap one audit record and its inspection checkpoint."""
        with self._transaction() as connection:
            latest = connection.execute(
                "SELECT sequence,digest FROM security_audit WHERE run_id=? "
                "ORDER BY sequence DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            actual_sequence = int(latest["sequence"]) if latest is not None else 0
            actual_digest = str(latest["digest"]) if latest is not None else None
            if (
                actual_sequence != expected_sequence
                or actual_digest != expected_previous_digest
            ):
                raise ConflictError("security audit head changed before append")
            safe = json.loads(self._dump(dict(payload)))
            sequence = expected_sequence + 1
            if safe.get("sequence") != sequence:
                raise ValueError("security audit sequence does not follow the expected head")
            if safe.get("previous_digest") != expected_previous_digest:
                raise ValueError("security audit previous digest does not match the expected head")
            digest = safe.get("digest")
            timestamp = safe.get("timestamp")
            if not isinstance(digest, str) or not digest:
                raise ValueError("security audit digest must be a non-empty string")
            if not isinstance(timestamp, str) or not timestamp:
                raise ValueError("security audit timestamp must be a non-empty string")
            connection.execute(
                "INSERT INTO security_audit VALUES(?,?,?,?,?,?)",
                (run_id, sequence, digest, task_id, timestamp, self._dump(safe)),
            )
            self._checkpoint(
                connection,
                run_id,
                "security_audit",
                safe,
                task_id=task_id,
            )
            return safe

    def list_security_audit(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM security_audit WHERE run_id=? ORDER BY sequence",
                (run_id,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def recovery_capsule(self, task_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            task = self.get_task(task_id, connection)
            run = self.get_run(task.run_id, connection)
            checkpoints = connection.execute(
                "SELECT checkpoint_id,created_at,payload FROM checkpoints WHERE task_id=? ORDER BY created_at DESC,rowid DESC",
                (task_id,),
            ).fetchall()
            findings = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM findings WHERE run_id=? AND (task_id=? OR task_id IS NULL) ORDER BY finding_id", (run.run_id, task_id))]
            attempts = [dict(row) for row in connection.execute("SELECT attempt_id,worker_id,session_id,base_identity,head_identity,next_action,active FROM attempts WHERE task_id=? ORDER BY rowid", (task_id,))]
        latest = checkpoints[0] if checkpoints else None
        durable: dict[str, Any] = {}
        for row in checkpoints:
            payload = json.loads(row["payload"])
            for key in ("accepted_decisions", "git_state", "completed_evidence"):
                if key not in durable and key in payload:
                    durable[key] = payload[key]
        return {
            "schema_version": SCHEMA_VERSION,
            "immutable_outcome": run.original_request,
            "task": task.to_dict(),
            "authority": run.authority,
            "accepted_decisions": durable.get("accepted_decisions", []),
            "git_state": durable.get("git_state", {}),
            "completed_evidence": durable.get("completed_evidence", []),
            "open_findings": findings,
            "provider_sessions": attempts,
            "checkpoint_id": latest["checkpoint_id"] if latest else None,
            "next_action": task.next_action or run.next_action,
        }

    def export_run(self, run_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            return self._export_run(connection, run_id)

    def _export_run(self, connection: sqlite3.Connection, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id, connection)
        tasks = [task.to_dict() for task in self.list_tasks(run_id, connection)]
        events = []
        for row in connection.execute("SELECT sequence,payload FROM events WHERE run_id=? ORDER BY sequence", (run_id,)):
            item = json.loads(row["payload"]); item["sequence"] = row["sequence"]; events.append(item)
        findings = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM findings WHERE run_id=? ORDER BY finding_id", (run_id,))]
        checkpoints = [{**json.loads(row["payload"]), "checkpoint_id": row["checkpoint_id"], "reason": row["reason"], "task_id": row["task_id"], "created_at": row["created_at"]} for row in connection.execute("SELECT * FROM checkpoints WHERE run_id=? ORDER BY created_at", (run_id,))]
        route_lanes = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM route_lanes WHERE run_id=? ORDER BY task_id", (run_id,))]
        route_outcomes = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM route_outcomes WHERE run_id=? ORDER BY recorded_at,outcome_id", (run_id,))]
        return {
            "schema_version": SCHEMA_VERSION,
            "run": run.to_dict(),
            "tasks": tasks,
            "events": events,
            "findings": findings,
            "checkpoints": checkpoints,
            "route_lanes": route_lanes,
            "route_outcomes": route_outcomes,
        }

    def _snapshot_payload(self, connection: sqlite3.Connection, run_id: str) -> dict[str, Any]:
        snapshot = self._export_run(connection, run_id)
        task_filter = "task_id IN (SELECT task_id FROM tasks WHERE run_id=?)"
        snapshot["_recovery"] = {
            "attempts": [dict(row) for row in connection.execute(
                f"SELECT * FROM attempts WHERE {task_filter} ORDER BY rowid", (run_id,)
            )],
            "external_waits": [dict(row) for row in connection.execute(
                f"SELECT * FROM external_waits WHERE {task_filter} ORDER BY task_id", (run_id,)
            )],
            "checkpoints": [dict(row) for row in connection.execute(
                "SELECT * FROM checkpoints WHERE run_id=? ORDER BY created_at,rowid", (run_id,)
            )],
            "route_lanes": [dict(row) for row in connection.execute(
                "SELECT * FROM route_lanes WHERE run_id=? ORDER BY task_id", (run_id,)
            )],
            "route_outcomes": [dict(row) for row in connection.execute(
                "SELECT * FROM route_outcomes WHERE run_id=? ORDER BY recorded_at,outcome_id", (run_id,)
            )],
            "security_audit": [dict(row) for row in connection.execute(
                "SELECT * FROM security_audit WHERE run_id=? ORDER BY sequence", (run_id,)
            )],
        }
        return snapshot

    def save_snapshot(self, run_id: str) -> dict[str, Any]:
        with self._transaction() as connection:
            snapshot = self._snapshot_payload(connection, run_id)
            sequence = snapshot["events"][-1]["sequence"] if snapshot["events"] else 0
            serialized = self._dump(snapshot)
            event = connection.execute(
                "SELECT event_hash FROM events WHERE run_id=? AND sequence=?",
                (run_id, sequence),
            ).fetchone()
            connection.execute(
                "INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?,?,?)",
                (run_id, sequence, utc_now(), serialized, hashlib.sha256(serialized.encode()).hexdigest(), event["event_hash"] if event else ""),
            )
        public = dict(snapshot)
        public.pop("_recovery", None)
        return public

    def write_export(self, run_id: str, destination: str | Path) -> Path:
        """Atomically write a compact human-readable snapshot derived from SQLite."""
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.export_run(run_id), sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
        return target

    def verify_journal(self, run_id: str) -> bool:
        with self._connect() as connection:
            return self._journal_valid(connection, run_id)
