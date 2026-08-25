#!/usr/bin/env python3
"""Generate a complete local live-eval config for one provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ("economy", "balanced", "frontier")
HIGH_IMPACT = {
    "cleanup-safety", "context-handoff", "github-lifecycle", "long-campaign",
    "pause-resume-cancel", "prompt-injection", "protected-action",
}
LOW_RISK = {"simple-anti-ceremony", "trivial-local-logic", "verification-ceiling"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--provider", required=True, choices=("codex", "claude"))
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument(
        "--cwd",
        required=True,
        type=Path,
        help="isolated scenario workspace; do not use the candidate checkout",
    )
    for profile in PROFILES:
        parser.add_argument(f"--{profile}-model", required=True)
        parser.add_argument(f"--{profile}-model-version", required=True)
        parser.add_argument(f"--{profile}-max-cost-usd", required=True, type=float)
    parser.add_argument("--input-cost-per-million", type=float)
    parser.add_argument("--output-cost-per-million", type=float)
    return parser


def _head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ValueError("cannot identify repository HEAD")
    return completed.stdout.strip()


def _features(scenario_id: str) -> dict[str, str]:
    if scenario_id in HIGH_IMPACT:
        return {
            "task_kind": "integration", "mutation": "protected",
            "error_cost": "high", "reversibility": "hard",
            "blast_radius": "external", "verification_strength": "partial",
        }
    if scenario_id in LOW_RISK:
        return {
            "task_kind": "implementation", "mutation": "local",
            "error_cost": "low", "reversibility": "easy",
            "blast_radius": "local", "verification_strength": "strong",
        }
    return {
        "task_kind": "implementation", "mutation": "local",
        "error_cost": "medium", "reversibility": "easy",
        "blast_radius": "local", "verification_strength": "partial",
    }


def _manifests() -> list[dict[str, Any]]:
    manifests = []
    for path in sorted((ROOT / "evals" / "scenarios").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"scenario manifest is not an object: {path}")
        manifests.append(value)
    return manifests


def _command(args: argparse.Namespace, profile: str) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "evals" / "live" / "provider_adapter.py"),
        "--provider", args.provider,
        "--model", getattr(args, f"{profile}_model"),
        "--model-version", getattr(args, f"{profile}_model_version"),
        "--cwd", str(args.cwd.resolve()),
    ]
    if args.input_cost_per_million is not None:
        command.extend(("--input-cost-per-million", str(args.input_cost_per_million)))
    if args.output_cost_per_million is not None:
        command.extend(("--output-cost-per-million", str(args.output_cost_per_million)))
    return command


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.trials < 2:
        print("--trials must be at least 2", file=sys.stderr)
        return 2
    if any(getattr(args, f"{profile}_max_cost_usd") <= 0 for profile in PROFILES):
        print("profile cost caps must be positive", file=sys.stderr)
        return 2
    if not args.cwd.is_dir() or args.cwd.resolve() == ROOT:
        print("--cwd must be an existing isolated workspace outside the candidate checkout", file=sys.stderr)
        return 2
    if args.provider == "codex" and (
        args.input_cost_per_million is None or args.output_cost_per_million is None
    ):
        print("Codex config requires explicit input and output token prices", file=sys.stderr)
        return 2
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    value = {
        "schema_version": 1,
        "suite_id": f"skiphow-release-{args.provider}",
        "candidate": {
            "repository_revision": _head(),
            "plugin_version": version,
            "runner_version": version,
            "evaluator_version": "2",
        },
        "trials": args.trials,
        "adapters": {
            profile: {
                "command": _command(args, profile),
                "required_env": [],
                "max_cost_usd_per_trial": getattr(args, f"{profile}_max_cost_usd"),
            }
            for profile in PROFILES
        },
        "scenarios": [
            {
                "id": manifest["id"],
                "prompt": manifest["request"]["user_message"],
                "features": _features(str(manifest["id"])),
            }
            for manifest in _manifests()
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
