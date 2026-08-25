#!/usr/bin/env python3
"""Run deterministic local checks without requiring either supported host."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
from typing import Iterable
from urllib.parse import unquote, urlsplit
import venv


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-dev.txt"


def managed_env_path() -> Path:
    """Keep generated check dependencies outside the repository tree."""
    cache_root = Path(
        os.environ.get(
            "SKIPHOW_CHECK_CACHE_DIR",
            str(Path(tempfile.gettempdir()) / "skiphow-check"),
        )
    )
    repository_key = hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:16]
    python_key = f"python-{sys.version_info.major}.{sys.version_info.minor}"
    return cache_root / repository_key / python_key


MANAGED_ENV = managed_env_path()
DEPENDENCY_STAMP = MANAGED_ENV / ".skiphow-requirements"
PERSONAL_PATH = re.compile(
    r"(?:/(?:Users|home)/[^/\s]+/|"
    + "/"
    + "root/"
    + r"|[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+[\\/]|~/\.(?:codex|claude)(?:/|\b)"
    + r"|\$(?:\{)?HOME(?:\})?[\\/]|%USERPROFILE%[\\/])"
)


def pinned_requirements() -> dict[str, str]:
    """Read the exact development dependency versions used by local checks."""
    result: dict[str, str] = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        name, separator, expected = value.partition("==")
        if not separator or not name or not expected:
            raise ValueError(f"development requirement must pin one exact version: {value}")
        result[name] = expected
    return result


def requirements_satisfied() -> bool:
    """Return whether the current interpreter has every pinned check dependency."""
    try:
        return all(version(name) == expected for name, expected in pinned_requirements().items())
    except PackageNotFoundError:
        return False


def managed_python() -> Path:
    """Return the interpreter path for the repository-managed virtual environment."""
    return MANAGED_ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def bootstrap_dependencies() -> int:
    """Prepare pinned check dependencies and restart this command in the managed env."""
    try:
        fingerprint = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    except OSError as exc:
        print(f"cannot read {REQUIREMENTS.relative_to(ROOT)}: {exc}", file=sys.stderr)
        return 2
    python = managed_python()
    if not python.is_file():
        print("preparing cached environment for repository checks", flush=True)
        try:
            venv.EnvBuilder(with_pip=True).create(MANAGED_ENV)
        except OSError as exc:
            print(f"cannot create {MANAGED_ENV.relative_to(ROOT)}: {exc}", file=sys.stderr)
            return 2
    current_is_managed = Path(sys.executable).resolve() == python.resolve()
    try:
        installed_fingerprint = DEPENDENCY_STAMP.read_text(encoding="utf-8").strip()
    except OSError:
        installed_fingerprint = ""
    if current_is_managed or installed_fingerprint != fingerprint:
        try:
            completed = subprocess.run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "-r",
                    str(REQUIREMENTS),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print("installing check dependencies timed out after 300 seconds", file=sys.stderr)
            return 2
        if completed.returncode:
            print(completed.stdout + completed.stderr, file=sys.stderr)
            return 2
        DEPENDENCY_STAMP.write_text(fingerprint + "\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["SKIPHOW_CHECK_BOOTSTRAPPED"] = "1"
    os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], environment)
    return 2


def checked(
    command: list[str],
    *,
    timeout: int = 120,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    """Run one bounded local command and retain concise failure output."""
    command_environment = os.environ.copy()
    command_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        command_environment.update(env)
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=command_environment,
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
    if result.returncode == 0:
        paths = (ROOT / os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw)
    else:
        ignored = {".git", ".venv", ".pytest_cache", "__pycache__", "build"}
        paths = (
            path
            for path in ROOT.rglob("*")
            if not any(part in ignored or part.endswith(".egg-info") for part in path.parts)
        )
    for path in paths:
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
    import yaml

    errors: list[str] = []
    for path in repository_files({".yml", ".yaml"}):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"invalid YAML {path.relative_to(ROOT)}: {exc}")
    return errors


def validate_markdown_links() -> list[str]:
    from markdown_it import MarkdownIt

    markdown = MarkdownIt("commonmark")
    errors: list[str] = []
    for path in repository_files({".md"}):
        text = path.read_text(encoding="utf-8")
        for token in markdown.parse(text):
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
        ROOT / "src",
        ROOT / "schemas",
        ROOT / "evals",
        ROOT / "docs",
        ROOT / "pyproject.toml",
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
    if not (ROOT / ".git").exists():
        return []
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
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != version:
        errors.append("version mismatch in pyproject.toml")
    package_source = (ROOT / "src/skiphow/__init__.py").read_text(encoding="utf-8")
    if f'__version__ = "{version}"' not in package_source:
        errors.append("version mismatch in src/skiphow/__init__.py")
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
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
    ]
    for command in commands:
        passed, output = checked(command)
        if not passed:
            errors.append(f"failed {' '.join(command)}: {output}")
    return errors + validate_diff(base)


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if not requirements_satisfied():
        if "--offline" in raw_args:
            print(
                "repository checks UNVERIFIED: pinned dependencies are absent from the "
                f"prepared cache at {MANAGED_ENV}; run scripts/check.py --prepare-only while online",
                file=sys.stderr,
            )
            return 2
        if os.environ.get("SKIPHOW_CHECK_BOOTSTRAPPED") == "1":
            print("managed check environment does not satisfy requirements-dev.txt", file=sys.stderr)
            return 2
        return bootstrap_dependencies()
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="base commit for candidate-diff validation")
    parser.add_argument(
        "--pytest",
        nargs=argparse.REMAINDER,
        help="run pytest with the remaining arguments inside the managed environment",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="prepare the managed environment without running repository checks",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="never bootstrap dependencies from the network; report missing cache as UNVERIFIED",
    )
    args = parser.parse_args(raw_args)
    if args.prepare_only:
        print(sys.executable)
        return 0
    if args.pytest is not None:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    *args.pytest,
                ],
                cwd=ROOT,
                env=environment,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print("focused pytest run timed out after 120 seconds", file=sys.stderr)
            return 2
        return completed.returncode
    errors = offline_checks(args.base)
    if errors:
        print("repository checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("local deterministic checks passed")
    print("Codex official validator: UNVERIFIED (run scripts/check_hosts.py)")
    print("Claude package validation: UNVERIFIED (run scripts/check_hosts.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
