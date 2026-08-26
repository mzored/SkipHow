#!/usr/bin/env python3
"""Summarize a Claude Code stream-json transcript: turns, cost, time, tools, delegations.

Usage: python scripts/run_summary.py <out.jsonl> [<out.jsonl> ...]
Prints one line per file so paired runs (with and without the plugin) can be compared.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


class TranscriptError(ValueError):
    """The transcript cannot support a summary."""


def summarize(path: Path) -> dict[str, object]:
    tools: Counter[str] = Counter()
    delegations: Counter[str] = Counter()
    models: Counter[str] = Counter()
    skill = False
    result: dict[str, object] | None = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TranscriptError(f"{path}:{number}: not a JSON event: {exc}") from exc
        if not isinstance(event, dict):
            raise TranscriptError(f"{path}:{number}: event is not an object")
        if event.get("type") == "assistant":
            message = event.get("message", {})
            models[message.get("model", "?")] += 1
            for block in message.get("content", []):
                if block.get("type") != "tool_use":
                    continue
                tools[block["name"]] += 1
                inputs = block.get("input", {})
                if block["name"] == "Skill":
                    skill = True
                if block["name"] == "Agent":
                    delegations[inputs.get("subagent_type", "inherit")] += 1
        elif event.get("type") == "result":
            # A streaming-input run emits one cumulative result per turn; the last wins.
            result = event
    if result is None:
        raise TranscriptError(f"{path}: no terminal result event; the run did not finish")
    for field in ("num_turns", "total_cost_usd", "duration_ms"):
        value = result.get(field)
        if field in result and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise TranscriptError(f"{path}: result event has a non-numeric {field}")

    def measured(field: str, scale: float = 1.0, digits: int | None = 2) -> float | int | None:
        # A field the host did not report stays absent. Reporting it as zero is how a
        # truncated run became a plausible receipt in the first place.
        return None if field not in result else round(result[field] / scale, digits)

    return {
        "file": str(path),
        "turns": result.get("num_turns"),
        "cost_usd": measured("total_cost_usd"),
        "seconds": measured("duration_ms", 1000, None),
        "tool_calls": sum(tools.values()),
        "skill": skill,
        "delegations": dict(delegations),
        "models": dict(models),
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    for argument in argv:
        try:
            print(json.dumps(summarize(Path(argument))))
        except (OSError, TranscriptError) as exc:
            print(f"unusable transcript: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
