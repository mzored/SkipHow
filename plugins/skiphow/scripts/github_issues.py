#!/usr/bin/env python3
"""Optional GitHub Issues adapter for SkipHow.

The core plugin does not import this module. It runs only after a workflow has
decided to use GitHub for persistence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from dataclasses import dataclass
from functools import cache
from typing import Any, Sequence


TIMEOUT_SECONDS = 30
REMOTE_RE = re.compile(r"(?:github\.com[:/])([^/]+)/([^/]+?)(?:\.git)?$")
OID_RE = re.compile(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}")


class GitHubError(RuntimeError):
    """A bounded GitHub adapter operation failed."""


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    url: str


@dataclass(frozen=True)
class PullRequestGate:
    """Fresh delivery evidence for one exact pull-request head."""

    head: str
    checks_green: bool
    approved: bool
    mergeable: bool
    missing_checks: tuple[str, ...]


@dataclass(frozen=True)
class IssueMutation:
    status: str
    url: str
    relationships: tuple[str, ...]


def run(args: Sequence[str], *, cwd: str = ".") -> str:
    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitHubError(f"cannot run {args[0]}: {exc}") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise GitHubError(detail or f"{' '.join(args[:2])} failed")
    return result.stdout.strip()


def repo_at(cwd: str = ".") -> str:
    remote = run(["git", "remote", "get-url", "origin"], cwd=cwd)
    match = REMOTE_RE.search(remote)
    if not match:
        raise GitHubError("origin is not a GitHub repository")
    return f"{match.group(1)}/{match.group(2)}"


def available(repo: str | None = None, *, cwd: str = ".") -> bool:
    if shutil.which("gh") is None:
        return False
    try:
        run(["gh", "auth", "status"])
        run(["gh", "repo", "view", repo or repo_at(cwd), "--json", "nameWithOwner"])
    except GitHubError:
        return False
    return True


def _issues(payload: str) -> list[Issue]:
    try:
        rows = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GitHubError("gh returned invalid JSON") from exc
    if not isinstance(rows, list):
        raise GitHubError("gh returned an unexpected issue list")
    issues: list[Issue] = []
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("number"), int)
            or not isinstance(row.get("title"), str)
            or not row["title"]
            or not isinstance(row.get("url"), str)
            or not row["url"]
        ):
            raise GitHubError("gh returned an incomplete issue candidate")
        issues.append(Issue(row["number"], row["title"], row["url"]))
    return issues


def _search(repo: str, query: str) -> list[Issue]:
    return _issues(
        run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                "all",
                "--search",
                query,
                "--limit",
                "20",
                "--json",
                "number,title,url",
            ]
        )
    )


def _json_object(payload: str, *, operation: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GitHubError(f"{operation} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise GitHubError(f"{operation} returned an unexpected value")
    return value


def _validated_oid(value: str) -> str:
    if not OID_RE.fullmatch(value):
        raise GitHubError("expected head must be a full Git object ID")
    return value.lower()


def _validate_branch(branch: str) -> None:
    invalid = (
        not branch
        or branch.startswith("-")
        or branch.startswith("/")
        or branch.endswith(("/", ".", ".lock"))
        or ".." in branch
        or "//" in branch
        or "@{" in branch
        or any(character in branch for character in " ~^:?*[\\")
        or any(part in {"", ".", ".."} for part in branch.split("/"))
    )
    if invalid:
        raise GitHubError("invalid branch name")


def find_candidates(repo: str, summary: str, evidence: str | None = None) -> list[Issue]:
    """Return bounded search candidates without making a duplicate decision."""
    summary_query = " ".join(summary.split())
    if not summary_query:
        raise GitHubError("candidate search requires a non-empty summary")
    if len(summary_query) > 512:
        raise GitHubError("candidate search summary is too long")
    summary_query = summary_query.replace("\\", " ").replace('"', " ")
    queries = [f'"{summary_query}" in:title']
    evidence_query = " ".join((evidence or "").split())
    if len(evidence_query) > 512:
        raise GitHubError("candidate search evidence is too long")
    if evidence_query and evidence_query.casefold() != summary_query.casefold():
        evidence_query = evidence_query.replace("\\", " ").replace('"', " ")
        queries.append(f'"{evidence_query}"')

    candidates: list[Issue] = []
    seen: set[int] = set()
    for query in queries:
        for issue in _search(repo, query):
            if issue.number not in seen:
                seen.add(issue.number)
                candidates.append(issue)
            if len(candidates) == 20:
                return candidates
    return candidates


def find_duplicate(repo: str, summary: str) -> Issue | None:
    """Return only an exact-title duplicate; semantic matching belongs to the controller."""
    normalized = " ".join(summary.split()).casefold()
    for issue in find_candidates(repo, summary):
        candidate = " ".join(issue.title.split()).casefold()
        if candidate == normalized:
            return issue
    return None


@cache
def available_issue_types(repo: str) -> set[str]:
    """Return repository-supported issue types, or an empty set when unavailable."""
    try:
        payload = json.loads(run(["gh", "api", f"repos/{repo}/issue-types"]))
    except (GitHubError, json.JSONDecodeError):
        return set()
    if not isinstance(payload, list):
        return set()
    return {
        str(row["name"])
        for row in payload
        if isinstance(row, dict)
        and isinstance(row.get("name"), str)
        and row.get("is_enabled", True) is not False
    }


@cache
def supported_create_flags() -> set[str]:
    try:
        help_text = run(["gh", "issue", "create", "--help"])
    except GitHubError:
        return set()
    available = set(re.findall(r"(?m)^\s+(?:-\w,\s+)?(--[\w-]+)(?:\s|$)", help_text))
    return available & {"--type", "--parent", "--blocked-by", "--blocking"}


def persist(
    repo: str,
    kind: str,
    title: str,
    body: str,
    *,
    parent: str | None = None,
    blocked_by: str | None = None,
    blocking: str | None = None,
) -> str:
    flags = supported_create_flags()
    args = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
    optional = {
        "--type": kind if kind in available_issue_types(repo) else None,
        "--parent": parent,
        "--blocked-by": blocked_by,
        "--blocking": blocking,
    }
    for flag, value in optional.items():
        if value and flag in flags:
            args.extend([flag, value])
    output = run(args).splitlines()
    if not output:
        raise GitHubError("gh issue create returned no issue URL")
    url = output[-1]
    if not re.fullmatch(rf"https://github\.com/{re.escape(repo)}/issues/\d+", url):
        raise GitHubError("gh issue create returned an unexpected issue URL")
    return url


def ensure_issue(
    repo: str,
    operation_id: str,
    kind: str,
    title: str,
    body: str,
    *,
    allow_create: bool = False,
    parent: int | None = None,
    blocked_by: int | None = None,
    blocking: int | None = None,
) -> IssueMutation:
    """Reconcile one caller-authorized create operation by a durable identity."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", operation_id):
        raise GitHubError("operation_id must be a stable non-secret identifier")
    relationships = tuple(
        sorted(
            (relation, other)
            for relation, other in (
                ("parent", parent),
                ("blocked_by", blocked_by),
                ("blocking", blocking),
            )
            if other is not None
        )
    )
    digest = hashlib.sha256(
        json.dumps(
            {
                "kind": kind,
                "title": title,
                "body": body,
                "relationships": relationships,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode()
    ).hexdigest()
    prefix = f"<!-- skiphow-operation:{operation_id}:"
    marker = f"{prefix}{digest} -->"
    try:
        rows = json.loads(
            run(
                [
                    "gh",
                    "api",
                    f"repos/{repo}/issues",
                    "--method",
                    "GET",
                    "-f",
                    "state=all",
                    "-f",
                    "per_page=100",
                    "--paginate",
                    "--slurp",
                ]
            )
        )
    except json.JSONDecodeError as exc:
        raise GitHubError("gh returned invalid operation listing JSON") from exc
    if not isinstance(rows, list):
        raise GitHubError("gh returned an unexpected operation listing result")
    if rows and all(isinstance(page, list) for page in rows):
        rows = [row for page in rows for row in page]
    matches = [
        row
        for row in rows
        if (
            isinstance(row, dict)
            and "pull_request" not in row
            and prefix in str(row.get("body", ""))
        )
    ]
    if len(matches) > 1:
        raise GitHubError("operation identity is already attached to multiple issues")
    status = "UNCHANGED"
    if matches:
        row = matches[0]
        if marker not in str(row.get("body", "")):
            raise GitHubError("operation identity was reused with a different payload")
        url = row.get("html_url") or row.get("url")
        number = row.get("number")
        if not isinstance(url, str) or not isinstance(number, int):
            raise GitHubError("operation listing returned an incomplete issue")
    else:
        if not allow_create:
            return IssueMutation("NOT_FOUND", "", ())
        url = persist(repo, kind, title, f"{body}\n\n{marker}")
        match = re.search(r"/issues/(\d+)(?:$|[?#])", url)
        if not match:
            raise GitHubError("created Issue URL has no issue number")
        number = int(match.group(1))
        status = "CREATED"
    outcomes: list[str] = []
    for relation, other in (
        ("parent", parent),
        ("blocked_by", blocked_by),
        ("blocking", blocking),
    ):
        if other is not None:
            outcomes.append(f"{relation}:{create_relationship(repo, number, relation, other)}")
    return IssueMutation(status, url, tuple(outcomes))


def create_relationship(repo: str, issue: int, relation: str, other: int) -> str:
    """Create a native Issue relationship, or preserve a marked linked reference."""
    if issue == other:
        raise GitHubError("an issue cannot relate to itself")
    if relation == "parent":
        container, member = other, issue
        suffix = "sub_issues"
    elif relation == "subissue":
        container, member = issue, other
        suffix = "sub_issues"
    elif relation == "blocked_by":
        container, member = issue, other
        suffix = "dependencies/blocked_by"
    elif relation == "blocking":
        container, member = other, issue
        suffix = "dependencies/blocked_by"
    else:
        raise GitHubError(f"unknown issue relationship: {relation}")
    endpoint = f"repos/{repo}/issues/{container}/{suffix}"
    try:
        existing = json.loads(run(["gh", "api", endpoint, "--paginate", "--slurp"]))
    except (GitHubError, json.JSONDecodeError):
        return _fallback_relationship_reference(repo, issue, relation, other)
    if not isinstance(existing, list):
        return _fallback_relationship_reference(repo, issue, relation, other)
    if existing and all(isinstance(page, list) for page in existing):
        existing = [row for page in existing for row in page]
    if any(
        isinstance(row, dict) and row.get("number") == member
        for row in existing
    ):
        return "UNCHANGED"
    try:
        member_data = _json_object(
            run(["gh", "api", f"repos/{repo}/issues/{member}"]),
            operation="gh issue API",
        )
    except GitHubError:
        return _fallback_relationship_reference(repo, issue, relation, other)
    database_id = member_data.get("id")
    if not isinstance(database_id, int):
        return _fallback_relationship_reference(repo, issue, relation, other)
    try:
        run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                endpoint,
                "-F",
                f"sub_issue_id={database_id}" if suffix == "sub_issues" else f"issue_id={database_id}",
            ]
        )
    except GitHubError:
        return _fallback_relationship_reference(repo, issue, relation, other)
    return "LINKED"


