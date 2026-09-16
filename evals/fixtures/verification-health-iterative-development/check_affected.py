"""Native affected selection for one intermediate owner-visible edit."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "account-label": ("account_label", "Profile"),
    "settings-label": ("settings_label", "Preferences"),
    "persisted-default": ("persisted_preference_default", "comfortable"),
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in EXPECTED:
        print("choose one target from: " + ", ".join(EXPECTED), file=sys.stderr)
        return 2
    field, expected = EXPECTED[sys.argv[1]]
    state = json.loads((ROOT / "product-state.json").read_text(encoding="utf-8"))
    assert state[field] == expected
    print(f"PASS: {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
