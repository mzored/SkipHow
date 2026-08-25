#!/usr/bin/env python3
"""Run the opt-in GitHub lifecycle gate in an owned disposable repository.

This script is deliberately separate from ``scripts/check.py``. It creates remote
GitHub state and therefore requires an explicit live opt-in. Progress is written
after every reconciled phase so an interrupted run can be resumed without creating
duplicate Issues, branches, or pull requests.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Sequence
import uuid


SCHEMA_VERSION = 1
HARNESS_VERSION = "1"
ROOT = Path(__file__).resolve().parents[1]
ENV_OPT_IN = "SKIPHOW_GITHUB_E2E"
REPO_PREFIX = "skiphow-e2e-"
BRANCH = "skiphow/e2e-delivery"
PHASES = (
    "repository",
    "initial_commit",
    "issues",
    "branch",
    "pull_request",
    "ci_success",
    "merge",
    "issue_closed",
    "branch_cleanup",
    "complete",
)
OID = re.compile(r"^[0-9a-f]{40}$")
OWNER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


class GateError(RuntimeError):
    """A refusal, failed command, or unmet lifecycle condition."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    allowed: frozenset[int] = frozenset({0}),
    timeout: float = 180.0,
) -> subprocess.CompletedProcess[str]:
    """Run one argv-only command and return its captured result."""
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError(f"command failed to start: {command[0]}: {type(exc).__name__}") from exc
    if completed.returncode not in allowed:
        detail = (completed.stderr or completed.stdout).strip()
        raise GateError(
            f"command exited {completed.returncode}: {' '.join(command[:3])}: {detail}"
        )
    return completed


def json_output(command: Sequence[str], *, cwd: Path | None = None) -> Any:
    completed = run(command, cwd=cwd)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GateError(f"command returned invalid JSON: {' '.join(command[:3])}") from exc


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def candidate_identity() -> dict[str, Any]:
    revision = run(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.strip()
    dirty = bool(
        run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=ROOT,
        ).stdout.strip()
    )
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    harness_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "repository_revision": revision,
        "repository_dirty": dirty,
        "version": version,
        "harness_sha256": harness_hash,
    }


def load_state(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read state {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise GateError("state has an unsupported schema")
    return value


def new_state(path: Path, owner: str) -> dict[str, Any]:
    if not OWNER.fullmatch(owner):
        raise GateError("--owner must be one GitHub user or organization login")
    run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:10]}"
    name = f"{REPO_PREFIX}{run_id.lower()}"
    workspace = path.with_suffix(path.suffix + ".workspace").resolve()
    if workspace.exists():
        raise GateError(f"refusing pre-existing sandbox workspace: {workspace}")
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "harness_version": HARNESS_VERSION,
        "run_id": run_id,
        "owner": owner,
        "repo": f"{owner}/{name}",
        "ownership_marker": f"skiphow-github-e2e:{run_id}",
        "workspace": str(workspace),
        "started_at": utc_now(),
        "candidate": candidate_identity(),
        "completed_phases": [],
        "events": [],
    }
    atomic_json(path, state)
    return state


def mark(path: Path, state: dict[str, Any], phase: str, evidence: dict[str, Any]) -> None:
    if phase not in PHASES:
        raise GateError(f"unknown phase: {phase}")
    completed = state.setdefault("completed_phases", [])
    if phase not in completed:
        completed.append(phase)
        state.setdefault("events", []).append(
            {"at": utc_now(), "phase": phase, "evidence": evidence}
        )
    state["updated_at"] = utc_now()
    atomic_json(path, state)


def force_crash_after(
    path: Path,
    state: dict[str, Any],
    phase: str,
    requested_phase: str | None,
) -> None:
    if requested_phase != phase:
        return
    state["forced_interruption"] = {"phase": phase, "at": utc_now(), "exit_code": 75}
    state["updated_at"] = utc_now()
    atomic_json(path, state)
    os._exit(75)


