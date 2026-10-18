"""Fail when a Python file exceeds the line limit or drifts from the baseline."""

import json
import pathlib
import sys

LIMIT = 20
root = pathlib.Path(__file__).resolve().parent.parent
baseline = json.loads((root / "config/file-size-baseline.json").read_text())
errors = []
for path in sorted(root.rglob("*.py")):
    name = path.relative_to(root).as_posix()
    lines = len(path.read_text().splitlines())
    if name in baseline and lines != baseline[name]:
        errors.append(f"{name}: {lines} lines, baseline says {baseline[name]}")
    elif name not in baseline and lines > LIMIT:
        errors.append(f"{name}: {lines} lines, limit {LIMIT}")
for error in errors:
    print(error)
sys.exit(1 if errors else 0)
