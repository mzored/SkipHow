"""Deterministic checks for the example project.

Runs offline. It never installs anything and never creates an environment.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def missing_pins() -> list[str]:
    missing: list[str] = []
    for line in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, expected = line.partition("==")
        try:
            installed = version(name)
        except PackageNotFoundError:
            missing.append(f"{line} (not installed)")
            continue
        if installed != expected:
            missing.append(f"{line} (found {installed})")
    return missing


def main() -> int:
    missing = missing_pins()
    if missing:
        print("missing check dependencies: " + ", ".join(missing), file=sys.stderr)
        print("install them with: python -m pip install -r requirements-dev.txt", file=sys.stderr)
        return 1
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/config_checks.py"],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
