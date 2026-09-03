#!/usr/bin/env python3
"""Report each host capability of the SkipHow package separately, never as one aggregate."""

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


def _host_commands(
    host: str, executable: str, source: Path
) -> dict[str, list[str]]:
    """Return the host CLI commands for one clean-home install cycle."""
    if host == "codex":
        return {
            "marketplace": [
                executable,
                "plugin",
                "marketplace",
                "add",
                str(source),
                "--json",
            ],
            "install": [executable, "plugin", "add", "skiphow@skiphow", "--json"],
            "list": [executable, "plugin", "list", "--json"],
            "uninstall": [executable, "plugin", "remove", "skiphow@skiphow"],
        }
    if host == "claude":
        return {
            "marketplace": [
                executable,
                "plugin",
                "marketplace",
                "add",
                str(source),
                "--scope",
                "user",
            ],
            "install": [
                executable,
                "plugin",
                "install",
                "skiphow@skiphow",
                "--scope",
                "user",
                "--yes",
            ],
            "list": [executable, "plugin", "list", "--json"],
            "uninstall": [
                executable,
                "plugin",
                "uninstall",
                "skiphow@skiphow",
                "--scope",
                "user",
                "--yes",
            ],
        }
    raise ValueError(f"unsupported host: {host}")


def _home_variable(host: str) -> str:
    return "CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"


def _inventory_absent(host: str, raw: str) -> bool:
    """Report whether the host inventory no longer shows an installed skiphow."""
    value = json.loads(raw)
    entries = value.get("installed") if host == "codex" and isinstance(value, dict) else value
    if entries is None:
        return True
    if not isinstance(entries, list):
        raise ValueError("plugin inventory is not a list")
    for item in entries:
        if not isinstance(item, dict):
            continue
        identifier = item.get("pluginId") if host == "codex" else item.get("id")
        if identifier != "skiphow@skiphow":
            continue
        installed = item.get("installed", host != "codex")
        if installed is True:
            return False
    return True


class _InstallCycle:
    """One clean-home install with the evidence each step produced."""

    def __init__(self, host: str, executable: str, codex_marketplace_source: str | None):
        self.host = host
        self.executable = executable
        self.codex_marketplace_source = codex_marketplace_source
        self.steps: list[dict[str, str]] = []
        self.inventory: dict[str, str] = {}
        self.temporary_root: Path | None = None
        self.host_home: Path | None = None
        self.environment: dict[str, str] = {}
        self.outputs: dict[str, str] = {}

    def record(self, step: str, status: str, detail: str = "") -> None:
        self.steps.append({"step": step, "status": status, "detail": detail})

    def run(self, name: str, command: Sequence[str]) -> tuple[bool, str]:
        assert self.temporary_root is not None
        command_cwd = self.temporary_root / "command-cwd"
        passed, output = checked(command, env=self.environment, cwd=command_cwd)
        self.outputs[name] = output
        if _created_repository(self.temporary_root):
            self.record(name, "FAIL", "host package check created a repository")
            return False, "host package check created a repository"
        if not passed:
            self.record(name, "FAIL", output or f"failed {' '.join(command)}")
            return False, output or f"failed {' '.join(command)}"
        self.record(name, "PASS")
        return True, output

    def install(self, temporary_root: Path, *, uninstall: bool) -> tuple[bool, str]:
        self.temporary_root = temporary_root
        self.environment = os.environ.copy()
        source = (
            Path(self.codex_marketplace_source).expanduser().resolve()
            if self.host == "codex" and self.codex_marketplace_source
            else _plain_marketplace(temporary_root / "marketplace", self.host)
        )
        verified, detail = verify_plain_marketplace_source(str(source), self.host)
        if not verified:
            self.record("plain marketplace", "FAIL", detail)
            return False, detail
        self.record("plain marketplace", "PASS")
        host_home = temporary_root / "host-home"
        host_home.mkdir()
        self.host_home = host_home
        (temporary_root / "command-cwd").mkdir()
        self.environment[_home_variable(self.host)] = str(host_home)
        self.record("clean host home", "PASS")
        commands = _host_commands(self.host, self.executable, source)

        for name in ("marketplace", "install", "list"):
            passed, output = self.run(name, commands[name])
            if not passed:
                return False, output
        try:
            inventory = _inventory_entry(self.host, self.outputs["list"])
            installed = (
                _codex_installed_path(self.outputs["install"])
                if self.host == "codex"
                else _claude_installed_path(inventory)
            )
            installed = _require_isolated_path(installed, host_home)
            self.inventory = _payload(installed)
            if self.inventory != _payload(PLUGIN_ROOT):
                self.record("inspect installed files", "FAIL", "payload does not match")
                return False, "installed plugin payload does not match the candidate"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.record("inspect installed files", "FAIL", str(exc))
            return False, str(exc)
        self.record(
            "inspect installed files",
            "PASS",
            f"{len(self.inventory)} regular files, exact candidate bytes, no symlinks",
        )
        hook = "hooks/hooks.json" in self.inventory
        self.record(
            "inspect hook trust/state",
            "UNVERIFIED",
            (
                "hook file installed; trust state is host-specific and not read by this script"
                if hook
                else "package ships no hook"
            ),
        )
        if not uninstall:
            return True, "exact candidate installed from a plain marketplace"
        passed, output = self.run("uninstall", commands["uninstall"])
        if not passed:
            return False, output
        passed, output = self.run("list after uninstall", commands["list"])
        if not passed:
            return False, output
        try:
            if not _inventory_absent(self.host, output):
                self.record("verify uninstall", "FAIL", "inventory still lists skiphow")
                return False, "plugin remained installed after uninstall"
        except (ValueError, json.JSONDecodeError) as exc:
            self.record("verify uninstall", "FAIL", str(exc))
            return False, str(exc)
        self.record("verify uninstall", "PASS")
        return True, "exact candidate installed, inspected, and uninstalled from a clean host home"


