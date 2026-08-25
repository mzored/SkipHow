#!/usr/bin/env python3
"""Run local grader contract checks and validate scenario manifests."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.graders import grade_files, validate_manifest  # noqa: E402
from evals.graders.outcome import ManifestError  # noqa: E402


def _object(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _validate_rule_registry(scenario_ids: set[str]) -> list[str]:
    errors: list[str] = []
    path = ROOT / "evals/deterministic/rules.json"
    if not path.is_file():
        return ["evals/deterministic/rules.json is missing"]
    registry = _object(path)
    if registry.get("schema_version") != 1:
        errors.append("evals/deterministic/rules.json must use schema_version 1")
    rules = registry.get("rules")
    if not isinstance(rules, list) or not rules:
        return [*errors, "evals/deterministic/rules.json has no rules array"]
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, Mapping):
            errors.append(f"deterministic rule {index} is not an object")
            continue
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            errors.append(f"deterministic rule {index} has no rule_id")
        elif rule_id in seen:
            errors.append(f"duplicate deterministic rule_id {rule_id!r}")
        else:
            seen.add(rule_id)
        owner_file = rule.get("owner_file")
        if not isinstance(owner_file, str) or not owner_file:
            errors.append(f"deterministic rule {rule_id!r} has no owner_file")
        else:
            owner_path = (ROOT / owner_file).resolve()
            if not owner_path.is_relative_to(ROOT) or not owner_path.is_file():
                errors.append(f"deterministic rule {rule_id!r} has invalid owner_file")
        scenarios = rule.get("eval_scenarios")
        if not isinstance(scenarios, list) or not scenarios or not all(
            isinstance(item, str) for item in scenarios
        ):
            errors.append(f"deterministic rule {rule_id!r} has invalid eval_scenarios")
        else:
            unknown = sorted(set(scenarios) - scenario_ids)
            if unknown:
                errors.append(
                    f"deterministic rule {rule_id!r} references unknown scenarios: "
                    + ", ".join(unknown)
                )
    return errors


def main() -> int:
    errors: list[str] = []
    fixtures = ROOT / "evals/fixtures/deterministic"
    manifest_path = fixtures / "scenario.json"
    cases = _object(fixtures / "cases.json").get("cases")
    if not isinstance(cases, list):
        errors.append("evals/fixtures/deterministic/cases.json has no cases array")
    else:
        for index, case in enumerate(cases):
            if not isinstance(case, Mapping):
                errors.append(f"fixture case {index} is not an object")
                continue
            receipt = case.get("receipt")
            expected = case.get("verdict")
            if not isinstance(receipt, str) or expected not in {"PASS", "FAIL"}:
                errors.append(f"fixture case {index} has invalid receipt or verdict")
                continue
            try:
                actual = grade_files(manifest_path, fixtures / receipt).verdict
            except ManifestError as exc:
                errors.append(f"fixture case {index} is invalid: {exc}")
                continue
            if actual != expected:
                errors.append(f"fixture case {index}: expected {expected}, got {actual}")

    scenario_ids: set[str] = set()
    scenario_root = ROOT / "evals/scenarios"
    for path in sorted(scenario_root.glob("*.json")) if scenario_root.is_dir() else ():
        try:
            manifest = _object(path)
            validate_manifest(manifest)
            scenario_id = manifest.get("id")
            if isinstance(scenario_id, str):
                if scenario_id in scenario_ids:
                    errors.append(f"duplicate scenario id {scenario_id!r}")
                scenario_ids.add(scenario_id)
        except (OSError, ValueError, json.JSONDecodeError, ManifestError) as exc:
            errors.append(f"invalid scenario {path.relative_to(ROOT)}: {exc}")
    errors.extend(_validate_rule_registry(scenario_ids))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("deterministic eval contracts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
