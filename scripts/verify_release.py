#!/usr/bin/env python3
"""Run SkipHow's deterministic release checks, with opt-in host smoke checks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import yaml


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = MarkdownIt("commonmark")
PERSONAL_PATH = re.compile(
    r"(?:/(?:Users|home)/[^/\s]+/|"
    + "/"
    + "root/"
    + r"|[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+[\\/]|~/\.(?:codex|claude)(?:/|\b)"
    + r"|\$(?:\{)?HOME(?:\})?[\\/]|%USERPROFILE%[\\/])"
)


def checked(
    command: list[str],
    *,
    timeout: int = 120,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Run one bounded command and retain concise evidence for the release log."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def repository_files(suffixes: Iterable[str]) -> Iterable[Path]:
    """Yield candidate-owned files from Git, excluding ambient workspace state."""
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot enumerate candidate files: {detail}")
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = ROOT / os.fsdecode(raw_path)
        if path.suffix.lower() in suffixes:
            yield path


def validate_json() -> list[str]:
    errors: list[str] = []
    for path in repository_files({".json"}):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    return errors


def validate_yaml() -> list[str]:
    """Parse every YAML document with the repository's pinned parser."""
    errors: list[str] = []
    for path in repository_files({".yml", ".yaml"}):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"invalid YAML {path.relative_to(ROOT)}: {exc}")
    return errors


def validate_markdown_links() -> list[str]:
    errors: list[str] = []
    for path in repository_files({".md"}):
        text = path.read_text(encoding="utf-8")
        for token in MARKDOWN.parse(text):
            for child in token.children or ():
                if child.type != "link_open":
                    continue
                target = child.attrGet("href")
                if not target:
                    continue
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or (not parsed.path and parsed.fragment):
                    continue
                target_path = unquote(parsed.path)
                if not target_path:
                    continue
                candidate = (path.parent / target_path).resolve()
                try:
                    candidate.relative_to(ROOT)
                except ValueError:
                    errors.append(f"link escapes repository: {path.relative_to(ROOT)} -> {target}")
                    continue
                if not candidate.exists():
                    errors.append(f"broken local link: {path.relative_to(ROOT)} -> {target}")
    return errors


def source_scan() -> list[str]:
    errors: list[str] = []
    roots = [
        ROOT / ".agents",
        ROOT / ".claude-plugin",
        ROOT / "plugins",
        ROOT / "adapters",
        ROOT / "scripts",
        ROOT / "docs",
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
    ]
    for path in repository_files({".md", ".py", ".json", ".yaml", ".yml"}):
        if not any(path == source or path.is_relative_to(source) for source in roots):
            continue
        text = path.read_text(encoding="utf-8")
        for match in PERSONAL_PATH.finditer(text):
            errors.append(
                f"non-portable personal path {match.group(0)!r} in {path.relative_to(ROOT)}"
            )
    return errors


def validate_diff(base: str | None) -> list[str]:
    """Check working changes and the committed candidate diff for whitespace errors."""
    errors: list[str] = []
    commands = [["git", "diff", "--check"]]
    if base:
        commands.append(["git", "diff", "--check", base, "HEAD"])
    for command in commands:
        passed, output = checked(command)
        if not passed:
            errors.append(f"failed {' '.join(command)}: {output}")
    return errors


def bundled_codex_plugin_validator() -> Path | None:
    """Find the plugin validator supplied by the active Codex runtime."""
    configured = os.environ.get("CODEX_PLUGIN_VALIDATOR")
    if configured:
        validator = Path(configured).expanduser().resolve()
        return validator if validator.is_file() else None
    codex_home = os.environ.get("CODEX_HOME")
    if not codex_home:
        return None
    validator = (
        Path(codex_home)
        / "skills"
        / ".system"
        / "plugin-creator"
        / "scripts"
        / "validate_plugin.py"
    )
    return validator if validator.is_file() else None