def repo_name_is_owned(state: dict[str, Any]) -> bool:
    repo = state.get("repo")
    owner = state.get("owner")
    run_id = state.get("run_id")
    if not all(isinstance(value, str) and value for value in (repo, owner, run_id)):
        return False
    return repo == f"{owner}/{REPO_PREFIX}{run_id.lower()}"


def remote_repo(state: dict[str, Any], *, missing_ok: bool = False) -> dict[str, Any] | None:
    if not repo_name_is_owned(state):
        raise GateError("state does not identify an owned disposable repository")
    completed = run(
        ["gh", "api", f"repos/{state['repo']}"],
        allowed=frozenset({0, 1}),
    )
    if completed.returncode:
        if missing_ok and "HTTP 404" in completed.stderr:
            return None
        detail = completed.stderr.strip() or "unknown gh error"
        raise GateError(f"owned repository is unavailable: {state['repo']}: {detail}")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GateError("gh returned invalid repository JSON") from exc
    if not isinstance(value, dict):
        raise GateError("gh returned unexpected repository JSON")
    if (
        value.get("full_name", "").casefold() != str(state["repo"]).casefold()
        or value.get("private") is not True
        or value.get("description") != state.get("ownership_marker")
        or value.get("archived") is True
    ):
        raise GateError("repository ownership marker, visibility, or identity does not match")
    return value


