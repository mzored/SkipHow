"""Offline oracle for the coupling fixture."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    plan = json.loads((ROOT / "verification-plan.json").read_text(encoding="utf-8"))
    rendered = json.loads((ROOT / "rendered-navigation.json").read_text(encoding="utf-8"))
    items = rendered["items"]
    assert [item["tab_index"] for item in items] == list(range(len(items)))
    assert len({item["href"] for item in items}) == len(items)
    assert plan["coupling_repaired"] is True
    assert plan["mechanical_high_level_rewrites"] == 0
    assert plan["coverage_placement"] == {
        "destination reachability": "stable contract checks",
        "keyboard focus order": "browser artifact check",
    }
    print("PASS: stable contract coverage and unique rendered-browser evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
