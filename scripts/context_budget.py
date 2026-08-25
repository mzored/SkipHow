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


def load_limits(path: Path = BASELINE) -> dict[str, int]:
    """Load the one committed budget for the public skill."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("context budget must use schema_version 1")
    raw = payload.get("root_skill_limits")
    if not isinstance(raw, dict):
        raise ValueError("context budget has no root_skill_limits object")
    limits = {"bytes": raw.get("bytes"), "words": raw.get("words")}
    if not all(isinstance(value, int) and value > 0 for value in limits.values()):
        raise ValueError("root skill limits must be positive integers")
    return limits  # type: ignore[return-value]


ROOT_SKILL_LIMITS = load_limits()


def metrics(text: str) -> dict[str, int]:
    """Return stable UTF-8 byte and whitespace-delimited word counts."""
    return {"bytes": len(text.encode("utf-8")), "words": len(text.split())}


def collect_report(path: Path = SKILL) -> dict[str, Any]:
    """Measure the only instruction file loaded when SkipHow is invoked."""
    measured = metrics(path.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "root_skill": path.relative_to(ROOT).as_posix(),
        "measured": measured,
        "limits": dict(ROOT_SKILL_LIMITS),
    }


def budget_errors(report: dict[str, Any]) -> list[str]:
    """Explain each exceeded limit with both the measured and allowed values."""
    measured = report["measured"]
    limits = report["limits"]
    return [
        f"root skill {unit} exceed the limit: {measured[unit]} > {limits[unit]}"
        for unit in ("bytes", "words")
        if measured[unit] > limits[unit]
    ]


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
            "context budget passed: "
            f"{measured['words']} words, {measured['bytes']} bytes"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
