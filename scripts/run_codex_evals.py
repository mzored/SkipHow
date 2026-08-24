#!/usr/bin/env python3
"""Validate SkipHow behavioral evals, or run them through Codex on request."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "plugins/skiphow/evals/behavioral_scenarios.json"
RESPONSE_SCHEMA = ROOT / "plugins/skiphow/evals/response_schema.json"
REQUIRED_ASSERTIONS = {
    "intent": str,
    "execution_shape": str,
    "owner_question": bool,
    "ceremony": str,
    "tracker_touched": bool,
    "durable": bool,
    "testing": str,
    "review": str,
    "product_acceptance": bool,
    "escalation": str,
}
ESCALATION_CLASSES = {
    "none",
    "owner-decision",
    "protected-action",
    "missing-authority",
    "external-prerequisite",
}
ESCALATION_BRIEF_FIELDS = (
    "recommendation",
    "evidence",
    "consequence_of_waiting",
    "decision_or_action_needed",
)

TOOL_ITEM_TYPES = {
    "command_execution",
    "mcp_tool_call",
    "dynamic_tool_call",
    "web_search",
    "collaboration_tool_call",
}


def codex_metrics(output: str) -> dict[str, Any]:
    """Extract secondary efficiency signals from Codex JSONL when available."""
    metrics: dict[str, Any] = {"tool_calls": 0}
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") in TOOL_ITEM_TYPES:
            metrics["tool_calls"] += 1
        usage = event.get("usage")
        if isinstance(usage, dict):
            metrics["usage"] = usage
    return metrics


def snapshot_candidate(output_dir: Path) -> tuple[str, str, Path]:
    """Create a clean detached snapshot of the exact repository candidate."""
    identity = subprocess.run(
        ["git", "rev-parse", "HEAD", "HEAD^{tree}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if identity.returncode != 0 or status.returncode != 0 or status.stdout.strip():
        raise ValueError("live evaluation requires a clean candidate commit")
    candidate_commit, candidate_tree = identity.stdout.splitlines()
    candidate_dir = output_dir / "candidate"
    for command, label in (
        (["git", "clone", "--quiet", "--shared", "--no-checkout", str(ROOT), str(candidate_dir)], "candidate snapshot"),
        (["git", "-C", str(candidate_dir), "checkout", "--quiet", "--detach", candidate_commit], "candidate checkout"),
    ):
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = (completed.stdout + completed.stderr).strip()
            raise ValueError(f"{label} failed: {detail}")
    snapshot_identity = subprocess.run(
        ["git", "rev-parse", "HEAD", "HEAD^{tree}"],
        cwd=candidate_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    snapshot_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=candidate_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        snapshot_identity.returncode != 0
        or snapshot_identity.stdout.splitlines() != [candidate_commit, candidate_tree]
        or snapshot_status.returncode != 0
        or snapshot_status.stdout.strip()
    ):
        raise ValueError("candidate snapshot identity check failed")
    return candidate_commit, candidate_tree, candidate_dir


def stage_runtime(candidate_dir: Path, runtime_dir: Path) -> None:
    """Stage host packages without exposing the behavioral oracle."""
    for relative in (Path(".agents"), Path(".claude-plugin"), Path("adapters")):
        shutil.copytree(candidate_dir / relative, runtime_dir / relative)
    plugin_source = candidate_dir / "plugins" / "skiphow"
    plugin_target = runtime_dir / "plugins" / "skiphow"
    plugin_target.parent.mkdir(parents=True)
    shutil.copytree(
        plugin_source,
        plugin_target,
        ignore=shutil.ignore_patterns("evals", "__pycache__"),
    )
    if any(runtime_dir.rglob("behavioral_scenarios.json")):
        raise ValueError("behavioral oracle leaked into the staged runtime")


def load_corpus(path: Path) -> dict[str, Any]:
    """Load and validate the portable, machine-readable behavioral corpus."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read eval corpus {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("eval corpus must be an object with schema_version 1")
    scenarios = document.get("scenarios")
    if not isinstance(scenarios, list) or not 20 <= len(scenarios) <= 50:
        raise ValueError("eval corpus must contain 20 to 50 scenarios")
    identifiers: set[str] = set()
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            raise ValueError(f"scenario {index} must be an object")
        identifier = scenario.get("id")
        prompt = scenario.get("prompt")
        assertions = scenario.get("assertions")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise ValueError(f"scenario {index} has a missing or duplicate id")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"scenario {identifier} has no prompt")
        if not isinstance(assertions, dict) or set(assertions) != set(REQUIRED_ASSERTIONS):
            raise ValueError(f"scenario {identifier} has an incomplete assertion set")
        for name, expected_type in REQUIRED_ASSERTIONS.items():
            if type(assertions[name]) is not expected_type or assertions[name] == "":
                raise ValueError(f"scenario {identifier} has an invalid {name} assertion")
        if assertions["escalation"] not in ESCALATION_CLASSES:
            raise ValueError(f"scenario {identifier} has an invalid escalation assertion")
        identifiers.add(identifier)
    return document