def _fallback_relationship_reference(
    repo: str, issue: int, relation: str, other: int
) -> str:
    """Best-effort fallback that never claims a native relationship was created."""
    labels = {
        "parent": "Parent reference",
        "subissue": "Sub-issue reference",
        "blocked_by": "Blocked-by reference",
        "blocking": "Blocking reference",
    }
    marker = f"<!-- skiphow-relationship-reference:{relation}:{other} -->"
    try:
        comments = json.loads(
            run(
                [
                    "gh",
                    "api",
                    f"repos/{repo}/issues/{issue}/comments",
                    "--paginate",
                    "--slurp",
                ]
            )
        )
        if not isinstance(comments, list):
            return "UNVERIFIED"
        if comments and all(isinstance(page, list) for page in comments):
            comments = [row for page in comments for row in page]
        if any(
            isinstance(row, dict) and marker in str(row.get("body", ""))
            for row in comments
        ):
            return "UNVERIFIED"
        reference = f"https://github.com/{repo}/issues/{other}"
        run(
            [
                "gh",
                "issue",
                "comment",
                str(issue),
                "--repo",
                repo,
                "--body",
                "\n".join(
                    [
                        marker,
                        f"{labels[relation]}: {reference}",
                        "",
                        "Native relationship status: UNVERIFIED",
                    ]
                ),
            ]
        )
    except (GitHubError, json.JSONDecodeError):
        pass
    return "UNVERIFIED"