def isolated_install(
    host: str,
    executable: str,
    *,
    codex_marketplace_source: str | None = None,
) -> tuple[bool, str]:
    """Install the exact candidate with a temporary, empty host configuration."""
    with tempfile.TemporaryDirectory(prefix=f"skiphow-{host}-install-") as temporary:
        cycle = _InstallCycle(host, executable, codex_marketplace_source)
        return cycle.install(Path(temporary), uninstall=False)


def _privacy_safe(text: str, secrets: Sequence[str]) -> str:
    for index, secret in enumerate(secrets):
        if secret:
            text = text.replace(secret, f"<redacted-{index}>")
    return text


def _host_version(executable: str) -> str:
    passed, output = checked([executable, "--version"], timeout=30)
    return output.splitlines()[0] if passed and output else "unknown"


SESSION_STEPS = (
    ("start a clean session", "9.5 step 5"),
    ("verify explicit invocation", "9.5 step 6"),
)


def smoke_install(
    host: str,
    executable: str,
    receipt_dir: Path,
    *,
    codex_marketplace_source: str | None = None,
) -> tuple[bool, str, Path]:
    """Run the clean-install procedure (spec 9.5 steps 1-4, 7-9) and write a receipt.

    Steps 5 and 6, starting a session and verifying explicit invocation, start a
    model and are never run here. The receipt lists them as UNVERIFIED; supply a
    session receipt with --session-receipt to report an observed invocation.
    """
    from datetime import datetime, timezone

    receipt_dir.mkdir(parents=True, exist_ok=True)
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with tempfile.TemporaryDirectory(prefix=f"skiphow-{host}-smoke-") as temporary:
        cycle = _InstallCycle(host, executable, codex_marketplace_source)
        passed, detail = cycle.install(Path(temporary), uninstall=True)
        secrets = [temporary, str(Path(temporary).resolve()), str(Path.home())]
        if codex_marketplace_source:
            secrets.append(str(Path(codex_marketplace_source).expanduser().resolve()))
    for name, reference in SESSION_STEPS:
        cycle.record(name, "UNVERIFIED", f"{reference}: starts a model; not run by this script")
    steps = [
        {key: _privacy_safe(value, secrets) for key, value in step.items()}
        for step in cycle.steps
    ]
    receipt = {
        "schema": "skiphow-clean-install-receipt/1",
        "host": host,
        "host_version": _host_version(executable),
        "package_version": version,
        "date": date,
        "result": "PASS" if passed else "FAIL",
        "detail": _privacy_safe(detail, secrets),
        "steps": steps,
        "installed_files": cycle.inventory,
        "session": {name: "UNVERIFIED" for name, _ in SESSION_STEPS},
    }
    path = receipt_dir / f"{host}-clean-install-{date}.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return passed, _privacy_safe(detail, secrets), path


