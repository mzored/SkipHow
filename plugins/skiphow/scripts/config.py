#!/usr/bin/env python3
"""Strict, dependency-free configuration for optional SkipHow helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


CONFIG_PATH = Path(".skiphow/config.json")
TRACKERS = frozenset({"auto", "none", "github", "local"})
KEYS = frozenset({"tracker", "project", "campaign_root"})
PROJECT_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/([1-9][0-9]*)$")


class ConfigError(ValueError):
    """The optional SkipHow configuration is invalid."""


@dataclass(frozen=True)
class Config:
    tracker: str = "auto"
    project: str | None = None
    campaign_root: str = ".skiphow/runs"

    def campaign_path(self, project_root: str | Path = ".") -> Path:
        root = Path(project_root).resolve()
        candidate = (root / self.campaign_root).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ConfigError("campaign_root must stay inside the project") from exc
        return candidate


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


def parse_config(value: Any) -> Config:
    if not isinstance(value, dict):
        raise ConfigError("configuration must be a JSON object")
    unknown = sorted(set(value) - KEYS)
    if unknown:
        raise ConfigError(f"unknown configuration key(s): {', '.join(unknown)}")

    tracker = value.get("tracker", "auto")
    if not isinstance(tracker, str) or tracker not in TRACKERS:
        allowed = ", ".join(sorted(TRACKERS))
        raise ConfigError(f"tracker must be one of: {allowed}")
    return Config(
        tracker=tracker,
        project=_project(value.get("project")),
        campaign_root=_campaign_root(value.get("campaign_root", ".skiphow/runs")),
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