def update_issue(
    repo: str,
    issue: int,
    *,
    title: str | None = None,
    body: str | None = None,
    state: str | None = None,
    expected_title_digest: str | None = None,
    expected_body_digest: str | None = None,
) -> str:
    """Reconcile caller-selected Issue fields and return its canonical URL."""
    if title is None and body is None and state is None:
        raise GitHubError("update_issue requires at least one requested field")
    desired_state = state.upper() if state else None
    if desired_state not in {None, "OPEN", "CLOSED"}:
        raise GitHubError("issue state must be OPEN or CLOSED")
    current = _json_object(
        run(
            [
                "gh",
                "issue",
                "view",
                str(issue),
                "--repo",
                repo,
                "--json",
                "title,body,state,url",
            ]
        ),
        operation="gh issue view",
    )
    url = current.get("url")
    if not isinstance(url, str) or not url:
        raise GitHubError("gh issue view returned no issue URL")
    for field, desired, expected in (
        ("title", title, expected_title_digest),
        ("body", body, expected_body_digest),
    ):
        if desired is None:
            continue
        if expected is None:
            raise GitHubError(f"updating {field} requires its expected digest")
        observed = str(current.get(field, ""))
        digest = hashlib.sha256(observed.encode()).hexdigest()
        if digest != expected:
            raise GitHubError(f"Issue {field} changed concurrently")
    edit = ["gh", "issue", "edit", str(issue), "--repo", repo]
    if title is not None and title != current.get("title"):
        edit.extend(["--title", title])
    if body is not None and body != current.get("body"):
        edit.extend(["--body", body])
    if len(edit) > 6:
        run(edit)
    if desired_state and desired_state != current.get("state"):
        verb = "close" if desired_state == "CLOSED" else "reopen"
        run(["gh", "issue", verb, str(issue), "--repo", repo])
    return url


