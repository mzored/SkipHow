"""Offline oracle that preserves the unique cross-boundary failure signal."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from system import persist, restart_and_read, serialize

ROOT = Path(__file__).resolve().parent
BOUNDARIES = ["serialization", "persistence", "restart", "runtime readback"]


def main() -> int:
    evidence = json.loads((ROOT / "evidence.json").read_text(encoding="utf-8"))
    plan = evidence["verification_plan"]
    assert plan["cross_boundary_check_enabled"] is True
    assert plan["setup_instances"] == 1
    assert plan["required_boundaries"] == BOUNDARIES
    assert set(evidence["narrow_checks"].values()) == {"pass"}
    with TemporaryDirectory() as directory:
        persisted = Path(directory) / "config.json"
        persist(serialize("custom"), persisted)
        observed = restart_and_read(persisted)
    assert observed != "custom", "fixture defect disappeared; unique failure signal is gone"
    print("PASS: cross-boundary check retained and still detects the integration failure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
