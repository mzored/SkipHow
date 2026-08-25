"""Durable GitHub delivery coordination for a completed campaign lane."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Protocol, Sequence

from .schemas import RUN_TERMINAL, RunStatus, TaskStatus
from .security import AuthorityGrant, ProtectedAction, check_protected_action
from .store import RunnerStore


OID = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[A-Za-z0-9_.-]+$")
MERGE_POLICIES = frozenset({"when_green", "when_green_and_approved"})


class DeliveryError(RuntimeError):
    """Delivery configuration, authority, or reconciled state is unsafe."""


class DeliveryInterrupted(RuntimeError):
    """Test-only abrupt failure after an external side effect."""


@contextmanager
def operation_lock(database: Path, operation_id: str):
    """Hold a process-released exclusive lock across reconciliation and mutation."""
    lock_root = database.parent / ".github-delivery-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(operation_id.encode()).hexdigest() + ".lock"
    path = lock_root / name
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, b"0")
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise DeliveryError("another process owns this delivery operation") from exc
        yield
    finally:
        if sys.platform == "win32":
            import msvcrt

            try:
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


@dataclass(frozen=True, slots=True)
class DeliveryPlan:
    operation_id: str
    task_id: str
    repo: str
    issue: int
    branch: str
    base: str
    expected_head: str
    owner: str
    title: str
    body: str
    required_checks: tuple[str, ...]
    merge_policy: str
    cleanup_remote: bool = True

    def __post_init__(self) -> None:
        if not self.operation_id or not self.task_id or not REPOSITORY.fullmatch(self.repo):
            raise DeliveryError("delivery needs an operation ID and owner/repository")
        if self.issue < 1 or not self.branch or not self.base or not self.owner:
            raise DeliveryError("issue, branch, base, and owner are required")
        if self.branch == self.base:
            raise DeliveryError("delivery branch must differ from the default base branch")
        if not OID.fullmatch(self.expected_head):
            raise DeliveryError("expected_head must be a full lowercase commit SHA")
        if not self.required_checks or any(not item for item in self.required_checks):
            raise DeliveryError("the authoritative required-check set must not be empty")
        if len(set(self.required_checks)) != len(self.required_checks):
            raise DeliveryError("required checks must be unique")
        if self.merge_policy not in MERGE_POLICIES:
            raise DeliveryError("durable delivery requires an explicit green merge policy")
        if not self.cleanup_remote:
            raise DeliveryError("verified durable delivery requires owned remote cleanup")

    @property
    def digest(self) -> str:
        encoded = json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @property
    def marker(self) -> str:
        return f"<!-- skiphow-delivery:{self.operation_id}:{self.digest} -->"

    @property
    def pull_request_body(self) -> str:
        return f"{self.body.rstrip()}\n\nCloses #{self.issue}\n\n{self.marker}"


@dataclass(frozen=True, slots=True)
class PullRequestState:
    number: int
    url: str
    head: str
    state: str
    mergeable: str
    review_decision: str
    checks: Mapping[str, tuple[str, ...]]
    merged_at: str | None = None
    base: str = ""
    base_head: str = ""
    merge_commit: str | None = None

    def required_checks_green(self, required: Sequence[str]) -> bool:
        return all(
            self.checks.get(name)
            and all(value == "SUCCESS" for value in self.checks[name])
            for name in required
        )


class DeliveryBackend(Protocol):
    def default_branch(self, plan: DeliveryPlan) -> str: ...
    def reconcile_pull_request(self, plan: DeliveryPlan) -> PullRequestState | None: ...
    def create_pull_request(self, plan: DeliveryPlan) -> PullRequestState: ...
    def refresh_pull_request(self, plan: DeliveryPlan, number: int) -> PullRequestState: ...
    def merge_pull_request(self, plan: DeliveryPlan, number: int) -> None: ...
    def issue_state(self, plan: DeliveryPlan, pull_request: int | None = None) -> str: ...
    def remote_branch_head(self, plan: DeliveryPlan) -> str | None: ...
    def cleanup_remote_branch(self, plan: DeliveryPlan, number: int) -> None: ...
    def default_contains(self, plan: DeliveryPlan) -> bool: ...


class GhDeliveryBackend:
    """Non-interactive gh/git implementation with exact-state checks."""

    def __init__(self, cwd: Path):
        self.cwd = cwd.resolve()

    def _run(
        self,
        command: Sequence[str],
        *,
        allowed: frozenset[int] = frozenset({0}),
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            list(command),
            cwd=self.cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        if completed.returncode not in allowed:
            detail = (completed.stderr or completed.stdout).strip()
            raise DeliveryError(f"command failed: {' '.join(command[:3])}: {detail}")
        return completed

    def _json(self, command: Sequence[str]) -> Any:
        try:
            return json.loads(self._run(command).stdout)
        except json.JSONDecodeError as exc:
            raise DeliveryError("gh returned invalid JSON") from exc

    def default_branch(self, plan: DeliveryPlan) -> str:
        value = self._json(
            ["gh", "repo", "view", plan.repo, "--json", "defaultBranchRef"]
        )
        if not isinstance(value, Mapping) or not isinstance(value.get("defaultBranchRef"), Mapping):
            raise DeliveryError("GitHub repository has no resolvable default branch")
        name = value["defaultBranchRef"].get("name")
        if not isinstance(name, str) or not name:
            raise DeliveryError("GitHub repository has no resolvable default branch")
        return name

    @staticmethod
    def _pull_request(value: Mapping[str, Any]) -> PullRequestState:
        checks: dict[str, list[str]] = {}
        for item in value.get("statusCheckRollup") or []:
            if not isinstance(item, Mapping):
                continue
            name = item.get("name") or item.get("context")
            state = item.get("conclusion") or item.get("state") or item.get("status")
            if name and state:
                checks.setdefault(str(name), []).append(str(state).upper())
        return PullRequestState(
            number=int(value["number"]),
            url=str(value["url"]),
            head=str(value["headRefOid"]),
            state=str(value["state"]).upper(),
            mergeable=str(value.get("mergeable") or "UNKNOWN").upper(),
            review_decision=str(value.get("reviewDecision") or "").upper(),
            checks={key: tuple(states) for key, states in checks.items()},
            merged_at=value.get("mergedAt"),
            base=str(value.get("baseRefName") or ""),
            base_head=str(value.get("baseRefOid") or ""),
            merge_commit=(
                str(value["mergeCommit"].get("oid"))
                if isinstance(value.get("mergeCommit"), Mapping)
                and value["mergeCommit"].get("oid")
                else None
            ),
        )

    def reconcile_pull_request(self, plan: DeliveryPlan) -> PullRequestState | None:
        rows = self._json(
            [
                "gh", "pr", "list", "--repo", plan.repo, "--head", plan.branch,
                "--base", plan.base, "--state", "all", "--limit", "10",
                "--json", "number,url,body,headRefOid,baseRefName,baseRefOid,state,mergeable,reviewDecision,statusCheckRollup,mergedAt,mergeCommit",
            ]
        )
        if not isinstance(rows, list):
            raise DeliveryError("gh returned unexpected pull request list")
        matches = [row for row in rows if isinstance(row, Mapping) and plan.marker in str(row.get("body", ""))]
        if len(matches) > 1:
            raise DeliveryError("multiple pull requests use the delivery operation identity")
        if not matches:
            if rows:
                raise DeliveryError("delivery branch already has an unowned pull request")
            return None
        result = self._pull_request(matches[0])
        if result.head != plan.expected_head:
            raise DeliveryError("pull request head differs from the persisted delivery head")
        return result

    def create_pull_request(self, plan: DeliveryPlan) -> PullRequestState:
        self._run(
            [
                "gh", "pr", "create", "--repo", plan.repo, "--head", plan.branch,
                "--base", plan.base, "--title", plan.title, "--body", plan.pull_request_body,
            ]
        )
        result = self.reconcile_pull_request(plan)
        if result is None:
            raise DeliveryError("created pull request could not be reconciled")
        return result

    def refresh_pull_request(self, plan: DeliveryPlan, number: int) -> PullRequestState:
        value = self._json(
            [
                "gh", "pr", "view", str(number), "--repo", plan.repo,
                "--json", "number,url,headRefOid,baseRefName,baseRefOid,state,mergeable,reviewDecision,statusCheckRollup,mergedAt,mergeCommit",
            ]
        )
        if not isinstance(value, Mapping):
            raise DeliveryError("gh returned unexpected pull request state")
        result = self._pull_request(value)
        if result.head != plan.expected_head:
            raise DeliveryError("pull request head changed after verification")
        return result

    def merge_pull_request(self, plan: DeliveryPlan, number: int) -> None:
        self._run(
            [
                "gh", "pr", "merge", str(number), "--repo", plan.repo,
                "--merge", "--match-head-commit", plan.expected_head,
            ]
        )

    def issue_state(self, plan: DeliveryPlan, pull_request: int | None = None) -> str:
        value = self._json(
            [
                "gh", "issue", "view", str(plan.issue), "--repo", plan.repo,
                "--json", "state,closedByPullRequestsReferences",
            ]
        )
        if not isinstance(value, Mapping):
            raise DeliveryError("gh returned unexpected Issue state")
        state = str(value.get("state") or "").upper()
        if state == "CLOSED" and pull_request is not None:
            closing = value.get("closedByPullRequestsReferences") or []
            if not any(
                isinstance(item, Mapping) and int(item.get("number", -1)) == pull_request
                for item in closing
            ):
                raise DeliveryError("Issue closed without the reconciled pull request relation")
        return state

    def remote_branch_head(self, plan: DeliveryPlan) -> str | None:
        completed = self._run(
            ["gh", "api", f"repos/{plan.repo}/git/ref/heads/{plan.branch}"],
            allowed=frozenset({0, 1}),
        )
        if completed.returncode:
            if "HTTP 404" in completed.stderr:
                return None
            raise DeliveryError("remote branch lookup failed")
        try:
            head = json.loads(completed.stdout)["object"]["sha"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise DeliveryError("gh returned invalid branch state") from exc
        return str(head)

    def cleanup_remote_branch(self, plan: DeliveryPlan, number: int) -> None:
        current = self.refresh_pull_request(plan, number)
        remote = self.remote_branch_head(plan)
        if current.state != "MERGED" or current.head != plan.expected_head:
            raise DeliveryError("refusing cleanup without exact merged PR evidence")
        if remote is None:
            return
        if remote != plan.expected_head:
            raise DeliveryError("refusing cleanup because the remote branch changed")
        origin = self._run(["git", "remote", "get-url", "origin"]).stdout.strip()
        match = re.fullmatch(
            r"(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?",
            origin,
        )
        if match is None or match.group(1).casefold() != plan.repo.casefold():
            raise DeliveryError("refusing cleanup because origin differs from the delivery repository")
        configured_owner = self._run(
            ["git", "config", "--local", "--get", f"branch.{plan.branch}.skiphow-owner"],
            allowed=frozenset({0, 1}),
        )
        if configured_owner.returncode or configured_owner.stdout.strip() != plan.owner:
            raise DeliveryError("refusing cleanup without exact local branch ownership metadata")
        self._run(
            [
                "git", "push", f"--force-with-lease=refs/heads/{plan.branch}:{plan.expected_head}",
                "origin", f":refs/heads/{plan.branch}",
            ]
        )

    def default_contains(self, plan: DeliveryPlan) -> bool:
        value = self._json(
            ["gh", "api", f"repos/{plan.repo}/compare/{plan.expected_head}...{plan.base}"]
        )
        return isinstance(value, Mapping) and value.get("status") in {"ahead", "identical"}


class GitHubDeliveryCoordinator:
    """Reconcile one delivery operation from durable campaign checkpoints."""

    STATE_REASON = "github_delivery_state"
    RECEIPT_REASON = "github_delivery_receipt"

    def __init__(self, store: RunnerStore, backend: DeliveryBackend):
        self.store = store
        self.backend = backend

    def _authority(self, run_id: str, plan: DeliveryPlan) -> None:
        run = self.store.get_run(run_id)
        task = self.store.get_task(plan.task_id)
        if task.run_id != run_id:
            raise DeliveryError("delivery task does not belong to the campaign run")
        authority = run.authority
        exact = {
            "github_repository": plan.repo,
            "github_issue": plan.issue,
            "github_branch": plan.branch,
            "github_owner": plan.owner,
            "github_base": plan.base,
            "github_expected_head": plan.expected_head,
            "github_merge_policy": plan.merge_policy,
        }
        for key, expected in exact.items():
            if authority.get(key) != expected:
                raise DeliveryError(f"saved authority does not grant exact {key}")
        if authority.get("github_delivery") is not True:
            raise DeliveryError("saved authority does not grant GitHub delivery mutation")
        checks = authority.get("github_required_checks")
        if not isinstance(checks, list) or checks != list(plan.required_checks):
            raise DeliveryError("saved authority does not grant the exact required-check set")
        actions = authority.get("protected_actions")
        if not isinstance(actions, list) or not all(isinstance(item, str) for item in actions):
            raise DeliveryError("saved authority has no protected-action grant")
        actor = authority.get("actor", "owner")
        source = authority.get("source", "request")
        if not isinstance(actor, str) or not actor.strip():
            raise DeliveryError("saved authority actor must be a non-empty string")
        if not isinstance(source, str) or not source.strip():
            raise DeliveryError("saved authority source must be a non-empty string")
        try:
            grant = AuthorityGrant(
                actor=actor,
                source=source,
                protected_actions=frozenset(ProtectedAction(item) for item in actions),
            )
        except (TypeError, ValueError) as exc:
            raise DeliveryError("saved authority contains an unknown protected action") from exc
        decision = check_protected_action(ProtectedAction.PROTECTED_BRANCH_MERGE, grant)
        if not decision.allowed:
            raise DeliveryError(decision.reason)
        if plan.cleanup_remote and authority.get("github_cleanup") is not True:
            raise DeliveryError("saved authority does not grant owned remote cleanup")

    def _latest(self, run_id: str, plan: DeliveryPlan) -> dict[str, Any] | None:
        matches = [
            item
            for item in self.store.export_run(run_id)["checkpoints"]
            if item["reason"] == self.STATE_REASON
            and item.get("operation_id") == plan.operation_id
        ]
        if not matches:
            return None
        latest = matches[-1]
        if latest.get("plan_digest") != plan.digest:
            raise DeliveryError("operation identity was reused with a different delivery plan")
        return latest

    def _save(self, run_id: str, plan: DeliveryPlan, state: Mapping[str, Any]) -> None:
        payload = dict(state)
        payload.update({"operation_id": plan.operation_id, "plan_digest": plan.digest})
        self.store.checkpoint(run_id, self.STATE_REASON, payload, task_id=plan.task_id)

    def _receipt_exists(self, run_id: str, plan: DeliveryPlan) -> bool:
        return any(
            item["reason"] == self.RECEIPT_REASON
            and item.get("operation_id") == plan.operation_id
            for item in self.store.export_run(run_id)["checkpoints"]
        )

    def _save_receipt(self, run_id: str, plan: DeliveryPlan, receipt: Mapping[str, Any]) -> None:
        if not self._receipt_exists(run_id, plan):
            self.store.checkpoint(
                run_id,
                self.RECEIPT_REASON,
                receipt,
                task_id=plan.task_id,
            )

    def _before_mutation(
        self,
        run_id: str,
        plan: DeliveryPlan,
        state: dict[str, Any],
        action: str,
    ) -> None:
        prepared = {**state, "next_action": action, "mutation_prepared": action}
        self._save(run_id, plan, prepared)

    @staticmethod
    def _pr_evidence(pr: PullRequestState) -> dict[str, Any]:
        return {
            "number": pr.number,
            "url": pr.url,
            "head": pr.head,
            "state": pr.state,
            "mergeable": pr.mergeable,
            "review_decision": pr.review_decision,
            "checks": {name: list(states) for name, states in pr.checks.items()},
            "merged_at": pr.merged_at,
            "base": pr.base,
            "base_head": pr.base_head,
            "merge_commit": pr.merge_commit,
        }

    @staticmethod
    def _verify_delivered_pr(plan: DeliveryPlan, pr: PullRequestState) -> None:
        if pr.head != plan.expected_head or pr.base != plan.base:
            raise DeliveryError("pull request head or base differs from saved authority")
        if not pr.required_checks_green(plan.required_checks):
            raise DeliveryError("required checks are not successful on the delivered head")
        if plan.merge_policy == "when_green_and_approved" and pr.review_decision != "APPROVED":
            raise DeliveryError("required approval is absent from delivered PR evidence")
        if pr.state == "MERGED" and (not pr.merge_commit or not OID.fullmatch(pr.merge_commit)):
            raise DeliveryError("merged pull request lacks an exact merge commit identity")

    def advance(self, run_id: str, plan: DeliveryPlan) -> dict[str, Any]:
        with operation_lock(self.store.path, plan.operation_id):
            return self._advance(run_id, plan)

    def _advance(self, run_id: str, plan: DeliveryPlan) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        task = self.store.get_task(plan.task_id)
        if run.cancel_requested or run.status.value == "CANCELLED":
            raise DeliveryError("campaign is cancelled; delivery mutation is forbidden")
        if run.status in RUN_TERMINAL and run.status.value != "COMPLETED":
            raise DeliveryError(f"campaign is {run.status.value}; delivery mutation is forbidden")
        if run.status in {RunStatus.NEW, RunStatus.READY, RunStatus.PAUSED}:
            raise DeliveryError(f"campaign is {run.status.value}; delivery is not executable")
        if task.status != TaskStatus.DONE:
            raise DeliveryError("delivery task lacks a completed verified lane")
        self._authority(run_id, plan)
        if self.backend.default_branch(plan) != plan.base:
            raise DeliveryError("authorized base is not the repository default branch")
        state = self._latest(run_id, plan) or {
            "phase": "INTENT",
            "repo": plan.repo,
            "issue": plan.issue,
            "branch": plan.branch,
            "expected_head": plan.expected_head,
            "events": [],
        }
        phase = str(state["phase"])
        if phase == "COMPLETE":
            pr = self.backend.reconcile_pull_request(plan)
            if (
                pr is None
                or pr.state != "MERGED"
            ):
                raise DeliveryError("completed receipt no longer matches exact merged PR evidence")
            self._verify_delivered_pr(plan, pr)
            if self.backend.issue_state(plan, pr.number) != "CLOSED":
                raise DeliveryError("completed receipt no longer matches Issue state")
            if self.backend.remote_branch_head(plan) is not None:
                raise DeliveryError("completed receipt no longer matches owned branch cleanup")
            if not self.backend.default_contains(plan):
                raise DeliveryError("completed receipt no longer matches the default branch")
            receipt = dict(state["receipt"])
            self._save_receipt(run_id, plan, receipt)
            return receipt

        pr = self.backend.reconcile_pull_request(plan)
        if pr is None:
            branch_head = self.backend.remote_branch_head(plan)
            if branch_head != plan.expected_head:
                raise DeliveryError("remote delivery branch does not match expected head")
            if self.backend.issue_state(plan) != "OPEN":
                raise DeliveryError("canonical delivery Issue is not open before PR creation")
            self._before_mutation(run_id, plan, state, "create_pull_request")
            pr = self.backend.create_pull_request(plan)
        if pr.head != plan.expected_head:
            raise DeliveryError("reconciled pull request does not match expected head")
        if pr.base != plan.base:
            raise DeliveryError("reconciled pull request does not match authorized base")
        state.update({"phase": "PR_RECONCILED", "pull_request": self._pr_evidence(pr)})
        self._save(run_id, plan, state)

        if pr.state != "MERGED":
            pr = self.backend.refresh_pull_request(plan, pr.number)
            state["pull_request"] = self._pr_evidence(pr)
            if not pr.required_checks_green(plan.required_checks):
                state.update({"phase": "WAITING_CI", "next_action": "wait for required checks"})
                self._save(run_id, plan, state)
                return {"status": "WAITING_EXTERNAL", **state}
            if pr.mergeable != "MERGEABLE":
                state.update({"phase": "WAITING_MERGEABLE", "next_action": "wait for mergeability"})
                self._save(run_id, plan, state)
                return {"status": "WAITING_EXTERNAL", **state}
            if plan.merge_policy == "when_green_and_approved" and pr.review_decision != "APPROVED":
                state.update({"phase": "WAITING_REVIEW", "next_action": "wait for required approval"})
                self._save(run_id, plan, state)
                return {"status": "WAITING_EXTERNAL", **state}
            state.update({"phase": "CI_VERIFIED", "pull_request": self._pr_evidence(pr)})
            self._save(run_id, plan, state)
            self._before_mutation(run_id, plan, state, "merge_pull_request")
            self.backend.merge_pull_request(plan, pr.number)
            pr = self.backend.refresh_pull_request(plan, pr.number)
        if pr.state != "MERGED":
            state.update({"phase": "WAITING_MERGE", "next_action": "confirm merge"})
            self._save(run_id, plan, state)
            return {"status": "WAITING_EXTERNAL", **state}
        self._verify_delivered_pr(plan, pr)
        state.update({"phase": "MERGE_CONFIRMED", "pull_request": self._pr_evidence(pr)})
        self._save(run_id, plan, state)

        issue_state = self.backend.issue_state(plan, pr.number)
        if issue_state != "CLOSED":
            state.update({"phase": "WAITING_ISSUE_CLOSE", "next_action": "confirm Issue closure"})
            self._save(run_id, plan, state)
            return {"status": "WAITING_EXTERNAL", **state}
        state.update({"phase": "ISSUE_CLOSED", "issue_state": issue_state})
        self._save(run_id, plan, state)

        branch_head = self.backend.remote_branch_head(plan)
        if plan.cleanup_remote and branch_head is not None:
            if branch_head != plan.expected_head:
                raise DeliveryError("owned remote branch changed before cleanup")
            self._before_mutation(run_id, plan, state, "cleanup_remote_branch")
            self.backend.cleanup_remote_branch(plan, pr.number)
            branch_head = self.backend.remote_branch_head(plan)
        if branch_head is not None:
            raise DeliveryError("owned remote branch remains after cleanup")
        state.update({"phase": "CLEANUP_CONFIRMED", "remote_branch_head": None})
        self._save(run_id, plan, state)

        contains = self.backend.default_contains(plan)
        if not contains:
            raise DeliveryError("default branch does not contain the exact delivered head")
        receipt = {
            "schema_version": 1,
            "receipt_type": "github_campaign_delivery",
            "status": "VERIFIED",
            "run_id": run_id,
            "task_id": plan.task_id,
            "operation_id": plan.operation_id,
            "repository": plan.repo,
            "issue": plan.issue,
            "pull_request": pr.number,
            "delivered_head": plan.expected_head,
            "required_checks": list(plan.required_checks),
            "required_checks_source": "saved_run_authority",
            "check_states": {name: list(pr.checks.get(name, ())) for name in plan.required_checks},
            "merge_confirmed": True,
            "base": plan.base,
            "base_head": pr.base_head,
            "merge_commit": pr.merge_commit,
            "issue_closed": True,
            "owned_branch_cleaned": True,
            "default_contains_delivery": True,
            "evidence": {
                "pull_request": self._pr_evidence(pr),
                "issue_state": issue_state,
                "remote_branch_head": branch_head,
            },
        }
        state.update({"phase": "COMPLETE", "next_action": "none", "receipt": receipt})
        self._save(run_id, plan, state)
        self._save_receipt(run_id, plan, receipt)
        return receipt