def record_provenance(
    repo: str,
    issue: int,
    source: str,
    excerpt: str,
    *,
    evidence: str | None = None,
    key: str | None = None,
) -> str:
    """Add one provenance record unless its stable marker is already present."""
    if not source.strip() or not excerpt.strip():
        raise GitHubError("provenance requires a source and verbatim excerpt")
    canonical = json.dumps(
        {"source": source, "excerpt": excerpt, "evidence": evidence},
        ensure_ascii=False,
        sort_keys=True,
    )
    content_digest = hashlib.sha256(canonical.encode()).hexdigest()
    record_key = key or content_digest[:20]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", record_key):
        raise GitHubError("provenance key must be a stable non-secret identifier")
    prefix = f"<!-- skiphow-provenance:{record_key}:"
    marker = f"{prefix}{content_digest} -->"
    try:
        comments = json.loads(
            run(
                [
                    "gh",
                    "api",
                    f"repos/{repo}/issues/{issue}/comments",
                    "--paginate",
                    "--slurp",
                ]
            )
        )
    except json.JSONDecodeError as exc:
        raise GitHubError("gh returned invalid comment JSON") from exc
    if not isinstance(comments, list):
        raise GitHubError("gh returned an unexpected comment list")
    if comments and all(isinstance(page, list) for page in comments):
        comments = [row for page in comments for row in page]
    matches = [
        row
        for row in comments
        if isinstance(row, dict) and str(row.get("body", "")).startswith(prefix)
    ]
    if any(str(row.get("body", "")).startswith(marker) for row in matches):
        return "UNCHANGED"
    if matches:
        raise GitHubError("provenance key was reused with different content")
    parts = [marker, "## Evidence and provenance", f"Source: {source}", "", excerpt]
    if evidence:
        parts.extend(["", f"Observed evidence: {evidence}"])
    run(
        [
            "gh",
            "issue",
            "comment",
            str(issue),
            "--repo",
            repo,
            "--body",
            "\n".join(parts),
        ]
    )
    return "RECORDED"


def create_linked_branch(repo: str, issue: int, name: str) -> None:
    run(["gh", "issue", "develop", str(issue), "--repo", repo, "--name", name])


def record_delivery(repo: str, issue: int, url: str) -> None:
    if not url.startswith(("http://", "https://")):
        raise GitHubError("delivery provenance must be an http(s) URL")
    key = "delivery:" + hashlib.sha256(url.encode()).hexdigest()[:20]
    record_provenance(repo, issue, "delivery", url, key=key)


