"""Tests for the public skill's fixed instruction budget."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "skiphow_context_budget", ROOT / "scripts/context_budget.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


budget = load_module()


def test_budget_has_one_static_limit_for_the_root_skill() -> None:
    baseline = json.loads(budget.BASELINE.read_text(encoding="utf-8"))
    assert baseline == {
        "schema_version": 1,
        "root_skill_limits": {"bytes": 6000, "words": 700},
    }
    assert budget.ROOT_SKILL_LIMITS == {"bytes": 6000, "words": 700}


def test_report_measures_only_the_canonical_skill() -> None:
    report = budget.collect_report()
    assert report["root_skill"] == "plugins/skiphow/skills/skiphow/SKILL.md"
    assert report["measured"] == budget.metrics(
        budget.SKILL.read_text(encoding="utf-8")
    )
    assert set(report) == {"schema_version", "root_skill", "measured", "limits"}


def test_exceeded_limits_report_measured_and_allowed_values() -> None:
    report = {
        "measured": {"bytes": 6001, "words": 701},
        "limits": {"bytes": 6000, "words": 700},
    }
    errors = budget.budget_errors(report)
    assert any("6001 > 6000" in error for error in errors)
    assert any("701 > 700" in error for error in errors)


def test_invalid_budget_is_rejected(tmp_path: Path) -> None:
    baseline = tmp_path / "budget.json"
    baseline.write_text(
        json.dumps({"schema_version": 1, "root_skill_limits": {"bytes": 0, "words": 700}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="positive integers"):
        budget.load_limits(baseline)


def test_check_mode_never_writes_the_skill_or_budget() -> None:
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (budget.SKILL, budget.BASELINE)
    }
    assert budget.main(["--check"]) == 0
    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (budget.SKILL, budget.BASELINE)
    }
    assert after == before


def test_check_mode_fails_without_updating_the_limit(monkeypatch, capsys) -> None:
    report = {
        "schema_version": 1,
        "root_skill": "plugins/skiphow/skills/skiphow/SKILL.md",
        "measured": {"bytes": 6001, "words": 701},
        "limits": {"bytes": 6000, "words": 700},
    }
    before = budget.BASELINE.read_bytes()
    monkeypatch.setattr(budget, "collect_report", lambda: report)
    assert budget.main(["--check"]) == 1
    assert budget.BASELINE.read_bytes() == before
    error = capsys.readouterr().err
    assert "6001 > 6000" in error
    assert "701 > 700" in error
