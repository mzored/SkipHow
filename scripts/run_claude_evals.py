#!/usr/bin/env python3
"""Validate SkipHow's shared corpus, or run it through Claude Code on request."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CODEX_ADAPTER = ROOT / "scripts/run_codex_evals.py"
SPEC = importlib.util.spec_from_file_location("skiphow_shared_evals", CODEX_ADAPTER)
assert SPEC and SPEC.loader
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)


def structured_response(output: str) -> dict[str, Any]:
    """Extract Claude Code's schema-validated response from its JSON result."""
    document = json.loads(output)
    candidate = document.get("structured_output", document)
    if not isinstance(candidate, dict):
        raise ValueError("Claude result has no structured_output object")
    return candidate


def run_live(corpus: dict[str, Any], *, claude: str) -> int:
    """Run opt-in, isolated Claude Code evaluations against the local plugin."""
    schema = json.loads(shared.RESPONSE_SCHEMA.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for scenario in corpus["scenarios"]:
        prompt = (
            "Load and follow the SkipHow plugin for this evaluation. "
            "Classify the request under the Owner, Product Director, and CTO authority boundary. "
            "Return only the requested structured result. Set escalation to none unless the request "
            "needs an Owner decision, protected action, missing authority, or external prerequisite. "
            "For any other escalation value, provide a non-empty recommendation, evidence, "
            "consequence_of_waiting, and exact decision_or_action_needed.\n\n"
            f"Request: {scenario['prompt']}"
        )
        completed = subprocess.run(
            [
                claude,
                "--plugin-dir",
                str(ROOT),
                "--print",
                "--no-session-persistence",
                "--permission-mode",
                "dontAsk",
                "--tools",
                "",
                "--json-schema",
                json.dumps(schema, separators=(",", ":")),
                "--output-format",
                "json",
                prompt,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        record: dict[str, Any] = {
            "id": scenario["id"],
            "returncode": completed.returncode,
        }
        try:
            response = structured_response(completed.stdout)
            record["mismatches"] = shared.evaluate(response, scenario["assertions"])
        except (json.JSONDecodeError, ValueError) as exc:
            record["error"] = f"invalid structured response: {exc}"
        results.append(record)
    print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return 0 if all(
        item.get("returncode") == 0
        and not item.get("mismatches")
        and not item.get("error")
        for item in results
    ) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=shared.DEFAULT_CORPUS)
    parser.add_argument("--execute", action="store_true", help="run paid, live Claude Code evaluations")
    parser.add_argument("--claude", default="claude")
    args = parser.parse_args(argv)
    try:
        corpus = shared.load_corpus(args.corpus)
    except ValueError as exc:
        print(f"run_claude_evals: {exc}", file=sys.stderr)
        return 2
    if not args.execute:
        print(f"validated {len(corpus['scenarios'])} behavioral scenarios offline for Claude Code")
        return 0
    return run_live(corpus, claude=args.claude)


if __name__ == "__main__":
    raise SystemExit(main())
