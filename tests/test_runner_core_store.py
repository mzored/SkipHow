"""Deterministic store, scheduler, recovery, and reconciliation checks."""

import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skiphow.runner import DurableRunner  # noqa: E402
from skiphow.schemas import Event, Finding, RunStatus, SCHEMA_VERSION, TaskStatus  # noqa: E402
from skiphow.store import ConflictError, RunnerStore, StoreCorruptionError  # noqa: E402


def make_runner(tmp_path: Path, *, parallelism: int = 2, threshold: int = 3) -> tuple[DurableRunner, str]:
    runner = DurableRunner(tmp_path / "runner.db", parallelism=parallelism, circuit_threshold=threshold)
    run = runner.start("Deliver exact requested outcome", {"mutation": True}, budget={"cost": 10}, run_id="run")
    return runner, run.run_id


def test_revision_cas_and_append_only_journal(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    task = runner.add_task(run_id, "One", task_id="one")
    ready = runner.store.transition_task(task.task_id, TaskStatus.READY, expected_revision=0)
    with pytest.raises(ConflictError, match="stale task revision"):
        runner.store.transition_task(task.task_id, TaskStatus.CLAIMED, expected_revision=0)
    assert runner.store.get_task(task.task_id) == ready
    assert runner.store.verify_journal(run_id)

    with sqlite3.connect(tmp_path / "runner.db") as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM events")


def test_dependencies_bounded_claim_and_no_duplicate_claim(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path, parallelism=2)
    runner.add_task(run_id, "Root", task_id="root", priority=10)
    runner.add_task(run_id, "Child", task_id="child", dependencies=("root",))
    runner.add_task(run_id, "Independent", task_id="other", priority=5)

    first = runner.frontier(run_id, "worker-a", lease_seconds=10, now=100)
    assert [claim["task"].task_id for claim in first] == ["root", "other"]
    assert runner.frontier(run_id, "worker-b", lease_seconds=10, now=101) == []
    assert runner.store.get_task("child").status == TaskStatus.PROPOSED

    root = first[0]
    running = runner.store.transition_attempt(root["attempt_id"], "worker-a", TaskStatus.RUNNING, expected_task_revision=root["task"].revision, now=101)
    verifying = runner.store.transition_attempt(root["attempt_id"], "worker-a", TaskStatus.VERIFYING, expected_task_revision=running.revision, now=101)
    runner.store.transition_attempt(root["attempt_id"], "worker-a", TaskStatus.DONE, expected_task_revision=verifying.revision, now=101)
    runner.store.promote_ready(run_id)
    assert runner.store.get_task("child").status == TaskStatus.READY


def test_two_store_handles_cannot_claim_the_same_task(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path, parallelism=1)
    runner.add_task(run_id, "Race", task_id="race")
    first = DurableRunner(tmp_path / "runner.db", parallelism=1)
    second = DurableRunner(tmp_path / "runner.db", parallelism=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda item: item.frontier(run_id, "worker", now=10), (first, second)))
    assert sorted(len(result) for result in results) == [0, 1]
    export = runner.store.export_run(run_id)
    assert sum(event["kind"] == "task_transitioned" and event["data"]["to"] == "CLAIMED" for event in export["events"]) == 1


def test_expired_lease_recovery_fences_stale_worker(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path, parallelism=1)
    runner.add_task(run_id, "Lease work", task_id="leased")
    old = runner.frontier(run_id, "old", lease_seconds=5, now=10)[0]

    new = runner.frontier(run_id, "new", lease_seconds=5, now=15)[0]
    assert new["attempt_id"] != old["attempt_id"]
    with pytest.raises(ConflictError, match="stale, expired"):
        runner.store.renew_lease(old["attempt_id"], "old", lease_seconds=5, now=15)
    with pytest.raises(ConflictError, match="stale, expired"):
        runner.store.transition_attempt(old["attempt_id"], "old", TaskStatus.RUNNING, expected_task_revision=old["task"].revision, now=15)


