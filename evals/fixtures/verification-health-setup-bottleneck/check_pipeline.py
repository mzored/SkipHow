"""Offline oracle for the measured setup-bottleneck fixture."""

from __future__ import annotations

import json
from pathlib import Path

from coverage_checks import run_coverage
from pipeline import recurring_setup_seconds

ROOT = Path(__file__).resolve().parent


def main() -> int:
    timings = json.loads((ROOT / "ci-timings.json").read_text(encoding="utf-8"))
    plan = json.loads((ROOT / "pipeline-plan.json").read_text(encoding="utf-8"))
    measured = timings["measured_seconds"]
    setup_cost = sum(
        measured[name]
        for name in ("dependency_installation", "test_data_preparation", "service_startup")
    )
    assert setup_cost > measured["browser_execution"]
    optimized_setup_cost = recurring_setup_seconds(measured, plan)
    assert optimized_setup_cost < setup_cost
    assert plan["reuse_prepared_environment"] is True
    assert plan["reuse_started_services"] is True
    assert plan["reuse_test_data"] is True
    assert plan["browser_check_count"] == timings["browser_check_count"]
    assert plan["delivery_coverage"] == timings["delivery_contract"]
    assert run_coverage() == {
        "browser checks passed": timings["browser_check_count"],
        "contract checks passed": 2,
    }
    print("PASS: measured setup path optimized and 148 useful checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
