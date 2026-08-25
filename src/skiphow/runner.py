"""Small controller API built on the durable store."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .schemas import RUN_TERMINAL, Finding, Run, RunStatus, Task, TaskStatus
from .store import RunnerStore


class DurableRunner:
    def __init__(self, database: str | Path, *, parallelism: int = 1, circuit_threshold: int = 3):
        if parallelism < 1 or circuit_threshold < 1:
            raise ValueError("parallelism and circuit_threshold must be positive")
        self.store = RunnerStore(database)
        self.parallelism = parallelism
        self.circuit_threshold = circuit_threshold

    def start(self, original_request: str, authority: Mapping[str, Any], *, budget: Mapping[str, Any] | None = None, run_id: str | None = None) -> Run:
        run = self.store.create_run(Run.create(original_request, authority, budget=budget, run_id=run_id))
        run = self.store.transition_run(run.run_id, RunStatus.READY, expected_revision=run.revision)
        return self.store.transition_run(run.run_id, RunStatus.RUNNING, expected_revision=run.revision)

    def add_task(self, run_id: str, outcome: str, *, task_id: str | None = None, dependencies: tuple[str, ...] = (), constraints: tuple[str, ...] = (), priority: int = 0) -> Task:
        return self.store.add_task(Task.create(run_id, outcome, task_id=task_id, dependencies=dependencies, constraints=constraints, priority=priority))

    def frontier(
        self,
        run_id: str,
        worker_id: str,
        *,
        lease_seconds: float = 60,
        now: float | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        claim_limit = self.parallelism if limit is None else limit
        if claim_limit < 1 or claim_limit > self.parallelism:
            raise ValueError("frontier limit must be between 1 and runner parallelism")
        self.store.release_expired_leases(now=now)
        self.store.release_due_waits(run_id, now=now)
        self.store.promote_ready(run_id)
        return self.store.claim_ready(
            run_id,
            worker_id,
            limit=claim_limit,
            lease_seconds=lease_seconds,
            now=now,
        )

    def pause(self, run_id: str) -> Run:
        run = self.store.get_run(run_id)
        return self.store.transition_run(run_id, RunStatus.PAUSED, expected_revision=run.revision, next_action="resume when authorized")

    def resume(self, run_id: str) -> Run:
        run = self.store.get_run(run_id)
        return self.store.transition_run(run_id, RunStatus.RUNNING, expected_revision=run.revision, next_action="dispatch ready frontier")

    def cancel(self, run_id: str) -> Run:
        current = self.store.get_run(run_id)
        if current.status in RUN_TERMINAL:
            return current
        run = self.store.request_cancel(run_id, expected_revision=current.revision)
        for task in self.store.list_tasks(run_id):
            if task.status not in {TaskStatus.DONE, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.SUPERSEDED}:
                self.store.transition_task(task.task_id, TaskStatus.CANCELLED, expected_revision=task.revision, next_action="preserve partial work")
        return self.store.transition_run(run_id, RunStatus.CANCELLED, expected_revision=run.revision, next_action="cancelled and reconciled")

    def fail_attempt(self, task_id: str, signature: str) -> Task:
        task = self.store.get_task(task_id)
        return self.store.record_failure(task_id, signature, expected_revision=task.revision, threshold=self.circuit_threshold)

    def status(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        tasks = self.store.list_tasks(run_id)
        counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            counts[task.status.value] += 1
        findings = self.store.export_run(run_id)["findings"]
        active = next((task for task in tasks if task.status in {TaskStatus.CLAIMED, TaskStatus.RUNNING, TaskStatus.VERIFYING}), None)
        return {
            "outcome": run.original_request,
            "run_id": run_id,
            "status": run.status.value,
            "revision": run.revision,
            "tasks": counts,
            "current_task": active.outcome if active else None,
            "last_verified_progress": [task.outcome for task in tasks if task.status == TaskStatus.DONE],
            "saved_findings": len(findings),
            "budget": run.budget,
            "next_action": run.next_action,
            "owner_action": run.next_action if run.status == RunStatus.BLOCKED else None,
        }

    def reconcile(self, run_id: str) -> dict[str, Any]:
        """Derive the terminal run result from persisted task state."""
        run = self.store.get_run(run_id)
        tasks = self.store.list_tasks(run_id)
        if run.status in RUN_TERMINAL:
            return self.status(run_id)
        if run.cancel_requested:
            target, action = RunStatus.CANCELLED, "cancelled and reconciled"
        elif not tasks:
            target, action = RunStatus.COMPLETED, "no work remained"
        elif all(task.status == TaskStatus.DONE for task in tasks):
            target, action = RunStatus.COMPLETED, "all persisted tasks completed"
        elif any(task.status in {TaskStatus.BLOCKED, TaskStatus.CIRCUIT_BROKEN} for task in tasks) and all(task.status in {TaskStatus.DONE, TaskStatus.BLOCKED, TaskStatus.CIRCUIT_BROKEN, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.SUPERSEDED} for task in tasks):
            target, action = RunStatus.BLOCKED, "owner or external action required"
        elif any(task.status == TaskStatus.FAILED for task in tasks) and all(task.status in {TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.SUPERSEDED} for task in tasks):
            target, action = RunStatus.FAILED, "inspect failed task evidence"
        else:
            return self.status(run_id)
        self.store.transition_run(run_id, target, expected_revision=run.revision, next_action=action)
        self.store.save_snapshot(run_id)
        return self.status(run_id)

    def record_finding(self, run_id: str, summary: str, disposition: str, *, task_id: str | None = None, details: Mapping[str, Any] | None = None) -> Finding:
        return self.store.add_finding(Finding.create(run_id, summary, disposition, task_id=task_id, details=details))
