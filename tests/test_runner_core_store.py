"""Deterministic store, scheduler, recovery, and reconciliation checks."""

import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skiphow.runner import DurableRunner  # noqa: E402
from skiphow.schemas import Finding, RunStatus, TaskStatus  # noqa: E402
from skiphow.store import ConflictError, RunnerStore  # noqa: E402


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
