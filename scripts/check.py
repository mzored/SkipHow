#!/usr/bin/env python3
"""Run deterministic checks for the portable SkipHow plugin."""

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
from typing import Iterable
from urllib.parse import unquote, urlsplit
import venv


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins/skiphow"
SKILL_ROOT = PLUGIN_ROOT / "skills/skiphow"
CANONICAL_SKILL = SKILL_ROOT / "SKILL.md"
REQUIREMENTS = ROOT / "requirements-dev.txt"
REQUIRED_REFERENCES = frozenset(
    {
        "decision.md",
        "delivery.md",
        "diagnosis.md",
        "engineering.md",
        "github.md",
        "intake.md",
        "long-work.md",
        "methods/conflicts.md",
        "methods/design.md",
        "methods/prototype.md",
        "methods/review.md",
        "methods/testing.md",
        "model-routing.md",
    }
)
REMOVED_RUNTIME_PATHS = (
    ROOT / "src/skiphow",
    ROOT / "schemas",
    ROOT / "pyproject.toml",
    ROOT / "plugins/skiphow/scripts",
    ROOT / "adapters/claude",
    ROOT / ".claude-plugin/plugin.json",
)
PERSONAL_PATH = re.compile(
    r"(?:/(?:Users|home)/[^/\s]+/|"
    + "/"
    + "root/"
    + r"|[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+[\\/]"
    + r"|~/\.(?:codex|claude)(?:/|\b)|\$(?:\{)?HOME(?:\})?[\\/]"
    + r"|%USERPROFILE%[\\/])"
)
CONCRETE_MODEL_ID = re.compile(
    r"\b(?:gpt-\d[\w.-]*|claude-(?:\d|opus|sonnet|haiku)[\w.-]*|"
    r"gemini-\d[\w.-]*|llama-\d[\w.-]*|"
    r"mistral-(?:\d|small|medium|large)[\w.-]*|o[1-9](?:-[\w.-]+)?)\b",
    re.IGNORECASE,
)


def managed_env_path() -> Path:
    """Keep check dependencies outside the repository."""
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


def pinned_requirements() -> dict[str, str]:
    """Read the exact versions used by local checks."""
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
    """Return whether this interpreter has every pinned check dependency."""
    try:
        return all(version(name) == expected for name, expected in pinned_requirements().items())
    except PackageNotFoundError:
        return False


def managed_python() -> Path:
    return MANAGED_ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def bootstrap_dependencies() -> int:
    """Prepare pinned dependencies outside the checkout, then restart this command."""
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
            print(f"cannot create check environment: {exc}", file=sys.stderr)
            return 2
    try:
        installed_fingerprint = DEPENDENCY_STAMP.read_text(encoding="utf-8").strip()
    except OSError:
        installed_fingerprint = ""
    current_is_managed = Path(sys.executable).resolve() == python.resolve()
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
    """Run one bounded command without leaving Python bytecode in the checkout."""
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
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def repository_files(suffixes: Iterable[str] | None = None) -> Iterable[Path]:
    """Yield tracked and new non-ignored files, with a fallback outside Git."""
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
        if path.is_file() and (suffixes is None or path.suffix.lower() in suffixes):
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
    import yaml

    errors: list[str] = []
    for path in repository_files({".yml", ".yaml"}):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"invalid YAML {path.relative_to(ROOT)}: {exc}")
    return errors


def markdown_targets(path: Path) -> list[str]:
    """Return link destinations parsed as CommonMark."""
    from markdown_it import MarkdownIt

    result: list[str] = []
    for token in MarkdownIt("commonmark").parse(path.read_text(encoding="utf-8")):
        for child in token.children or ():
            if child.type == "link_open" and child.attrGet("href"):
                result.append(child.attrGet("href"))
    return result


def local_link(path: Path, target: str) -> Path | None:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or (not parsed.path and parsed.fragment):
        return None
    target_path = unquote(parsed.path)
    return (path.parent / target_path).resolve() if target_path else None


def validate_markdown_links() -> list[str]:
    errors: list[str] = []
    for path in repository_files({".md"}):
        try:
            targets = markdown_targets(path)
        except OSError as exc:
            errors.append(f"cannot read Markdown {path.relative_to(ROOT)}: {exc}")
            continue
        for target in targets:
            candidate = local_link(path, target)
            if candidate is None:
                continue
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                errors.append(f"link escapes repository: {path.relative_to(ROOT)} -> {target}")
                continue
            if not candidate.exists():
                errors.append(f"broken local link: {path.relative_to(ROOT)} -> {target}")
    return errors


def portability_scan() -> list[str]:
    """Reject personal paths from shipped files and public documentation."""
    roots = (
        PLUGIN_ROOT,
        ROOT / ".agents/plugins/marketplace.json",
        ROOT / ".claude-plugin/marketplace.json",
        ROOT / "docs",
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
    )
    errors: list[str] = []
    for path in repository_files():
        if not any(path == root or path.is_relative_to(root) for root in roots):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            errors.append(f"cannot read shipped file {path.relative_to(ROOT)}: {exc}")
            continue
        for match in PERSONAL_PATH.finditer(text):
            errors.append(f"personal path {match.group(0)!r} in {path.relative_to(ROOT)}")
    return errors


