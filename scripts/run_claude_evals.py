#!/usr/bin/env python3
"""Validate SkipHow's shared corpus, or run it through Claude Code on request."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
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


def claude_metrics(output: str) -> dict[str, Any]:
    """Extract secondary efficiency signals from Claude's JSON result."""
    document = json.loads(output)
    return {
        key: document[key]
        for key in ("usage", "num_turns", "total_cost_usd")
        if key in document
    }


def run_live(*, claude: str) -> int:
    """Run opt-in Claude Code evaluations against an exact isolated candidate."""
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="skiphow-claude-evals-") as temporary:
        output_dir = Path(temporary)
        try:
            candidate_commit, candidate_tree, candidate_dir = shared.snapshot_candidate(output_dir)
        except ValueError as exc:
            print(f"run_claude_evals: {exc}", file=sys.stderr)
            return 2
        corpus = shared.load_corpus(candidate_dir / shared.DEFAULT_CORPUS.relative_to(ROOT))
        schema = json.loads(
            (candidate_dir / shared.RESPONSE_SCHEMA.relative_to(ROOT)).read_text(encoding="utf-8")
        )
        runtime_dir = output_dir / "runtime"
        evaluation_dir = output_dir / "evaluation"
        evaluation_dir.mkdir()
        try:
            shared.stage_runtime(candidate_dir, runtime_dir)
        except (OSError, ValueError) as exc:
            print(f"run_claude_evals: runtime staging failed: {exc}", file=sys.stderr)
            return 2
        environment = os.environ.copy()
        claude_config = output_dir / "claude-config"
        claude_config.mkdir()
        environment["CLAUDE_CONFIG_DIR"] = str(claude_config)
        for scenario in corpus["scenarios"]:
            prompt = (
                "Load and follow the SkipHow plugin for this evaluation. "
                "Classify the request under the Owner, Product Director, and CTO authority boundary. "
                "Use execute as the normal technical shape, diagnose-then-execute only for an unknown cause, "
                "and campaign only when orchestration needs durable state. Report whether the tracker is touched. "
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
                    str(runtime_dir),
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
                cwd=evaluation_dir,
                env=environment,
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
                record["metrics"] = {
                    **claude_metrics(completed.stdout),
                    "campaign_selected": response.get("execution_shape") == "campaign",
                    "tracker_touched": response.get("tracker_touched"),
                }
            except (json.JSONDecodeError, ValueError) as exc:
                record["error"] = f"invalid structured response: {exc}"
            results.append(record)
        final_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=candidate_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if final_status.returncode != 0 or final_status.stdout.strip():
            print("run_claude_evals: candidate snapshot changed during evaluation", file=sys.stderr)
            return 2
    print(
        json.dumps(
            {
                "candidate_commit": candidate_commit,
                "candidate_tree": candidate_tree,
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
    )
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
    if args.corpus.resolve() != shared.DEFAULT_CORPUS.resolve():
        print("run_claude_evals: live evaluation uses only the corpus committed with the candidate", file=sys.stderr)
        return 2
    return run_live(claude=args.claude)


if __name__ == "__main__":
    raise SystemExit(main())
