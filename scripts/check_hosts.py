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


def validator_python() -> tuple[str | None, str]:
    """Select an interpreter that can run the official Codex validator."""
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


def default_codex_marketplace_source() -> str:
    """Use the repository origin for Codex, with a local fallback when no origin exists."""
    passed, output = checked(["git", "remote", "get-url", "origin"], timeout=30)
    return output.splitlines()[0] if passed and output else str(ROOT)


def verify_codex_marketplace_source(
    source: str, ref: str | None = None
) -> tuple[bool, str]:
    """Bind a Git marketplace source to the current committed candidate."""
    if Path(source).expanduser().is_dir():
        if ref is not None:
            return False, "a Codex marketplace ref cannot be used with a local source"
        return True, "local marketplace source"
    head_ok, local_head = checked(["git", "rev-parse", "HEAD"], timeout=30)
    if not head_ok or not local_head:
        return False, "cannot identify the local candidate commit"
    requested_ref = ref or "HEAD"
    remote_command = ["git", "ls-remote", source]
    if requested_ref != local_head:
        remote_command.extend([requested_ref, f"{requested_ref}^{{}}"])
    remote_ok, remote_output = checked(remote_command, timeout=180)
    remote_commits = {
        line.split()[0]
        for line in remote_output.splitlines()
        if line.split()
    }
    if not remote_ok or local_head not in remote_commits:
        resolved = ", ".join(sorted(remote_commits)) or "unavailable"
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
    """Install the candidate through one host's isolated marketplace."""
    with tempfile.TemporaryDirectory(prefix=f"skiphow-{host}-install-") as temporary:
        environment = os.environ.copy()
        if host == "codex":
            source = codex_marketplace_source or default_codex_marketplace_source()
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


def runner_package_check() -> tuple[bool, str]:
    """Build the runner wheel from a source copy and smoke-test its entry point."""
    with tempfile.TemporaryDirectory(prefix="skiphow-runner-package-") as temporary:
        root = Path(temporary)
        source = root / "source"
        build_environment = root / "build-environment"
        install_environment = root / "install-environment"
        wheel_directory = root / "dist"
        try:
            shutil.copytree(
                ROOT,
                source,
                ignore=shutil.ignore_patterns(
                    ".git", ".venv", ".pytest_cache", "__pycache__", "build", "dist"
                ),
            )
        except OSError as exc:
            return False, f"cannot copy runner source: {exc}"
        steps = (
            [sys.executable, "-m", "venv", str(build_environment)],
            [sys.executable, "-m", "venv", str(install_environment)],
        )
        for command in steps:
            passed, output = checked(command, timeout=180)
            if not passed:
                return False, output or f"failed {' '.join(command)}"
        build_python = build_environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        install_python = install_environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        passed, output = checked(
            [
                str(build_python),
                "-m",
                "pip",
                "wheel",
                str(source),
                "--no-deps",
                "--wheel-dir",
                str(wheel_directory),
            ],
            timeout=300,
        )
        if not passed:
            return False, output or "runner wheel build failed without output"
        wheels = sorted(wheel_directory.glob("skiphow_runner-*.whl"))
        if len(wheels) != 1:
            return False, f"expected one runner wheel, found {len(wheels)}"
        wheel = wheels[0]
        passed, output = checked(
            [str(install_python), "-m", "pip", "install", "--no-deps", str(wheel)],
            timeout=300,
        )
        if not passed:
            return False, output or "isolated runner install failed without output"
        passed, output = checked(
            [str(install_python), "-m", "skiphow", "--help"], timeout=60
        )
        if not passed:
            return False, output or "installed runner CLI smoke failed without output"
        expected_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        passed, output = checked(
            [
                str(install_python),
                "-c",
                "import skiphow; print(skiphow.__version__)",
            ],
            timeout=30,
        )
        if not passed or output.splitlines()[-1:] != [expected_version]:
            actual = output.splitlines()[-1] if output else "unavailable"
            return False, f"installed runner version {actual!r} != {expected_version!r}"
        return True, f"built and smoke-tested {wheel.name} in an isolated environment"


def output_is_inside_repository(path: Path) -> bool:
    """Return whether writing a receipt would change the candidate worktree."""
    return path.expanduser().resolve().is_relative_to(ROOT.resolve())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-codex-validator", action="store_true")
    parser.add_argument("--require-claude", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--require-codex-install", action="store_true")
    parser.add_argument("--require-claude-install", action="store_true")
    parser.add_argument(
        "--codex-marketplace-source",
        help="Codex Git or local marketplace source; defaults to the repository origin",
    )
    parser.add_argument(
        "--codex-marketplace-ref",
        help="Exact Git ref for the Codex marketplace source; defaults to HEAD",
    )
    parser.add_argument("--skip-runner-package", action="store_true")
    parser.add_argument("--require-runner-package", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.output is not None and output_is_inside_repository(args.output):
        print("- host proof receipt must be written outside the repository", file=sys.stderr)
        return 2
    errors: list[str] = []
    checks: dict[str, dict[str, str]] = {}

    codex = shutil.which("codex")
    claude = shutil.which("claude")
    cli_versions = {
        "codex": cli_version(codex),
        "claude": cli_version(claude),
    }

    if args.skip_runner_package:
        checks["runner_package"] = proof(
            "UNVERIFIED", "runner wheel build and isolated install skipped by request"
        )
    else:
        passed, output = runner_package_check()
        print(f"Runner package: {'PASS' if passed else 'FAIL'}")
        checks["runner_package"] = proof(
            "VERIFIED" if passed else "FAILED",
            "runner wheel build, isolated install, and CLI smoke",
        )
        if not passed and args.require_runner_package:
            errors.append(output or "runner package check failed without output")

    validator = codex_validator()
    if validator is None:
        print("Codex official validator: UNVERIFIED")
        checks["codex_validator"] = proof(
            "UNVERIFIED", "configured Codex official validator was unavailable"
        )
        if args.require_codex_validator:
            errors.append("configured Codex official validator is unavailable")
    else:
        python, python_reference = validator_python()
        if python is None:
            passed, output = False, python_reference
        else:
            passed, output = checked(
                [python, str(validator), str(ROOT / "plugins" / "skiphow")]
            )
        status = "VERIFIED" if passed else "FAILED"
        print(f"Codex official validator: {'PASS' if passed else 'FAIL'}")
        checks["codex_validator"] = proof(
            status,
            f"Codex official plugin validator via {python_reference}",
        )
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
            source = (
                args.codex_marketplace_source or default_codex_marketplace_source()
                if host == "codex"
                else None
            )
            passed, output = isolated_install(
                host,
                executable,
                codex_marketplace_source=source,
                codex_marketplace_ref=(
                    args.codex_marketplace_ref if host == "codex" else None
                ),
            )
            status = "VERIFIED" if passed else "FAILED"
            print(f"{host.capitalize()} isolated install: {'PASS' if passed else 'FAIL'}")
            reference = f"isolated {host} plugin install"
            if host == "codex":
                reference += " from exact configured marketplace source"
            checks[f"{host}_install"] = proof(status, reference)
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