def verify_repository_marker_file(state: dict[str, Any]) -> None:
    value = json_output(
        ["gh", "api", f"repos/{state['repo']}/contents/.skiphow-e2e-owner.json"]
    )
    if not isinstance(value, dict) or value.get("encoding") != "base64":
        raise GateError("owned repository marker file is unavailable")
    try:
        encoded = "".join(str(value["content"]).split())
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        marker = json.loads(decoded)
    except (KeyError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GateError("owned repository marker file is invalid") from exc
    if not isinstance(marker, dict) or marker != {
        "run_id": state.get("run_id"),
        "ownership_marker": state.get("ownership_marker"),
    }:
        raise GateError("owned repository marker file does not match persisted state")


def ensure_repository(state: dict[str, Any]) -> dict[str, Any]:
    existing = remote_repo(state, missing_ok=True)
    if existing is not None:
        return existing
    run(
        [
            "gh",
            "repo",
            "create",
            str(state["repo"]),
            "--private",
            "--description",
            str(state["ownership_marker"]),
            "--disable-wiki",
        ]
    )
    created = remote_repo(state)
    assert created is not None
    return created


def remote_ref(repo: str, branch: str) -> str | None:
    completed = run(
        ["gh", "api", f"repos/{repo}/git/ref/heads/{branch}"],
        allowed=frozenset({0, 1}),
    )
    if completed.returncode:
        if "HTTP 404" in completed.stderr or (
            "HTTP 409" in completed.stderr
            and "repository is empty" in completed.stderr.casefold()
        ):
            return None
        raise GateError(f"cannot read remote ref {branch}: {completed.stderr.strip()}")
    try:
        value = json.loads(completed.stdout)
        oid = value["object"]["sha"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise GateError("gh returned invalid ref JSON") from exc
    if not isinstance(oid, str) or not OID.fullmatch(oid):
        raise GateError("GitHub returned an invalid ref identity")
    return oid


def configure_git(workspace: Path) -> None:
    run(["git", "config", "user.name", "SkipHow E2E"], cwd=workspace)
    run(["git", "config", "user.email", "skiphow-e2e@users.noreply.github.com"], cwd=workspace)


def workspace_marker(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": state["run_id"],
        "repo": state["repo"],
        "ownership_marker": state["ownership_marker"],
    }


def claim_workspace(state: dict[str, Any]) -> Path:
    workspace = Path(str(state["workspace"]))
    marker_path = workspace / ".skiphow-e2e-workspace.json"
    if not workspace.exists():
        workspace.mkdir(parents=True)
    if not marker_path.exists() and not any(workspace.iterdir()):
        marker_path.write_text(
            json.dumps(workspace_marker(state), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"refusing unowned workspace: {workspace}") from exc
    if marker != workspace_marker(state):
        raise GateError(f"workspace ownership marker does not match: {workspace}")
    return workspace


def canonical_remote(url: str) -> str | None:
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?",
        url.strip(),
    )
    return match.group(1).casefold() if match else None


def ensure_local_repository(state: dict[str, Any], *, fetch_main: bool) -> Path:
    workspace = claim_workspace(state)
    if not (workspace / ".git").is_dir():
        run(["git", "init", "--initial-branch=main"], cwd=workspace)
    remotes = run(["git", "remote"], cwd=workspace).stdout.split()
    if "origin" not in remotes:
        run(
            ["git", "remote", "add", "origin", f"https://github.com/{state['repo']}.git"],
            cwd=workspace,
        )
    origin = run(["git", "remote", "get-url", "origin"], cwd=workspace).stdout.strip()
    if canonical_remote(origin) != str(state["repo"]).casefold():
        raise GateError("workspace origin does not match the owned sandbox repository")
    configure_git(workspace)
    if fetch_main:
        run(["git", "fetch", "origin", "main"], cwd=workspace)
    return workspace


def ensure_workspace(state: dict[str, Any]) -> Path:
    return ensure_local_repository(state, fetch_main=True)


def ensure_initial_commit(state: dict[str, Any]) -> str:
    repo = str(state["repo"])
    existing = remote_ref(repo, "main")
    if existing:
        ensure_workspace(state)
        return existing
    workspace = ensure_local_repository(state, fetch_main=False)
    unborn_branch = run(["git", "symbolic-ref", "--short", "HEAD"], cwd=workspace).stdout.strip()
    if unborn_branch != "main":
        run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], cwd=workspace)
    (workspace / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (workspace / "README.md").write_text("# SkipHow GitHub E2E sandbox\n", encoding="utf-8")
    (workspace / ".skiphow-e2e-owner.json").write_text(
        json.dumps(
            {"run_id": state["run_id"], "ownership_marker": state["ownership_marker"]},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / ".github/workflows/e2e.yml").write_text(
        """name: SkipHow E2E
on:
  pull_request:
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Verify event
        run: test -n "$GITHUB_SHA"
""",
        encoding="utf-8",
    )
    run(
        [
            "git",
            "add",
            "README.md",
            ".skiphow-e2e-owner.json",
            ".skiphow-e2e-workspace.json",
            ".github/workflows/e2e.yml",
        ],
        cwd=workspace,
    )
    staged = run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=workspace,
        allowed=frozenset({0, 1}),
    )
    if staged.returncode == 1:
        run(["git", "commit", "-m", "Initialize owned SkipHow E2E sandbox"], cwd=workspace)
    oid = run(["git", "rev-parse", "HEAD"], cwd=workspace).stdout.strip()
    if not OID.fullmatch(oid):
        raise GateError("local Git returned an invalid commit identity")
    run(["git", "push", "--set-upstream", "origin", "main"], cwd=workspace)
    return oid


def issue_rows(repo: str) -> list[dict[str, Any]]:
    value = json_output(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--limit",
            "100",
            "--json",
            "number,title,body,state,url,blockedBy",
        ]
    )
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise GateError("gh returned unexpected Issue JSON")
    return value


def issue_with_marker(repo: str, marker: str) -> dict[str, Any] | None:
    matches = [row for row in issue_rows(repo) if marker in str(row.get("body", ""))]
    if len(matches) > 1:
        raise GateError(f"multiple Issues contain lifecycle marker {marker}")
    return matches[0] if matches else None


