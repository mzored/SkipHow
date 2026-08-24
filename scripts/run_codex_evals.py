#!/usr/bin/env python3
"""Validate SkipHow behavioral evals, or run them through Codex on request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "plugins/skiphow/evals/behavioral_scenarios.json"
RESPONSE_SCHEMA = ROOT / "plugins/skiphow/evals/response_schema.json"
REQUIRED_ASSERTIONS = {
    "route": str,
    "owner_question": bool,
    "ceremony": str,
    "durable": bool,
    "testing": str,
    "review": str,
    "product_acceptance": bool,
}


def load_corpus(path: Path) -> dict[str, Any]:
    """Load and validate the portable, machine-readable behavioral corpus."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read eval corpus {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("eval corpus must be an object with schema_version 1")
    scenarios = document.get("scenarios")
    if not isinstance(scenarios, list) or not 20 <= len(scenarios) <= 40:
        raise ValueError("eval corpus must contain 20 to 40 scenarios")
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
        identifiers.add(identifier)
    return document


def evaluate(response: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Return assertion names whose structured response differs from the oracle."""
    return [name for name, value in expected.items() if response.get(name) != value]


def run_live(corpus: dict[str, Any], *, codex: str) -> int:
    """Run opt-in ephemeral structured Codex evaluations and print JSON results."""
    schema = RESPONSE_SCHEMA.resolve()
    if not schema.is_file():
        print(f"missing response schema: {schema}", file=sys.stderr)
        return 2
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="skiphow-evals-") as temporary:
        output_dir = Path(temporary)
        for scenario in corpus["scenarios"]:
            result_path = output_dir / f"{scenario['id']}.json"
            prompt = (
                "Load and follow $skiphow for this evaluation. Classify this SkipHow request. "
                "Return only the requested JSON object. "
                "Respect the Owner, Product Director, and CTO authority boundary.\n\n"
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
                    prompt,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            record: dict[str, Any] = {"id": scenario["id"], "returncode": completed.returncode}
            try:
                response = json.loads(result_path.read_text(encoding="utf-8"))
                record["mismatches"] = evaluate(response, scenario["assertions"])
            except (OSError, json.JSONDecodeError) as exc:
                record["error"] = f"invalid structured response: {exc}"
            results.append(record)
    print(json.dumps({"results": results}, indent=2, sort_keys=True))
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
    return run_live(corpus, codex=args.codex)


if __name__ == "__main__":
    raise SystemExit(main())
