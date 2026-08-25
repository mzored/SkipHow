#!/usr/bin/env python3
"""Read-only SkipHow readiness report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


TIMEOUT_SECONDS = 15


def _load_config_module():
    path = Path(__file__).with_name("config.py")
    spec = importlib.util.spec_from_file_location("skiphow_config", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


_config = _load_config_module()
ConfigError = _config.ConfigError
load_config = _config.load_config


def succeeds(args: Sequence[str], *, cwd: str = ".") -> bool:
    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def configured_project(cwd: str = ".") -> str | None:
    return load_config(cwd).project


def package_proof(receipt: str | None) -> str:
    if receipt is None:
        return "UNVERIFIED (no receipt supplied)"
    path = Path(receipt)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return f"FAILED ({path}: {exc})"
    if not isinstance(value, dict):
        return f"FAILED ({path}: receipt must be a JSON object)"
    status = value.get("status")
    reference = value.get("reference")
    if status not in {"VERIFIED", "UNVERIFIED", "FAILED"} or not isinstance(
        reference, str
    ) or not reference:
        return f"FAILED ({path}: expected status VERIFIED|UNVERIFIED|FAILED and reference)"
    return f"{status} ({reference})"


def report(
    repo: str | None = None,
    *,
    cwd: str = ".",
    package_receipt: str | None = None,
) -> list[str]:
    repository_ready = succeeds(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    gh_available = shutil.which("gh") is not None and succeeds(["gh", "auth", "status"])
    if gh_available:
        repo_args = ["gh", "repo", "view"]
        if repo:
            repo_args.append(repo)
        repo_args.extend(["--json", "nameWithOwner"])
        gh_available = succeeds(repo_args, cwd=cwd)

    try:
        project = configured_project(cwd)
        config_state = "VALID"
    except ConfigError as exc:
        project = None
        config_state = f"INVALID ({exc})"
    if project is None:
        project_state = "NOT CONFIGURED"
    elif not gh_available:
        project_state = "UNAVAILABLE"
    else:
        owner, number = project.rsplit("/", 1)
        project_state = (
            "CONNECTED"
            if succeeds(["gh", "project", "view", number, "--owner", owner, "--format", "json"])
            else "UNAVAILABLE"
        )

    host_available = any(
        shutil.which(executable) is not None and succeeds([executable, "--version"])
        for executable in ("codex", "claude")
    )
    return [
        "Core: READY",
        f"Repository: {'READY' if repository_ready else 'LIMITED'}",
        f"GitHub Issues: {'AVAILABLE' if gh_available else 'NOT AVAILABLE'}",
        f"GitHub Project: {project_state}",
        f"Configuration: {config_state}",
        f"Host CLI: {'AVAILABLE' if host_available else 'NOT AVAILABLE'}",
        f"Package proof: {package_proof(package_receipt)}",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skiphow-doctor")
    parser.add_argument("repo", nargs="?")
    parser.add_argument(
        "--require",
        choices=("repository", "github", "project", "configuration", "host", "package"),
    )
    parser.add_argument("--package-proof-receipt")
    args = parser.parse_args(argv)
    lines = report(args.repo, package_receipt=args.package_proof_receipt)
    print("\n".join(lines))
    if args.require == "repository" and "Repository: READY" not in lines:
        return 1
    if args.require == "github" and "GitHub Issues: AVAILABLE" not in lines:
        return 1
    if args.require == "project" and "GitHub Project: CONNECTED" not in lines:
        return 1
    if args.require == "configuration" and "Configuration: VALID" not in lines:
        return 1
    if args.require == "host" and "Host CLI: AVAILABLE" not in lines:
        return 1
    if args.require == "package" and not any(
        line.startswith("Package proof: VERIFIED ") for line in lines
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
