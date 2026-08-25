"""Runtime configuration readers for the optional runner."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any


PROJECT_KEYS = frozenset(
    {"schema_version", "tracker", "delivery", "findings", "campaign_root"}
)
V1_KEYS = frozenset({"tracker", "project", "campaign_root"})
TRACKER_KEYS = frozenset({"type", "project"})
DELIVERY_KEYS = frozenset({"merge_policy", "cleanup"})
FINDINGS_KEYS = frozenset({"persist"})
PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[1-9][0-9]*$")


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    tracker: str = "auto"
    project: str | None = None
    merge_policy: str = "never"
    cleanup: str = "merged_only"
    findings_persist: str = "local"
    campaign_root: str = ".skiphow/runs"

    def run_root(self, root: Path) -> Path:
        if not isinstance(self.campaign_root, str) or not self.campaign_root:
            raise ConfigError("campaign_root must be a non-empty string")
        relative = PurePosixPath(self.campaign_root)
        windows = PureWindowsPath(self.campaign_root)
        if (
            not self.campaign_root
            or "\\" in self.campaign_root
            or relative.is_absolute()
            or windows.is_absolute()
            or windows.drive
            or ".." in relative.parts
            or str(relative) in {"", "."}
        ):
            raise ConfigError("campaign_root must be a relative directory inside the project")
        project = root.resolve()
        candidate = (project / relative).resolve()
        try:
            candidate.relative_to(project)
        except ValueError as exc:
            raise ConfigError("campaign_root escapes the project") from exc
        return candidate


@dataclass(frozen=True, slots=True)
class PersonalConfig:
    execution_preference: str = "auto"
    cost_preference: str = "balanced"
    max_cost_per_run: float | None = None
    max_duration: int | None = None
    max_parallelism: int | str = "auto"
    providers: dict[str, dict[str, Any]] = field(default_factory=dict)


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{path} must contain a JSON object")
    return value


def _object(value: Any, field: str, allowed: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field} must be a JSON object")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ConfigError(f"unknown {field} field(s): {', '.join(unknown)}")
    return value


def _project(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or PROJECT_RE.fullmatch(value) is None:
        raise ConfigError("tracker.project must be null or an owner/number value")
    return value


def load_project_config(root: str | Path = ".") -> ProjectConfig:
    project_root = Path(root)
    path = project_root / ".skiphow" / "config.json"
    if not path.is_file():
        return ProjectConfig()
    value = _read(path)
    if value.get("schema_version") == 2:
        _object(value, "project configuration", PROJECT_KEYS)
        tracker = _object(value.get("tracker", {}), "tracker", TRACKER_KEYS)
        delivery = _object(value.get("delivery", {}), "delivery", DELIVERY_KEYS)
        findings = _object(value.get("findings", {}), "findings", FINDINGS_KEYS)
        config = ProjectConfig(
            tracker=tracker.get("type", "auto"),
            project=_project(tracker.get("project")),
            merge_policy=delivery.get("merge_policy", "never"),
            cleanup=delivery.get("cleanup", "merged_only"),
            findings_persist=findings.get("persist", "local"),
            campaign_root=value.get("campaign_root", ".skiphow/runs"),
        )
    elif set(value) <= V1_KEYS:
        config = ProjectConfig(
            tracker=value.get("tracker", "auto"),
            project=_project(value.get("project")),
            campaign_root=value.get("campaign_root", ".skiphow/runs"),
        )
    else:
        raise ConfigError("unsupported project configuration schema")
    if config.tracker not in {"auto", "none", "github", "local"}:
        raise ConfigError("invalid tracker type")
    if config.merge_policy not in {
        "never", "when_green", "when_green_and_approved", "auto_merge_or_queue"
    }:
        raise ConfigError("invalid merge policy")
    if config.cleanup not in {"merged_only", "never"}:
        raise ConfigError("invalid cleanup policy")
    if config.findings_persist not in {"local", "tracker", "ask", "off"}:
        raise ConfigError("invalid finding persistence policy")
    config.run_root(project_root)
    return config


def load_personal_config(path: str | Path | None = None) -> PersonalConfig:
    if path is None:
        base = Path(os.environ.get("SKIPHOW_CONFIG_HOME", Path.home() / ".config" / "skiphow"))
        candidate = base / "config.json"
    else:
        candidate = Path(path)
    if not candidate.is_file():
        return PersonalConfig()
    value = _read(candidate)
    allowed = {
        "execution_preference", "cost_preference", "max_cost_per_run",
        "max_duration", "max_parallelism", "providers",
    }
    if set(value) - allowed:
        raise ConfigError("unknown personal configuration fields")
    config = PersonalConfig(**value)
    if config.cost_preference not in {"auto", "economy", "balanced", "quality"}:
        raise ConfigError("invalid cost preference")
    if config.execution_preference not in {"auto", "direct", "durable"}:
        raise ConfigError("invalid execution preference")
    if config.max_cost_per_run is not None and (
        not isinstance(config.max_cost_per_run, (int, float))
        or isinstance(config.max_cost_per_run, bool)
        or config.max_cost_per_run < 0
    ):
        raise ConfigError("max_cost_per_run must be null or non-negative")
    if config.max_duration is not None and (
        not isinstance(config.max_duration, int)
        or isinstance(config.max_duration, bool)
        or config.max_duration <= 0
    ):
        raise ConfigError("max_duration must be null or a positive integer")
    if config.max_parallelism != "auto" and (
        not isinstance(config.max_parallelism, int)
        or isinstance(config.max_parallelism, bool)
        or config.max_parallelism <= 0
    ):
        raise ConfigError("max_parallelism must be auto or a positive integer")
    if not isinstance(config.providers, dict):
        raise ConfigError("providers must be an object")
    return config
