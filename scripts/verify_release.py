#!/usr/bin/env python3
"""Run SkipHow's deterministic release checks, with opt-in host smoke checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
LOCAL_LINK = re.compile(r"(?<!!)\[[^]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
FORBIDDEN_PORTABLE_TEXT = ("/" + "Users/", "~/" + ".codex", "~/" + ".claude")


def checked(command: list[str], *, timeout: int = 120) -> tuple[bool, str]:
    """Run one bounded command and retain concise evidence for the release log."""
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
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
    ignored = {".git", ".venv", "__pycache__"}
    for path in ROOT.rglob("*"):
        if any(part in ignored for part in path.parts) or not path.is_file():
            continue
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


def validate_yaml_guard() -> list[str]:
    """Check the portable YAML subset used for metadata and GitHub Actions files."""
    errors: list[str] = []
    for path in repository_files({".yml", ".yaml"}):
        lines = path.read_text(encoding="utf-8").splitlines()
        if any("\t" in line for line in lines):
            errors.append(f"invalid YAML indentation in {path.relative_to(ROOT)}: tabs are not allowed")
        if not any(line and not line.lstrip().startswith("#") for line in lines):
            errors.append(f"empty YAML document {path.relative_to(ROOT)}")
        for number, line in enumerate(lines, start=1):
            content = line.strip()
            if content and not content.startswith(("#", "- ")) and ":" not in content:
                errors.append(f"invalid YAML mapping at {path.relative_to(ROOT)}:{number}")
    return errors


def validate_markdown_links() -> list[str]:
    errors: list[str] = []
    for path in repository_files({".md"}):
        text = path.read_text(encoding="utf-8")
        for target in LOCAL_LINK.findall(text):
            if target.startswith(("#", "http://", "https://", "mailto:", "<")):
                continue
            target_path = target.split("#", 1)[0]
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
    roots = [ROOT / "plugins", ROOT / "adapters", ROOT / "scripts", ROOT / "docs", ROOT / "README.md"]
    for source in roots:
        paths = [source] if source.is_file() else source.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".json", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_PORTABLE_TEXT:
                if forbidden in text:
                    errors.append(f"non-portable text {forbidden!r} in {path.relative_to(ROOT)}")
    return errors


def offline_checks() -> list[str]:
    errors = validate_json() + validate_yaml_guard() + validate_markdown_links() + source_scan()
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        passed, output = checked(command)
        if not passed:
            errors.append(f"failed {' '.join(command)}: {output}")
    return errors


def host_checks() -> list[str]:
    """Run opt-in, ephemeral host checks. Missing hosts are explicitly skipped."""
    errors: list[str] = []
    head_ok, head = checked(["git", "rev-parse", "HEAD"])
    print(f"HEAD: {head if head_ok else 'unavailable: ' + head}")
    for executable in ("codex", "claude", "gh"):
        found = shutil.which(executable)
        if not found:
            print(f"SKIP {executable}: not installed")
            continue
        passed, output = checked([found, "--version"])
        if not passed:
            errors.append(f"{executable} version check failed: {output}")
            continue
        print(f"TOOL {executable}: {output.splitlines()[0]}")
    codex = shutil.which("codex")
    if codex:
        with tempfile.TemporaryDirectory(prefix="skiphow-codex-smoke-") as temporary:
            schema = Path(temporary) / "schema.json"
            output = Path(temporary) / "response.json"
            schema.write_text('{"type":"object","required":["ok"],"properties":{"ok":{"type":"boolean"}}}', encoding="utf-8")
            passed, detail = checked([
                codex, "exec", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check",
                "--output-schema", str(schema), "--output-last-message", str(output),
                "Return JSON with ok set to true.",
            ])
            if not passed:
                errors.append(f"Codex ephemeral structured smoke failed: {detail}")
            else:
                print("PASS Codex ephemeral structured smoke")
    claude = shutil.which("claude")
    if claude:
        passed, detail = checked([
            claude, "--plugin-dir", str(ROOT), "--print", "--tools", "", "Reply with SKIPHOW_SMOKE."
        ])
        if not passed:
            errors.append(f"Claude local-plugin smoke failed: {detail}")
        else:
            print("PASS Claude local-plugin smoke")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", action="store_true", help="run paid host smoke checks when hosts are installed")
    args = parser.parse_args(argv)
    errors = offline_checks()
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
