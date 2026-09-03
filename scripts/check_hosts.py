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
    """Report whether this interpreter already has the validator's YAML dependency.

    This never installs anything. Preparing dependencies on the caller's behalf
    would reach a package index from an ordinary check, so an interpreter without
    PyYAML leaves the Codex validator unrun rather than silently provisioned.
    """
    available, _ = checked([sys.executable, "-c", "import yaml"], timeout=30)
    if available:
        return sys.executable, "current Python"
    return None, (
        "this Python lacks the validator's PyYAML dependency; install it yourself, "
        "then rerun: python -m pip install -r requirements-dev.txt"
    )


def _payload(root: Path) -> dict[str, str]:
    try:
        relative = root.relative_to(ROOT)
    except ValueError:
        linked_component = root.is_symlink()
    else:
        current = ROOT
        linked_component = False
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                linked_component = True
                break
    if not root.is_dir() or linked_component:
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


def _marketplace_manifest(host: str) -> tuple[str, Path]:
    relative = (
        ".agents/plugins/marketplace.json"
        if host == "codex"
        else ".claude-plugin/marketplace.json"
    )
    path = ROOT / relative
    current = ROOT
    linked = False
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            linked = True
            break
    if linked or not path.is_file():
        raise ValueError(f"marketplace manifest must be a regular non-symlink file: {relative}")
    return relative, path


def _plain_marketplace(destination: Path, host: str) -> Path:
    manifest, candidate_manifest = _marketplace_manifest(host)
    _payload(PLUGIN_ROOT)
    destination.mkdir(parents=True, exist_ok=False)
    destination_manifest = destination / manifest
    destination_manifest.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(candidate_manifest, destination_manifest)
    shutil.copytree(PLUGIN_ROOT, destination / "plugins/skiphow", symlinks=True)
    _payload(destination)
    return destination


def verify_plain_marketplace_source(source: str, host: str) -> tuple[bool, str]:
    """Require a repository-free local marketplace with the exact package bytes."""
    marketplace = Path(source).expanduser().resolve()
    try:
        manifest, candidate_manifest = _marketplace_manifest(host)
        marketplace_payload = _payload(marketplace)
        if (marketplace / manifest).read_bytes() != candidate_manifest.read_bytes():
            return False, "marketplace manifest does not match the candidate"
        plugin_payload = _payload(PLUGIN_ROOT)
        if _payload(marketplace / "plugins/skiphow") != plugin_payload:
            return False, "marketplace plugin payload does not match the candidate"
        expected = {
            manifest: hashlib.sha256(candidate_manifest.read_bytes()).hexdigest(),
            **{f"plugins/skiphow/{name}": digest for name, digest in plugin_payload.items()},
        }
        if marketplace_payload != expected:
            return False, "marketplace contains files outside the exact candidate package"
    except (OSError, ValueError) as exc:
        return False, str(exc)
    return True, "plain marketplace contains the exact candidate package"


def _inventory_entry(host: str, raw: str) -> dict[str, object]:
    """Return the one enabled installed entry reported by the host inventory."""
    value = json.loads(raw)
    entries = value.get("installed") if host == "codex" and isinstance(value, dict) else value
    if not isinstance(entries, list):
        raise ValueError("plugin inventory is not a list")
    matches: list[dict[str, object]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        identifier = item.get("pluginId") if host == "codex" else item.get("id")
        if identifier == "skiphow@skiphow":
            matches.append(item)
    if len(matches) != 1:
        raise ValueError("expected exactly one skiphow@skiphow inventory entry")
    match = matches[0]
    installed = (
        match.get("installed") is True
        if host == "codex"
        else match.get("installed", True) is True
    )
    if match.get("enabled") is not True or not installed:
        raise ValueError("skiphow@skiphow inventory entry is not enabled and installed")
    return match


def _codex_installed_path(raw: str) -> Path:
    """Read the installed payload path from `codex plugin add --json`."""
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Codex plugin add output is not an object")
    if value.get("pluginId") != "skiphow@skiphow":
        raise ValueError("Codex plugin add output has the wrong pluginId")
    path = value.get("installedPath")
    if not isinstance(path, str) or not path:
        raise ValueError("Codex plugin add output omitted installedPath")
    return Path(path).expanduser().resolve()


def _claude_installed_path(item: dict[str, object]) -> Path:
    """Read the installed payload path from Claude's verified inventory entry."""
    path = item.get("installPath")
    if not isinstance(path, str) or not path:
        raise ValueError("Claude plugin inventory omitted installPath")
    return Path(path).expanduser().resolve()


def _require_isolated_path(installed: Path, host_home: Path) -> Path:
    """Reject a host claim that resolves outside its fresh configuration home."""
    resolved_home = host_home.resolve()
    resolved_installed = installed.resolve()
    if resolved_installed == resolved_home or not resolved_installed.is_relative_to(resolved_home):
        raise ValueError("installed package path is outside the isolated host home")
    return resolved_installed


def _created_repository(root: Path) -> bool:
    return any(path.name == ".git" for path in root.rglob("*"))


def _codex_policy_block(output: str) -> bool:
    lowered = output.lower()
    # Both halves are required. "requirements.toml" alone matched an ordinary parse
    # error; the denial language alone would match an unrelated refusal. The observed
    # message is: marketplace source `...` is not allowed by requirements from
    # /etc/codex/requirements.toml
    refused = "not allowed" in lowered or "allowed source" in lowered
    policy = "requirements.toml" in lowered or "source policy" in lowered
    return refused and policy and ("marketplace source" in lowered or "allowed source" in lowered)


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
        command_cwd = temporary_root / "command-cwd"
        command_cwd.mkdir()
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

        outputs: list[str] = []
        for command in commands:
            output = ""
            passed, output = checked(command, env=environment, cwd=command_cwd)
            outputs.append(output)
            if _created_repository(temporary_root):
                return False, "host package check created a repository"
            if not passed:
                return False, output or f"failed {' '.join(command)}"
        try:
            inventory = _inventory_entry(host, outputs[2])
            installed = (
                _codex_installed_path(outputs[1])
                if host == "codex"
                else _claude_installed_path(inventory)
            )
            installed = _require_isolated_path(installed, host_home)
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
            print(f"Codex package validation: UNVERIFIED ({detail})")
            if args.require_codex_validator:
                errors.append(detail)
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