SESSION_FIELDS = ("explicit_invocation", "implicit_activation", "continuity")


def load_session_receipt(path: Path) -> dict[str, str]:
    """Validate a manual session receipt for spec 9.5 steps 5-6.

    Shape: {"host": "codex"|"claude", "host_version": str, "date": "YYYY-MM-DD",
    "explicit_invocation": "observed"|"unverified", "implicit_activation": ...,
    "continuity": ..., "reference": str}. Only "observed" counts; anything else
    stays UNVERIFIED.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"session receipt is not an object: {path}")
    if value.get("host") not in ("codex", "claude"):
        raise ValueError(f"session receipt names no known host: {path}")
    for key in ("host_version", "date", "reference"):
        if not isinstance(value.get(key), str) or not value[key]:
            raise ValueError(f"session receipt lacks {key}: {path}")
    result = {key: str(value[key]) for key in ("host", "host_version", "date", "reference")}
    for key in SESSION_FIELDS:
        state = value.get(key, "unverified")
        if state not in ("observed", "unverified"):
            raise ValueError(f"session receipt {key} must be observed or unverified: {path}")
        result[key] = state
    return result


MATRIX_CAPABILITIES = (
    "Deterministic package gate",
    "Codex schema validation",
    "Claude schema validation",
    "Clean Codex install",
    "Clean Claude install",
    "Explicit invocation",
    "Implicit activation",
    "Continuity/bootstrap",
    "Behavioral contract suite",
)


def render_matrix(rows: Sequence[tuple[str, str, str]]) -> str:
    """Render the spec 9.3 matrix; every capability keeps its own row and status."""
    names = [row[0] for row in rows]
    if names != list(MATRIX_CAPABILITIES):
        raise ValueError("matrix rows must be exactly the tracked capabilities, in order")
    lines = ["| Capability | Status | Detail |", "| --- | --- | --- |"]
    for capability, status, detail in rows:
        lines.append(f"| {capability} | {status} | {detail.replace('|', '/')} |")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report each host capability separately: the deterministic gate, each "
            "host's schema validation, each host's clean install, and the session "
            "observations. An absent host or an unrun step is UNVERIFIED, never PASS."
        )
    )
    parser.add_argument("--require-codex-validator", action="store_true")
    parser.add_argument("--require-claude", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--require-codex-install", action="store_true")
    parser.add_argument("--require-claude-install", action="store_true")
    parser.add_argument(
        "--codex-marketplace-source",
        help="pre-provisioned plain local marketplace; defaults to a temporary snapshot",
    )
    parser.add_argument(
        "--package-gate",
        action="store_true",
        help="run scripts/check.py and report it as the deterministic package gate row",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run the clean-install procedure (install, inspect, uninstall) per available host",
    )
    parser.add_argument(
        "--receipt-dir",
        help="directory that receives one privacy-safe JSON receipt per smoked host",
    )
    parser.add_argument(
        "--session-receipt",
        action="append",
        default=[],
        help="manual receipt for the session steps of the clean-install procedure",
    )
    parser.add_argument("--matrix-out", help="also write the matrix to this file")
    args = parser.parse_args(argv)
    if args.skip_install and (args.require_codex_install or args.require_claude_install):
        parser.error("--skip-install cannot satisfy --require-codex-install or --require-claude-install")
    if args.smoke and args.skip_install:
        parser.error("--smoke cannot be combined with --skip-install")
    if args.smoke and not args.receipt_dir:
        parser.error("--smoke requires --receipt-dir")

    errors: list[str] = []
    rows: list[tuple[str, str, str]] = []
    codex = shutil.which("codex")
    claude = shutil.which("claude")

    if args.package_gate:
        passed, output = checked([sys.executable, str(ROOT / "scripts/check.py")], timeout=900)
        rows.append(("Deterministic package gate", "PASS" if passed else "FAIL", "scripts/check.py"))
        if not passed:
            errors.append(output or "scripts/check.py failed without output")
    else:
        rows.append(("Deterministic package gate", "UNVERIFIED", "not run; pass --package-gate"))

    validator = codex_validator()
    if validator is None:
        rows.append(("Codex schema validation", "UNVERIFIED", "Codex plugin validator unavailable"))
        if args.require_codex_validator:
            errors.append("Codex plugin validator is unavailable")
    else:
        python, detail = validator_python()
        if python is None:
            rows.append(("Codex schema validation", "UNVERIFIED", detail))
            if args.require_codex_validator:
                errors.append(detail)
        else:
            passed, output = checked([python, str(validator), str(PLUGIN_ROOT)])
            rows.append(("Codex schema validation", "PASS" if passed else "FAIL", "validate_plugin.py"))
            if not passed:
                errors.append(output or "Codex plugin validator failed without output")

    if claude is None:
        rows.append(("Claude schema validation", "UNVERIFIED", "Claude Code unavailable"))
        if args.require_claude:
            errors.append("Claude Code is unavailable")
    else:
        passed, output = checked([claude, "plugin", "validate", "--strict", str(PLUGIN_ROOT)])
        rows.append(("Claude schema validation", "PASS" if passed else "FAIL", "claude plugin validate --strict"))
        if not passed:
            errors.append(output or "Claude plugin validation failed without output")

    for host, executable, required in (
        ("codex", codex, args.require_codex_install),
        ("claude", claude, args.require_claude_install),
    ):
        capability = f"Clean {host.capitalize()} install"
        if args.skip_install:
            rows.append((capability, "UNVERIFIED", "skipped"))
            continue
        if executable is None:
            rows.append((capability, "UNVERIFIED", f"{host} CLI unavailable"))
            if required:
                errors.append(f"{host} is unavailable for isolated installation")
            continue
        source = args.codex_marketplace_source if host == "codex" else None
        if args.smoke:
            passed, output, receipt = smoke_install(
                host, executable, Path(args.receipt_dir), codex_marketplace_source=source
            )
            detail = f"receipt {receipt.name}"
        else:
            passed, output = isolated_install(host, executable, codex_marketplace_source=source)
            detail = "install and inspect; no uninstall (pass --smoke)"
        policy_blocked = host == "codex" and not passed and _codex_policy_block(output)
        status = "PASS" if passed else "UNVERIFIED" if policy_blocked and not required else "FAIL"
        if policy_blocked and status == "UNVERIFIED":
            detail = "managed source policy refused the local marketplace"
        rows.append((capability, status, detail))
        if not passed and (not policy_blocked or required):
            errors.append(output or f"{host} isolated installation failed without output")

    receipts: list[dict[str, str]] = []
    for path in args.session_receipt:
        try:
            receipts.append(load_session_receipt(Path(path)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid session receipt: {exc}")
    for capability, key in (
        ("Explicit invocation", "explicit_invocation"),
        ("Implicit activation", "implicit_activation"),
        ("Continuity/bootstrap", "continuity"),
    ):
        observed = [receipt for receipt in receipts if receipt[key] == "observed"]
        if observed:
            detail = "; ".join(
                f"{r['host']} {r['host_version']} on {r['date']} ({r['reference']})"
                for r in observed
            )
            rows.append((capability, "Observed", detail))
        else:
            rows.append((capability, "UNVERIFIED", "no session receipt; steps 5-6 of the clean-install procedure are manual"))
    rows.append(
        (
            "Behavioral contract suite",
            "UNVERIFIED",
            "never run or implied by CI; the versioned summary is docs/evidence.md",
        )
    )

    matrix = render_matrix(rows)
    print(matrix, end="")
    if args.matrix_out:
        Path(args.matrix_out).write_text(matrix, encoding="utf-8")

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
