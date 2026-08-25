#!/usr/bin/env python3
"""Deterministic adapter fixture. It never contacts a model or the network."""

from __future__ import annotations

import json
import sys


def main() -> int:
    request = json.load(sys.stdin)
    profile = request["profile"]
    json.dump(
        {
            "provider": "fixture",
            "model_id": f"fake-{profile}",
            "model_version": "1",
            "terminal_success": True,
            "environment_correct": True,
            "unauthorized_mutations": False,
            "unresolved_blocking_findings": 0,
            "recovery_success": None,
            "cleanup_correct": True,
            "cost_usd": 0.0,
            "metrics": {
                "tokens": 0,
                "tool_calls": 0,
                "secret_debug_dump": request.get("prompt"),
            },
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
