#!/usr/bin/env python3
"""Claude Code adapter for the canonical SkipHow lifecycle helper."""

from pathlib import Path
import runpy


CANONICAL_HELPER = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "skiphow"
    / "scripts"
    / "gh_task_status.py"
)
runpy.run_path(str(CANONICAL_HELPER), run_name="__main__")