def ensure_issue(
    repo: str,
    *,
    marker: str,
    title: str,
    body: str,
    blocked_by: int | None = None,
) -> dict[str, Any]:
    existing = issue_with_marker(repo, marker)
    if existing is not None:
        return existing
    command = [
        "gh",
        "issue",
        "create",
        "--repo",
        repo,
        "--title",
        title,
        "--body",
        f"{body}\n\n<!-- {marker} -->",
    ]
    if blocked_by is not None:
        command.extend(["--blocked-by", str(blocked_by)])
    run(command)
    created = issue_with_marker(repo, marker)
    if created is None:
        raise GateError("created Issue could not be reconciled")
    return created


def ensure_issues(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    repo = str(state["repo"])
    signal_marker = f"skiphow-e2e-signal:{state['run_id']}"
    delivery_marker = f"skiphow-e2e-delivery:{state['run_id']}"
    signal = ensure_issue(
        repo,
        marker=signal_marker,
        title="E2E signal: deliver the sandbox marker",
        body="Synthetic signal owned by the SkipHow GitHub lifecycle gate.",
    )
    delivery = ensure_issue(
        repo,
        marker=delivery_marker,
        title="E2E delivery: add the verified marker",
        body="This delivery is blocked by the synthetic signal until intake completes.",
        blocked_by=int(signal["number"]),
    )
    blocked_value = delivery.get("blockedBy") or []
    blocked = (
        blocked_value.get("nodes", [])
        if isinstance(blocked_value, dict)
        else blocked_value
    )
    if not isinstance(blocked, list):
        raise GateError("GitHub returned an invalid blocking dependency shape")
    if not any(int(item.get("number", -1)) == int(signal["number"]) for item in blocked if isinstance(item, dict)):
        raise GateError("GitHub did not record the native blocking dependency")
    if str(signal.get("state", "")).upper() != "CLOSED":
        run(["gh", "issue", "close", str(signal["number"]), "--repo", repo, "--reason", "completed"])
    return signal, delivery


def ensure_branch(state: dict[str, Any]) -> str:
    repo = str(state["repo"])
    existing = remote_ref(repo, BRANCH)
    if existing:
        return existing
    workspace = ensure_workspace(state)
    run(["git", "fetch", "origin", "main"], cwd=workspace)
    branch_exists = run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{BRANCH}"],
        cwd=workspace,
        allowed=frozenset({0, 1}),
    ).returncode == 0
    if branch_exists:
        run(["git", "switch", BRANCH], cwd=workspace)
    else:
        run(["git", "switch", "--create", BRANCH, "origin/main"], cwd=workspace)
    (workspace / "delivered.txt").write_text(
        f"verified delivery for {state['run_id']}\n", encoding="utf-8"
    )
    run(["git", "add", "delivered.txt"], cwd=workspace)
    staged = run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=workspace,
        allowed=frozenset({0, 1}),
    )
    if staged.returncode == 1:
        run(["git", "commit", "-m", "Deliver the E2E sandbox marker"], cwd=workspace)
    changed = run(
        ["git", "diff", "--name-only", "origin/main...HEAD"], cwd=workspace
    ).stdout.splitlines()
    if changed != ["delivered.txt"]:
        raise GateError("owned delivery branch contains an unexpected change set")
    oid = run(["git", "rev-parse", "HEAD"], cwd=workspace).stdout.strip()
    if not OID.fullmatch(oid):
        raise GateError("local Git returned an invalid branch identity")
    run(
        [
            "git",
            "push",
            "--set-upstream",
            "origin",
            BRANCH,
        ],
        cwd=workspace,
    )
    return oid


def pr_rows(repo: str) -> list[dict[str, Any]]:
    value = json_output(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--head",
            BRANCH,
            "--limit",
            "10",
            "--json",
            "number,url,state,headRefOid,mergedAt",
        ]
    )
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise GateError("gh returned unexpected pull request JSON")
    return value


