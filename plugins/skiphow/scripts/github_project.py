#!/usr/bin/env python3
"""Synchronize an explicitly configured optional GitHub Project."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


TIMEOUT_SECONDS = 30
LIST_LIMIT = 10_000
PROJECT_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/([1-9][0-9]*)$")


class ProjectError(RuntimeError):
    """An optional Project operation failed."""


@dataclass(frozen=True)
class Project:
    owner: str
    number: int

    @classmethod
    def parse(cls, value: str) -> "Project":
        if not PROJECT_RE.fullmatch(value):
            raise ProjectError("project must be explicit owner/number")
        owner, number = value.rsplit("/", 1)
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


def collection(args: Sequence[str], key: str) -> list[dict[str, Any]]:
    value = run_json(args)
    rows = value.get(key)
    if not isinstance(rows, list):
        raise ProjectError(f"gh returned an unexpected Project {key} list")
    total = value.get("totalCount")
    if isinstance(total, int) and total > len(rows):
        raise ProjectError(f"Project {key} list was incomplete ({len(rows)}/{total})")
    return [row for row in rows if isinstance(row, dict)]


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


def update_optional_view(
    project: Project,
    issue_url: str,
    state: str,
    *,
    status_field: str | None = None,
    status_mapping: Mapping[str, str] | None = None,
) -> str:
    """Update an explicitly mapped optional view, or return UNVERIFIED."""
    if not status_field or not status_mapping or state not in status_mapping:
        return "UNVERIFIED"
    option_name = status_mapping[state]
    if not isinstance(option_name, str) or not option_name:
        return "UNVERIFIED"

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

    items = collection(
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
            str(LIST_LIMIT),
            "--field",
            status_field,
        ],
        "items",
    )
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
    if item is not None and item.get(status_field) == option_name:
        return "UNCHANGED"

    fields = collection(
        [
            "gh",
            "project",
            "field-list",
            str(project.number),
            "--owner",
            project.owner,
            "--format",
            "json",
            "--limit",
            str(LIST_LIMIT),
        ],
        "fields",
    )
    status = next(
        (
            row
            for row in fields
            if isinstance(row, dict) and row.get("name") == status_field
        ),
        None,
    )
    if not status:
        raise ProjectError(f"configured Project has no {status_field!r} field")
    status_id = status.get("id")
    if not isinstance(status_id, str) or not status_id:
        raise ProjectError(f"configured Project field {status_field!r} has no id")
    option = next(
        (
            row
            for row in status.get("options") or []
            if isinstance(row, dict) and row.get("name") == option_name
        ),
        None,
    )
    if not option:
        raise ProjectError(
            f"configured Project field {status_field!r} has no {option_name!r} option"
        )
    option_id = option.get("id")
    if not isinstance(option_id, str) or not option_id:
        raise ProjectError(
            f"configured Project field {status_field!r} option {option_name!r} has no id"
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
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id:
        raise ProjectError("Project item has no id")

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
            status_id,
            "--single-select-option-id",
            option_id,
        ]
    )
    return "UPDATED"


def parse_status_mapping(value: str | None) -> dict[str, str] | None:
    if value is None:
        return None
    try:
        mapping = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ProjectError("status mapping must be a JSON object") from exc
    if not isinstance(mapping, dict) or any(
        not isinstance(key, str) or not isinstance(option, str) or not option
        for key, option in mapping.items()
    ):
        raise ProjectError("status mapping must map state strings to option strings")
    return mapping


def main(argv: Sequence[str] | None = None) -> int:
    root = argparse.ArgumentParser(prog="skiphow-github-project")
    root.add_argument("project")
    root.add_argument("issue_url", nargs="?")
    root.add_argument("state", nargs="?")
    root.add_argument("--status-field")
    root.add_argument("--status-map")
    args = root.parse_args(argv)
    try:
        project = Project.parse(args.project)
        if args.issue_url and args.state:
            try:
                mapping = parse_status_mapping(args.status_map)
                outcome = update_optional_view(
                    project,
                    args.issue_url,
                    args.state,
                    status_field=args.status_field,
                    status_mapping=mapping,
                )
            except ProjectError as exc:
                print(f"UNVERIFIED: {exc}")
                return 0
            print(outcome)
            return 0
        print("CONNECTED" if available(project) else "UNAVAILABLE")
        return 0
    except ProjectError as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