def load_json(relative: str) -> dict[str, object]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return value


def validate_version() -> list[str]:
    """Keep release metadata aligned with the single VERSION file."""
    release = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    errors: list[str] = []
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", release):
        errors.append(f"VERSION must be a stable semantic version: {release!r}")
    records = {
        "plugins/skiphow/.codex-plugin/plugin.json": ("version",),
        "plugins/skiphow/.claude-plugin/plugin.json": ("version",),
    }
    for relative, keys in records.items():
        value: object = load_json(relative)
        for key in keys:
            value = value[key]  # type: ignore[index]
        if value != release:
            errors.append(f"version mismatch in {relative}: {value!r} != {release!r}")
    marketplace = load_json(".claude-plugin/marketplace.json")
    plugins = marketplace.get("plugins")
    plugin_entry = plugins[0] if isinstance(plugins, list) and plugins else {}
    if isinstance(plugin_entry, dict) and "version" in plugin_entry:
        errors.append("Claude marketplace must defer plugin version to plugin.json")
    metadata = marketplace.get("metadata")
    if isinstance(metadata, dict) and "version" in metadata:
        errors.append("Claude marketplace must not keep a legacy duplicate version")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"^## {re.escape(release)} \(\d{{4}}-\d{{2}}-\d{{2}}\)$", changelog, re.MULTILINE):
        errors.append(f"CHANGELOG.md has no {release} release heading")
    if f"| {release.rsplit('.', 1)[0]}.x | Yes |" not in (
        ROOT / "SECURITY.md"
    ).read_text(encoding="utf-8"):
        errors.append(f"SECURITY.md does not support {release.rsplit('.', 1)[0]}.x")
    return errors


def validate_release_version_change(base: str | None) -> list[str]:
    """Require a monotonic version bump whenever the packaged plugin changes."""
    if not base or not (ROOT / ".git").exists():
        return []
    passed, changed = checked(["git", "diff", "--name-only", f"{base}...HEAD"])
    if not passed:
        return [f"cannot inspect release diff from {base}: {changed}"]
    if not any(path == "plugins/skiphow" or path.startswith("plugins/skiphow/") for path in changed.splitlines()):
        return []
    passed, previous = checked(["git", "show", f"{base}:VERSION"])
    if not passed:
        return [f"cannot read VERSION at {base}: {previous}"]
    current = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if previous.strip() == current:
        return ["plugins/skiphow changed without a VERSION bump"]
    previous_match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", previous.strip())
    current_match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", current)
    if previous_match is None or current_match is None:
        return ["cannot compare invalid stable semantic versions"]
    previous_parts = tuple(int(value) for value in previous_match.groups())
    current_parts = tuple(int(value) for value in current_match.groups())
    if current_parts <= previous_parts:
        return [f"plugin version must increase from {previous.strip()} to a later stable version"]
    return []


def validate_runtime_removal() -> list[str]:
    """Prevent the retired runner and policy copies from returning unnoticed."""
    return [
        f"retired runtime path still exists: {path.relative_to(ROOT)}"
        for path in REMOVED_RUNTIME_PATHS
        if path.is_file()
        or (path.is_dir() and any(item.is_file() for item in path.rglob("*")))
    ]


def model_id_scan(paths: Iterable[Path] | None = None) -> list[str]:
    """Keep provider model IDs out of portable skill policy."""
    candidates = list(paths) if paths is not None else [
        CANONICAL_SKILL,
        *sorted((SKILL_ROOT / "references").rglob("*.md")),
    ]
    errors: list[str] = []
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot scan model policy {path}: {exc}")
            continue
        for match in CONCRETE_MODEL_ID.finditer(content):
            try:
                relative = path.relative_to(ROOT)
            except ValueError:
                relative = path
            errors.append(f"concrete model ID {match.group(0)!r} in {relative}")
    return errors