def ensure_pr(state: dict[str, Any], issue: int, expected_head: str) -> dict[str, Any]:
    repo = str(state["repo"])
    matches = pr_rows(repo)
    if len(matches) > 1:
        raise GateError("multiple pull requests use the owned delivery branch")
    if not matches:
        run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                repo,
                "--head",
                BRANCH,
                "--base",
                "main",
                "--title",
                "Deliver the SkipHow E2E marker",
                "--body",
                f"Owned lifecycle proof for {state['run_id']}.\n\nCloses #{issue}",
            ]
        )
        matches = pr_rows(repo)
    if len(matches) != 1 or matches[0].get("headRefOid") != expected_head:
        raise GateError("pull request does not match the expected delivery head")
    return matches[0]


def pr_state(repo: str, number: int) -> dict[str, Any]:
    value = json_output(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--repo",
            repo,
            "--json",
            "number,url,state,headRefOid,baseRefOid,mergeable,mergedAt,statusCheckRollup",
        ]
    )
    if not isinstance(value, dict):
        raise GateError("gh returned unexpected pull request state")
    return value


def checks_green(pr: dict[str, Any], expected_head: str) -> bool:
    if pr.get("headRefOid") != expected_head:
        raise GateError("pull request head changed while waiting for checks")
    checks = pr.get("statusCheckRollup") or []
    if not isinstance(checks, list) or not checks:
        return False
    terminal = []
    for check in checks:
        if not isinstance(check, dict):
            return False
        state = str(check.get("conclusion") or check.get("state") or check.get("status") or "").upper()
        terminal.append(state == "SUCCESS")
        if state in {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}:
            raise GateError(f"pull request check failed: {check.get('name') or check.get('context')}")
    return bool(terminal) and all(terminal)


