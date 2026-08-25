"""Tests for runtime context measurement and its decreasing limits."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


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


def report_with(count: int, references: list[dict[str, str]] | None = None) -> dict:
    return {
        "routes": {
            route: {"bytes": count, "words": count, "files": list(files)}
            for route, files in budget.ROUTES.items()
        },
        "runtime_references": {"discovered": references or [], "route_edges": {}},
    }


def baseline_with(count: int) -> dict:
    return {
        "schema_version": 2,
        "v0_6_reference": budget.V06_REFERENCE,
        "targets": budget.TARGETS,
        "routes": {
            route: {"bytes": count, "words": count} for route in budget.ROUTES
        },
        "runtime_references": [],
        "increase_explanations": [],
    }


def test_v06_reference_and_closure_separator_are_stable() -> None:
    assert budget.metrics("one two\nthree") == {"bytes": 13, "words": 3}
    assert budget.metrics("a\n".join(["one", "two"])) == {"bytes": 8, "words": 2}
    assert budget.V06_REFERENCE["diagnosis"] == {"bytes": 32402, "words": 4654}
    assert budget.V06_REFERENCE["codebase_design"] == {"bytes": 28931, "words": 3896}


def test_runtime_routes_exclude_source_only_files_and_forbid_upstream_loads() -> None:
    report, errors = budget.collect_report()
    assert errors == []
    for route in report["routes"].values():
        assert all("/upstream/" not in f"/{path}" for path in route["files"])
    source_files = {
        path for path, item in report["files"].items() if item["kind"] == "source_only"
    }
    assert "references/engineering/diagnose/upstream/SKILL.md" in source_files
    assert "references/capabilities/testing/upstream/tests.md" in source_files


def test_route_closures_follow_validated_runtime_edges() -> None:
    assert budget.ROUTES["clear"] == budget.ROUTES["common"]
    assert "references/engineering/develop/SKILL.md" not in budget.ROUTES["clear"]
    assert (
        "SKILL.md",
        "references/engineering/cto/SKILL.md",
    ) in budget.ROUTE_EDGES["clear"]
    report, errors = budget.collect_report()
    assert errors == []
    discovered = {
        (item["source"], item["target"])
        for item in report["runtime_references"]["discovered"]
    }
    for edges in budget.ROUTE_EDGES.values():
        assert set(edges).issubset(discovered)


def test_source_manifest_covers_every_vendored_group() -> None:
    manifest = json.loads(budget.SOURCE_MANIFEST.read_text(encoding="utf-8"))
    declared = {
        (budget.SKILL_ROOT / item["vendored_at"]).resolve()
        for item in manifest["sources"]
    }
    actual = {
        path.resolve() for path in budget.SKILL_ROOT.rglob("upstream") if path.is_dir()
    }
    assert declared == actual
    for item in manifest["sources"]:
        assert item["provenance"] == "exact_pinned_copy"
        assert (budget.SKILL_ROOT / item["adaptation_path"]).is_file()
        assert item["source_repository"].startswith("https://")
        assert len(item["pinned_commit"]) == 40
        assert item["files"]
        assert all(len(file["sha256"]) == 64 for file in item["files"])
        assert item["license"] == "MIT"
        assert item["last_reviewed"]
    assert budget.validate_source_manifest() == []


def test_update_lowers_limits_and_refuses_an_unexplained_increase(
    tmp_path: Path, monkeypatch
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(baseline_with(100)), encoding="utf-8")
    monkeypatch.setattr(budget, "BASELINE", baseline)

    assert budget.update_baseline(report_with(90), accept_increase=False, reason=None) == []
    lowered = json.loads(baseline.read_text(encoding="utf-8"))
    assert all(item == {"bytes": 90, "words": 90} for item in lowered["routes"].values())

    errors = budget.update_baseline(report_with(91), accept_increase=False, reason=None)
    assert any("refusing to raise" in error for error in errors)
    assert json.loads(baseline.read_text(encoding="utf-8")) == lowered


def test_accepted_increase_records_a_specific_explanation(
    tmp_path: Path, monkeypatch
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(baseline_with(80)), encoding="utf-8")
    monkeypatch.setattr(budget, "BASELINE", baseline)

    assert budget.update_baseline(
        report_with(81), accept_increase=True, reason="new runtime safety rule"
    ) == []
    updated = json.loads(baseline.read_text(encoding="utf-8"))
    explanation = updated["increase_explanations"][0]
    assert explanation == {
        "route": "router",
        "unit": "bytes",
        "from": 80,
        "to": 81,
        "reason": "new runtime safety rule",
    }


def test_check_automatically_lowers_baseline_and_leaves_a_file_diff(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(baseline_with(51)), encoding="utf-8")
    monkeypatch.setattr(budget, "BASELINE", baseline)
    monkeypatch.setattr(budget, "collect_report", lambda: (report_with(50), []))

    assert budget.main(["--check"]) == 0
    lowered = json.loads(baseline.read_text(encoding="utf-8"))
    assert all(item == {"bytes": 50, "words": 50} for item in lowered["routes"].values())
    assert "lowered" in capsys.readouterr().out


def test_automatic_lower_preserves_a_matching_base_increase_explanation(
    tmp_path: Path, monkeypatch
) -> None:
    baseline = tmp_path / "baseline.json"
    previous = baseline_with(120)
    previous["increase_explanations"] = [
        {
            "route": "clear",
            "unit": "bytes",
            "from": 100,
            "to": 120,
            "reason": "required safety instruction",
        }
    ]
    baseline.write_text(json.dumps(previous), encoding="utf-8")
    monkeypatch.setattr(budget, "BASELINE", baseline)

    assert budget.update_baseline(report_with(110), accept_increase=False, reason=None) == []
    updated = json.loads(baseline.read_text(encoding="utf-8"))
    assert updated["increase_explanations"] == [
        {
            "route": "clear",
            "unit": "bytes",
            "from": 100,
            "to": 110,
            "reason": "required safety instruction",
        }
    ]


def test_new_runtime_reference_needs_an_explained_update(
    tmp_path: Path, monkeypatch
) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(baseline_with(50)), encoding="utf-8")
    monkeypatch.setattr(budget, "BASELINE", baseline)
    reference = [{"source": "SKILL.md", "target": "references/new/SKILL.md"}]
    report = report_with(50, reference)

    errors = budget.update_baseline(report, accept_increase=False, reason=None)
    assert any("actionable runtime references" in error for error in errors)
    assert budget.update_baseline(
        report, accept_increase=True, reason="load new required policy"
    ) == []
    updated = json.loads(baseline.read_text(encoding="utf-8"))
    assert updated["runtime_references"] == reference
    assert updated["increase_explanations"][-1]["route"] == "runtime_references"


def test_upstream_lint_covers_action_synonyms_and_indirect_phrasing() -> None:
    examples = (
        "Read `upstream/SKILL.md` before work",
        "Use `upstream/SKILL.md` for the method",
        "See `upstream/SOURCE.md` and apply its rules",
        "The instructions in `upstream/SKILL.md` govern this capability",
    )
    assert all(budget.UPSTREAM_REFERENCE.search(text) for text in examples)