def validate_plugin_static() -> list[str]:
    """Check the one-skill package shared by Codex and Claude."""
    errors: list[str] = []
    codex_path = PLUGIN_ROOT / ".codex-plugin/plugin.json"
    claude_path = PLUGIN_ROOT / ".claude-plugin/plugin.json"
    for path in (codex_path, claude_path, CANONICAL_SKILL):
        if not path.is_file():
            errors.append(f"missing plugin file: {path.relative_to(ROOT)}")
    if errors:
        return errors

    codex = json.loads(codex_path.read_text(encoding="utf-8"))
    claude = json.loads(claude_path.read_text(encoding="utf-8"))
    for host, manifest in (("Codex", codex), ("Claude", claude)):
        if not isinstance(manifest, dict) or manifest.get("name") != "skiphow":
            errors.append(f"{host} manifest must describe the skiphow plugin")
            continue
        if manifest.get("skills") != "./skills/":
            errors.append(f"{host} manifest must load ./skills/")
        if "hooks" in manifest:
            errors.append(f"{host} manifest must not declare hooks")

    public_skills = sorted(PLUGIN_ROOT.rglob("SKILL.md"))
    if public_skills != [CANONICAL_SKILL]:
        found = ", ".join(path.relative_to(PLUGIN_ROOT).as_posix() for path in public_skills)
        errors.append(f"plugin must contain one canonical SKILL.md, found: {found or 'none'}")

    top_level = {
        path.name
        for path in PLUGIN_ROOT.iterdir()
        if path.is_file() or any(child.is_file() for child in path.rglob("*"))
    }
    unexpected = sorted(top_level - {".claude-plugin", ".codex-plugin", "skills", "LICENSE"})
    if unexpected:
        errors.append(f"plugin has unexpected top-level entries: {', '.join(unexpected)}")
    package_license = PLUGIN_ROOT / "LICENSE"
    if not package_license.is_file() or package_license.read_bytes() != (ROOT / "LICENSE").read_bytes():
        errors.append("plugin must include the repository MIT license")

    references = SKILL_ROOT / "references"
    actual_references = {
        path.relative_to(references).as_posix()
        for path in references.rglob("*.md")
        if path.is_file()
    } if references.is_dir() else set()
    if actual_references != REQUIRED_REFERENCES:
        missing = sorted(REQUIRED_REFERENCES - actual_references)
        extra = sorted(actual_references - REQUIRED_REFERENCES)
        if missing:
            errors.append(f"missing skill references: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected skill references: {', '.join(extra)}")
    errors.extend(model_id_scan())

    linked: set[Path] = set()
    pending = [CANONICAL_SKILL]
    seen: set[Path] = set()
    while pending:
        source = pending.pop()
        if source in seen:
            continue
        seen.add(source)
        for target in markdown_targets(source):
            candidate = local_link(source, target)
            if candidate is None or candidate.suffix != ".md":
                continue
            try:
                candidate.relative_to(SKILL_ROOT)
            except ValueError:
                continue
            if candidate != CANONICAL_SKILL:
                linked.add(candidate)
                pending.append(candidate)
    for reference in sorted(REQUIRED_REFERENCES):
        expected = (references / reference).resolve()
        if expected not in linked:
            errors.append(f"canonical skill does not link references/{reference}")
    orphaned = sorted(
        path.relative_to(references).as_posix()
        for path in references.rglob("*.md")
        if path.resolve() not in linked
    )
    if orphaned:
        errors.append(f"orphaned skill references: {', '.join(orphaned)}")

    hook_paths = [path for path in PLUGIN_ROOT.rglob("*") if "hooks" in path.parts]
    if hook_paths:
        errors.append("plugin package must not include hooks")

    try:
        codex_marketplace = load_json(".agents/plugins/marketplace.json")
        codex_source = codex_marketplace["plugins"][0]["source"]  # type: ignore[index]
        if codex_source != {"source": "local", "path": "./plugins/skiphow"}:
            errors.append("Codex marketplace must package only plugins/skiphow")
    except (KeyError, IndexError, TypeError, ValueError, OSError, json.JSONDecodeError):
        errors.append("Codex marketplace does not contain the skiphow package")
    try:
        claude_marketplace = load_json(".claude-plugin/marketplace.json")
        if claude_marketplace["plugins"][0]["source"] != "./plugins/skiphow":  # type: ignore[index]
            errors.append("Claude marketplace must package only plugins/skiphow")
    except (KeyError, IndexError, TypeError, ValueError, OSError, json.JSONDecodeError):
        errors.append("Claude marketplace does not contain the skiphow package")
    return errors


def validate_diff(base: str | None) -> list[str]:
    if not (ROOT / ".git").exists():
        return []
    commands = [["git", "diff", "--check"]]
    if base:
        commands.append(["git", "diff", "--check", base, "HEAD"])
    errors: list[str] = []
    for command in commands:
        passed, output = checked(command)
        if not passed:
            errors.append(f"failed {' '.join(command)}: {output}")
    return errors


def offline_checks(base: str | None = None) -> list[str]:
    errors = (
        validate_json()
        + validate_yaml()
        + validate_markdown_links()
        + portability_scan()
        + validate_version()
        + validate_runtime_removal()
        + validate_plugin_static()
        + validate_release_version_change(base)
    )
    commands = [
        [sys.executable, "scripts/context_budget.py", "--check"],
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
                f"prepared cache at {MANAGED_ENV}",
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
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(raw_args)
    if args.prepare_only:
        print(sys.executable)
        return 0
    if args.pytest is not None:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args.pytest],
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
    print("Host package checks: UNVERIFIED (run scripts/check_hosts.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
