#!/usr/bin/env python3
"""Validate and install the SkipHow plugin with each available host."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
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


def _payload(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"package directory is unavailable: {root}")
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        if path.name == ".git":
            raise ValueError("marketplace source must not contain a repository")
        if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError("marketplace source must contain ordinary files and directories only")
        if stat.S_ISREG(mode):
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not result:
        raise ValueError("package payload is empty")
    return result


def _plain_marketplace(destination: Path, host: str) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    metadata = ".agents" if host == "codex" else ".claude-plugin"
    shutil.copytree(ROOT / metadata, destination / metadata)
    shutil.copytree(PLUGIN_ROOT, destination / "plugins/skiphow")
    _payload(destination)
    return destination


def verify_plain_marketplace_source(source: str, host: str) -> tuple[bool, str]:
    """Require a repository-free local marketplace with the exact package bytes."""
    marketplace = Path(source).expanduser().resolve()
    try:
        marketplace_payload = _payload(marketplace)
        manifest = ".agents/plugins/marketplace.json" if host == "codex" else ".claude-plugin/marketplace.json"
        if (marketplace / manifest).read_bytes() != (ROOT / manifest).read_bytes():
            return False, "marketplace manifest does not match the candidate"
        plugin_payload = _payload(PLUGIN_ROOT)
        if _payload(marketplace / "plugins/skiphow") != plugin_payload:
            return False, "marketplace plugin payload does not match the candidate"
        expected = {
            manifest: hashlib.sha256((ROOT / manifest).read_bytes()).hexdigest(),
            **{f"plugins/skiphow/{name}": digest for name, digest in plugin_payload.items()},
        }
        if marketplace_payload != expected:
            return False, "marketplace contains files outside the exact candidate package"
    except (OSError, ValueError) as exc:
        return False, str(exc)
    return True, "plain marketplace contains the exact candidate package"


def _installed_path(host: str, raw: str) -> Path:
    value = json.loads(raw)
    entries = value.get("installed") if host == "codex" and isinstance(value, dict) else value
    if not isinstance(entries, list):
        raise ValueError("plugin inventory is not a list")
    matches = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        identifier = item.get("pluginId") if host == "codex" else item.get("id")
        if identifier == "skiphow@skiphow" and item.get("enabled") is True and item.get("installed", True) is True:
            matches.append(item)
    if len(matches) != 1:
        raise ValueError("expected one enabled skiphow@skiphow installation")
    item = matches[0]
    source = item.get("source") if host == "codex" else None
    path = source.get("path") if isinstance(source, dict) else item.get("installPath")
    if not isinstance(path, str) or not path:
        raise ValueError("host inventory omitted the installed package path")
    return Path(path).resolve()


def _created_repository(root: Path) -> bool:
    return any(path.name == ".git" for path in root.rglob("*"))


def _codex_policy_block(output: str) -> bool:
    lowered = output.lower()
    # Both halves are required. "requirements.toml" alone matched an ordinary parse
    # error; the denial language alone would match an unrelated refusal. The observed
    # message is: marketplace source `...` is not allowed by requirements from
    # /etc/codex/requirements.toml
    refused = "not allowed" in lowered or "allowed source" in lowered
    return refused and ("requirements.toml" in lowered or "source policy" in lowered)


def isolated_install(
    host: str,
    executable: str,
    *,
    codex_marketplace_source: str | None = None,
) -> tuple[bool, str]:
    """Install the exact candidate with a temporary, empty host configuration."""
    with tempfile.TemporaryDirectory(prefix=f"skiphow-{host}-install-") as temporary:
        environment = os.environ.copy()
        temporary_root = Path(temporary)
        source = (
            Path(codex_marketplace_source).expanduser().resolve()
            if host == "codex" and codex_marketplace_source
            else _plain_marketplace(temporary_root / "marketplace", host)
        )
        verified, detail = verify_plain_marketplace_source(str(source), host)
        if not verified:
            return False, detail
        host_home = temporary_root / "host-home"
        host_home.mkdir()
        if host == "codex":
            environment["CODEX_HOME"] = str(host_home)
            marketplace_command = [
                executable,
                "plugin",
                "marketplace",
                "add",
                str(source),
                "--json",
            ]
            commands = (
                marketplace_command,
                [executable, "plugin", "add", "skiphow@skiphow", "--json"],
                [executable, "plugin", "list", "--json"],
            )
        elif host == "claude":
            environment["CLAUDE_CONFIG_DIR"] = str(host_home)
            commands = (
                [executable, "plugin", "marketplace", "add", str(source), "--scope", "user"],
                [
                    executable,
                    "plugin",
                    "install",
                    "skiphow@skiphow",
                    "--scope",
                    "user",
                    "--yes",
                ],
                [executable, "plugin", "list", "--json"],
            )
        else:
            raise ValueError(f"unsupported host: {host}")

        output = ""
        for command in commands:
            passed, output = checked(command, env=environment)
            if _created_repository(temporary_root):
                return False, "host package check created a repository"
            if not passed:
                return False, output or f"failed {' '.join(command)}"
        try:
            installed = _installed_path(host, output)
            if _payload(installed) != _payload(PLUGIN_ROOT):
                return False, "installed plugin payload does not match the candidate"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return False, str(exc)
        return True, "exact candidate installed from a plain marketplace"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-codex-validator", action="store_true")
    parser.add_argument("--require-claude", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--require-codex-install", action="store_true")
    parser.add_argument("--require-claude-install", action="store_true")
    parser.add_argument(
        "--codex-marketplace-source",
        help="pre-provisioned plain local marketplace; defaults to a temporary snapshot",
    )
    args = parser.parse_args(argv)
    if args.skip_install and (args.require_codex_install or args.require_claude_install):
        parser.error("--skip-install cannot satisfy --require-codex-install or --require-claude-install")

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
            )
            policy_blocked = host == "codex" and not passed and _codex_policy_block(output)
            status = "PASS" if passed else "UNVERIFIED" if policy_blocked and not required else "FAIL"
            print(f"{host.capitalize()} isolated install: {status}")
            if not passed:
                if not policy_blocked or required:
                    errors.append(output or f"{host} isolated installation failed without output")

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
