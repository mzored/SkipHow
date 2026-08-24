#!/usr/bin/env python3
"""Run optional exact-host and official package validation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


def checked(command: Sequence[str], *, timeout: int = 180) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            list(command),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def codex_validator() -> Path | None:
    configured = os.environ.get("CODEX_PLUGIN_VALIDATOR")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        return candidate if candidate.is_file() else None
    codex_home = os.environ.get("CODEX_HOME")
    if not codex_home:
        return None
    candidate = (
        Path(codex_home)
        / "skills"
        / ".system"
        / "plugin-creator"
        / "scripts"
        / "validate_plugin.py"
    )
    return candidate if candidate.is_file() else None


def isolated_install(host: str, executable: str) -> tuple[bool, str]:
    """Install the current worktree through one host's local marketplace path."""
    with tempfile.TemporaryDirectory(prefix=f"skiphow-{host}-install-") as temporary:
        environment = os.environ.copy()
        if host == "codex":
            environment["CODEX_HOME"] = temporary
            commands = (
                [executable, "plugin", "marketplace", "add", str(ROOT), "--json"],
                [executable, "plugin", "add", "skiphow@skiphow", "--json"],
                [executable, "plugin", "list", "--json"],
            )
        else:
            environment["CLAUDE_CONFIG_DIR"] = temporary
            commands = (
                [executable, "plugin", "marketplace", "add", str(ROOT), "--scope", "user"],
                [
                    executable,
                    "plugin",
                    "install",
                    "skiphow@skiphow",
                    "--scope",
                    "user",
                    "--yes",
                ],
                [executable, "plugin", "list"],
            )
        outputs: list[str] = []
        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                return False, str(exc)
            outputs.append((result.stdout + result.stderr).strip())
            if result.returncode:
                return False, outputs[-1]
        if "skiphow" not in outputs[-1]:
            return False, "installed plugin was absent from host listing"
        return True, outputs[-1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-codex-validator", action="store_true")
    parser.add_argument("--require-claude", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--require-codex-install", action="store_true")
    parser.add_argument("--require-claude-install", action="store_true")
    args = parser.parse_args(argv)
    errors: list[str] = []

    validator = codex_validator()
    if validator is None:
        print("Codex official validator: UNVERIFIED")
        if args.require_codex_validator:
            errors.append("configured Codex official validator is unavailable")
    else:
        passed, output = checked(
            [sys.executable, str(validator), str(ROOT / "plugins" / "skiphow")]
        )
        print(f"Codex official validator: {'PASS' if passed else 'FAIL'}")
        if not passed:
            errors.append(output or "Codex validator failed without output")

    claude = shutil.which("claude")
    if claude is None:
        print("Claude package validation: UNVERIFIED")
        if args.require_claude:
            errors.append("Claude Code is unavailable")
    else:
        passed, output = checked([claude, "plugin", "validate", "--strict", str(ROOT)])
        print(f"Claude package validation: {'PASS' if passed else 'FAIL'}")
        if not passed:
            errors.append(output or "Claude validation failed without output")

    if not args.skip_install:
        for host, required in (
            ("codex", args.require_codex_install),
            ("claude", args.require_claude_install),
        ):
            executable = shutil.which(host)
            if executable is None:
                print(f"{host.capitalize()} isolated install: UNVERIFIED")
                if required:
                    errors.append(f"{host} is unavailable for isolated installation")
                continue
            passed, output = isolated_install(host, executable)
            print(f"{host.capitalize()} isolated install: {'PASS' if passed else 'UNVERIFIED'}")
            if not passed and required:
                errors.append(output or f"{host} isolated installation failed")

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
