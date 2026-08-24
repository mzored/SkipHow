#!/usr/bin/env python3
"""Validate outcome evals or run them in isolated repositories."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = ROOT / "plugins/skiphow/evals/outcome_scenarios.json"
ACTIVATION = ROOT / "plugins/skiphow/evals/activation_scenarios.json"
SHARED_SPEC = importlib.util.spec_from_file_location(
    "skiphow_eval_shared", ROOT / "scripts/run_codex_evals.py"
)
assert SHARED_SPEC and SHARED_SPEC.loader
shared = importlib.util.module_from_spec(SHARED_SPEC)
SHARED_SPEC.loader.exec_module(shared)


def load(path: Path, *, minimum: int) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    scenarios = document.get("scenarios") if isinstance(document, dict) else None
    if document.get("schema_version") != 1 or not isinstance(scenarios, list):
        raise ValueError(f"invalid eval corpus: {path}")
    if len(scenarios) < minimum:
        raise ValueError(f"{path.name} needs at least {minimum} scenarios")
    identifiers = [row.get("id") for row in scenarios if isinstance(row, dict)]
    if len(identifiers) != len(set(identifiers)) or any(not value for value in identifiers):
        raise ValueError(f"{path.name} has missing or duplicate ids")
    return document


def validate_corpora() -> tuple[dict[str, Any], dict[str, Any]]:
    activation = load(ACTIVATION, minimum=10)
    outcomes = load(OUTCOMES, minimum=5)
    categories = {row.get("category") for row in activation["scenarios"]}
    if categories != {"direct", "indirect", "follow-up", "negative", "boundary"}:
        raise ValueError("activation corpus must cover all five categories")
    for scenario in outcomes["scenarios"]:
        if not isinstance(scenario.get("fixture"), dict) or not isinstance(
            scenario.get("graders"), dict
        ):
            raise ValueError(f"outcome {scenario.get('id')} lacks fixture or graders")
    return activation, outcomes


def run(command: Sequence[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def write_fixture(repo: Path, fixture: dict[str, str]) -> None:
    for relative, contents in fixture.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "SkipHow eval"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=repo, check=True)


def grade(repo: Path, fixture: dict[str, str], graders: dict[str, Any], gh_log: Path) -> list[str]:
    failures: list[str] = []
    for relative in graders.get("changed", []):
        path = repo / relative
        original = fixture.get(relative)
        if not path.exists() or (original is not None and path.read_text(encoding="utf-8") == original):
            failures.append(f"{relative} did not change")
    for relative in graders.get("unchanged", []):
        path = repo / relative
        if not path.exists() or path.read_text(encoding="utf-8") != fixture.get(relative):
            failures.append(f"{relative} changed")
    for relative in graders.get("absent", []):
        if (repo / relative).exists():
            failures.append(f"unexpected {relative}")
    calls = len(gh_log.read_text(encoding="utf-8").splitlines()) if gh_log.exists() else 0
    if calls != graders.get("gh_calls", 0):
        failures.append(f"expected {graders.get('gh_calls', 0)} gh calls, got {calls}")
    return failures


def run_live(host: str, executable: str) -> int:
    _, outcomes = validate_corpora()
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="skiphow-outcomes-") as temporary:
        root = Path(temporary)
        try:
            commit, tree, candidate = shared.snapshot_candidate(root)
        except ValueError as exc:
            print(f"run_outcome_evals: {exc}", file=sys.stderr)
            return 2
        runtime = root / "runtime"
        shared.stage_runtime(candidate, runtime)
        host_home = root / "host-home"
        host_home.mkdir()
        base_env = os.environ.copy()
        if host == "codex":
            base_env["CODEX_HOME"] = str(host_home)
            for command in (
                [executable, "plugin", "marketplace", "add", str(runtime), "--json"],
                [executable, "plugin", "add", "skiphow@skiphow", "--json"],
            ):
                completed = run(command, cwd=root, env=base_env)
                if completed.returncode:
                    print(completed.stdout + completed.stderr, file=sys.stderr)
                    return 2
        else:
            base_env["CLAUDE_CONFIG_DIR"] = str(host_home)

        for scenario in outcomes["scenarios"]:
            repo = root / scenario["id"]
            repo.mkdir()
            write_fixture(repo, scenario["fixture"])
            shim_dir = repo / ".eval-bin"
            shim_dir.mkdir()
            gh_log = repo / ".gh-calls"
            shim = shim_dir / "gh"
            shim.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$SKIPHOW_GH_LOG\"\nexit 64\n",
                encoding="utf-8",
            )
            shim.chmod(0o755)
            environment = dict(base_env)
            environment["PATH"] = f"{shim_dir}{os.pathsep}{environment.get('PATH', '')}"
            environment["SKIPHOW_GH_LOG"] = str(gh_log)
            prompt = scenario["prompt"]
            if host == "codex":
                command = [
                    executable,
                    "exec",
                    "--ephemeral",
                    "--sandbox",
                    "workspace-write",
                    prompt,
                ]
            else:
                command = [
                    executable,
                    "--plugin-dir",
                    str(runtime),
                    "--print",
                    "--no-session-persistence",
                    "--permission-mode",
                    "dontAsk",
                    prompt,
                ]
            completed = run(command, cwd=repo, env=environment)
            records.append(
                {
                    "id": scenario["id"],
                    "returncode": completed.returncode,
                    "failures": grade(repo, scenario["fixture"], scenario["graders"], gh_log),
                }
            )
    print(json.dumps({"candidate_commit": commit, "candidate_tree": tree, "results": records}, indent=2))
    return 0 if all(not row["returncode"] and not row["failures"] for row in records) else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("codex", "claude"))
    parser.add_argument("--executable")
    args = parser.parse_args(argv)
    try:
        activation, outcomes = validate_corpora()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"run_outcome_evals: {exc}", file=sys.stderr)
        return 2
    if not args.host:
        print(
            f"validated {len(activation['scenarios'])} activation and "
            f"{len(outcomes['scenarios'])} outcome scenarios offline"
        )
        return 0
    return run_live(args.host, args.executable or args.host)


if __name__ == "__main__":
    raise SystemExit(main())