def test_expired_lease_recovers_verifying_task(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path, parallelism=1)
    runner.add_task(run_id, "Verify after crash", task_id="verifying")
    claim = runner.frontier(run_id, "old", lease_seconds=5, now=10)[0]
    running = runner.store.transition_attempt(
        claim["attempt_id"], "old", TaskStatus.RUNNING,
        expected_task_revision=claim["task"].revision, now=11,
    )
    runner.store.transition_attempt(
        claim["attempt_id"], "old", TaskStatus.VERIFYING,
        expected_task_revision=running.revision, now=11,
    )

    replacement = runner.frontier(run_id, "new", lease_seconds=5, now=15)

    assert [item["task"].task_id for item in replacement] == ["verifying"]
    with pytest.raises(ConflictError, match="stale, expired"):
        runner.store.transition_attempt(
            claim["attempt_id"], "old", TaskStatus.DONE,
            expected_task_revision=running.revision + 1, now=15,
        )


def test_pause_resume_cancel_are_durable_and_gate_dispatch(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    runner.add_task(run_id, "Pending", task_id="pending")
    paused = runner.pause(run_id)
    assert paused.status == RunStatus.PAUSED
    assert runner.frontier(run_id, "worker", now=1) == []

    reopened = DurableRunner(tmp_path / "runner.db", parallelism=2)
    assert reopened.store.get_run(run_id).status == RunStatus.PAUSED
    reopened.resume(run_id)
    assert len(reopened.frontier(run_id, "worker", now=2)) == 1
    cancelled = reopened.cancel(run_id)
    assert cancelled.status == RunStatus.CANCELLED
    assert reopened.store.get_run(run_id).cancel_requested is True
    assert reopened.store.get_task("pending").status == TaskStatus.CANCELLED
    assert reopened.frontier(run_id, "another", now=3) == []


def test_repeated_failure_trips_circuit_and_independent_lane_runs(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path, parallelism=1, threshold=2)
    runner.add_task(run_id, "Fragile", task_id="fragile", priority=10)
    runner.add_task(run_id, "Independent", task_id="independent")
    first = runner.frontier(run_id, "worker", now=0)[0]
    running = runner.store.transition_attempt(first["attempt_id"], "worker", TaskStatus.RUNNING, expected_task_revision=first["task"].revision, now=0)
    retry = runner.fail_attempt(running.task_id, "same-error")
    assert retry.status == TaskStatus.READY

    second = runner.frontier(run_id, "worker", now=1)[0]
    running = runner.store.transition_attempt(second["attempt_id"], "worker", TaskStatus.RUNNING, expected_task_revision=second["task"].revision, now=1)
    broken = runner.fail_attempt(running.task_id, "same-error")
    assert broken.status == TaskStatus.CIRCUIT_BROKEN
    assert broken.next_action == "material course correction required"
    assert runner.frontier(run_id, "other", now=2)[0]["task"].task_id == "independent"


def test_checkpoint_recovery_capsule_excludes_transcript(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    task = runner.add_task(run_id, "Continue exact task", task_id="handoff", constraints=("do not deploy",))
    ready = runner.store.transition_task(task.task_id, TaskStatus.READY, expected_revision=task.revision, next_action="run focused checks")
    runner.record_finding(run_id, "Unrelated defect", "PERSISTED", task_id=task.task_id)
    checkpoint_id = runner.store.checkpoint(
        run_id,
        "before handoff",
        {
            "accepted_decisions": ["use sqlite"],
            "git_state": {"head": "abc"},
            "completed_evidence": ["unit tests passed"],
            "raw_transcript": "must not be loaded",
        },
        task_id=task.task_id,
    )

    capsule = RunnerStore(tmp_path / "runner.db").recovery_capsule(task.task_id)
    assert capsule["immutable_outcome"] == "Deliver exact requested outcome"
    assert capsule["task"]["constraints"] == ["do not deploy"]
    assert capsule["accepted_decisions"] == ["use sqlite"]
    assert capsule["git_state"] == {"head": "abc"}
    assert capsule["completed_evidence"] == ["unit tests passed"]
    assert capsule["checkpoint_id"] == checkpoint_id
    assert capsule["next_action"] == "run focused checks"
    assert "raw_transcript" not in json.dumps(capsule)


def test_recovery_capsule_carries_facts_across_later_checkpoint(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    runner.add_task(run_id, "Continue exact task", task_id="handoff")
    runner.store.checkpoint(
        run_id,
        "accepted plan",
        {
            "accepted_decisions": ["keep the public contract"],
            "git_state": {"head": "abc"},
            "completed_evidence": ["focused tests passed"],
        },
        task_id="handoff",
    )
    latest = runner.store.checkpoint(
        run_id,
        "provider error",
        {"type": "ConnectionError", "next_action": "retry"},
        task_id="handoff",
    )

    capsule = runner.store.recovery_capsule("handoff")

    assert capsule["checkpoint_id"] == latest
    assert capsule["accepted_decisions"] == ["keep the public contract"]
    assert capsule["git_state"] == {"head": "abc"}
    assert capsule["completed_evidence"] == ["focused tests passed"]


def test_snapshot_export_and_final_report_come_from_state(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    task = runner.add_task(run_id, "Verified work", task_id="done")
    claim = runner.frontier(run_id, "worker", now=0)[0]
    running = runner.store.transition_attempt(claim["attempt_id"], "worker", TaskStatus.RUNNING, expected_task_revision=claim["task"].revision, now=0)
    verifying = runner.store.transition_attempt(claim["attempt_id"], "worker", TaskStatus.VERIFYING, expected_task_revision=running.revision, now=0)
    runner.store.transition_attempt(claim["attempt_id"], "worker", TaskStatus.DONE, expected_task_revision=verifying.revision, now=0)
    runner.record_finding(run_id, "Saved observation", "PERSISTED")

    report = runner.reconcile(run_id)
    assert report["status"] == "COMPLETED"
    assert report["last_verified_progress"] == ["Verified work"]
    assert report["saved_findings"] == 1
    assert runner.reconcile(run_id) == report
    snapshot = runner.store.save_snapshot(run_id)
    assert snapshot["run"]["status"] == "COMPLETED"
    assert snapshot["events"][-1]["kind"] == "run_transitioned"
    export_path = tmp_path / "status.json"
    export_path.write_text("truncated", encoding="utf-8")
    runner.store.write_export(run_id, export_path)
    assert json.loads(export_path.read_text(encoding="utf-8"))["run"]["status"] == "COMPLETED"


def test_process_kill_rolls_back_incomplete_transaction(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    before = runner.store.export_run(run_id)
    script = """
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1], isolation_level=None)
connection.execute('BEGIN IMMEDIATE')
connection.execute("UPDATE runs SET status='FAILED' WHERE run_id='run'")
connection.execute("INSERT INTO events(event_id,run_id,kind,occurred_at,payload) VALUES('uncommitted','run','bad','now','{}')")
os._exit(9)
"""
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path / "runner.db")], check=False)
    assert result.returncode == 9
    reopened = RunnerStore(tmp_path / "runner.db")
    assert reopened.get_run(run_id).status == RunStatus.RUNNING
    assert reopened.export_run(run_id)["events"] == before["events"]
    assert reopened.verify_journal(run_id)


def test_database_newer_than_code_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version = 99")
    with pytest.raises(RuntimeError, match="newer than supported"):
        RunnerStore(path)


def _downgrade_store_to_released_v1(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("DROP TRIGGER events_no_update")
        connection.execute("DROP TRIGGER events_no_delete")
        connection.execute("ALTER TABLE events DROP COLUMN previous_hash")
        connection.execute("ALTER TABLE events DROP COLUMN event_hash")
        connection.execute("ALTER TABLE snapshots DROP COLUMN payload_hash")
        connection.execute("ALTER TABLE snapshots DROP COLUMN journal_hash")
        for table in ("runs", "tasks", "events", "findings"):
            for row in connection.execute(f"SELECT rowid AS storage_rowid,payload FROM {table}").fetchall():
                value = json.loads(row["payload"])
                value["schema_version"] = 1
                connection.execute(
                    f"UPDATE {table} SET payload=? WHERE rowid=?",
                    (json.dumps(value, sort_keys=True, separators=(",", ":")), row["storage_rowid"]),
                )
        for row in connection.execute("SELECT rowid AS storage_rowid,payload FROM snapshots").fetchall():
            value = json.loads(row["payload"])
            value["schema_version"] = 1
            value["run"]["schema_version"] = 1
            for field in ("tasks", "events", "findings"):
                for record in value[field]:
                    record["schema_version"] = 1
            connection.execute(
                "UPDATE snapshots SET payload=? WHERE rowid=?",
                (json.dumps(value, sort_keys=True, separators=(",", ":")), row["storage_rowid"]),
            )
        connection.execute(
            "CREATE TRIGGER events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END"
        )
        connection.execute(
            "CREATE TRIGGER events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END"
        )
        connection.execute("PRAGMA user_version = 1")


def test_released_v1_migration_backs_up_and_resumes_state(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    path = tmp_path / "runner.db"
    runner.add_task(run_id, "Resume after upgrade", task_id="resume")
    runner.store.save_snapshot(run_id)
    _downgrade_store_to_released_v1(path)

    migrated = RunnerStore(path)

    assert migrated.last_backup_path is not None
    assert migrated.last_backup_path.exists()
    with sqlite3.connect(migrated.last_backup_path) as backup:
        assert backup.execute("PRAGMA user_version").fetchone()[0] == 1
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert migrated.get_task("resume").status == TaskStatus.PROPOSED
    assert migrated.verify_journal(run_id)


def test_v1_migration_preserves_nested_user_schema_versions(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "nested.db")
    nested = {"document": {"schema_version": 1, "value": "owner-data"}}
    run = runner.start("Keep nested documents", nested, run_id="nested")
    runner.record_finding(
        run.run_id, "Nested evidence", "PERSISTED", details=nested
    )
    runner.store.append_event(Event.create(run.run_id, "custom_evidence", nested))
    runner.store.save_snapshot(run.run_id)
    _downgrade_store_to_released_v1(tmp_path / "nested.db")

    migrated = RunnerStore(tmp_path / "nested.db")
    exported = migrated.export_run(run.run_id)
    with sqlite3.connect(tmp_path / "nested.db") as connection:
        snapshot = json.loads(connection.execute("SELECT payload FROM snapshots").fetchone()[0])

    assert migrated.get_run(run.run_id).authority["document"]["schema_version"] == 1
    assert exported["findings"][0]["details"]["document"]["schema_version"] == 1
    custom = next(event for event in exported["events"] if event["kind"] == "custom_evidence")
    assert custom["data"]["document"]["schema_version"] == 1
    assert snapshot["run"]["authority"]["document"]["schema_version"] == 1
    assert snapshot["schema_version"] == SCHEMA_VERSION


def test_failed_v1_migration_keeps_database_and_backup_at_v1(tmp_path: Path) -> None:
    runner, _ = make_runner(tmp_path)
    path = tmp_path / "runner.db"
    _downgrade_store_to_released_v1(path)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER events_no_update")
        connection.execute("UPDATE events SET payload='not-json' WHERE sequence=1")
        connection.execute(
            "CREATE TRIGGER events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END"
        )

    with pytest.raises(json.JSONDecodeError):
        RunnerStore(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        columns = {row[1] for row in connection.execute("PRAGMA table_info(events)")}
        assert "event_hash" not in columns
    backups = list(tmp_path.glob("runner.db.v1.*.bak"))
    assert len(backups) == 1


def test_exact_head_snapshot_repairs_committed_materialized_corruption_after_process_exit(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    runner.add_task(run_id, "Recover me", task_id="recover")
    runner.store.save_snapshot(run_id)
    path = tmp_path / "runner.db"
    script = """
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1], isolation_level=None)
connection.execute("UPDATE tasks SET status='FAILED',payload='not-json' WHERE task_id='recover'")
connection.execute('PRAGMA wal_checkpoint(FULL)')
os._exit(23)
"""
    result = subprocess.run([sys.executable, "-c", script, str(path)], check=False)
    assert result.returncode == 23

    reopened = RunnerStore(path)

    assert reopened.get_task("recover").status == TaskStatus.PROPOSED
    assert reopened.verify_journal(run_id)


def test_snapshot_cannot_hide_journal_corruption(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    runner.store.save_snapshot(run_id)
    path = tmp_path / "runner.db"
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER events_no_update")
        connection.execute("UPDATE events SET event_hash=? WHERE run_id=?", ("0" * 64, run_id))

    with pytest.raises(StoreCorruptionError, match="event journal integrity"):
        RunnerStore(path)


def test_startup_detects_task_row_deleted_behind_the_journal(tmp_path: Path) -> None:
    runner, _ = make_runner(tmp_path)
    runner.add_task("run", "Must remain", task_id="deleted")
    with sqlite3.connect(tmp_path / "runner.db") as connection:
        connection.execute("DELETE FROM tasks WHERE task_id='deleted'")

    with pytest.raises(StoreCorruptionError, match="no exact-head snapshot"):
        RunnerStore(tmp_path / "runner.db")


def test_startup_detects_security_audit_row_deleted_behind_checkpoint(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    runner.store.append_security_audit(
        run_id,
        {
            "sequence": 1,
            "previous_digest": None,
            "digest": "audit-digest",
            "timestamp": "2026-08-25T00:00:00+00:00",
        },
        expected_sequence=0,
        expected_previous_digest=None,
    )
    with sqlite3.connect(tmp_path / "runner.db") as connection:
        connection.execute("DELETE FROM security_audit WHERE run_id=?", (run_id,))

    with pytest.raises(StoreCorruptionError, match="no exact-head snapshot"):
        RunnerStore(tmp_path / "runner.db")


def test_snapshot_blocks_concurrent_writer_until_one_consistent_image_is_saved(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    runner.add_task(run_id, "Concurrent", task_id="task")
    captured = threading.Event()
    release = threading.Event()
    writer_started = threading.Event()

    class PausingStore(RunnerStore):
        def _snapshot_payload(self, connection: sqlite3.Connection, target_run: str) -> dict[str, object]:
            value = super()._snapshot_payload(connection, target_run)
            captured.set()
            assert release.wait(timeout=5)
            return value

    store = PausingStore(tmp_path / "runner.db")

    def write() -> None:
        writer_started.set()
        runner.store.transition_task("task", TaskStatus.READY, expected_revision=0)

    with ThreadPoolExecutor(max_workers=2) as pool:
        snapshot_future = pool.submit(store.save_snapshot, run_id)
        assert captured.wait(timeout=5)
        writer_future = pool.submit(write)
        assert writer_started.wait(timeout=5)
        assert not writer_future.done()
        release.set()
        snapshot = snapshot_future.result(timeout=5)
        writer_future.result(timeout=5)

    assert snapshot["tasks"][0]["status"] == TaskStatus.PROPOSED
    assert snapshot["events"][-1]["kind"] == "task_created"
    assert RunnerStore(tmp_path / "runner.db").get_task("task").status == TaskStatus.READY


def test_external_wait_persists_deadline_and_reenters_frontier_once(tmp_path: Path) -> None:
    runner, run_id = make_runner(tmp_path)
    runner.add_task(run_id, "Wait for CI", task_id="ci")
    claim = runner.frontier(run_id, "worker", lease_seconds=100, now=10)[0]
    running = runner.store.transition_attempt(
        claim["attempt_id"], "worker", TaskStatus.RUNNING,
        expected_task_revision=claim["task"].revision, now=10,
    )
    waiting = runner.store.wait_external(
        claim["attempt_id"], "worker", expected_task_revision=running.revision,
        due_at=30, reason="required checks", now=10,
    )
    assert waiting.status == TaskStatus.WAITING_EXTERNAL
    assert DurableRunner(tmp_path / "runner.db").frontier(run_id, "early", now=29) == []
    ready = DurableRunner(tmp_path / "runner.db").frontier(run_id, "recheck", now=30)
    assert [item["task"].task_id for item in ready] == ["ci"]
    assert DurableRunner(tmp_path / "runner.db").store.release_due_waits(run_id, now=31) == []
    reasons = {
        item["reason"] for item in runner.store.export_run(run_id)["checkpoints"]
    }
    assert "before_external_wait" in reasons


def test_store_redacts_secrets_before_persistence_and_export(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.db")
    secret = "sk-proj-abcdefghijklmnopqrstuv"
    run = runner.start(
        f"Use credential {secret}",
        {"access_token": secret},
        run_id="redacted",
    )
    runner.add_task(run.run_id, f"Do not expose {secret}", task_id="task")
    runner.store.checkpoint(
        run.run_id,
        f"provider error {secret}",
        {"diagnostic": f"token={secret}"},
        task_id="task",
    )
    runner.record_finding(
        run.run_id,
        f"Provider printed {secret}",
        "PERSISTED",
        task_id="task",
    )

    persisted = (tmp_path / "runner.db").read_bytes()
    exported = json.dumps(runner.store.export_run(run.run_id))

    assert secret.encode() not in persisted
    assert secret not in exported
    assert "[REDACTED]" in exported