def evaluate(response: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Return assertion names whose structured response differs from the oracle."""
    mismatches = [name for name, value in expected.items() if response.get(name) != value]
    if response.get("escalation") != "none":
        mismatches.extend(
            name
            for name in ESCALATION_BRIEF_FIELDS
            if not isinstance(response.get(name), str) or not response[name].strip()
        )
    return mismatches


def run_live(*, codex: str) -> int:
    """Snapshot the exact commit, install it in isolation, and run live evaluations."""
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="skiphow-evals-") as temporary:
        output_dir = Path(temporary)
        try:
            candidate_commit, candidate_tree, candidate_dir = snapshot_candidate(output_dir)
        except ValueError as exc:
            print(f"run_codex_evals: {exc}", file=sys.stderr)
            return 2
        schema = output_dir / "response_schema.json"
        shutil.copy2(candidate_dir / RESPONSE_SCHEMA.relative_to(ROOT), schema)
        corpus = load_corpus(candidate_dir / DEFAULT_CORPUS.relative_to(ROOT))
        if not schema.is_file():
            print(f"missing response schema: {schema}", file=sys.stderr)
            return 2
        runtime_dir = output_dir / "runtime"
        evaluation_dir = output_dir / "evaluation"
        evaluation_dir.mkdir()
        try:
            stage_runtime(candidate_dir, runtime_dir)
        except (OSError, ValueError) as exc:
            print(f"run_codex_evals: runtime staging failed: {exc}", file=sys.stderr)
            return 2
        codex_home = output_dir / "codex-home"
        codex_home.mkdir()
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(codex_home)
        for command, label in (
            ([codex, "plugin", "marketplace", "add", str(runtime_dir), "--json"], "marketplace discovery"),
            ([codex, "plugin", "add", "skiphow@skiphow", "--json"], "candidate installation"),
            ([codex, "plugin", "list", "--json"], "candidate listing"),
        ):
            completed = subprocess.run(
                command,
                cwd=evaluation_dir,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            detail = (completed.stdout + completed.stderr).strip()
            if completed.returncode != 0 or (label == "candidate listing" and "skiphow" not in detail):
                print(f"run_codex_evals: {label} failed: {detail}", file=sys.stderr)
                return 2
        for scenario in corpus["scenarios"]:
            result_path = output_dir / f"{scenario['id']}.json"
            prompt = (
                "Use the installed SkipHow candidate to classify this realistic project request. "
                "Return only the requested JSON object. Inspect the candidate's instructions instead "
                "of assuming a routing policy. Fill every required field and explain the classification "
                "briefly in reason.\n\n"
                f"Request: {scenario['prompt']}"
            )
            completed = subprocess.run(
                [
                    codex,
                    "exec",
                    "--ephemeral",
                    "--sandbox",
                    "read-only",
                    "--output-schema",
                    str(schema),
                    "--output-last-message",
                    str(result_path),
                    "--json",
                    prompt,
                ],
                cwd=evaluation_dir,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            record: dict[str, Any] = {"id": scenario["id"], "returncode": completed.returncode}
            try:
                response = json.loads(result_path.read_text(encoding="utf-8"))
                record["mismatches"] = evaluate(response, scenario["assertions"])
                record["metrics"] = {
                    **codex_metrics(completed.stdout),
                    "campaign_selected": response.get("execution_shape") == "campaign",
                    "tracker_touched": response.get("tracker_touched"),
                }
            except (OSError, json.JSONDecodeError) as exc:
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
            print("run_codex_evals: candidate snapshot changed during evaluation", file=sys.stderr)
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
    return 0 if all(item.get("returncode") == 0 and not item.get("mismatches") and not item.get("error") for item in results) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--execute", action="store_true", help="run paid, live Codex evaluations")
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args(argv)
    try:
        corpus = load_corpus(args.corpus)
    except ValueError as exc:
        print(f"run_codex_evals: {exc}", file=sys.stderr)
        return 2
    if not args.execute:
        print(f"validated {len(corpus['scenarios'])} behavioral scenarios offline")
        return 0
    if args.corpus.resolve() != DEFAULT_CORPUS.resolve():
        print("run_codex_evals: live evaluation uses only the corpus committed with the candidate", file=sys.stderr)
        return 2
    return run_live(codex=args.codex)


if __name__ == "__main__":
    raise SystemExit(main())
