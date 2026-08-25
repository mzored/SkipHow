"""Trusted readers for live receipts. They never execute candidate code."""

from __future__ import annotations

import hashlib
import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import stat
import subprocess
from typing import Any, Iterable, Mapping

try:
    from .schema import Status
except ImportError:  # Allows ``python evals/live/run.py`` during local use.
    from schema import Status


INBOX_ID = re.compile(r"^## ([A-Za-z0-9][A-Za-z0-9_.-]{0,79})$")
INBOX_FIELDS = (
    "Recorded",
    "Source",
    "Original",
    "Normalized",
    "Disposition",
    "Links",
    "Evidence",
    "Open questions",
)
DISPOSITIONS = {"NEW", "UPDATE", "DUPLICATE", "RELATED", "NEEDS_RESEARCH", "DISMISSED"}
RFC3339_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def plain_directory(root: Path) -> None:
    """Reject a fixture or workspace that carries a repository into a trial."""
    if not root.is_dir():
        raise ValueError(f"directory does not exist: {root}")
    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"plain directory must not contain symlinks: {path}")
        if path.name == ".git":
            raise ValueError(f"plain directory must not contain .git: {root}")
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f"plain directory must not contain special entries: {path}")


def file_inventory(root: Path) -> dict[str, dict[str, Any]]:
    plain_directory(root)
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        details = path.lstat()
        relative = path.relative_to(root).as_posix()
        mode = oct(stat.S_IMODE(details.st_mode))
        if stat.S_ISDIR(details.st_mode):
            result[relative] = {"type": "directory", "mode": mode}
        elif stat.S_ISREG(details.st_mode):
            result[relative] = {"type": "file", "mode": mode, "sha256": _sha256(path), "bytes": details.st_size}
        else:  # ``plain_directory`` rejects this first; keep the reader fail-closed.
            raise ValueError(f"unsupported filesystem entry: {path}")
    return result


def tree_delta(before: Mapping[str, Mapping[str, Any]], after_root: Path) -> dict[str, Any]:
    """Compare a saved inventory with a later plain workspace."""
    after = file_inventory(after_root)
    before_names, after_names = set(before), set(after)
    return {
        "collector": "tree_delta",
        "added": sorted(after_names - before_names),
        "removed": sorted(before_names - after_names),
        "modified": sorted(name for name in before_names & after_names if before[name] != after[name]),
        "after": after,
    }


