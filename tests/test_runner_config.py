"""Schema-parity tests for the optional runner configuration reader."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "skiphow_runner_config_test", ROOT / "src/skiphow/config.py"
)
assert SPEC and SPEC.loader
config = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = config
SPEC.loader.exec_module(config)


def write_config(root: Path, value: object) -> None:
    path = root / ".skiphow" / "config.json"
    path.parent.mkdir()
    path.write_text(json.dumps(value), encoding="utf-8")


def test_v2_accepts_schema_fields_and_defaults(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        {
            "schema_version": 2,
            "tracker": {"type": "github", "project": "owner-/12"},
            "delivery": {
                "merge_policy": "when_green_and_approved",
                "cleanup": "never",
            },
            "findings": {"persist": "tracker"},
            "campaign_root": ".skiphow/campaigns",
        },
    )
    assert config.load_project_config(tmp_path) == config.ProjectConfig(
        tracker="github",
        project="owner-/12",
        merge_policy="when_green_and_approved",
        cleanup="never",
        findings_persist="tracker",
        campaign_root=".skiphow/campaigns",
    )


@pytest.mark.parametrize(
    "value, field",
    (
        ({"schema_version": 2, "unknown": True}, "project configuration"),
        ({"schema_version": 2, "tracker": {"type": "auto", "extra": 1}}, "tracker"),
        ({"schema_version": 2, "delivery": {"extra": 1}}, "delivery"),
        ({"schema_version": 2, "findings": {"extra": 1}}, "findings"),
    ),
)
def test_v2_rejects_unknown_fields(
    tmp_path: Path, value: dict[str, object], field: str
) -> None:
    write_config(tmp_path, value)
    with pytest.raises(config.ConfigError, match=f"unknown {field} field"):
        config.load_project_config(tmp_path)


@pytest.mark.parametrize(
    "project",
    ("owner/0", "owner/01", "owner_name/1", "/1", "owner/", 12, True),
)
def test_tracker_project_matches_schema_pattern(
    tmp_path: Path, project: object
) -> None:
    write_config(
        tmp_path,
        {"schema_version": 2, "tracker": {"type": "github", "project": project}},
    )
    with pytest.raises(config.ConfigError, match="tracker.project"):
        config.load_project_config(tmp_path)


@pytest.mark.parametrize("field", ("tracker", "delivery", "findings"))
def test_v2_nested_sections_must_be_objects(tmp_path: Path, field: str) -> None:
    write_config(tmp_path, {"schema_version": 2, field: None})
    with pytest.raises(config.ConfigError, match=f"{field} must be a JSON object"):
        config.load_project_config(tmp_path)


def test_v1_read_behavior_is_preserved(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        {
            "tracker": "github",
            "project": "owner/7",
            "campaign_root": ".skiphow/legacy-runs",
        },
    )
    assert config.load_project_config(tmp_path) == config.ProjectConfig(
        tracker="github",
        project="owner/7",
        campaign_root=".skiphow/legacy-runs",
    )


@pytest.mark.parametrize("campaign_root", (None, 1, False, ""))
def test_campaign_root_matches_schema_string_contract(
    tmp_path: Path, campaign_root: object
) -> None:
    write_config(
        tmp_path, {"schema_version": 2, "campaign_root": campaign_root}
    )
    with pytest.raises(config.ConfigError, match="campaign_root"):
        config.load_project_config(tmp_path)
