#!/usr/bin/env python3
"""Read-only SkipHow readiness report."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


TIMEOUT_SECONDS = 15
PROJECT_RE = re.compile(r"^\s*project:\s*([^#\s]+)\s*$", re.MULTILINE)


def succeeds(args: Sequence[str], *, cwd: str = ".") -> bool:
    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def configured_project(cwd: str = ".") -> str | None:
    path = Path(cwd) / ".skiphow" / "config.yml"
    if not path.is_file():
        return None
    match = PROJECT_RE.search(path.read_text(encoding="utf-8"))
    if not match or match.group(1) in {"auto", "disabled"}:
        return None
    value = match.group(1)
    owner, separator, number = value.rpartition("/")
    return value if separator and owner and number.isdigit() else None


def report(repo: str | None = None, *, cwd: str = ".") -> list[str]:
    repository_ready = succeeds(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    gh_available = shutil.which("gh") is not None and succeeds(["gh", "auth", "status"])
    if gh_available and repo:
        gh_available = succeeds(["gh", "repo", "view", repo, "--json", "nameWithOwner"])

    project = configured_project(cwd)
    if project is None:
        project_state = "NOT CONFIGURED"
    elif not gh_available:
        project_state = "UNAVAILABLE"
    else:
        owner, number = project.rsplit("/", 1)
        project_state = (
            "CONNECTED"
            if succeeds(["gh", "project", "view", number, "--owner", owner, "--format", "json"])
            else "UNAVAILABLE"
        )

    host_verified = any(
        shutil.which(executable) is not None and succeeds([executable, "--version"])
        for executable in ("codex", "claude")
    )
    return [
        "Core: READY",
        f"Repository: {'READY' if repository_ready else 'LIMITED'}",
        f"GitHub Issues: {'AVAILABLE' if gh_available else 'NOT AVAILABLE'}",
        f"GitHub Project: {project_state}",
        f"Host checks: {'VERIFIED' if host_verified else 'UNVERIFIED'}",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skiphow-doctor")
    parser.add_argument("repo", nargs="?")
    parser.add_argument("--require", choices=("repository", "github", "project"))
    args = parser.parse_args(argv)
    lines = report(args.repo)
    print("\n".join(lines))
    if args.require == "repository" and "Repository: READY" not in lines:
        return 1
    if args.require == "github" and "GitHub Issues: AVAILABLE" not in lines:
        return 1
    if args.require == "project" and "GitHub Project: CONNECTED" not in lines:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
