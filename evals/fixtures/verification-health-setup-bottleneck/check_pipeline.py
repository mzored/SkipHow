"""Offline oracle for the measured setup-bottleneck fixture."""

from __future__ import annotations

import json
from pathlib import Path

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
    assert plan["reuse_prepared_environment"] is True
    assert plan["reuse_started_services"] is True
    assert plan["browser_check_count"] == timings["browser_check_count"]
    assert plan["delivery_coverage"] == timings["delivery_contract"]
    print("PASS: measured setup path optimized and useful coverage preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