def _worktrees(cwd: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    row: dict[str, str] = {}
    for line in run(["git", "worktree", "list", "--porcelain"], cwd=cwd).splitlines():
        if not line:
            if row:
                rows.append(row)
                row = {}
            continue
        key, _, value = line.partition(" ")
        row[key] = value
    if row:
        rows.append(row)
    return rows


def _branch_metadata(cwd: str, branch: str) -> tuple[str | None, str | None]:
    try:
        values = run(
            [
                "git",
                "config",
                "--local",
                "--get-regexp",
                rf"^branch\.{re.escape(branch)}\.skiphow-(owner|worktree)$",
            ],
            cwd=cwd,
        )
    except GitHubError:
        return None, None
    metadata: dict[str, str] = {}
    for line in values.splitlines():
        key, _, value = line.partition(" ")
        metadata[key.rsplit(".", 1)[-1]] = value
    return metadata.get("owner"), metadata.get("worktree")


def ensure_owned_worktree(
    cwd: str,
    path: str,
    branch: str,
    start_point: str,
    owner: str,
) -> str:
    """Create or reconcile one explicitly owned branch/worktree pair."""
    if not owner or not branch or not path:
        raise GitHubError("worktree ownership requires owner, branch, and path")
    _validate_branch(branch)
    target = str(Path(path).resolve())
    rows = _worktrees(cwd)
    matches = [row for row in rows if str(Path(row.get("worktree", ".")).resolve()) == target]
    branch_ref = f"refs/heads/{branch}"
    owner_value, owned_path = _branch_metadata(cwd, branch)
    if matches:
        if matches[0].get("branch") != branch_ref or owner_value != owner or owned_path != target:
            raise GitHubError("existing worktree is not the requested system-owned lane")
        return "UNCHANGED"
    refs = run(["git", "for-each-ref", "--format=%(refname)", branch_ref], cwd=cwd)
    if owner_value is not None or owned_path is not None:
        if owner_value != owner or owned_path != target:
            raise GitHubError("branch ownership metadata does not match this lane")
        if refs.strip():
            run(["git", "worktree", "add", target, branch], cwd=cwd)
        else:
            start_oid = run(
                [
                    "git",
                    "rev-parse",
                    "--verify",
                    "--end-of-options",
                    f"{start_point}^{{commit}}",
                ],
                cwd=cwd,
            )
            _validated_oid(start_oid)
            run(["git", "worktree", "add", "-b", branch, target, start_oid], cwd=cwd)
        return "RESTORED"
    if refs.strip():
        raise GitHubError("refusing to claim an existing unowned branch")
    start_oid = run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{start_point}^{{commit}}"],
        cwd=cwd,
    )
    _validated_oid(start_oid)
    run(["git", "config", "--local", f"branch.{branch}.skiphow-owner", owner], cwd=cwd)
    run(["git", "config", "--local", f"branch.{branch}.skiphow-worktree", target], cwd=cwd)
    run(["git", "worktree", "add", "-b", branch, target, start_oid], cwd=cwd)
    return "CREATED"


def ensure_pull_request(
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str,
    *,
    expected_head: str,
) -> str:
    """Return an existing PR for head/base, or create exactly one."""
    expected_head = _validated_oid(expected_head)
    payload = run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            head,
            "--base",
            base,
            "--state",
            "open",
            "--limit",
            "2",
            "--json",
            "url,headRefOid",
        ]
    )
    try:
        rows = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GitHubError("gh returned invalid pull request JSON") from exc
    if not isinstance(rows, list):
        raise GitHubError("gh returned an unexpected pull request list")
    matches = [row for row in rows if isinstance(row, dict) and row.get("url")]
    if len(matches) > 1:
        raise GitHubError("multiple pull requests already use the requested head and base")
    if matches:
        if matches[0].get("headRefOid") != expected_head:
            raise GitHubError("open pull request head differs from expected head")
        return str(matches[0]["url"])
    output = run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--head",
            head,
            "--base",
            base,
            "--title",
            title,
            "--body",
            body,
        ]
    ).splitlines()
    if not output:
        raise GitHubError("gh pr create returned no pull request URL")
    return output[-1]


def pull_request_gate(
    repo: str,
    pull_request: int,
    expected_head: str,
    required_checks: Sequence[str],
) -> PullRequestGate:
    """Read required checks, review, mergeability, and exact-head identity together."""
    expected_head = _validated_oid(expected_head)
    current = _json_object(
        run(
            [
                "gh",
                "pr",
                "view",
                str(pull_request),
                "--repo",
                repo,
                "--json",
                "headRefOid,mergeable,reviewDecision,statusCheckRollup",
            ]
        ),
        operation="gh pr view",
    )
    head = str(current.get("headRefOid", ""))
    if head != expected_head:
        raise GitHubError("pull request head changed after verification")
    states: dict[str, list[str]] = {}
    for check in current.get("statusCheckRollup") or []:
        if not isinstance(check, dict):
            continue
        name = check.get("name") or check.get("context")
        state = check.get("conclusion") or check.get("state")
        if name and state:
            states.setdefault(str(name), []).append(str(state).upper())
    missing = tuple(
        name
        for name in required_checks
        if not states.get(name) or any(state != "SUCCESS" for state in states[name])
    )
    return PullRequestGate(
        head=head,
        checks_green=not missing,
        approved=current.get("reviewDecision") == "APPROVED",
        mergeable=current.get("mergeable") == "MERGEABLE",
        missing_checks=missing,
    )


