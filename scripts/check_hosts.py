#!/usr/bin/env python3
"""Validate and install the SkipHow plugin with each available host."""

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
PLUGIN_ROOT = ROOT / "plugins/skiphow"


def checked(
    command: Sequence[str],
    *,
    timeout: int = 180,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    environment = os.environ.copy()
    if env:
        environment.update(env)
    try:
        result = subprocess.run(
            list(command),
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def codex_validator() -> Path | None:
    """Locate the validator shipped with the Codex plugin creator."""
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


def validator_python() -> tuple[str | None, str]:
    """Choose a Python interpreter with the validator's YAML dependency."""
    available, _ = checked([sys.executable, "-c", "import yaml"], timeout=30)
    if available:
        return sys.executable, "current Python"
    prepared, output = checked(
        [sys.executable, "scripts/check.py", "--prepare-only"],
        timeout=300,
    )
    managed = Path(output.splitlines()[-1]) if output else Path()
    if prepared and managed.is_file():
        return str(managed), "repository-managed Python"
    return None, output or "could not prepare repository-managed Python"


def verify_codex_marketplace_source(
    source: str, ref: str | None = None
) -> tuple[bool, str]:
    """Require a Git marketplace ref to match the current committed candidate."""
    local_source = Path(source).expanduser()
    if local_source.is_dir():
        if ref is not None:
            return False, "a Codex marketplace ref cannot be used with a local source"
        if local_source.resolve() != ROOT.resolve():
            return False, f"local marketplace source must be the candidate checkout: {ROOT}"
        return True, "candidate checkout as local marketplace source"

    head_ok, local_head = checked(["git", "rev-parse", "HEAD"], timeout=30)
    if not head_ok or not local_head:
        return False, "cannot identify the current candidate commit"

    requested_ref = ref or "HEAD"
    command = ["git", "ls-remote", source]
    if requested_ref != local_head:
        command.extend([requested_ref, f"{requested_ref}^{{}}"])
    remote_ok, output = checked(command)
    commits = {line.split()[0] for line in output.splitlines() if line.split()}
    if not remote_ok or local_head not in commits:
        resolved = ", ".join(sorted(commits)) or "unavailable"
        return False, (
            f"Codex marketplace ref {requested_ref!r} resolves to {resolved}, "
            f"not candidate {local_head}"
        )
    return True, f"Git marketplace ref {requested_ref!r} at {local_head}"


def isolated_install(
    host: str,
    executable: str,
    *,
    codex_marketplace_source: str | None = None,
    codex_marketplace_ref: str | None = None,
) -> tuple[bool, str]:
    """Install the exact candidate with a temporary, empty host configuration."""
    with tempfile.TemporaryDirectory(prefix=f"skiphow-{host}-install-") as temporary:
        environment = os.environ.copy()
        if host == "codex":
            source = codex_marketplace_source or str(ROOT)
            verified, detail = verify_codex_marketplace_source(
                source, codex_marketplace_ref
            )
            if not verified:
                return False, detail
            environment["CODEX_HOME"] = temporary
            marketplace_command = [
                executable,
                "plugin",
                "marketplace",
                "add",
                source,
            ]
            if codex_marketplace_ref is not None:
                marketplace_command.extend(["--ref", codex_marketplace_ref])
            marketplace_command.append("--json")
            commands = (
                marketplace_command,
                [executable, "plugin", "add", "skiphow@skiphow", "--json"],
                [executable, "plugin", "list", "--json"],
            )
        elif host == "claude":
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
        else:
            raise ValueError(f"unsupported host: {host}")

        output = ""
        for command in commands:
            passed, output = checked(command, env=environment)
            if not passed:
                return False, output or f"failed {' '.join(command)}"
        if "skiphow" not in output.lower():
            return False, "installed plugin was absent from the host listing"
        return True, output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-codex-validator", action="store_true")
    parser.add_argument("--require-claude", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--require-codex-install", action="store_true")
    parser.add_argument("--require-claude-install", action="store_true")
    parser.add_argument(
        "--codex-marketplace-source",
        help="local or Git marketplace source; defaults to this checkout",
    )
    parser.add_argument(
        "--codex-marketplace-ref",
        help="Git ref that must resolve to the current candidate commit",
    )
    args = parser.parse_args(argv)

    errors: list[str] = []
    codex = shutil.which("codex")
    claude = shutil.which("claude")

    validator = codex_validator()
    if validator is None:
        print("Codex package validation: UNVERIFIED")
        if args.require_codex_validator:
            errors.append("Codex plugin validator is unavailable")
    else:
        python, detail = validator_python()
        if python is None:
            passed, output = False, detail
        else:
            passed, output = checked([python, str(validator), str(PLUGIN_ROOT)])
        print(f"Codex package validation: {'PASS' if passed else 'FAIL'}")
        if not passed:
            errors.append(output or "Codex plugin validator failed without output")

    if claude is None:
        print("Claude package validation: UNVERIFIED")
        if args.require_claude:
            errors.append("Claude Code is unavailable")
    else:
        passed, output = checked([claude, "plugin", "validate", "--strict", str(PLUGIN_ROOT)])
        print(f"Claude package validation: {'PASS' if passed else 'FAIL'}")
        if not passed:
            errors.append(output or "Claude plugin validation failed without output")

    if args.skip_install:
        print("Codex isolated install: UNVERIFIED (skipped)")
        print("Claude isolated install: UNVERIFIED (skipped)")
    else:
        for host, executable, required in (
            ("codex", codex, args.require_codex_install),
            ("claude", claude, args.require_claude_install),
        ):
            if executable is None:
                print(f"{host.capitalize()} isolated install: UNVERIFIED")
                if required:
                    errors.append(f"{host} is unavailable for isolated installation")
                continue
            passed, output = isolated_install(
                host,
                executable,
                codex_marketplace_source=(
                    args.codex_marketplace_source if host == "codex" else None
                ),
                codex_marketplace_ref=(
                    args.codex_marketplace_ref if host == "codex" else None
                ),
            )
            print(f"{host.capitalize()} isolated install: {'PASS' if passed else 'FAIL'}")
            if not passed:
                errors.append(output or f"{host} isolated installation failed without output")

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
