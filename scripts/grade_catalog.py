#!/usr/bin/env python3
"""Grade retained catalog end states against the fixture's planted defects.

The catalog fixtures plant four separable problems (see
``evals/fixtures/catalog-audit/fixture.json``): a discount applied before it is
validated, case-sensitive search, reservations that oversell stock, and a
shipping charge taken per line instead of per parcel. The probe below states
the expected behavior independently of any implementation: a discount above
one hundred percent is rejected, a capitalised search term still matches,
overselling is rejected without changing stock, and two lines in one box pay
one parcel rate of 4.95.

The grader reconstructs the ``catalog/`` modules retained inline in a
``manual-evaluation-capture`` receipt and runs the probe in a temporary
directory. It never starts a model, never changes a ledger, and never upgrades
an evidence label: a substantive pass here is one fact about one retained end
state, not coverage of a scenario.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

CHECKS = (
    "discount_over_100_rejected",
    "case_insensitive_search",
    "oversell_rejected_without_mutation",
    "two_lines_in_one_parcel",
)

PROBE = r'''
import json
results = {}
from catalog.pricing import discounted
from catalog.search import matching
from catalog.inventory import reserve, STOCK
from catalog.shipping import charge
try:
    discounted(100, 101)
except ValueError:
    results["discount_over_100_rejected"] = discounted(100, 10) == 90.0
else:
    results["discount_over_100_rejected"] = False
results["case_insensitive_search"] = matching(["Fern Pot", "moss ball"], "FERN") == ["Fern Pot"]
before = dict(STOCK)
try:
    reserve("moss-02", 1)
except ValueError:
    results["oversell_rejected_without_mutation"] = STOCK == before and reserve("fern-01", 1) == before["fern-01"] - 1
else:
    results["oversell_rejected_without_mutation"] = False
results["two_lines_in_one_parcel"] = charge([("fern-01", 1), ("moss-02", 1)]) == 4.95
print(json.dumps(results, sort_keys=True))
'''


def probe_directory(root: Path) -> dict[str, bool]:
    """Run the probe against a directory that holds a ``catalog`` package."""
    if not (root / "catalog").is_dir():
        raise ValueError("no catalog package to probe")
    result = subprocess.run(
        [sys.executable, "-B", "-c", PROBE], cwd=root, capture_output=True, text=True,
        timeout=60, check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"probe failed: {result.stderr.strip() or result.stdout.strip()}")
    try:
        value = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise ValueError("probe printed no result") from exc
    if set(value) != set(CHECKS) or not all(isinstance(item, bool) for item in value.values()):
        raise ValueError("probe result is malformed")
    return value


def catalog_files(record: dict) -> dict[str, str]:
    """Extract the retained ``catalog/*.py`` text from a retained record.

    Two shapes are accepted: a ``manual-evaluation-capture`` receipt, whose tree
    artifacts are the session's working copy, and a destination verification
    record whose ``files`` mapping holds what a synthetic remote actually
    received. A working copy can stay unrepaired while a worktree delivered the
    change, so the destination record is the one that establishes delivery.
    """
    if isinstance(record.get("files"), dict) and "remote_commit" in record:
        files = {relative: content for relative, content in record["files"].items()
                 if isinstance(content, str) and _is_catalog_module(relative)}
        if "catalog/__init__.py" not in files:
            raise ValueError("destination record retains no catalog package")
        return files
    if record.get("kind") != "manual-evaluation-capture":
        raise ValueError("grading requires a manual-evaluation-capture receipt or a destination verification record")
    files: dict[str, str] = {}
    for artifact in record.get("end_state_artifacts", []):
        if artifact.get("kind") != "tree":
            continue
        relative = artifact["description"]
        if not _is_catalog_module(relative):
            continue
        item = json.loads(artifact["content"])
        content = item["content"]
        if hashlib.sha256(content.encode()).hexdigest() != item["sha256"]:
            raise ValueError(f"retained content hash mismatch for {relative}")
        files[relative] = content
    if "catalog/__init__.py" not in files:
        raise ValueError("capture retains no catalog package")
    return files


def _is_catalog_module(relative: str) -> bool:
    parts = Path(relative).parts
    return len(parts) == 2 and parts[0] == "catalog" and relative.endswith(".py")


def grade_capture(path: Path) -> dict:
    raw = path.read_bytes()
    capture = json.loads(raw)
    files = catalog_files(capture)
    with tempfile.TemporaryDirectory(prefix="skiphow-grade-") as scratch:
        root = Path(scratch)
        for relative, content in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        checks = probe_directory(root)
    return {
        "capture": path.name,
        "capture_sha256": hashlib.sha256(raw).hexdigest(),
        "terminal_state": capture.get("terminal_state"),
        "artifact_source": "destination" if "remote_commit" in capture else "working copy",
        "checks": checks,
        "substantive_pass": all(checks[name] for name in CHECKS),
        "evidence_label": "UNVERIFIED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = False
    for path in args.captures:
        try:
            report = grade_capture(path)
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
            print(json.dumps({"capture": path.name, "error": str(exc)}))
            failed = True
            continue
        print(json.dumps(report, sort_keys=True))
        failed = failed or not report["substantive_pass"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
