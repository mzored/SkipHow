"""Strict, dependency-free schema checks for the optional live suite."""

from __future__ import annotations

from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


class Status(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    UNVERIFIED = "UNVERIFIED"


# A lower number wins. A failed assertion must never disappear behind a later pass.
STATUS_PRECEDENCE = {
    Status.FAILED: 0,
    Status.BLOCKED: 1,
    Status.UNVERIFIED: 2,
    Status.PASSED: 3,
}

SUPPORTED_COLLECTORS = frozenset(
    {"tree_delta", "structured_file", "host_event", "git_state", "github_state", "provider_usage"}
)
APPROVED_SCENARIOS = frozenset(
    {
        "small-fix",
        "unknown-bug-reproducer",
        "reuse-feature",
        "mixed-intake",
        "nontechnical-owner",
        "independent-finding",
        "multi-issue-github-delivery",
        "restart-resume-external-state",
        "protected-action",
        "adaptive-vs-all-deep",
        "technical-review",
        "merge-conflict",
    }
)


def aggregate_status(values: list[Status | str]) -> Status:
    """Return the least favorable status under the published precedence rule."""
    if not values:
        return Status.UNVERIFIED
    parsed = [value if isinstance(value, Status) else Status(value) for value in values]
    return min(parsed, key=STATUS_PRECEDENCE.__getitem__)


def _relative_file(value: object, field: str, errors: list[str], scenario: str) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{scenario}: {field} must name a file")
        return
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{scenario}: {field} must stay inside evals/live")


def validate_suite(data: Mapping[str, Any]) -> list[str]:
    """Validate only the small manifest language understood by this runner."""
    errors: list[str] = []
    if data.get("suite_version") != 1:
        errors.append("suite_version must be 1")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        return [*errors, "scenarios must be a list"]
    seen: set[str] = set()
    for item in scenarios:
        if not isinstance(item, dict):
            errors.append("each scenario must be an object")
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append("scenario id must be a nonempty string")
            continue
        if identifier in seen:
            errors.append(f"duplicate scenario id: {identifier}")
        seen.add(identifier)
        if item.get("host") not in {"codex", "claude", "either"}:
            errors.append(f"{identifier}: host must be codex, claude, or either")
        if item.get("execution") not in {"single", "restart", "paired", "github"}:
            errors.append(f"{identifier}: unsupported execution shape")
        if not isinstance(item.get("explicit_skill"), bool):
            errors.append(f"{identifier}: explicit_skill must be a boolean")
        for field in ("prompt", "fixture", "oracle"):
            _relative_file(item.get(field), field, errors, identifier)
        if item.get("execution") == "restart":
            _relative_file(item.get("resume_prompt"), "resume_prompt", errors, identifier)
            _relative_file(item.get("checkpoint_oracle"), "checkpoint_oracle", errors, identifier)
        collectors = item.get("collectors")
        if not isinstance(collectors, list) or not collectors:
            errors.append(f"{identifier}: collectors must be a nonempty list")
        elif any(not isinstance(name, str) or name not in SUPPORTED_COLLECTORS for name in collectors):
            errors.append(f"{identifier}: unsupported collector")
    missing = APPROVED_SCENARIOS - seen
    extra = seen - APPROVED_SCENARIOS
    if missing:
        errors.append("missing approved scenarios: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unapproved scenarios: " + ", ".join(sorted(extra)))
    return errors


def load_suite(path: Path) -> dict[str, Any]:
    """Read a suite after validating both JSON syntax and its compact contract."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read suite: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("suite root must be an object")
    errors = validate_suite(data)
    base = path.parent
    if not errors:
        for scenario in data["scenarios"]:
            identifier = scenario["id"]
            resource_fields = ["prompt", "fixture", "oracle"]
            if scenario.get("execution") == "restart":
                resource_fields.extend(["resume_prompt", "checkpoint_oracle"])
            for field in resource_fields:
                resource = base / scenario[field]
                try:
                    inside = resource.resolve().is_relative_to(base.resolve())
                except OSError:
                    inside = False
                if not inside or not resource.exists():
                    errors.append(f"{identifier}: missing {field}")
            if not (base / scenario["prompt"]).is_file() or not (base / scenario["oracle"]).is_file():
                errors.append(f"{identifier}: prompt and oracle must be files")
            if scenario.get("execution") == "restart" and not (base / scenario["resume_prompt"]).is_file():
                errors.append(f"{identifier}: resume prompt must be a file")
            if not (base / scenario["fixture"]).is_dir():
                errors.append(f"{identifier}: fixture must be a directory")
            fixture = base / scenario["fixture"]
            if fixture.is_dir() and any(item.name == ".git" or item.is_symlink() for item in fixture.rglob("*")):
                errors.append(f"{identifier}: fixture must not contain .git or symlinks")
            oracle = base / scenario["oracle"]
            try:
                assertions = json.loads(oracle.read_text(encoding="utf-8"))["assertions"]
            except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
                errors.append(f"{identifier}: invalid oracle: {exc}")
                continue
            if not isinstance(assertions, list):
                errors.append(f"{identifier}: oracle assertions must be a list")
                continue
            oracle_collectors: set[str] = set()
            for assertion in assertions:
                if not isinstance(assertion, dict) or assertion.get("collector") not in SUPPORTED_COLLECTORS:
                    errors.append(f"{identifier}: oracle uses an unsupported collector")
                    continue
                collector = assertion["collector"]
                oracle_collectors.add(collector)
                if "required" in assertion and not isinstance(assertion["required"], bool):
                    errors.append(f"{identifier}: assertion required must be a boolean")
                if collector == "tree_delta":
                    positive = assertion.get("unchanged") is True or any(
                        assertion.get(field)
                        for field in ("required_added", "required_removed", "required_modified")
                    )
                    if not positive:
                        errors.append(f"{identifier}: tree_delta needs unchanged or a required delta")
                    if not all(field in assertion for field in ("allowed_added", "allowed_removed", "allowed_modified")) and not assertion.get("unchanged"):
                        errors.append(f"{identifier}: mutable tree_delta needs exact allowed sets")
                    for relative in assertion.get("expected_text", {}):
                        _relative_file(relative, "expected text path", errors, identifier)
                if collector == "structured_file":
                    _relative_file(assertion.get("path"), "assertion path", errors, identifier)
                    if assertion.get("kind") not in {"json", "append_only_inbox", "append_only_handoff"}:
                        errors.append(f"{identifier}: unsupported structured file grammar")
                    if "expected_added_records" in assertion and not all(
                        isinstance(item, dict) for item in assertion["expected_added_records"]
                    ):
                        errors.append(f"{identifier}: expected_added_records must contain objects")
                    for relationship in assertion.get("relationships", []):
                        if not isinstance(relationship, dict) or not isinstance(relationship.get("source"), dict) or not isinstance(relationship.get("target"), dict):
                            errors.append(f"{identifier}: relationships need source and target objects")
                if collector == "github_state":
                    _relative_file(assertion.get("snapshot", "github-state.json"), "snapshot", errors, identifier)
            if oracle_collectors != set(scenario["collectors"]):
                errors.append(f"{identifier}: manifest collectors must match oracle collectors")
    if errors:
        raise ValueError("invalid suite: " + "; ".join(errors))
    return data
