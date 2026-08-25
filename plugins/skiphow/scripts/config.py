#!/usr/bin/env python3
"""Strict, dependency-free project and personal configuration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


CONFIG_PATH = Path(".skiphow/config.json")
TRACKERS = frozenset({"auto", "none", "github", "local"})
PROJECT_KEYS = frozenset(
    {"schema_version", "tracker", "delivery", "findings", "campaign_root"}
)
V1_KEYS = frozenset({"tracker", "project", "campaign_root"})
MERGE_POLICIES = frozenset(
    {"never", "when_green", "when_green_and_approved", "auto_merge_or_queue"}
)
CLEANUP_POLICIES = frozenset({"merged_only", "never"})
FINDING_POLICIES = frozenset({"local", "tracker", "ask", "off"})
COST_PREFERENCES = frozenset({"auto", "economy", "balanced", "quality"})
PROJECT_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/([1-9][0-9]*)$")


class ConfigError(ValueError):
    """The optional SkipHow configuration is invalid."""


@dataclass(frozen=True)
class Config:
    schema_version: int = 2
    tracker: str = "auto"
    project: str | None = None
    campaign_root: str = ".skiphow/runs"
    merge_policy: str = "never"
    cleanup: str = "merged_only"
    findings_persist: str = "local"

    def campaign_path(self, project_root: str | Path = ".") -> Path:
        root = Path(project_root).resolve()
        candidate = (root / self.campaign_root).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ConfigError("campaign_root must stay inside the project") from exc
        return candidate

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "tracker": {"type": self.tracker, "project": self.project},
            "delivery": {
                "merge_policy": self.merge_policy,
                "cleanup": self.cleanup,
            },
            "findings": {"persist": self.findings_persist},
            "campaign_root": self.campaign_root,
        }


@dataclass(frozen=True)
class PersonalConfig:
    execution_preference: str = "auto"
    cost_preference: str = "balanced"
    max_cost_per_run: float | None = None
    max_duration: int | None = None
    max_parallelism: int | str = "auto"
    providers: dict[str, dict[str, Any]] | None = None


def _project(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError("project must be null or an explicit owner/number string")
    if not PROJECT_RE.fullmatch(value):
        raise ConfigError("project must be null or an explicit owner/number string")
    return value


def _campaign_root(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError("campaign_root must be a non-empty relative path")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        "\0" in value
        or "\\" in value
        or posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or ".." in posix.parts
    ):
        raise ConfigError("campaign_root must be a relative path inside the project")
    if str(posix) in {"", "."}:
        raise ConfigError("campaign_root must name a directory inside the project")
    return value


def _enum(value: Any, allowed: frozenset[str], field: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ConfigError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return value


def _object(value: Any, field: str, keys: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field} must be a JSON object")
    unknown = sorted(set(value) - keys)
    if unknown:
        raise ConfigError(f"unknown {field} key(s): {', '.join(unknown)}")
    return value


def parse_config(value: Any) -> Config:
    if not isinstance(value, dict):
        raise ConfigError("configuration must be a JSON object")
    is_v1 = "schema_version" not in value and set(value) <= V1_KEYS
    allowed = V1_KEYS if is_v1 else PROJECT_KEYS
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ConfigError(f"unknown configuration key(s): {', '.join(unknown)}")
    if is_v1:
        tracker = _enum(value.get("tracker", "auto"), TRACKERS, "tracker")
        project = _project(value.get("project"))
        delivery: dict[str, Any] = {}
        findings: dict[str, Any] = {}
    else:
        if value.get("schema_version") != 2:
            raise ConfigError("schema_version must be 2")
        tracker_value = _object(
            value.get("tracker", {}), "tracker", frozenset({"type", "project"})
        )
        tracker = _enum(tracker_value.get("type", "auto"), TRACKERS, "tracker.type")
        project = _project(tracker_value.get("project"))
        delivery = _object(
            value.get("delivery", {}),
            "delivery",
            frozenset({"merge_policy", "cleanup"}),
        )
        findings = _object(
            value.get("findings", {}), "findings", frozenset({"persist"})
        )
    return Config(
        tracker=tracker,
        project=project,
        campaign_root=_campaign_root(value.get("campaign_root", ".skiphow/runs")),
        merge_policy=_enum(
            delivery.get("merge_policy", "never"), MERGE_POLICIES, "delivery.merge_policy"
        ),
        cleanup=_enum(
            delivery.get("cleanup", "merged_only"), CLEANUP_POLICIES, "delivery.cleanup"
        ),
        findings_persist=_enum(
            findings.get("persist", "local"), FINDING_POLICIES, "findings.persist"
        ),
    )


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ConfigError(f"duplicate configuration key: {key}")
        value[key] = item
    return value


def load_config(project_root: str | Path = ".") -> Config:
    path = Path(project_root) / CONFIG_PATH
    if not path.is_file():
        return Config()
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ConfigError(f"invalid JSON constant: {constant}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read {CONFIG_PATH}: {exc}") from exc
    config = parse_config(value)
    config.campaign_path(project_root)
    return config


def migrate_config(project_root: str | Path = ".") -> Path | None:
    """Rewrite a v1 project config as v2 and retain one adjacent backup."""
    path = Path(project_root) / CONFIG_PATH
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    value = json.loads(raw, object_pairs_hook=_strict_object)
    config = parse_config(value)
    if isinstance(value, dict) and value.get("schema_version") == 2:
        return None
    backup = path.with_suffix(".json.v1.bak")
    if not backup.exists():
        backup.write_text(raw, encoding="utf-8")
    path.write_text(json.dumps(config.as_dict(), indent=2) + "\n", encoding="utf-8")
    return backup


def personal_config_path() -> Path:
    configured = os.environ.get("SKIPHOW_CONFIG_HOME")
    base = Path(configured) if configured else Path.home() / ".config" / "skiphow"
    return base / "config.json"


def parse_personal_config(value: Any) -> PersonalConfig:
    keys = frozenset(
        {
            "execution_preference",
            "cost_preference",
            "max_cost_per_run",
            "max_duration",
            "max_parallelism",
            "providers",
        }
    )
    item = _object(value, "personal configuration", keys)
    execution = _enum(
        item.get("execution_preference", "auto"),
        frozenset({"auto", "direct", "durable"}),
        "execution_preference",
    )
    cost = _enum(item.get("cost_preference", "balanced"), COST_PREFERENCES, "cost_preference")
    maximum = item.get("max_cost_per_run")
    if maximum is not None and (
        not isinstance(maximum, (int, float)) or isinstance(maximum, bool) or maximum < 0
    ):
        raise ConfigError("max_cost_per_run must be null or a non-negative number")
    duration = item.get("max_duration")
    if duration is not None and (
        not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0
    ):
        raise ConfigError("max_duration must be null or a positive number of seconds")
    parallelism = item.get("max_parallelism", "auto")
    if parallelism != "auto" and (
        not isinstance(parallelism, int) or isinstance(parallelism, bool) or parallelism <= 0
    ):
        raise ConfigError("max_parallelism must be auto or a positive integer")
    providers = item.get("providers", {})
    if not isinstance(providers, dict) or not all(
        isinstance(name, str) and isinstance(settings, dict)
        for name, settings in providers.items()
    ):
        raise ConfigError("providers must map provider names to JSON objects")
    return PersonalConfig(execution, cost, maximum, duration, parallelism, providers)


def load_personal_config(path: str | Path | None = None) -> PersonalConfig:
    candidate = Path(path) if path is not None else personal_config_path()
    if not candidate.is_file():
        return PersonalConfig(providers={})
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read personal configuration: {exc}") from exc
    return parse_personal_config(value)
