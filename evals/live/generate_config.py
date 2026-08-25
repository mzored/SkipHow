#!/usr/bin/env python3
"""Generate a complete local live-eval config for one provider."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="generated config path outside the candidate checkout",
    )
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
    git_identity: list[str] = []
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            git_identity = completed.stdout.splitlines()
    except OSError:
        pass
    if (
        len(git_identity) == 2
        and Path(git_identity[0]).resolve() == ROOT.resolve()
        and git_identity[1].strip()
    ):
        return git_identity[1].strip()

    # Source archives deliberately omit .git. They still need a stable identity for
    # non-release config generation and deterministic tests. Release mode remains
    # stricter: evals/live/run.py requires a clean Git checkout and exact HEAD.
    digest = hashlib.sha256()
    root_excluded = {
        ".mypy_cache", ".pytest_cache", ".ruff_cache", ".skiphow", ".venv",
        "build", "dist", "venv",
    }

    def included(path: Path) -> bool:
        relative = path.relative_to(ROOT)
        return (
            (path.is_file() or path.is_symlink())
            and relative.parts[0] not in root_excluded
            and not any(
                part in {".git", "__pycache__"} or part.endswith(".egg-info")
                for part in relative.parts
            )
        )

    files = sorted(
        (path for path in ROOT.rglob("*") if included(path)),
        key=lambda path: os.fsencode(path.relative_to(ROOT).as_posix()),
    )
    if not files:
        raise ValueError("cannot identify repository or archive contents")
    for path in files:
        relative = os.fsencode(path.relative_to(ROOT).as_posix())
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        if path.is_symlink():
            digest.update(b"L")
            data = os.fsencode(os.readlink(path))
        else:
            digest.update(b"X" if path.stat().st_mode & 0o111 else b"F")
            data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return f"archive-sha256:{digest.hexdigest()}"


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


def _inside_candidate(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False
    return True


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
    if not args.cwd.is_dir() or _inside_candidate(args.cwd):
        print("--cwd must be an existing isolated workspace outside the candidate checkout", file=sys.stderr)
        return 2
    if _inside_candidate(args.output):
        print("--output must be outside the candidate checkout", file=sys.stderr)
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
