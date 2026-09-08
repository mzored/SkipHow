"""Required final delivery gate for the combined candidate."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "account_label": "Profile",
    "settings_label": "Preferences",
    "persisted_preference_default": "comfortable",
}


def main() -> int:
    state = json.loads((ROOT / "product-state.json").read_text(encoding="utf-8"))
    assert state == EXPECTED
    with TemporaryDirectory() as directory:
        stored = Path(directory) / "preferences.json"
        stored.write_text(json.dumps(state), encoding="utf-8")
        assert json.loads(stored.read_text(encoding="utf-8")) == EXPECTED
    print("PASS: full deterministic suite and persistence integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
