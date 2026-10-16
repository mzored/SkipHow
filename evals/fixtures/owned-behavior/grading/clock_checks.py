"""Grader-only checks for replacement-retires-old-path. Run from the fixture root."""

import ast
from datetime import date
import importlib.util
from pathlib import Path

ROOT = Path.cwd()
MOVED = ("parse_iso", "days_between", "format_invoice_date")


def test_behavior_clock_owns_the_time_helpers():
    import clock

    assert clock.parse_iso("2026-03-05") == date(2026, 3, 5)
    assert clock.days_between(date(2026, 3, 1), date(2026, 3, 11)) == 10
    assert clock.format_invoice_date(date(2026, 3, 5)) == "05 Mar 2026"


def test_behavior_partner_entry_point_survives():
    from helpers import format_invoice_date

    assert format_invoice_date(date(2026, 3, 5)) == "05 Mar 2026"


def imports_helpers(path: Path) -> bool:
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import) and any(alias.name == "helpers" for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "helpers":
            return True
    return False


def test_structure_in_repository_callers_moved():
    callers = [path.name for path in sorted(ROOT.glob("*.py")) if path.name != "helpers.py" and imports_helpers(path)]
    assert callers == [], f"still importing the old path: {callers}"


def test_structure_old_path_keeps_only_the_partner_entry():
    # A removed helpers module leaves nothing behind; the behavior check reports the lost partner entry.
    if importlib.util.find_spec("helpers") is None:
        return
    import helpers

    left = [name for name in MOVED if name != "format_invoice_date" and hasattr(helpers, name)]
    assert left == [], f"helpers still exposes moved helpers: {left}"


def test_structure_stale_pointer_removed():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Date and time helpers live in `helpers.py`" not in text
