"""Transactional SQLite state and append-only journal for the runner."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
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


class RunnerStore:
    """Own runner state in SQLite and expose revision-checked operations."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
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
            if version > SCHEMA_VERSION:
                raise RuntimeError(f"database schema {version} is newer than supported {SCHEMA_VERSION}")
            connection.executescript(
                """
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
                    kind TEXT NOT NULL, occurred_at TEXT NOT NULL, payload TEXT NOT NULL
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
                    PRIMARY KEY (run_id, event_sequence)
                );
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
                """
            )
            if version == 0:
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _dump(self, value: Mapping[str, Any]) -> str:
        safe = self._redactor.redact(value)
        return json.dumps(safe, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    def _safe_text(self, value: str) -> str:
        return self._redactor.redact_text(value)

    def _event(self, connection: sqlite3.Connection, event: Event) -> int:
        payload = event.to_dict()
        cursor = connection.execute(
            "INSERT INTO events(event_id,run_id,task_id,kind,occurred_at,payload) VALUES(?,?,?,?,?,?)",
            (event.event_id, event.run_id, event.task_id, self._safe_text(event.kind), event.occurred_at, self._dump(payload)),
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
            run = self.get_run(run_id, connection)
            tasks = [task.to_dict() for task in self.list_tasks(run_id, connection)]
            events = []
            for row in connection.execute("SELECT sequence,payload FROM events WHERE run_id=? ORDER BY sequence", (run_id,)):
                item = json.loads(row["payload"]); item["sequence"] = row["sequence"]; events.append(item)
            findings = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM findings WHERE run_id=? ORDER BY finding_id", (run_id,))]
            checkpoints = [{**json.loads(row["payload"]), "checkpoint_id": row["checkpoint_id"], "reason": row["reason"], "task_id": row["task_id"], "created_at": row["created_at"]} for row in connection.execute("SELECT * FROM checkpoints WHERE run_id=? ORDER BY created_at", (run_id,))]
        return {"schema_version": SCHEMA_VERSION, "run": run.to_dict(), "tasks": tasks, "events": events, "findings": findings, "checkpoints": checkpoints}

    def save_snapshot(self, run_id: str) -> dict[str, Any]:
        snapshot = self.export_run(run_id)
        sequence = snapshot["events"][-1]["sequence"] if snapshot["events"] else 0
        with self._transaction() as connection:
            connection.execute("INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?)", (run_id, sequence, utc_now(), self._dump(snapshot)))
        return snapshot

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
        export = self.export_run(run_id)
        sequences = [event["sequence"] for event in export["events"]]
        return sequences == sorted(sequences) and len(sequences) == len(set(sequences)) and bool(sequences) and export["events"][0]["kind"] == "run_created"