def merge_pull_request(
    repo: str,
    pull_request: int,
    *,
    policy: str,
    expected_head: str,
    required_checks: Sequence[str] = (),
    checks_verified: bool = False,
    has_blocking_finding: bool = False,
) -> str:
    """Apply a caller-selected merge policy to fresh exact-head evidence."""
    policies = {"never", "when_green", "when_green_and_approved", "auto_merge_or_queue"}
    if policy not in policies:
        raise GitHubError(f"unknown merge policy: {policy}")
    if policy == "never":
        return "NOT_AUTHORIZED"
    if not checks_verified:
        return "UNVERIFIED"
    expected_head = _validated_oid(expected_head)
    gate = pull_request_gate(repo, pull_request, expected_head, required_checks)
    approval_required = policy == "when_green_and_approved"
    if has_blocking_finding or not gate.checks_green or not gate.mergeable:
        return "NOT_READY"
    if approval_required and not gate.approved:
        return "NOT_READY"
    args = [
        "gh",
        "pr",
        "merge",
        str(pull_request),
        "--repo",
        repo,
        "--match-head-commit",
        expected_head,
    ]
    args.append("--auto" if policy == "auto_merge_or_queue" else "--merge")
    run(args)
    return "MERGE_REQUESTED"


def cleanup_owned_worktree(
    cwd: str,
    path: str,
    branch: str,
    owner: str,
    *,
    expected_head: str,
    merged_into: str,
) -> str:
    """Remove a clean owned lane only when its exact head is merged."""
    _validate_branch(branch)
    expected_head = _validated_oid(expected_head)
    target = str(Path(path).resolve())
    rows = _worktrees(cwd)
    matches = [row for row in rows if str(Path(row.get("worktree", ".")).resolve()) == target]
    if not matches:
        refs = run(
            ["git", "for-each-ref", "--format=%(refname)", f"refs/heads/{branch}"],
            cwd=cwd,
        )
        if not refs:
            return "UNCHANGED"
        owner_value, owned_path = _branch_metadata(cwd, branch)
        if owner_value != owner or owned_path != target:
            raise GitHubError("branch remains without matching ownership metadata")
        actual_head = run(["git", "rev-parse", branch], cwd=cwd)
        if actual_head != expected_head:
            raise GitHubError("owned branch head changed after verification")
        unique = run(
            ["git", "rev-list", "--max-count=1", expected_head, f"^{merged_into}"],
            cwd=cwd,
        )
        if unique:
            raise GitHubError("refusing to remove a branch with commits absent from merge target")
        run(["git", "branch", "-d", branch], cwd=cwd)
        run(["git", "worktree", "prune"], cwd=cwd)
        return "REMOVED"
    owner_value, owned_path = _branch_metadata(cwd, branch)
    if owner_value != owner or owned_path != target:
        raise GitHubError("refusing cleanup without exact ownership metadata")
    if matches[0].get("branch") != f"refs/heads/{branch}":
        raise GitHubError("owned path now points at a different branch")
    actual_head = run(["git", "rev-parse", "HEAD"], cwd=target)
    if actual_head != expected_head:
        raise GitHubError("owned branch head changed after verification")
    if run(["git", "status", "--porcelain"], cwd=target):
        raise GitHubError("refusing to remove a dirty worktree")
    ancestors = run(
        ["git", "rev-list", "--max-count=1", expected_head, f"^{merged_into}"], cwd=cwd
    )
    if ancestors:
        raise GitHubError("refusing to remove a branch with commits absent from merge target")
    run(["git", "worktree", "remove", target], cwd=cwd)
    run(["git", "branch", "-d", branch], cwd=cwd)
    run(["git", "worktree", "prune"], cwd=cwd)
    return "REMOVED"


