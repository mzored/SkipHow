#!/usr/bin/env python3
"""Optional GitHub Issues adapter for SkipHow.

The core plugin does not import this module. It runs only after a workflow has
decided to use GitHub for persistence.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from functools import cache
from typing import Any, Sequence


TIMEOUT_SECONDS = 30
REMOTE_RE = re.compile(r"(?:github\.com[:/])([^/]+)/([^/]+?)(?:\.git)?$")


class GitHubError(RuntimeError):
    """A bounded GitHub adapter operation failed."""


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    url: str


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
    return [
        Issue(int(row["number"]), str(row["title"]), str(row["url"]))
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("number"), int)
        and row.get("title")
        and row.get("url")
    ]


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
                "open",
                "--search",
                query,
                "--limit",
                "20",
                "--json",
                "number,title,url",
            ]
        )
    )


def find_candidates(repo: str, summary: str, evidence: str | None = None) -> list[Issue]:
    """Return bounded search candidates without making a duplicate decision."""
    summary_query = " ".join(summary.split())
    queries = [f"{summary_query} in:title"]
    evidence_query = " ".join((evidence or "").split())
    if evidence_query and evidence_query.casefold() != summary_query.casefold():
        queries.append(evidence_query)

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
    duplicate = find_duplicate(repo, title)
    if duplicate:
        return duplicate.url

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
    return output[-1]


def create_linked_branch(repo: str, issue: int, name: str) -> None:
    run(["gh", "issue", "develop", str(issue), "--repo", repo, "--name", name])


def record_delivery(repo: str, issue: int, url: str) -> None:
    if not url.startswith(("http://", "https://")):
        raise GitHubError("delivery provenance must be an http(s) URL")
    run(
        [
            "gh",
            "issue",
            "comment",
            str(issue),
            "--repo",
            repo,
            "--body",
            f"Delivery: {url}",
        ]
    )


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
    branch = commands.add_parser("create-linked-branch")
    branch.add_argument("repo")
    branch.add_argument("issue", type=int)
    branch.add_argument("name")
    delivery = commands.add_parser("record-delivery")
    delivery.add_argument("repo")
    delivery.add_argument("issue", type=int)
    delivery.add_argument("url")
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
        if args.command == "create-linked-branch":
            create_linked_branch(args.repo, args.issue, args.name)
            return 0
        record_delivery(args.repo, args.issue, args.url)
        return 0
    except GitHubError as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
