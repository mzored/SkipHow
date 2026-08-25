#!/usr/bin/env python3
"""Run deterministic local checks without requiring either supported host."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
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


def repository_files(suffixes: Iterable[str] | None = None) -> Iterable[Path]:
    """Yield tracked and new non-ignored files reported by Git."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot enumerate repository files: {detail}")
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = ROOT / os.fsdecode(raw_path)
        if not path.is_file():
            continue
        if suffixes is None or path.suffix.lower() in suffixes:
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
    for path in repository_files():
        if not any(path == source or path.is_relative_to(source) for source in roots):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            errors.append(f"cannot read distributable source {path.relative_to(ROOT)}: {exc}")
            continue
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


def validate_version() -> list[str]:
    """Check every release record against the single VERSION source."""
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    errors: list[str] = []
    records = {
        "plugins/skiphow/.codex-plugin/plugin.json": ("version",),
        ".claude-plugin/plugin.json": ("version",),
        ".claude-plugin/marketplace.json": ("metadata", "version"),
    }
    for relative, keys in records.items():
        value: object = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        for key in keys:
            value = value[key]  # type: ignore[index]
        if value != version:
            errors.append(f"version mismatch in {relative}: {value!r} != {version!r}")
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    if marketplace["plugins"][0]["version"] != version:
        errors.append("version mismatch in .claude-plugin/marketplace.json plugin entry")
    if f"## {version}" not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
        errors.append(f"CHANGELOG.md has no {version} release heading")
    if f"| {version.rsplit('.', 1)[0]}.x | Yes |" not in (
        ROOT / "SECURITY.md"
    ).read_text(encoding="utf-8"):
        errors.append("SECURITY.md does not support the current release line")
    return errors


def validate_plugin_static() -> list[str]:
    """Check public metadata and the one-skill package shape locally."""
    manifest = json.loads(
        (ROOT / "plugins/skiphow/.codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    interface = manifest.get("interface") or {}
    prompts = interface.get("defaultPrompt") or []
    errors: list[str] = []
    if len(str(interface.get("shortDescription") or "")) > 30:
        errors.append("Codex shortDescription exceeds 30 characters")
    if not isinstance(prompts, list) or len(prompts) > 3:
        errors.append("Codex defaultPrompt must contain at most three prompts")
    skill_manifests = sorted((ROOT / "plugins/skiphow/skills").glob("*/SKILL.md"))
    if [path.parent.name for path in skill_manifests] != ["skiphow"]:
        errors.append("only plugins/skiphow/skills/skiphow may be public")
    if any((ROOT / "plugins/skiphow/hooks").glob("*.json")):
        errors.append("default package must not include lifecycle hooks")
    return errors


def offline_checks(base: str | None = None) -> list[str]:
    errors = (
        validate_json()
        + validate_yaml()
        + validate_markdown_links()
        + source_scan()
        + validate_version()
        + validate_plugin_static()
    )
    context_budget = [sys.executable, "scripts/context_budget.py", "--check"]
    if base:
        context_budget.extend(["--base", base])
    commands = [
        context_budget,
        [sys.executable, "scripts/run_codex_evals.py"],
        [sys.executable, "scripts/run_claude_evals.py"],
        [sys.executable, "scripts/run_outcome_evals.py"],
        [sys.executable, "-m", "pytest", "-q"],
    ]
    for command in commands:
        passed, output = checked(command)
        if not passed:
            errors.append(f"failed {' '.join(command)}: {output}")
    return errors + validate_diff(base)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="base commit for candidate-diff validation")
    args = parser.parse_args(argv)
    errors = offline_checks(args.base)
    if errors:
        print("release verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("local deterministic checks passed")
    print("Codex official validator: UNVERIFIED (run scripts/check_hosts.py)")
    print("Claude package validation: UNVERIFIED (run scripts/check_hosts.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
