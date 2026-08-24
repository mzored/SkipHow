#!/usr/bin/env python3
"""Synchronize an explicitly configured optional GitHub Project."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from typing import Any, Sequence


TIMEOUT_SECONDS = 30


class ProjectError(RuntimeError):
    """An optional Project operation failed."""


@dataclass(frozen=True)
class Project:
    owner: str
    number: int

    @classmethod
    def parse(cls, value: str) -> "Project":
        owner, separator, number = value.rpartition("/")
        if not separator or not owner or not number.isdigit():
            raise ProjectError("project must be explicit owner/number")
        return cls(owner, int(number))


def run(args: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProjectError(f"cannot run {args[0]}: {exc}") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ProjectError(detail or f"{' '.join(args[:2])} failed")
    return result.stdout.strip()


def run_json(args: Sequence[str]) -> dict[str, Any]:
    try:
        value = json.loads(run(args))
    except json.JSONDecodeError as exc:
        raise ProjectError("gh returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ProjectError("gh returned an unexpected Project value")
    return value


def available(project: Project) -> bool:
    try:
        run(
            [
                "gh",
                "project",
                "view",
                str(project.number),
                "--owner",
                project.owner,
                "--format",
                "json",
            ]
        )
    except ProjectError:
        return False
    return True


def update_optional_view(project: Project, issue_url: str, state: str) -> None:
    view = run_json(
        [
            "gh",
            "project",
            "view",
            str(project.number),
            "--owner",
            project.owner,
            "--format",
            "json",
        ]
    )
    project_id = str(view.get("id") or "")
    if not project_id:
        raise ProjectError("configured Project has no id")

    items = run_json(
        [
            "gh",
            "project",
            "item-list",
            str(project.number),
            "--owner",
            project.owner,
            "--format",
            "json",
            "--limit",
            "100",
        ]
    ).get("items") or []
    item = next(
        (
            row
            for row in items
            if isinstance(row, dict)
            and isinstance(row.get("content"), dict)
            and row["content"].get("url") == issue_url
        ),
        None,
    )
    if item is None:
        item = run_json(
            [
                "gh",
                "project",
                "item-add",
                str(project.number),
                "--owner",
                project.owner,
                "--url",
                issue_url,
                "--format",
                "json",
            ]
        )
    item_id = str(item.get("id") or "")
    if not item_id:
        raise ProjectError("Project item has no id")

    fields = run_json(
        [
            "gh",
            "project",
            "field-list",
            str(project.number),
            "--owner",
            project.owner,
            "--format",
            "json",
        ]
    ).get("fields") or []
    status = next(
        (row for row in fields if isinstance(row, dict) and row.get("name") == "Status"),
        None,
    )
    if not status:
        raise ProjectError("configured Project has no Status field")
    option = next(
        (
            row
            for row in status.get("options") or []
            if isinstance(row, dict) and row.get("name") == state
        ),
        None,
    )
    if not option:
        raise ProjectError(f"configured Project Status has no {state!r} option")
    run(
        [
            "gh",
            "project",
            "item-edit",
            "--id",
            item_id,
            "--project-id",
            project_id,
            "--field-id",
            str(status["id"]),
            "--single-select-option-id",
            str(option["id"]),
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    root = argparse.ArgumentParser(prog="skiphow-github-project")
    root.add_argument("project")
    root.add_argument("issue_url", nargs="?")
    root.add_argument("state", nargs="?")
    args = root.parse_args(argv)
    try:
        project = Project.parse(args.project)
        if args.issue_url and args.state:
            update_optional_view(project, args.issue_url, args.state)
            print("UPDATED")
            return 0
        print("CONNECTED" if available(project) else "UNAVAILABLE")
        return 0
    except ProjectError as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
