"""Connect contributor verification to an optional installed host queue."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


def enter_host_admission(raw_args: list[str], entrypoint: Path, label: str) -> int | None:
    """Replace the entrypoint before its subprocess execution budgets begin."""
    adapter = shutil.which("agent-verify")
    if adapter is None:
        return None
    try:
        inherited = subprocess.run([adapter, "inherited", "--memory", "4", "--cpus", "4"],
                                   check=False).returncode
        if inherited == 0:
            return None
        if inherited != 1:
            print("host admission could not validate the inherited grant", file=sys.stderr)
            return 78
        os.execv(adapter, [adapter, "--memory", "4", "--cpus", "4", "--timeout", "2700",
                           "--label", label, "--", sys.executable, str(entrypoint.resolve()),
                           *raw_args])
    except OSError as error:
        print(f"host admission could not start: {error}", file=sys.stderr)
        return 78
    raise AssertionError("host admission exec returned")
