#!/usr/bin/env python3
"""Measure the canonical skill against its fixed instruction budget."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/skiphow/skills/skiphow/SKILL.md"
BASELINE = ROOT / "scripts/context_budget_baseline.json"


REFERENCES = SKILL.parent / "references"


def load_limits(path: Path = BASELINE) -> dict[str, dict[str, int]]:
    """Load the committed budgets for the root skill and its lazy references."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise ValueError("context budget must use schema_version 2")
    limits: dict[str, dict[str, int]] = {}
    for key, fields in (
        ("root_skill_limits", ("bytes", "words")),
        ("reference_limits", ("total_words", "file_words")),
    ):
        raw = payload.get(key)
        if not isinstance(raw, dict):
            raise ValueError(f"context budget has no {key} object")
        values = {field: raw.get(field) for field in fields}
        if not all(isinstance(value, int) and value > 0 for value in values.values()):
            raise ValueError(f"{key} must be positive integers")
        limits[key] = values  # type: ignore[assignment]
    return limits


LIMITS = load_limits()
ROOT_SKILL_LIMITS = LIMITS["root_skill_limits"]
REFERENCE_LIMITS = LIMITS["reference_limits"]


def metrics(text: str) -> dict[str, int]:
    """Return stable UTF-8 byte and whitespace-delimited word counts."""
    return {"bytes": len(text.encode("utf-8")), "words": len(text.split())}


def collect_report(path: Path = SKILL, references: Path = REFERENCES) -> dict[str, Any]:
    """Measure the root skill and every lazy reference it can load."""
    measured = metrics(path.read_text(encoding="utf-8"))
    files = {
        item.relative_to(references).as_posix(): metrics(item.read_text(encoding="utf-8"))["words"]
        for item in sorted(references.rglob("*.md"))
    }
    return {
        "schema_version": 2,
        "root_skill": path.relative_to(ROOT).as_posix(),
        "measured": measured,
        "limits": dict(ROOT_SKILL_LIMITS),
        "references": {"files": files, "total_words": sum(files.values()), "limits": dict(REFERENCE_LIMITS)},
    }


def budget_errors(report: dict[str, Any]) -> list[str]:
    """Explain each exceeded limit with both the measured and allowed values."""
    measured = report["measured"]
    limits = report["limits"]
    errors = [
        f"root skill {unit} exceed the limit: {measured[unit]} > {limits[unit]}"
        for unit in ("bytes", "words")
        if measured[unit] > limits[unit]
    ]
    references = report.get("references")
    if references:
        ref_limits = references["limits"]
        if references["total_words"] > ref_limits["total_words"]:
            errors.append(
                f"references words exceed the limit: {references['total_words']} > {ref_limits['total_words']}"
            )
        for name, words in references["files"].items():
            if words > ref_limits["file_words"]:
                errors.append(f"reference {name} words exceed the limit: {words} > {ref_limits['file_words']}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the skill exceeds its limit")
    parser.add_argument("--json", action="store_true", help="print the measurement report")
    args = parser.parse_args(argv)

    try:
        report = collect_report()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"context budget: {exc}", file=sys.stderr)
        return 1

    errors = budget_errors(report)
    if args.json or not args.check:
        print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        for error in errors:
            print(f"context budget: {error}", file=sys.stderr)
        return 1
    if args.check:
        measured = report["measured"]
        print(
            "context budget passed: root "
            f"{measured['words']} words, {measured['bytes']} bytes; "
            f"references {report['references']['total_words']} words"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