def wait_for_checks(
    repo: str,
    number: int,
    expected_head: str,
    *,
    timeout_seconds: float,
    poll_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while True:
        current = pr_state(repo, number)
        if checks_green(current, expected_head):
            return current
        if time.monotonic() >= deadline:
            raise GateError("timed out waiting for pull request checks")
        time.sleep(poll_seconds)


def ensure_merge(state: dict[str, Any], pr: int, expected_head: str) -> dict[str, Any]:
    repo = str(state["repo"])
    current = pr_state(repo, pr)
    if current.get("headRefOid") != expected_head:
        raise GateError("pull request head changed before merge")
    if str(current.get("state", "")).upper() != "MERGED":
        if not checks_green(current, expected_head):
            raise GateError("refusing merge without successful exact-head checks")
        run(
            [
                "gh",
                "pr",
                "merge",
                str(pr),
                "--repo",
                repo,
                "--merge",
                "--match-head-commit",
                expected_head,
            ]
        )
        current = pr_state(repo, pr)
    if str(current.get("state", "")).upper() != "MERGED":
        raise GateError("GitHub did not confirm the pull request merge")
    return current


def verify_issue_closed(repo: str, number: int) -> dict[str, Any]:
    value = json_output(
        ["gh", "issue", "view", str(number), "--repo", repo, "--json", "number,state,url"]
    )
    if not isinstance(value, dict) or str(value.get("state", "")).upper() != "CLOSED":
        raise GateError("delivery Issue did not close after merge")
    return value


def verify_default_contains(repo: str, delivery_head: str) -> dict[str, Any]:
    value = json_output(["gh", "api", f"repos/{repo}/compare/{delivery_head}...main"])
    if not isinstance(value, dict) or value.get("status") not in {"ahead", "identical"}:
        raise GateError("default branch does not contain the exact delivery head")
    return {
        "status": value["status"],
        "ahead_by": value.get("ahead_by"),
        "behind_by": value.get("behind_by"),
    }


def cleanup_branch(state: dict[str, Any], pr_number: int, expected_head: str) -> None:
    repo = str(state["repo"])
    current = pr_state(repo, pr_number)
    if (
        str(current.get("state", "")).upper() != "MERGED"
        or current.get("headRefOid") != expected_head
    ):
        raise GateError("refusing branch cleanup without exact merged PR evidence")
    remote = remote_ref(repo, BRANCH)
    if remote is None:
        return
    if remote != expected_head:
        raise GateError("refusing branch cleanup because the remote head changed")
    workspace = ensure_workspace(state)
    run(
        [
            "git",
            "push",
            f"--force-with-lease=refs/heads/{BRANCH}:{expected_head}",
            "origin",
            f":refs/heads/{BRANCH}",
        ],
        cwd=workspace,
    )
    if remote_ref(repo, BRANCH) is not None:
        raise GateError("owned remote branch still exists after cleanup")


def write_receipt(path: Path, state: dict[str, Any]) -> None:
    current_candidate = candidate_identity()
    if current_candidate != state.get("candidate") or current_candidate["repository_dirty"]:
        raise GateError("candidate changed or became dirty during the GitHub gate")
    phases = [event.get("phase") for event in state.get("events", [])]
    expected = ["issues", "pull_request", "ci_success", "merge", "branch_cleanup"]
    positions = [phases.index(phase) for phase in expected if phase in phases]
    lifecycle_order = (
        ["issue", "pull_request", "ci_success", "merge", "cleanup"]
        if len(positions) == len(expected) and positions == sorted(positions)
        else []
    )
    recovery = state.get("forced_interruption")
    resume_count = int(state.get("resume_count", 0))
    reconciliation = state.get("final_reconciliation")
    if not isinstance(recovery, dict) or resume_count < 1:
        raise GateError("receipt requires a demonstrated forced interruption and resume")
    if not isinstance(reconciliation, dict):
        raise GateError("receipt requires final GitHub reconciliation")
    if lifecycle_order == []:
        raise GateError("recorded lifecycle phases are incomplete or out of order")
    receipt = {
        "schema_version": 1,
        "receipt_type": "github_lifecycle_e2e",
        "status": "VERIFIED",
        "scenario_id": "github-lifecycle",
        "harness_version": HARNESS_VERSION,
        "run_id": state["run_id"],
        "generated_at": utc_now(),
        "candidate": state.get("candidate"),
        "repository": state["repo"],
        "repository_visibility": "PRIVATE",
        "issue": state["delivery_issue"],
        "pull_request": state["pull_request"],
        "head": state["delivery_head"],
        "observations": {
            "lifecycle-order": lifecycle_order,
            "merged-state-correct": reconciliation.get("default_contains_delivery") is True,
            "owned-branch-cleaned": reconciliation.get("owned_branch_exists"),
            "no-merge-before-green": positions[3] < positions[2],
            "no-unrelated-issue-close": reconciliation.get("unrelated_issues_closed"),
        },
        "evidence": ["github_event_log", "git_state", "github_state"],
        "github_event_log": state["events"],
        "git_state": {"head": state["delivery_head"], "branch_exists": False},
        "github_state": {
            "repository": state["repo"],
            "private": True,
            "delivery_issue_state": "CLOSED",
            "pull_request_state": "MERGED",
            "owned_delivery_branch_exists": False,
        },
        "recovery": {
            "forced_interruption": recovery,
            "resume_count": resume_count,
            "idempotent_reconciliation": True,
        },
    }
    atomic_json(path, receipt)


def execute(
    state_path: Path,
    state: dict[str, Any],
    *,
    timeout_seconds: float,
    poll_seconds: float,
    receipt_path: Path,
    crash_after: str | None,
) -> None:
    repo = str(state["repo"])
    completed = set(state.get("completed_phases", []))
    if "complete" in completed:
        remote_repo(state)
        expected_head = str(state.get("delivery_head", ""))
        pull_request = int(state.get("pull_request", 0))
        delivery_issue = int(state.get("delivery_issue", 0))
        if not OID.fullmatch(expected_head) or not pull_request or not delivery_issue:
            raise GateError("completed state lacks exact lifecycle identities")
        current = pr_state(repo, pull_request)
        if (
            str(current.get("state", "")).upper() != "MERGED"
            or current.get("headRefOid") != expected_head
        ):
            raise GateError("completed state no longer matches the merged pull request")
        verify_issue_closed(repo, delivery_issue)
        if remote_ref(repo, BRANCH) is not None:
            raise GateError("completed state has an unexpected owned remote branch")
        write_receipt(receipt_path, state)
        return
    repository = ensure_repository(state)
    mark(state_path, state, "repository", {"url": repository.get("html_url"), "private": True})
    main_head = ensure_initial_commit(state)
    mark(state_path, state, "initial_commit", {"head": main_head})
    signal, delivery = ensure_issues(state)
    state["signal_issue"] = int(signal["number"])
    state["delivery_issue"] = int(delivery["number"])
    mark(
        state_path,
        state,
        "issues",
        {"signal": state["signal_issue"], "delivery": state["delivery_issue"], "native_dependency": True},
    )
    force_crash_after(state_path, state, "issues", crash_after)
    completed = set(state.get("completed_phases", []))
    if "merge" in completed:
        delivery_head = str(state.get("delivery_head", ""))
        pull_request_number = int(state.get("pull_request", 0))
        if not OID.fullmatch(delivery_head) or not pull_request_number:
            raise GateError("merged state lacks exact delivery identities")
        merged = pr_state(repo, pull_request_number)
        if (
            str(merged.get("state", "")).upper() != "MERGED"
            or merged.get("headRefOid") != delivery_head
        ):
            raise GateError("persisted merge does not match current GitHub state")
    else:
        delivery_head = ensure_branch(state)
        state["delivery_head"] = delivery_head
        mark(state_path, state, "branch", {"branch": BRANCH, "head": delivery_head})
        pull_request = ensure_pr(state, int(delivery["number"]), delivery_head)
        state["pull_request"] = int(pull_request["number"])
        mark(
            state_path,
            state,
            "pull_request",
            {"number": state["pull_request"], "url": pull_request["url"]},
        )
        force_crash_after(state_path, state, "pull_request", crash_after)
        checked = wait_for_checks(
            repo,
            state["pull_request"],
            delivery_head,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
        )
        check_evidence = [
            {
                "name": item.get("name") or item.get("context"),
                "conclusion": item.get("conclusion") or item.get("state"),
            }
            for item in checked.get("statusCheckRollup", [])
            if isinstance(item, dict)
        ]
        mark(
            state_path,
            state,
            "ci_success",
            {"head": delivery_head, "checks": check_evidence},
        )
        force_crash_after(state_path, state, "ci_success", crash_after)
        merged = ensure_merge(state, state["pull_request"], delivery_head)
        mark(
            state_path,
            state,
            "merge",
            {"merged_at": merged.get("mergedAt"), "head": delivery_head},
        )
    closed = verify_issue_closed(repo, int(delivery["number"]))
    mark(
        state_path,
        state,
        "issue_closed",
        {"number": closed["number"], "state": closed["state"]},
    )
    if "branch_cleanup" not in set(state.get("completed_phases", [])):
        cleanup_branch(state, state["pull_request"], delivery_head)
        mark(state_path, state, "branch_cleanup", {"branch": BRANCH, "removed": True})
    elif remote_ref(repo, BRANCH) is not None:
        raise GateError("persisted cleanup does not match current GitHub state")
    comparison = verify_default_contains(repo, delivery_head)
    rows = issue_rows(repo)
    related = {int(state["signal_issue"]), int(state["delivery_issue"])}
    unrelated_closed = sum(
        int(row.get("number", -1)) not in related
        and str(row.get("state", "")).upper() == "CLOSED"
        for row in rows
    )
    state["final_reconciliation"] = {
        "default_contains_delivery": True,
        "comparison": comparison,
        "owned_branch_exists": remote_ref(repo, BRANCH) is not None,
        "unrelated_issues_closed": unrelated_closed,
        "pull_request_state": "MERGED",
        "delivery_issue_state": "CLOSED",
    }
    mark(
        state_path,
        state,
        "complete",
        {"receipt": str(receipt_path.resolve()), **state["final_reconciliation"]},
    )
    write_receipt(receipt_path, state)


def cleanup_repository(state_path: Path, state: dict[str, Any], confirmation: str) -> None:
    if confirmation != state.get("repo"):
        raise GateError("--confirm-delete must exactly match the owned sandbox repository")
    if "complete" not in state.get("completed_phases", []):
        raise GateError("refusing repository deletion before a completed lifecycle receipt")
    existing = remote_repo(state, missing_ok=True)
    if existing is not None:
        verify_repository_marker_file(state)
        run(["gh", "repo", "delete", str(state["repo"]), "--yes"])
    if remote_repo(state, missing_ok=True) is not None:
        raise GateError("owned sandbox still exists after deletion")
    state["repository_deleted_at"] = utc_now()
    state["updated_at"] = utc_now()
    atomic_json(state_path, state)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--state", required=True, type=Path)
    result.add_argument("--owner", help="GitHub user or organization for a new sandbox")
    result.add_argument("--receipt", type=Path)
    result.add_argument("--resume", action="store_true")
    result.add_argument("--live", action="store_true")
    result.add_argument("--timeout-seconds", type=float, default=900.0)
    result.add_argument("--poll-seconds", type=float, default=10.0)
    result.add_argument("--crash-after", choices=("issues", "pull_request", "ci_success"))
    result.add_argument("--cleanup", action="store_true")
    result.add_argument("--confirm-delete")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if not args.live or os.environ.get(ENV_OPT_IN) != "1":
            raise GateError(f"live GitHub mutations require --live and {ENV_OPT_IN}=1")
        if args.timeout_seconds <= 0 or args.poll_seconds <= 0:
            raise GateError("timeouts must be positive")
        state_path = args.state.resolve()
        if state_path.is_relative_to(ROOT):
            raise GateError("--state must be outside the candidate repository")
        if state_path.exists():
            if not args.resume and not args.cleanup:
                raise GateError("state already exists; use --resume")
            state = load_state(state_path)
            if args.resume:
                state["resume_count"] = int(state.get("resume_count", 0)) + 1
                state["last_resumed_at"] = utc_now()
                atomic_json(state_path, state)
            if args.crash_after:
                raise GateError("--crash-after is only valid for the initial run")
            if args.owner and args.owner.casefold() != str(state.get("owner", "")).casefold():
                raise GateError("--owner does not match persisted state")
        else:
            if args.resume or args.cleanup:
                raise GateError("cannot resume or clean up without persisted state")
            if not args.owner:
                raise GateError("--owner is required for a new sandbox")
            if not args.crash_after:
                raise GateError("a new gate run requires --crash-after to prove recovery")
            candidate = candidate_identity()
            if candidate["repository_dirty"]:
                raise GateError("the GitHub release gate requires a clean committed candidate")
            state = new_state(state_path, args.owner)
        if args.cleanup:
            cleanup_repository(state_path, state, args.confirm_delete or "")
            print(json.dumps({"status": "CLEANED", "repository": state["repo"]}))
            return 0
        receipt = (args.receipt or state_path.with_suffix(".receipt.json")).resolve()
        if receipt.is_relative_to(ROOT):
            raise GateError("--receipt must be outside the candidate repository")
        execute(
            state_path,
            state,
            timeout_seconds=args.timeout_seconds,
            poll_seconds=args.poll_seconds,
            receipt_path=receipt,
            crash_after=args.crash_after,
        )
        print(json.dumps({"status": "VERIFIED", "repository": state["repo"], "receipt": str(receipt)}))
        return 0
    except GateError as exc:
        print(f"GitHub E2E UNVERIFIED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