def validate_codex_plugin() -> list[str]:
    """Validate the distributable Codex plugin with the bundled validator."""
    validator = bundled_codex_plugin_validator()
    if validator is None:
        return [
            "Codex plugin validator is unavailable; run release verification from a Codex runtime "
            "that bundles plugin-creator"
        ]
    command = [sys.executable, str(validator), str(ROOT / "plugins" / "skiphow")]
    passed, output = checked(command)
    if passed:
        return []
    detail = output or "validator exited without output"
    return [f"Codex plugin validation failed: {detail}"]


def offline_checks(base: str | None = None) -> list[str]:
    errors = (
        validate_json()
        + validate_yaml()
        + validate_markdown_links()
        + source_scan()
        + validate_codex_plugin()
    )
    commands = [
        [sys.executable, "scripts/run_codex_evals.py"],
        [sys.executable, "scripts/run_claude_evals.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    ]
    for command in commands:
        passed, output = checked(command)
        if not passed:
            errors.append(f"failed {' '.join(command)}: {output}")
    return errors + validate_diff(base)


def host_checks() -> list[str]:
    """Install the exact candidate in isolated host homes and run smoke checks."""
    errors: list[str] = []
    head_ok, head = checked(["git", "rev-parse", "HEAD"])
    print(f"HEAD: {head if head_ok else 'unavailable: ' + head}")
    clean_ok, dirty = checked(["git", "status", "--porcelain"])
    if not clean_ok or dirty:
        errors.append("host verification requires a clean exact candidate commit")
    for executable in ("codex", "claude"):
        found = shutil.which(executable)
        if not found:
            errors.append(f"{executable} is not installed; host support is unverified")
            continue
        passed, output = checked([found, "--version"])
        if not passed:
            errors.append(f"{executable} version check failed: {output}")
            continue
        print(f"TOOL {executable}: {output.splitlines()[0]}")
    with tempfile.TemporaryDirectory(prefix="skiphow-host-smoke-") as temporary:
        temporary_path = Path(temporary)
        codex = shutil.which("codex")
        if codex:
            codex_home = temporary_path / "codex-home"
            codex_home.mkdir()
            codex_env = os.environ.copy()
            codex_env["CODEX_HOME"] = str(codex_home)
            for command, label in (
                ([codex, "plugin", "marketplace", "add", str(ROOT), "--json"], "Codex marketplace discovery"),
                ([codex, "plugin", "add", "skiphow@skiphow", "--json"], "Codex plugin installation"),
                ([codex, "plugin", "list", "--json"], "Codex plugin listing"),
            ):
                passed, detail = checked(command, env=codex_env)
                if not passed or (label == "Codex plugin listing" and "skiphow" not in detail):
                    errors.append(f"{label} failed: {detail}")
                    break
            else:
                print("PASS Codex isolated marketplace installation")

        claude = shutil.which("claude")
        if claude:
            passed, detail = checked([claude, "plugin", "validate", "--strict", str(ROOT)])
            if not passed:
                errors.append(f"Claude strict plugin validation failed: {detail}")
            else:
                print("PASS Claude strict plugin validation")
            claude_home = temporary_path / "claude-home"
            claude_home.mkdir()
            claude_env = os.environ.copy()
            claude_env["CLAUDE_CONFIG_DIR"] = str(claude_home)
            for command, label in (
                ([claude, "plugin", "marketplace", "add", str(ROOT), "--scope", "user"], "Claude marketplace discovery"),
                ([claude, "plugin", "install", "skiphow@skiphow", "--scope", "user", "--yes"], "Claude plugin installation"),
                ([claude, "plugin", "list"], "Claude plugin listing"),
            ):
                passed, detail = checked(command, env=claude_env)
                if not passed or (label == "Claude plugin listing" and "skiphow" not in detail):
                    errors.append(f"{label} failed: {detail}")
                    break
            else:
                print("PASS Claude isolated marketplace installation")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="base commit for candidate-diff validation")
    parser.add_argument("--host", action="store_true", help="run isolated host installation checks")
    args = parser.parse_args(argv)
    errors = offline_checks(args.base)
    if args.host:
        errors.extend(host_checks())
    if errors:
        print("release verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("release verification passed" + (" with requested host checks" if args.host else " offline"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
