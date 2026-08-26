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


def summarize(path: Path) -> dict[str, object]:
    tools: Counter[str] = Counter()
    delegations: Counter[str] = Counter()
    models: Counter[str] = Counter()
    skill = False
    result: dict[str, object] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
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
            result = event
    return {
        "file": str(path),
        "turns": result.get("num_turns"),
        "cost_usd": round(result.get("total_cost_usd", 0), 2),
        "seconds": round(result.get("duration_ms", 0) / 1000),
        "tool_calls": sum(tools.values()),
        "skill": skill,
        "delegations": dict(delegations),
        "models": dict(models),
    }


if __name__ == "__main__":
    for argument in sys.argv[1:]:
        print(json.dumps(summarize(Path(argument))))
