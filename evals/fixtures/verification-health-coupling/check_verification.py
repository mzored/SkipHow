"""Offline oracle for the coupling fixture."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    coverage = json.loads((ROOT / "coverage-map.json").read_text(encoding="utf-8"))
    rendered = json.loads((ROOT / "rendered-navigation.json").read_text(encoding="utf-8"))
    items = rendered["items"]
    assert coverage["presentation_coupled_checks"] == []
    assert coverage["stable_destination_contract_check"] is True
    assert coverage["rendered_keyboard_check"] is True
    assert [item["tab_index"] for item in items] == list(range(len(items)))
    assert {item["href"] for item in items} == {"/", "/profile", "/settings"}
    print("PASS: stable contract coverage and unique rendered-browser evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
