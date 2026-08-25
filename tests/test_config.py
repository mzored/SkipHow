"""Tests for the canonical optional configuration."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/skiphow/scripts/config.py"
SPEC = importlib.util.spec_from_file_location("skiphow_config_test", SCRIPT)
assert SPEC and SPEC.loader
config = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = config
SPEC.loader.exec_module(config)


def write_config(root: Path, value: object) -> None:
    path = root / ".skiphow" / "config.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_missing_config_is_zero_config() -> None:
    assert config.load_config("/path/that/does/not/exist") == config.Config()


def test_canonical_config_accepts_only_implemented_fields(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        {
            "tracker": "github",
            "project": "owner/12",
            "campaign_root": ".skiphow/campaigns",
        },
    )
    assert config.load_config(tmp_path) == config.Config(
        tracker="github", project="owner/12", campaign_root=".skiphow/campaigns"
    )

    write_config(tmp_path, {"strict_lifecycle": True})
    with pytest.raises(config.ConfigError, match="unknown configuration key"):
        config.load_config(tmp_path)


def test_v2_project_config_and_reversible_v1_migration(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        {
            "schema_version": 2,
            "tracker": {"type": "local", "project": None},
            "delivery": {"merge_policy": "when_green", "cleanup": "merged_only"},
            "findings": {"persist": "ask"},
            "campaign_root": ".skiphow/runs",
        },
    )
    loaded = config.load_config(tmp_path)
    assert loaded.tracker == "local"
    assert loaded.merge_policy == "when_green"
    assert loaded.findings_persist == "ask"

    write_config(tmp_path, {"tracker": "github", "project": "owner/12"})
    backup = config.migrate_config(tmp_path)
    assert backup and backup.read_text(encoding="utf-8")
    migrated = json.loads((tmp_path / ".skiphow/config.json").read_text())
    assert migrated["schema_version"] == 2
    assert migrated["tracker"] == {"type": "github", "project": "owner/12"}
    assert config.migrate_config(tmp_path) is None


def test_personal_config_keeps_provider_details_out_of_project(tmp_path: Path) -> None:
    path = tmp_path / "personal.json"
    path.write_text(
        json.dumps(
            {
                "execution_preference": "auto",
                "cost_preference": "quality",
                "max_cost_per_run": 12.5,
                "max_duration": 3600,
                "max_parallelism": 3,
                "providers": {"example": {"models": ["configured-locally"]}},
            }
        ),
        encoding="utf-8",
    )
    loaded = config.load_personal_config(path)
    assert loaded.cost_preference == "quality"
    assert loaded.providers == {"example": {"models": ["configured-locally"]}}


@pytest.mark.parametrize(
    "campaign_root",
    ("../outside", "/tmp/runs", "C:\\runs", "nested/../../outside", "."),
)
def test_campaign_root_must_stay_inside_project(
    tmp_path: Path, campaign_root: str
) -> None:
    write_config(tmp_path, {"campaign_root": campaign_root})
    with pytest.raises(config.ConfigError, match="campaign_root"):
        config.load_config(tmp_path)


def test_invalid_tracker_project_and_json_are_clear(tmp_path: Path) -> None:
    write_config(tmp_path, {"tracker": "jira"})
    with pytest.raises(config.ConfigError, match="tracker must be one of"):
        config.load_config(tmp_path)

    write_config(tmp_path, {"project": "auto"})
    with pytest.raises(config.ConfigError, match="owner/number"):
        config.load_config(tmp_path)

    path = tmp_path / ".skiphow" / "config.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(config.ConfigError, match="cannot read"):
        config.load_config(tmp_path)


def test_duplicate_keys_and_symlink_escape_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / ".skiphow" / "config.json"
    path.parent.mkdir()
    path.write_text('{"tracker":"auto","tracker":"none"}', encoding="utf-8")
    with pytest.raises(config.ConfigError, match="duplicate configuration key"):
        config.load_config(tmp_path)

    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    path.write_text('{"campaign_root":"linked/runs"}', encoding="utf-8")
    with pytest.raises(config.ConfigError, match="stay inside"):
        config.load_config(tmp_path)
