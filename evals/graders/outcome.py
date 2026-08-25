"""Grade scenario receipts without executing agents, commands, or network calls.

The scenario manifest describes observable predicates. A receipt supplies the
observations recorded by an eval harness. Required predicates must match and
forbidden predicates must not match. The grader deliberately does not infer a
pass from prose or from a missing observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


MISSING = object()
SUPPORTED_OPERATORS = frozenset(
    {
        "contains",
        "equals",
        "greater_than",
        "greater_than_or_equal",
        "less_than_or_equal",
        "matches",
        "not_contains",
        "set_equals",
    }
)


class ManifestError(ValueError):
    """Raised when a manifest or receipt cannot be graded safely."""


@dataclass(frozen=True)
class CheckResult:
    """One evaluated scenario predicate."""

    rule_id: str
    category: str
    passed: bool
    observation: str
    operator: str
    expected: Any
    actual: Any
    evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.rule_id,
            "category": self.category,
            "passed": self.passed,
            "observation": self.observation,
            "operator": self.operator,
            "expected": self.expected,
            "actual": self.actual,
            "evidence": list(self.evidence),
            "missing_evidence": list(self.missing_evidence),
            "message": self.message,
        }


@dataclass(frozen=True)
class GradeReport:
    """Machine-readable deterministic grade."""

    scenario_id: str
    verdict: str
    checks: tuple[CheckResult, ...]
    errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "scenario_id": self.scenario_id,
            "verdict": self.verdict,
            "passed": self.passed,
            "summary": {
                "checks": len(self.checks),
                "passed": sum(check.passed for check in self.checks),
                "failed": sum(not check.passed for check in self.checks),
                "errors": len(self.errors),
            },
            "checks": [check.as_dict() for check in self.checks],
            "errors": list(self.errors),
        }


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ManifestError(f"{path} must contain a JSON object")
    return value


def _segments(path: str) -> list[str]:
    if path.startswith("/"):
        if path == "/":
            return [""]
        return [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]
    return path.split(".") if path else []


def _resolve_path(document: Any, path: str) -> Any:
    current = document
    for segment in _segments(path):
        if isinstance(current, Mapping):
            if segment not in current:
                return MISSING
            current = current[segment]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            try:
                index = int(segment)
            except ValueError:
                return MISSING
            if index < 0 or index >= len(current):
                return MISSING
            current = current[index]
        else:
            return MISSING
    return current


def _actual_value(receipt: Mapping[str, Any], rule: Mapping[str, Any]) -> tuple[Any, str]:
    rule_id = rule.get("id")
    observations = receipt.get("observations")
    if isinstance(observations, Mapping) and isinstance(rule_id, str) and rule_id in observations:
        return observations[rule_id], f"observations.{rule_id}"

    candidates: list[str] = []
    observation = rule.get("observation")
    if isinstance(observation, str):
        candidates.append(observation)
    for candidate in candidates:
        actual = _resolve_path(receipt, candidate)
        if actual is not MISSING:
            return actual, candidate
        if isinstance(observations, Mapping):
            actual = _resolve_path(observations, candidate)
            if actual is not MISSING:
                return actual, f"observations.{candidate}"
    return MISSING, candidates[0] if candidates else ""


def _required_evidence(rule: Mapping[str, Any]) -> tuple[str, ...]:
    value = rule.get("evidence", [])
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if all(isinstance(item, str) and item for item in value):
            return tuple(value)
    raise ManifestError(f"rule {rule.get('id')!r} evidence must be a string array")


def _available_evidence(receipt: Mapping[str, Any]) -> set[str]:
    value = receipt.get("evidence", {})
    if isinstance(value, Mapping):
        return {str(key) for key, item in value.items() if item is not None}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return {item for item in value if isinstance(item, str)}
    return set()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _contains(actual: Any, expected: Any) -> bool:
    if isinstance(actual, str):
        return isinstance(expected, str) and expected in actual
    if isinstance(actual, Mapping):
        return expected in actual
    if isinstance(actual, Sequence) and not isinstance(actual, (str, bytes, bytearray)):
        if isinstance(expected, Sequence) and not isinstance(expected, (str, bytes, bytearray)):
            return all(item in actual for item in expected)
        return expected in actual
    return False


def _evaluate(operator: str, actual: Any, expected: Any) -> bool:
    if operator == "equals":
        return actual == expected
    if operator == "contains":
        return _contains(actual, expected)
    if operator == "not_contains":
        return not _contains(actual, expected)
    if operator == "set_equals":
        if not isinstance(actual, Sequence) or isinstance(actual, (str, bytes, bytearray)):
            return False
        if not isinstance(expected, Sequence) or isinstance(expected, (str, bytes, bytearray)):
            return False
        try:
            return set(actual) == set(expected)
        except TypeError:
            return False
    if operator == "less_than_or_equal":
        return _is_number(actual) and _is_number(expected) and actual <= expected
    if operator == "greater_than_or_equal":
        return _is_number(actual) and _is_number(expected) and actual >= expected
    if operator == "greater_than":
        return _is_number(actual) and _is_number(expected) and actual > expected
    if operator == "matches":
        return isinstance(actual, str) and isinstance(expected, str) and fnmatchcase(actual, expected)
    raise ManifestError(f"unsupported operator {operator!r}")


def _rules(grading: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = grading.get(key, [])
    if not isinstance(value, list):
        raise ManifestError(f"grading.{key} must be an array")
    result: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for index, rule in enumerate(value):
        if not isinstance(rule, Mapping):
            raise ManifestError(f"grading.{key}[{index}] must be an object")
        rule_id = rule.get("id")
        operator = rule.get("operator")
        if not isinstance(rule_id, str) or not rule_id:
            raise ManifestError(f"grading.{key}[{index}].id must be a non-empty string")
        if rule_id in seen:
            raise ManifestError(f"duplicate rule id {rule_id!r} in grading.{key}")
        seen.add(rule_id)
        if operator not in SUPPORTED_OPERATORS:
            raise ManifestError(f"grading.{key}[{index}] has unsupported operator {operator!r}")
        if "expected" not in rule:
            raise ManifestError(f"grading.{key}[{index}] has no expected value")
        if not isinstance(rule.get("observation"), str):
            raise ManifestError(f"grading.{key}[{index}].observation must be a string")
        _required_evidence(rule)
        result.append(rule)
    return result


def _check(rule: Mapping[str, Any], receipt: Mapping[str, Any], category: str) -> CheckResult:
    rule_id = str(rule["id"])
    operator = str(rule["operator"])
    expected = rule["expected"]
    evidence = _required_evidence(rule)
    missing_evidence = tuple(sorted(set(evidence) - _available_evidence(receipt)))
    actual, source = _actual_value(receipt, rule)
    if actual is MISSING:
        return CheckResult(
            rule_id,
            category,
            False,
            source,
            operator,
            expected,
            None,
            evidence,
            missing_evidence,
            "receipt has no observation for this rule",
        )
    predicate_matched = _evaluate(operator, actual, expected)
    passed = predicate_matched if category == "required_outcome" else not predicate_matched
    passed = passed and not missing_evidence
    if category == "required_outcome":
        message = "required outcome matched" if passed else "required outcome did not match"
    else:
        message = "forbidden effect was absent" if passed else "forbidden effect occurred"
    if missing_evidence:
        message = "receipt lacks evidence: " + ", ".join(missing_evidence)
    return CheckResult(
        rule_id,
        category,
        passed,
        source,
        operator,
        expected,
        actual,
        evidence,
        missing_evidence,
        message,
    )


def validate_manifest(manifest: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    """Validate a version-1 manifest and return its two rule groups."""
    scenario_id = manifest.get("id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ManifestError("scenario manifest id must be a non-empty string")
    if manifest.get("schema_version") != 1:
        raise ManifestError(f"scenario {scenario_id!r} must use schema_version 1")
    grading = manifest.get("grading")
    if not isinstance(grading, Mapping):
        raise ManifestError(f"scenario {scenario_id!r} has no grading object")
    pass_condition = grading.get("pass_condition")
    if pass_condition not in (None, "all_required_outcomes_and_no_forbidden_effects"):
        raise ManifestError(f"scenario {scenario_id!r} has unsupported pass_condition {pass_condition!r}")

    required = _rules(grading, "required_outcomes")
    forbidden = _rules(grading, "forbidden_effects")
    all_ids = [str(rule["id"]) for rule in (*required, *forbidden)]
    if len(all_ids) != len(set(all_ids)):
        raise ManifestError(f"scenario {scenario_id!r} repeats a rule id across rule groups")
    if not all_ids:
        raise ManifestError(f"scenario {scenario_id!r} has no grading rules")
    return required, forbidden


def grade_scenario(manifest: Mapping[str, Any], receipt: Mapping[str, Any]) -> GradeReport:
    """Grade one receipt against one version-1 scenario manifest."""
    required, forbidden = validate_manifest(manifest)
    scenario_id = str(manifest["id"])
    receipt_id = receipt.get("scenario_id", receipt.get("id"))
    if receipt_id is not None and receipt_id != scenario_id:
        raise ManifestError(
            f"receipt scenario id {receipt_id!r} does not match manifest id {scenario_id!r}"
        )
    checks = [
        *(_check(rule, receipt, "required_outcome") for rule in required),
        *(_check(rule, receipt, "forbidden_effect") for rule in forbidden),
    ]
    verdict = "PASS" if all(check.passed for check in checks) else "FAIL"
    return GradeReport(scenario_id, verdict, tuple(checks))


def grade_files(manifest_path: Path, receipt_path: Path) -> GradeReport:
    """Load and grade two JSON files."""
    return grade_scenario(_load_json(manifest_path), _load_json(receipt_path))
