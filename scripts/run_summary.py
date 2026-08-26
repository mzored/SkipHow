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
            if result is not None:
                raise TranscriptError(f"{path}: more than one terminal result event")
            result = event
    if result is None:
        raise TranscriptError(f"{path}: no terminal result event; the run did not finish")
    for field in ("num_turns", "total_cost_usd", "duration_ms"):
        if not isinstance(result.get(field), (int, float)):
            raise TranscriptError(f"{path}: result event has no numeric {field}")
    return {
        "file": str(path),
        "turns": result["num_turns"],
        "cost_usd": round(result["total_cost_usd"], 2),
        "seconds": round(result["duration_ms"] / 1000),
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