def structured_file(
    path: Path,
    *,
    kind: str,
    before: str | None = None,
    expected_count: int | None = None,
    expected: Any = None,
    expected_added_records: list[Mapping[str, Any]] | None = None,
    relationships: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Read a declared text grammar. There is no command or expression mode."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"collector": "structured_file", "status": Status.FAILED.value, "detail": str(exc)}
    if kind == "json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            return {"collector": "structured_file", "status": Status.FAILED.value, "detail": str(exc)}
        matches = value == expected
        return {
            "collector": "structured_file",
            "status": (Status.PASSED if matches else Status.FAILED).value,
            "kind": kind,
            "matches_expected": matches,
            "value": value,
        }
    if kind != "append_only_inbox":
        raise ValueError(f"unsupported structured file grammar: {kind}")
    prior = before or ""
    if not text.startswith(prior):
        return {"collector": "structured_file", "status": Status.FAILED.value, "detail": "inbox is not append-only"}
    records, invalid = _inbox_records(text)
    count = len(records)
    added_records, added_invalid = _inbox_records(text[len(prior):])
    invalid.extend([f"appended: {item}" for item in added_invalid])
    added_count = len(added_records)
    expected_records = list(expected_added_records or [])
    unmatched = _unmatched_records(added_records, expected_records)
    broken_relationships = _broken_relationships(records, list(relationships or []))
    status = Status.PASSED if not invalid and not unmatched and not broken_relationships and (expected_count is None or count == expected_count) else Status.FAILED
    return {
        "collector": "structured_file",
        "status": status.value,
        "kind": kind,
        "count": count,
        "added_count": added_count,
        "invalid_records": invalid,
        "unmatched_expected_records": unmatched,
        "broken_relationships": broken_relationships,
        "added_records": added_records,
    }


def _inbox_records(text: str) -> tuple[list[dict[str, str]], list[str]]:
    """Parse the documented Markdown inbox blocks without interpreting their prose."""
    records: list[dict[str, str]] = []
    invalid: list[str] = []
    current: dict[str, str] | None = None
    for number, line in enumerate(text.splitlines(), 1):
        heading = INBOX_ID.fullmatch(line)
        if heading:
            if current is not None:
                _finish_record(current, records, invalid)
            current = {"id": heading.group(1), "line": str(number)}
            continue
        if not line.strip():
            continue
        if current is None:
            invalid.append(f"line {number}: content outside a record")
            continue
        if not line.startswith("- ") or ": " not in line:
            invalid.append(f"line {number}: expected labeled field")
            continue
        label, value = line[2:].split(": ", 1)
        if label not in INBOX_FIELDS or not value.strip() or label in current:
            invalid.append(f"line {number}: invalid inbox field")
            continue
        current[label] = value.strip()
    if current is not None:
        _finish_record(current, records, invalid)
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        invalid.append("stable record IDs must be unique")
    return records, invalid


def _finish_record(record: dict[str, str], records: list[dict[str, str]], invalid: list[str]) -> None:
    missing = [field for field in INBOX_FIELDS if field not in record]
    if missing:
        invalid.append(f"line {record['line']}: missing " + ", ".join(missing))
        return
    if record["Disposition"] not in DISPOSITIONS:
        invalid.append(f"line {record['line']}: invalid disposition")
        return
    if not RFC3339_UTC.fullmatch(record["Recorded"]):
        invalid.append(f"line {record['line']}: Recorded must be an RFC 3339 UTC timestamp")
        return
    records.append(record)


def _unmatched_records(records: list[dict[str, str]], expected: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Match expected field subsets one-to-one without prescribing generated IDs."""
    available = list(records)
    unmatched: list[dict[str, Any]] = []
    for wanted in expected:
        index = next(
            (
                number
                for number, record in enumerate(available)
                if all(_expected_value(record.get(str(field)), value) for field, value in wanted.items())
            ),
            None,
        )
        if index is None:
            unmatched.append(dict(wanted))
        else:
            available.pop(index)
    return unmatched


def _expected_value(actual: str | None, expected: Any) -> bool:
    if isinstance(expected, dict) and set(expected) == {"not"}:
        return actual != str(expected["not"])
    if isinstance(expected, dict) and set(expected) == {"contains"}:
        return actual is not None and str(expected["contains"]) in actual
    return actual == str(expected)


def _broken_relationships(records: list[dict[str, str]], relationships: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    broken: list[dict[str, Any]] = []
    for relationship in relationships:
        source_match = relationship.get("source")
        target_match = relationship.get("target")
        if not isinstance(source_match, dict) or not isinstance(target_match, dict):
            broken.append(dict(relationship))
            continue
        sources = [record for record in records if all(_expected_value(record.get(str(field)), value) for field, value in source_match.items())]
        targets = [record for record in records if all(_expected_value(record.get(str(field)), value) for field, value in target_match.items())]
        linked = False
        if len(sources) == 1 and len(targets) == 1:
            identifier = re.escape(targets[0]["id"])
            linked = re.search(rf"(?<![A-Za-z0-9_.-]){identifier}(?![A-Za-z0-9_.-])", sources[0]["Links"]) is not None
        if not linked:
            broken.append(dict(relationship))
    return broken


def host_event(
    events: Iterable[Mapping[str, Any]],
    *,
    event_type: str | None = None,
    event_types: Iterable[str] | None = None,
    fields: Mapping[str, Any] | None = None,
    absent: bool = False,
) -> dict[str, Any]:
    """Match literal host telemetry fields. Model prose is diagnostic, never proof."""
    requested = dict(fields or {})
    requested_types = set(event_types or ([event_type] if event_type else []))
    typed = [event for event in events if event.get("type") in requested_types]
    matches = [event for event in typed if all(event.get(key) == value for key, value in requested.items())]
    if requested_types & {"assistant", "message", "final", "model_final"}:
        return {"collector": "host_event", "status": Status.UNVERIFIED.value, "detail": "model text is diagnostic only", "matches": len(matches)}
    if absent:
        status = Status.PASSED if not matches else Status.FAILED
    elif matches:
        status = Status.PASSED
    elif typed:
        status = Status.FAILED
    else:
        status = Status.UNVERIFIED
    return {"collector": "host_event", "status": status.value, "matches": len(matches), "event_types": sorted(requested_types), "absent": absent}


def _git(root: Path, *arguments: str) -> tuple[bool, str]:
    try:
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_CEILING_DIRECTORIES": str(root.resolve().parent),
        }
        result = subprocess.run(["git", "-c", "core.hooksPath=", "-c", "core.fsmonitor=false", *arguments], cwd=root, env=environment, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def git_state(root: Path) -> dict[str, Any]:
    """Read a fixed Git state. It deliberately exposes no caller-provided command."""
    top_ok, top = _git(root, "rev-parse", "--show-toplevel")
    head_ok, head = _git(root, "rev-parse", "HEAD")
    status_ok, porcelain = _git(root, "status", "--porcelain=v1")
    branch_ok, branch = _git(root, "branch", "--show-current")
    worktrees_ok, worktrees = _git(root, "worktree", "list", "--porcelain")
    branches_ok, branches = _git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    exact_root = top_ok and Path(top).resolve() == root.resolve()
    return {
        "collector": "git_state",
        "status": (Status.PASSED if exact_root and head_ok and status_ok and branch_ok and worktrees_ok and branches_ok else Status.UNVERIFIED).value,
        "root": top if exact_root else None,
        "head": head if head_ok else None,
        "branch": branch if branch_ok else None,
        "porcelain": porcelain.splitlines() if status_ok else None,
        "worktree_count": worktrees.count("worktree ") if worktrees_ok else None,
        "local_branches": branches.splitlines() if branches_ok else None,
    }


def github_state(snapshot: Path, *, expected: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Read a preflight-produced GitHub JSON snapshot. This collector has no network path."""
    try:
        value = json.loads(snapshot.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"collector": "github_state", "status": Status.UNVERIFIED.value, "detail": str(exc)}
    if not expected:
        return {"collector": "github_state", "status": Status.UNVERIFIED.value, "detail": "no external expected GitHub state", "snapshot": value}
    mismatches = []
    for dotted, required in expected.items():
        if str(dotted).endswith("_at_least"):
            key = str(dotted).removesuffix("_at_least")
            actual = value.get(key) if isinstance(value, dict) else None
            if not isinstance(actual, (int, float)) or actual < required:
                mismatches.append(str(dotted))
            continue
        actual: Any = value
        for key in str(dotted).split("."):
            actual = actual.get(key) if isinstance(actual, dict) else None
        if actual != required:
            mismatches.append(str(dotted))
    return {"collector": "github_state", "status": (Status.PASSED if not mismatches else Status.FAILED).value, "expected": dict(expected), "mismatches": mismatches, "snapshot": value}


def provider_usage(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Sum provider telemetry already emitted by a host; never estimate a price from text."""
    usage = [event for event in events if isinstance(event.get("usage"), dict)]
    terminal = [event for event in usage if event.get("type") in {"usage", "result", "turn.completed"}]
    if terminal:
        usage = terminal
    if not usage:
        return {
            "collector": "provider_usage",
            "status": Status.UNVERIFIED.value,
            "cost_status": Status.UNVERIFIED.value,
            "cost_usd": None,
            "total_tokens": None,
            "observed_models": [],
            "includes_subagents": False,
            "detail": "host emitted no usage telemetry",
        }
    tokens = 0
    costs: list[Decimal] = []
    observed: set[str] = set()
    token_observations = 0
    invalid_fields = False
    includes_subagents = bool(usage) and all(
        event.get("includes_subagents") is True or event["usage"].get("includes_subagents") is True
        for event in usage
    )
    delegated_routes: list[dict[str, str]] = []
    root_routes: list[dict[str, str]] = []
    for event in usage:
        value = event["usage"]
        total = value.get("total_tokens")
        if total is None:
            if "input_tokens" in value or "output_tokens" in value:
                total = sum(int(value.get(name, 0) or 0) for name in ("input_tokens", "output_tokens"))
        if total is not None:
            try:
                parsed_tokens = int(total)
            except (TypeError, ValueError):
                invalid_fields = True
            else:
                if parsed_tokens < 0:
                    invalid_fields = True
                else:
                    tokens += parsed_tokens
                    token_observations += 1
        raw_cost = value.get("cost_usd", event.get("total_cost_usd"))
        if raw_cost is not None:
            try:
                parsed_cost = Decimal(str(raw_cost))
            except InvalidOperation:
                invalid_fields = True
            else:
                if not parsed_cost.is_finite() or parsed_cost < 0:
                    invalid_fields = True
                else:
                    costs.append(parsed_cost)
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        model = value.get("model", event.get("model", message.get("model")))
        if model:
            observed.add(str(model))
        raw_routes = value.get("delegated_routes", event.get("delegated_routes", []))
        if isinstance(raw_routes, list):
            for route in raw_routes:
                if isinstance(route, dict) and all(isinstance(route.get(field), str) and route[field] for field in ("tier", "model", "effort")):
                    delegated_routes.append({field: route[field] for field in ("tier", "model", "effort")})
        raw_root = value.get("root_route", event.get("root_route"))
        if isinstance(raw_root, dict) and all(isinstance(raw_root.get(field), str) and raw_root[field] for field in ("model", "effort")):
            root_routes.append({field: raw_root[field] for field in ("model", "effort")})
    unique_root_routes = {tuple(sorted(route.items())) for route in root_routes}
    return {
        "collector": "provider_usage",
        "status": (Status.PASSED if token_observations and not invalid_fields else Status.UNVERIFIED).value,
        "cost_status": (Status.PASSED if costs and not invalid_fields else Status.UNVERIFIED).value,
        "cost_usd": str(sum(costs, Decimal("0"))) if costs else None,
        "total_tokens": tokens,
        "observed_models": sorted(observed),
        "includes_subagents": includes_subagents,
        "delegated_routes": delegated_routes,
        "root_route": dict(next(iter(unique_root_routes))) if len(unique_root_routes) == 1 else None,
        "invalid_fields": invalid_fields,
    }
