"""Crash-window contracts for durable GitHub campaign delivery."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.github_delivery import (
    DeliveryError,
    DeliveryInterrupted,
    DeliveryPlan,
    GitHubDeliveryCoordinator,
    GhDeliveryBackend,
    PullRequestState,
    operation_lock,
)
from skiphow.runner import DurableRunner
from skiphow.cli import build_parser
from skiphow.schemas import TaskStatus


HEAD = "a" * 40


class FakeBackend:
    def __init__(self) -> None:
        self.pr: PullRequestState | None = None
        self.issue = "OPEN"
        self.branch_head: str | None = HEAD
        self.default_has_head = False
        self.checks_green = True
        self.crash_after: str | None = None
        self.fail_after_merge = False
        self.approved = True
        self.creates = 0
        self.merges = 0
        self.cleanups = 0

    def default_branch(self, plan):
        return "main"

    def _state(self, state: str = "OPEN") -> PullRequestState:
        return PullRequestState(
            7,
            "https://github.com/example/repo/pull/7",
            HEAD,
            state,
            "MERGEABLE",
            "APPROVED" if self.approved else "",
            {"verify": ("SUCCESS",) if self.checks_green else ("PENDING",)},
            "2026-08-25T00:00:00Z" if state == "MERGED" else None,
            "main",
            "b" * 40,
            "c" * 40 if state == "MERGED" else None,
        )

    def reconcile_pull_request(self, plan):
        return self.pr

    def create_pull_request(self, plan):
        self.creates += 1
        self.pr = self._state()
        if self.crash_after == "create":
            self.crash_after = None
            raise DeliveryInterrupted("crash after PR create")
        return self.pr

    def refresh_pull_request(self, plan, number):
        assert self.pr is not None and self.pr.number == number
        return self.pr

    def merge_pull_request(self, plan, number):
        self.merges += 1
        if self.fail_after_merge:
            self.checks_green = False
        self.pr = self._state("MERGED")
        self.issue = "CLOSED"
        self.default_has_head = True
        if self.crash_after == "merge":
            self.crash_after = None
            raise DeliveryInterrupted("crash after merge")

    def issue_state(self, plan, pull_request=None):
        return self.issue

    def remote_branch_head(self, plan):
        return self.branch_head

    def cleanup_remote_branch(self, plan, number):
        self.cleanups += 1
        self.branch_head = None
        if self.crash_after == "cleanup":
            self.crash_after = None
            raise DeliveryInterrupted("crash after cleanup")

    def default_contains(self, plan):
        return self.default_has_head


def authority(**overrides):
    value = {
        "actor": "owner",
        "source": "request",
        "github_delivery": True,
        "github_repository": "example/repo",
        "github_issue": 5,
        "github_branch": "skiphow/delivery",
        "github_owner": "run-1",
        "github_cleanup": True,
        "github_base": "main",
        "github_expected_head": HEAD,
        "github_merge_policy": "when_green",
        "github_required_checks": ["verify"],
        "protected_actions": ["protected-branch-merge"],
    }
    value.update(overrides)
    return value


def plan() -> DeliveryPlan:
    return DeliveryPlan(
        operation_id="delivery:run-1:task-1",
        task_id="task-1",
        repo="example/repo",
        issue=5,
        branch="skiphow/delivery",
        base="main",
        expected_head=HEAD,
        owner="run-1",
        title="Deliver the requested outcome",
        body="Outcome and verification evidence.",
        required_checks=("verify",),
        merge_policy="when_green",
    )


def coordinator(tmp_path: Path, backend: FakeBackend, *, saved_authority=None):
    runner = DurableRunner(tmp_path / "run.sqlite3")
    runner.start("Deliver through GitHub", saved_authority or authority(), run_id="run-1")
    runner.add_task("run-1", "Deliver the campaign result", task_id="task-1")
    claimed = runner.frontier("run-1", "worker", lease_seconds=60)[0]
    task = runner.store.get_task("task-1")
    for target in (
        TaskStatus.RUNNING,
        TaskStatus.VERIFYING,
        TaskStatus.DONE,
    ):
        task = runner.store.transition_attempt(
            claimed["attempt_id"],
            "worker",
            target,
            expected_task_revision=task.revision,
        )
    return runner, GitHubDeliveryCoordinator(runner.store, backend)


def test_delivery_receipt_is_derived_from_reconciled_environment(tmp_path: Path) -> None:
    backend = FakeBackend()
    runner, delivery = coordinator(tmp_path, backend)
    receipt = delivery.advance("run-1", plan())
    assert receipt["status"] == "VERIFIED"
    assert receipt["delivered_head"] == HEAD
    assert receipt["check_states"] == {"verify": ["SUCCESS"]}
    assert backend.creates == backend.merges == backend.cleanups == 1
    reasons = [item["reason"] for item in runner.store.export_run("run-1")["checkpoints"]]
    assert "github_delivery_receipt" in reasons
    assert reasons.count("github_delivery_state") >= 6
    replay = delivery.advance("run-1", plan())
    assert replay == receipt
    assert backend.creates == backend.merges == backend.cleanups == 1


@pytest.mark.parametrize("crash", ["create", "merge", "cleanup"])
def test_resume_reconciles_each_external_mutation_window_without_duplicates(
    tmp_path: Path, crash: str
) -> None:
    backend = FakeBackend()
    backend.crash_after = crash
    runner, delivery = coordinator(tmp_path, backend)
    with pytest.raises(DeliveryInterrupted):
        delivery.advance("run-1", plan())

    reopened = GitHubDeliveryCoordinator(
        DurableRunner(tmp_path / "run.sqlite3").store,
        backend,
    )
    receipt = reopened.advance("run-1", plan())
    assert receipt["status"] == "VERIFIED"
    assert backend.creates == 1
    assert backend.merges == 1
    assert backend.cleanups == 1
    checkpoints = runner.store.export_run("run-1")["checkpoints"]
    prepared = [item["mutation_prepared"] for item in checkpoints if item.get("mutation_prepared")]
    assert {
        "create_pull_request",
        "merge_pull_request",
        "cleanup_remote_branch",
    }.issubset(prepared)


def test_required_checks_release_to_external_wait_without_merge(tmp_path: Path) -> None:
    backend = FakeBackend()
    backend.checks_green = False
    _, delivery = coordinator(tmp_path, backend)
    waiting = delivery.advance("run-1", plan())
    assert waiting["status"] == "WAITING_EXTERNAL"
    assert waiting["phase"] == "WAITING_CI"
    assert backend.merges == 0
    backend.checks_green = True
    backend.pr = backend._state()
    assert delivery.advance("run-1", plan())["status"] == "VERIFIED"


def test_resume_persists_receipt_after_crash_between_complete_state_and_receipt(
    tmp_path: Path,
) -> None:
    backend = FakeBackend()
    runner, delivery = coordinator(tmp_path, backend)
    checkpoint = runner.store.checkpoint
    crashed = False

    def crash_before_receipt(run_id, reason, payload, **kwargs):
        nonlocal crashed
        if reason == delivery.RECEIPT_REASON and not crashed:
            crashed = True
            raise DeliveryInterrupted("crash before receipt checkpoint")
        return checkpoint(run_id, reason, payload, **kwargs)

    runner.store.checkpoint = crash_before_receipt  # type: ignore[method-assign]
    with pytest.raises(DeliveryInterrupted):
        delivery.advance("run-1", plan())

    reopened = DurableRunner(tmp_path / "run.sqlite3")
    receipt = GitHubDeliveryCoordinator(reopened.store, backend).advance("run-1", plan())
    assert receipt["status"] == "VERIFIED"
    receipts = [
        item
        for item in reopened.store.export_run("run-1")["checkpoints"]
        if item["reason"] == delivery.RECEIPT_REASON
    ]
    assert len(receipts) == 1


def test_exact_merge_authority_is_required_before_remote_mutation(tmp_path: Path) -> None:
    backend = FakeBackend()
    runner, delivery = coordinator(
        tmp_path,
        backend,
        saved_authority=authority(protected_actions=[]),
    )
    with pytest.raises(DeliveryError, match="protected-branch-merge"):
        delivery.advance("run-1", plan())
    assert backend.creates == 0
    assert runner.store.export_run("run-1")["checkpoints"] == []


def test_premerged_or_postmerge_failed_checks_cannot_produce_receipt(tmp_path: Path) -> None:
    backend = FakeBackend()
    backend.checks_green = False
    backend.pr = backend._state("MERGED")
    backend.issue = "CLOSED"
    backend.branch_head = None
    backend.default_has_head = True
    _, delivery = coordinator(tmp_path, backend)
    with pytest.raises(DeliveryError, match="required checks"):
        delivery.advance("run-1", plan())

    backend = FakeBackend()
    backend.fail_after_merge = True
    _, delivery = coordinator(tmp_path / "post", backend)
    with pytest.raises(DeliveryError, match="required checks"):
        delivery.advance("run-1", plan())


def test_approval_policy_is_bound_to_authority_and_final_evidence(tmp_path: Path) -> None:
    approved_plan = replace(plan(), merge_policy="when_green_and_approved")
    backend = FakeBackend()
    backend.approved = False
    _, delivery = coordinator(
        tmp_path,
        backend,
        saved_authority=authority(github_merge_policy="when_green_and_approved"),
    )
    waiting = delivery.advance("run-1", approved_plan)
    assert waiting["phase"] == "WAITING_REVIEW"
    assert backend.merges == 0


def test_operation_lock_refuses_concurrent_coordinator(tmp_path: Path) -> None:
    backend = FakeBackend()
    runner, delivery = coordinator(tmp_path, backend)
    with operation_lock(runner.store.path, plan().operation_id):
        with pytest.raises(DeliveryError, match="another process"):
            delivery.advance("run-1", plan())
    assert backend.creates == 0


def test_operation_identity_cannot_be_reused_for_changed_head(tmp_path: Path) -> None:
    backend = FakeBackend()
    _, delivery = coordinator(tmp_path, backend)
    backend.checks_green = False
    delivery.advance("run-1", plan())
    changed = replace(plan(), expected_head="b" * 40)
    with pytest.raises(DeliveryError, match="github_expected_head"):
        delivery.advance("run-1", changed)


def test_delivery_requires_distinct_branch_and_actual_default_base(tmp_path: Path) -> None:
    with pytest.raises(DeliveryError, match="must differ"):
        replace(plan(), branch="main")
    backend = FakeBackend()
    backend.default_branch = lambda plan: "trunk"  # type: ignore[method-assign]
    _, delivery = coordinator(tmp_path, backend)
    with pytest.raises(DeliveryError, match="repository default"):
        delivery.advance("run-1", plan())
    assert backend.creates == 0


def test_gh_backend_reads_the_repository_default_branch(tmp_path: Path) -> None:
    backend = GhDeliveryBackend(tmp_path)
    with patch.object(
        backend, "_json", return_value={"defaultBranchRef": {"name": "main"}}
    ) as query:
        assert backend.default_branch(plan()) == "main"
    query.assert_called_once_with(
        ["gh", "repo", "view", "example/repo", "--json", "defaultBranchRef"]
    )


def test_cli_exposes_delivery_as_a_separate_campaign_command() -> None:
    args = build_parser().parse_args(
        [
            "github-deliver",
            "run-1",
            "--operation-id",
            "delivery:run-1:task-1",
            "--task-id",
            "task-1",
            "--repo",
            "example/repo",
            "--issue",
            "5",
            "--branch",
            "skiphow/delivery",
            "--expected-head",
            HEAD,
            "--owner",
            "run-1",
            "--title",
            "Deliver outcome",
            "--body",
            "Verification evidence",
            "--required-check",
            "verify",
            "--merge-policy",
            "when_green",
        ]
    )
    assert args.command == "github-deliver"
    assert args.required_check == ["verify"]
