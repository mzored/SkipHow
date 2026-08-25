#!/usr/bin/env python3
"""Run optional exact-host and official package validation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
PROOF_STATUSES = frozenset({"VERIFIED", "UNVERIFIED", "FAILED"})


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


def proof(status: str, reference: str) -> dict[str, str]:
    if status not in PROOF_STATUSES:
        raise ValueError(f"invalid proof status: {status}")
    return {"status": status, "reference": reference}


def cli_version(executable: str | None) -> str | None:
    if executable is None:
        return None
    passed, output = checked([executable, "--version"], timeout=30)
    return output.splitlines()[0] if passed and output else None


def candidate_identity() -> dict[str, str | bool | None]:
    commit_ok, commit = checked(["git", "rev-parse", "HEAD"], timeout=30)
    tree_ok, tree = checked(["git", "rev-parse", "HEAD^{tree}"], timeout=30)
    status_ok, status = checked(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], timeout=30
    )
    return {
        "commit": commit if commit_ok and commit else None,
        "tree": tree if tree_ok and tree else None,
        "dirty": bool(status) if status_ok else None,
    }


def aggregate_proof(
    candidate: dict[str, str | bool | None], checks: dict[str, dict[str, str]]
) -> tuple[str, str]:
    statuses = [check["status"] for check in checks.values()]
    if "FAILED" in statuses:
        return "FAILED", "one or more recorded host checks failed"
    candidate_exact = (
        isinstance(candidate.get("commit"), str)
        and isinstance(candidate.get("tree"), str)
        and candidate.get("dirty") is False
    )
    if candidate_exact and statuses and all(status == "VERIFIED" for status in statuses):
        return "VERIFIED", f"all recorded host checks verified for {candidate['commit']}"
    return "UNVERIFIED", "candidate identity or one or more host checks remain unverified"


def write_receipt(
    path: Path,
    *,
    candidate: dict[str, str | bool | None],
    cli_versions: dict[str, str | None],
    checks: dict[str, dict[str, str]],
) -> None:
    status, reference = aggregate_proof(candidate, checks)
    value = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reference": reference,
        "candidate": candidate,
        "host_cli_versions": cli_versions,
        "checks": checks,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    errors: list[str] = []
    checks: dict[str, dict[str, str]] = {}

    codex = shutil.which("codex")
    claude = shutil.which("claude")
    cli_versions = {
        "codex": cli_version(codex),
        "claude": cli_version(claude),
    }

    validator = codex_validator()
    if validator is None:
        print("Codex official validator: UNVERIFIED")
        checks["codex_validator"] = proof(
            "UNVERIFIED", "configured Codex official validator was unavailable"
        )
        if args.require_codex_validator:
            errors.append("configured Codex official validator is unavailable")
    else:
        passed, output = checked(
            [sys.executable, str(validator), str(ROOT / "plugins" / "skiphow")]
        )
        status = "VERIFIED" if passed else "FAILED"
        print(f"Codex official validator: {'PASS' if passed else 'FAIL'}")
        checks["codex_validator"] = proof(status, "Codex official plugin validator")
        if not passed:
            errors.append(output or "Codex validator failed without output")

    if claude is None:
        print("Claude package validation: UNVERIFIED")
        checks["claude_package"] = proof(
            "UNVERIFIED", "Claude Code CLI was unavailable"
        )
        if args.require_claude:
            errors.append("Claude Code is unavailable")
    else:
        passed, output = checked([claude, "plugin", "validate", "--strict", str(ROOT)])
        print(f"Claude package validation: {'PASS' if passed else 'FAIL'}")
        checks["claude_package"] = proof(
            "VERIFIED" if passed else "FAILED", "claude plugin validate --strict"
        )
        if not passed:
            errors.append(output or "Claude validation failed without output")

    if args.skip_install:
        checks["codex_install"] = proof("UNVERIFIED", "isolated install skipped by request")
        checks["claude_install"] = proof("UNVERIFIED", "isolated install skipped by request")
    else:
        for host, required in (
            ("codex", args.require_codex_install),
            ("claude", args.require_claude_install),
        ):
            executable = codex if host == "codex" else claude
            if executable is None:
                print(f"{host.capitalize()} isolated install: UNVERIFIED")
                checks[f"{host}_install"] = proof(
                    "UNVERIFIED", f"{host} CLI was unavailable"
                )
                if required:
                    errors.append(f"{host} is unavailable for isolated installation")
                continue
            passed, output = isolated_install(host, executable)
            status = "VERIFIED" if passed else "FAILED"
            print(f"{host.capitalize()} isolated install: {'PASS' if passed else 'FAIL'}")
            checks[f"{host}_install"] = proof(status, f"isolated {host} plugin install")
            if not passed and required:
                errors.append(output or f"{host} isolated installation failed")

    candidate = candidate_identity()
    if args.output is not None:
        try:
            write_receipt(
                args.output,
                candidate=candidate,
                cli_versions=cli_versions,
                checks=checks,
            )
            print(f"Host proof receipt: {args.output}")
        except OSError as exc:
            errors.append(f"cannot write host proof receipt {args.output}: {exc}")

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