def cleanup_owned_remote_branch(
    cwd: str,
    repo: str,
    remote: str,
    branch: str,
    owner: str,
    *,
    expected_head: str,
    merged_pull_request: int,
) -> str:
    """Delete only the owned remote ref recorded as the merged PR head."""
    _validate_branch(branch)
    expected_head = _validated_oid(expected_head)
    remote_url = run(["git", "remote", "get-url", remote], cwd=cwd)
    remote_match = REMOTE_RE.search(remote_url)
    if not remote_match:
        raise GitHubError("cleanup remote is not a GitHub repository")
    remote_repo = f"{remote_match.group(1)}/{remote_match.group(2)}"
    pr = _json_object(
        run(
            [
                "gh",
                "pr",
                "view",
                str(merged_pull_request),
                "--repo",
                repo,
                "--json",
                "headRefName,headRefOid,headRepository,headRepositoryOwner,mergedAt",
            ]
        ),
        operation="gh pr view",
    )
    if (
        pr.get("headRefName") != branch
        or pr.get("headRefOid") != expected_head
        or not pr.get("mergedAt")
    ):
        raise GitHubError("pull request does not prove this exact branch head was merged")
    head_repository = pr.get("headRepository")
    head_owner = pr.get("headRepositoryOwner")
    head_repo = ""
    if isinstance(head_repository, dict) and isinstance(head_owner, dict):
        name = head_repository.get("name")
        login = head_owner.get("login")
        if isinstance(name, str) and isinstance(login, str):
            head_repo = f"{login}/{name}"
    if remote_repo.casefold() != head_repo.casefold():
        raise GitHubError("cleanup remote does not match the pull request head repository")
    output = run(
        ["git", "ls-remote", "--heads", remote, f"refs/heads/{branch}"], cwd=cwd
    )
    if not output:
        return "UNCHANGED"
    owner_value, _ = _branch_metadata(cwd, branch)
    if owner_value != owner:
        raise GitHubError("refusing remote cleanup without exact ownership metadata")
    remote_head = output.split()[0]
    if remote_head != expected_head:
        raise GitHubError("remote branch head changed after merge")
    lease = f"--force-with-lease=refs/heads/{branch}:{expected_head}"
    run(
        ["git", "push", lease, remote, f":refs/heads/{branch}"],
        cwd=cwd,
    )
    return "REMOVED"


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="skiphow-github-issues")
    commands = root.add_subparsers(dest="command", required=True)
    check = commands.add_parser("available")
    check.add_argument("repo", nargs="?")
    duplicate = commands.add_parser("find-duplicate")
    duplicate.add_argument("repo")
    duplicate.add_argument("summary")
    candidates = commands.add_parser("find-candidates")
    candidates.add_argument("repo")
    candidates.add_argument("summary")
    candidates.add_argument("--evidence")
    create = commands.add_parser("persist")
    create.add_argument("repo")
    create.add_argument("kind")
    create.add_argument("title")
    create.add_argument("body")
    create.add_argument("--parent")
    create.add_argument("--blocked-by")
    create.add_argument("--blocking")
    ensure = commands.add_parser("ensure-issue")
    ensure.add_argument("repo")
    ensure.add_argument("operation_id")
    ensure.add_argument("kind")
    ensure.add_argument("title")
    ensure.add_argument("body")
    ensure.add_argument("--allow-create", action="store_true")
    ensure.add_argument("--parent", type=int)
    ensure.add_argument("--blocked-by", type=int)
    ensure.add_argument("--blocking", type=int)
    update = commands.add_parser("update")
    update.add_argument("repo")
    update.add_argument("issue", type=int)
    update.add_argument("--title")
    update.add_argument("--body")
    update.add_argument("--state", choices=("open", "closed"))
    update.add_argument("--expected-title-digest")
    update.add_argument("--expected-body-digest")
    relationship = commands.add_parser("relationship")
    relationship.add_argument("repo")
    relationship.add_argument("issue", type=int)
    relationship.add_argument("relation", choices=("parent", "subissue", "blocked_by", "blocking"))
    relationship.add_argument("other", type=int)
    provenance = commands.add_parser("record-provenance")
    provenance.add_argument("repo")
    provenance.add_argument("issue", type=int)
    provenance.add_argument("source")
    provenance.add_argument("excerpt")
    provenance.add_argument("--evidence")
    provenance.add_argument("--key")
    branch = commands.add_parser("create-linked-branch")
    branch.add_argument("repo")
    branch.add_argument("issue", type=int)
    branch.add_argument("name")
    delivery = commands.add_parser("record-delivery")
    delivery.add_argument("repo")
    delivery.add_argument("issue", type=int)
    delivery.add_argument("url")
    worktree = commands.add_parser("ensure-worktree")
    worktree.add_argument("cwd")
    worktree.add_argument("path")
    worktree.add_argument("branch")
    worktree.add_argument("start_point")
    worktree.add_argument("owner")
    pull_request = commands.add_parser("ensure-pr")
    pull_request.add_argument("repo")
    pull_request.add_argument("head")
    pull_request.add_argument("base")
    pull_request.add_argument("title")
    pull_request.add_argument("body")
    pull_request.add_argument("expected_head")
    merge = commands.add_parser("merge-pr")
    merge.add_argument("repo")
    merge.add_argument("pull_request", type=int)
    merge.add_argument("policy", choices=("never", "when_green", "when_green_and_approved", "auto_merge_or_queue"))
    merge.add_argument("expected_head")
    merge.add_argument("--required-check", action="append", default=[])
    merge.add_argument("--checks-verified", action="store_true")
    merge.add_argument("--blocking-finding", action="store_true")
    cleanup = commands.add_parser("cleanup-worktree")
    cleanup.add_argument("cwd")
    cleanup.add_argument("path")
    cleanup.add_argument("branch")
    cleanup.add_argument("owner")
    cleanup.add_argument("expected_head")
    cleanup.add_argument("merged_into")
    remote_cleanup = commands.add_parser("cleanup-remote-branch")
    remote_cleanup.add_argument("cwd")
    remote_cleanup.add_argument("repo")
    remote_cleanup.add_argument("remote")
    remote_cleanup.add_argument("branch")
    remote_cleanup.add_argument("owner")
    remote_cleanup.add_argument("expected_head")
    remote_cleanup.add_argument("merged_pull_request", type=int)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "available":
            print("AVAILABLE" if available(args.repo) else "NOT AVAILABLE")
            return 0
        if args.command == "find-duplicate":
            issue = find_duplicate(args.repo, args.summary)
            print(issue.url if issue else "")
            return 0
        if args.command == "find-candidates":
            rows = find_candidates(args.repo, args.summary, args.evidence)
            print(json.dumps([issue.__dict__ for issue in rows], sort_keys=True))
            return 0
        if args.command == "persist":
            print(
                persist(
                    args.repo,
                    args.kind,
                    args.title,
                    args.body,
                    parent=args.parent,
                    blocked_by=args.blocked_by,
                    blocking=args.blocking,
                )
            )
            return 0
        if args.command == "ensure-issue":
            result = ensure_issue(
                args.repo,
                args.operation_id,
                args.kind,
                args.title,
                args.body,
                allow_create=args.allow_create,
                parent=args.parent,
                blocked_by=args.blocked_by,
                blocking=args.blocking,
            )
            print(json.dumps(result.__dict__, sort_keys=True))
            return 0
        if args.command == "update":
            print(
                update_issue(
                    args.repo,
                    args.issue,
                    title=args.title,
                    body=args.body,
                    state=args.state,
                    expected_title_digest=args.expected_title_digest,
                    expected_body_digest=args.expected_body_digest,
                )
            )
            return 0
        if args.command == "relationship":
            print(create_relationship(args.repo, args.issue, args.relation, args.other))
            return 0
        if args.command == "record-provenance":
            print(
                record_provenance(
                    args.repo,
                    args.issue,
                    args.source,
                    args.excerpt,
                    evidence=args.evidence,
                    key=args.key,
                )
            )
            return 0
        if args.command == "create-linked-branch":
            create_linked_branch(args.repo, args.issue, args.name)
            return 0
        if args.command == "record-delivery":
            record_delivery(args.repo, args.issue, args.url)
            return 0
        if args.command == "ensure-worktree":
            print(
                ensure_owned_worktree(
                    args.cwd,
                    args.path,
                    args.branch,
                    args.start_point,
                    args.owner,
                )
            )
            return 0
        if args.command == "ensure-pr":
            print(
                ensure_pull_request(
                    args.repo,
                    args.head,
                    args.base,
                    args.title,
                    args.body,
                    expected_head=args.expected_head,
                )
            )
            return 0
        if args.command == "merge-pr":
            print(
                merge_pull_request(
                    args.repo,
                    args.pull_request,
                    policy=args.policy,
                    expected_head=args.expected_head,
                    required_checks=args.required_check,
                    checks_verified=args.checks_verified,
                    has_blocking_finding=args.blocking_finding,
                )
            )
            return 0
        if args.command == "cleanup-worktree":
            print(
                cleanup_owned_worktree(
                    args.cwd,
                    args.path,
                    args.branch,
                    args.owner,
                    expected_head=args.expected_head,
                    merged_into=args.merged_into,
                )
            )
            return 0
        print(
            cleanup_owned_remote_branch(
                args.cwd,
                args.repo,
                args.remote,
                args.branch,
                args.owner,
                expected_head=args.expected_head,
                merged_pull_request=args.merged_pull_request,
            )
        )
        return 0
    except GitHubError as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
