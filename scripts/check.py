#!/usr/bin/env python3
"""Run deterministic checks for the portable SkipHow plugin."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Iterable
from urllib.parse import unquote, urlsplit
import venv


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins/skiphow"
REQUIREMENTS = ROOT / "requirements-dev.txt"
PERSONAL_PATH = re.compile(
    r"(?:(?<![\w.])/(?:Users|home)/[^/\s]+/?|"
    + "/"
    + "root/"
    + r"|[A-Za-z]:[\\/]+(?i:users)[\\/]+[^\\/\s]+[\\/]?"
    + r"|~/\.(?:codex|claude)(?:/|\b)|\$(?:\{)?HOME(?:\})?[\\/]"
    + r"|%USERPROFILE%[\\/])"
)
CONCRETE_MODEL_ID = re.compile(
    # A provider name, any number of family words, then a version component. Naming the
    # families instead would age: `claude-fable-5` and `claude-future-5` both slipped past
    # an enumerated list, and the invariant is no versioned ID at all.
    r"\b(?:(?:claude|gpt|gemini|llama|mistral|grok|qwen|deepseek)(?:-[a-z]+)*-?\d[\w.-]*|"
    r"mistral-(?:small|medium|large)[\w.-]*|o[1-9](?:-[\w.-]+)?|"
    r"(?:opus|sonnet|haiku|fable)-\d[\w.-]*)\b",
    re.IGNORECASE,
)
CONTINUITY_GROUPS = frozenset(
    {
        frozenset({"startup", "clear"}),
        frozenset({"compact", "resume"}),
    }
)
CONTINUITY_MATCHERS = frozenset().union(*CONTINUITY_GROUPS)
CORE_PACKAGE_FILES = frozenset(
    {
        "LICENSE",
        "SOURCES.json",
        "THIRD_PARTY_NOTICES.md",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "hooks/hooks.json",
        "skills/skiphow/SKILL.md",
    }
)
ALLOWED_PLUGIN_TOP_LEVEL = frozenset(
    {
        ".claude-plugin",
        ".codex-plugin",
        "hooks",
        "skills",
        "LICENSE",
        "SOURCES.json",
        "THIRD_PARTY_NOTICES.md",
    }
)
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AGENT_SKILL_FIELDS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)
MIT_PERMISSION_PARAGRAPH = """\
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:"""
MIT_WARRANTY_PARAGRAPH = """\
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
HOOK_COMMAND = re.compile(
    r"""^sh -c 'printf "%s\\n" "[^"'$`\\]+"; """
    r"""if \[ -f \.skiphow/handoff\.md \]; then printf "%s\\n" "[^"'$`\\]+"; fi; exit 0'$"""
)
HOOK_NOTICE_COMMAND = re.compile(
    r'''^sh -c 'printf "%s\\n" "[^"'$`\\]+"; exit 0'$'''
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
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None
    if result is not None and result.returncode == 0:
        paths = (ROOT / os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw)
    else:
        ignored = {".git", ".venv", ".pytest_cache", "__pycache__", "build"}
        paths = (
            path
            for path in ROOT.rglob("*")
            if not any(
                part in ignored or part.endswith(".egg-info")
                for part in path.relative_to(ROOT).parts
            )
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


def markdown_targets(path: Path, *, include_images: bool = True) -> list[str]:
    """Return resource destinations parsed as CommonMark."""
    from markdown_it import MarkdownIt

    result: list[str] = []
    for token in MarkdownIt("commonmark").parse(path.read_text(encoding="utf-8")):
        for child in token.children or ():
            if child.type == "link_open" and child.attrGet("href"):
                result.append(child.attrGet("href"))
            elif include_images and child.type == "image" and child.attrGet("src"):
                result.append(child.attrGet("src"))
    return result


def local_link(path: Path, target: str) -> Path | None:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or (not parsed.path and parsed.fragment):
        return None
    target_path = unquote(parsed.path)
    return (path.parent / target_path).resolve() if target_path else None


def skill_frontmatter(path: Path) -> tuple[dict[str, object] | None, str | None]:
    """Read the metadata block required by the Agent Skills specification."""
    import yaml

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, str(exc)
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if match is None:
        return None, "missing YAML frontmatter"
    try:
        value = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter: {exc}"
    if not isinstance(value, dict):
        return None, "frontmatter must be a mapping"
    if not text[match.end():].strip():
        return None, "skill body must not be empty"
    return value, None


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
    try:
        return _validate_version()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot validate release metadata: {exc}"]


def _validate_version() -> list[str]:
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
    released = re.findall(r"^## (\S+) \(\d{4}-\d{2}-\d{2}\)$", changelog, re.MULTILINE)
    if not released:
        errors.append("CHANGELOG.md has no dated release heading")
    elif released[0] != release:
        errors.append(f"CHANGELOG.md leads with {released[0]}, not the released {release}")
    if f"| {release.rsplit('.', 1)[0]}.x | Yes |" not in (
        ROOT / "SECURITY.md"
    ).read_text(encoding="utf-8"):
        errors.append(f"SECURITY.md does not support {release.rsplit('.', 1)[0]}.x")
    return errors


def validate_release_version_change(base: str | None) -> list[str]:
    """Require a monotonic version bump whenever the packaged plugin changes."""
    if not (ROOT / ".git").exists():
        return []
    changed_paths: set[str] = set()
    if base:
        passed, changed = checked(["git", "diff", "--name-only", f"{base}...HEAD"])
        if not passed:
            return [f"cannot inspect release diff from {base}: {changed}"]
        changed_paths.update(changed.splitlines())
    passed, changed = checked(["git", "diff", "--name-only", "HEAD"])
    if not passed:
        return [f"cannot inspect release diff from HEAD: {changed}"]
    changed_paths.update(changed.splitlines())
    passed, untracked = checked(
        ["git", "ls-files", "--others", "--exclude-standard"]
    )
    if not passed:
        return [f"cannot inspect untracked release files: {untracked}"]
    changed_paths.update(untracked.splitlines())
    if not any(
        path == "plugins/skiphow" or path.startswith("plugins/skiphow/")
        for path in changed_paths
    ):
        return []
    previous_ref = base or "HEAD"
    passed, previous = checked(["git", "show", f"{previous_ref}:VERSION"])
    if not passed:
        return [f"cannot read VERSION at {previous_ref}: {previous}"]
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



def model_id_scan(paths: Iterable[Path] | None = None) -> list[str]:
    """Keep provider model IDs out of portable skill policy."""
    candidates = (
        list(paths)
        if paths is not None
        else [path for path in sorted(PLUGIN_ROOT.rglob("*")) if path.is_file()]
    )
    errors: list[str] = []
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
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


def validate_continuity_hook(path: Path | None = None) -> list[str]:
    """Permit exactly one read-only SessionStart continuity hook."""
    path = path or PLUGIN_ROOT / "hooks/hooks.json"
    if not path.is_file():
        return ["plugin must ship hooks/hooks.json with the continuity hook"]
    relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {relative}: {exc}"]
    hooks = payload.get("hooks") if isinstance(payload, dict) else None
    if not isinstance(hooks, dict) or set(hooks) != {"SessionStart"}:
        return [f"{relative} must declare only SessionStart hooks"]
    groups = hooks["SessionStart"]
    if not isinstance(groups, list) or not groups:
        return [f"{relative} must list its SessionStart groups"]
    errors: list[str] = []
    if len(groups) != 2:
        errors.append(
            f"{relative} must declare exactly the startup|clear and "
            "compact|resume matcher groups"
        )
    matcher_groups: list[frozenset[str]] = []
    for group in groups:
        matcher = group.get("matcher", "") if isinstance(group, dict) else ""
        handlers = group.get("hooks") if isinstance(group, dict) else None
        sources = [item.strip() for item in str(matcher).split("|")]
        source_group = frozenset(sources)
        if (
            len(sources) != 2
            or any(not source for source in sources)
            or source_group not in CONTINUITY_GROUPS
        ):
            errors.append(
                f"{relative} must declare exactly the startup|clear and "
                "compact|resume matcher groups"
            )
            continue
        matcher_groups.append(source_group)
        if not isinstance(handlers, list) or len(handlers) != 1:
            errors.append(f"{relative} must use one handler per matcher group")
            continue
        handler = handlers[0]
        if not isinstance(handler, dict):
            errors.append(f"{relative} handler must be an object")
            continue
        command = handler.get("command", "")
        command = command if isinstance(command, str) else ""
        if handler.get("type") != "command" or not command.startswith("sh -c "):
            errors.append(f"{relative} handler must be a portable sh command")
        forbidden = (
            "curl", "wget", "http", ">", "rm ", "mv ", "git ", "python", "node",
            "cat ", "tail ", "$(", "`",
        )
        if any(token in command for token in forbidden):
            errors.append(f"{relative} handler must not write, fetch, or run programs")
        elif source_group == frozenset({"compact", "resume"}):
            if not HOOK_COMMAND.fullmatch(command):
                errors.append(
                    f"{relative} compact/resume handler must only announce an existing "
                    "checkpoint with the accepted read-only command shape"
                )
        elif not HOOK_NOTICE_COMMAND.fullmatch(command):
            # A denylist of program names cannot be complete; the accepted command is
            # one of two fixed shapes: print a startup notice, or conditionally print
            # a checkpoint notice after compaction or resume without reading the file.
            errors.append(f"{relative} startup/clear handler must match the read-only notice shape")
    if frozenset(matcher_groups) != CONTINUITY_GROUPS:
        errors.append(
            f"{relative} must declare exactly the startup|clear and "
            "compact|resume matcher groups"
        )
    other = [item for item in path.parent.rglob("*") if item.is_file() and item != path]
    if other:
        errors.append("plugin hooks/ may contain only hooks.json")
    return errors


def validate_openai_metadata(skill_dir: Path, skill_name: str) -> list[str]:
    """Validate optional OpenAI host metadata beside one top-level skill."""
    import yaml

    path = skill_dir / "agents/openai.yaml"
    relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    if not path.is_file():
        return []
    errors: list[str] = []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"cannot read {relative}: {exc}"]
    if not isinstance(payload, dict):
        return [f"{relative} must contain a YAML mapping"]
    interface = payload.get("interface")
    if "interface" in payload and not isinstance(interface, dict):
        errors.append(f"{relative} interface must be a mapping when present")
    elif isinstance(interface, dict):
        for key in ("display_name", "short_description", "default_prompt"):
            value = interface.get(key)
            if key in interface and (not isinstance(value, str) or not value.strip()):
                errors.append(f"{relative} interface.{key} must be nonempty when present")
        short = interface.get("short_description")
        if isinstance(short, str) and not 25 <= len(short.strip()) <= 64:
            errors.append(
                f"{relative} interface.short_description must be 25 to 64 characters"
            )
    policy = payload.get("policy")
    if "policy" in payload and not isinstance(policy, dict):
        errors.append(f"{relative} policy must be a mapping when present")
    elif isinstance(policy, dict):
        if "allow_implicit_invocation" in policy:
            implicit = policy.get("allow_implicit_invocation")
            if not isinstance(implicit, bool):
                errors.append(
                    f"{relative} policy.allow_implicit_invocation must be a boolean when present"
                )
            elif implicit is False:
                errors.append(
                    f"{relative} must not disable implicit invocation for the packaged owner skill"
                )
    return errors


def validate_skill_directory(skill_dir: Path) -> list[str]:
    """Validate one immediate child of the plugin's skills directory."""
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    name = skill_dir.name
    if not skill_file.is_file():
        return [f"top-level skill directory {name} must contain SKILL.md"]

    metadata, frontmatter_error = skill_frontmatter(skill_file)
    relative = skill_file.relative_to(ROOT) if skill_file.is_relative_to(ROOT) else skill_file
    if frontmatter_error is not None:
        errors.append(f"invalid skill {relative}: {frontmatter_error}")
    elif metadata is not None:
        unsupported = sorted(set(metadata) - AGENT_SKILL_FIELDS)
        if unsupported:
            errors.append(
                f"{relative} has unsupported Agent Skills fields: {', '.join(unsupported)}"
            )
        declared_name = metadata.get("name")
        description = metadata.get("description")
        if declared_name != name:
            errors.append(f"{relative} name must match its directory: {declared_name!r} != {name!r}")
        if (
            not isinstance(declared_name, str)
            or len(declared_name) > 64
            or SKILL_NAME.fullmatch(declared_name) is None
            or "--" in declared_name
        ):
            errors.append(f"{relative} has an invalid Agent Skills name")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{relative} description must be a nonempty string")
        elif len(description) > 1024:
            errors.append(f"{relative} description must be at most 1024 characters")
        license_name = metadata.get("license")
        if "license" in metadata and (
            not isinstance(license_name, str) or not license_name.strip()
        ):
            errors.append(f"{relative} license must be a nonempty string when present")
        compatibility = metadata.get("compatibility")
        if "compatibility" in metadata and (
            not isinstance(compatibility, str)
            or not compatibility.strip()
            or len(compatibility) > 500
        ):
            errors.append(
                f"{relative} compatibility must be a nonempty string of at most 500 characters"
            )
        extra_metadata = metadata.get("metadata")
        if "metadata" in metadata and (
            not isinstance(extra_metadata, dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in extra_metadata.items()
            )
        ):
            errors.append(f"{relative} metadata must map strings to strings")
        allowed_tools = metadata.get("allowed-tools")
        if "allowed-tools" in metadata and (
            not isinstance(allowed_tools, str) or not allowed_tools.strip()
        ):
            errors.append(f"{relative} allowed-tools must be a nonempty string when present")
    errors.extend(validate_skill_markdown_reachability(skill_dir))
    errors.extend(validate_openai_metadata(skill_dir, name))
    return errors


def validate_skill_markdown_reachability(skill_dir: Path) -> list[str]:
    """Require every Markdown reference to be linked from its skill, recursively."""
    references = skill_dir / "references"
    if not references.is_dir():
        return []

    root = skill_dir.resolve()
    pending = [(skill_dir / "SKILL.md").resolve()]
    seen: set[Path] = set()
    reachable: set[Path] = set()
    while pending:
        source = pending.pop()
        if source in seen or not source.is_file():
            continue
        seen.add(source)
        try:
            targets = markdown_targets(source, include_images=False)
        except OSError as exc:
            relative = source.relative_to(ROOT) if source.is_relative_to(ROOT) else source
            return [f"cannot inspect skill references from {relative}: {exc}"]
        for target in targets:
            candidate = local_link(source, target)
            if (
                candidate is None
                or candidate.suffix.lower() != ".md"
                or not candidate.is_relative_to(root)
                or not candidate.is_file()
            ):
                continue
            reachable.add(candidate)
            pending.append(candidate)

    markdown_references = {
        path.resolve() for path in references.rglob("*.md") if path.is_file()
    }
    orphans = sorted(markdown_references - reachable)
    return [
        f"skill {skill_dir.name} has unreachable Markdown reference: "
        f"{path.relative_to(root).as_posix()}"
        for path in orphans
    ]


def validate_plugin_links() -> list[str]:
    """Keep every local Markdown link inside the shipped plugin and resolvable."""
    errors: list[str] = []
    for path in sorted(PLUGIN_ROOT.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            targets = markdown_targets(path)
        except OSError as exc:
            errors.append(f"cannot read Markdown {path.relative_to(ROOT)}: {exc}")
            continue
        for target in targets:
            candidate = local_link(path, target)
            if candidate is None:
                continue
            relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            try:
                candidate.relative_to(PLUGIN_ROOT.resolve())
            except ValueError:
                errors.append(f"plugin link escapes package: {relative} -> {target}")
                continue
            if not candidate.exists():
                errors.append(f"broken plugin link: {relative} -> {target}")
    return errors


def validate_third_party_sources(skill_names: set[str]) -> list[str]:
    """Validate optional adapted-source provenance without pretending it is verbatim."""
    sources_path = PLUGIN_ROOT / "SOURCES.json"
    notices_path = PLUGIN_ROOT / "THIRD_PARTY_NOTICES.md"
    if not sources_path.exists() and not notices_path.exists():
        return []
    if not sources_path.is_file() or not notices_path.is_file():
        return ["SOURCES.json and THIRD_PARTY_NOTICES.md must be shipped together"]

    relative = sources_path.relative_to(ROOT) if sources_path.is_relative_to(ROOT) else sources_path
    try:
        payload = json.loads(sources_path.read_text(encoding="utf-8"))
        notices = notices_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read third-party provenance: {exc}"]
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        return [f"{relative} must contain a sources list"]
    errors: list[str] = []
    if not isinstance(payload.get("schema_version"), int) or payload["schema_version"] < 1:
        errors.append(f"{relative} schema_version must be a positive integer")
    if not payload["sources"]:
        errors.append(f"{relative} sources must not be empty when the manifest is present")
    if not notices.strip():
        errors.append("THIRD_PARTY_NOTICES.md must not be empty")
    normalized_notices = " ".join(notices.split())
    declared_skills: set[str] = set()
    for index, source in enumerate(payload["sources"]):
        label = f"{relative} source {index + 1}"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        repository = source.get("repository")
        parsed = urlsplit(repository) if isinstance(repository, str) else None
        if parsed is None or parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{label} repository must be an HTTPS source URL")
        commit = source.get("commit")
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-fA-F]{40}", commit) is None:
            errors.append(f"{label} commit must be a pinned 40-character hexadecimal revision")
        license_name = source.get("license")
        if not isinstance(license_name, str) or not license_name.strip():
            errors.append(f"{label} license must be present")
        attributions: dict[str, object] = {}
        for field in ("copyright", "provenance"):
            if field in source:
                attributions[field] = source[field]
        if not attributions or not any(
            isinstance(value, str) and value.strip() for value in attributions.values()
        ):
            errors.append(f"{label} provenance or copyright must be present")
        for field, value in attributions.items():
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label} {field} must be a nonempty string when present")
            elif value not in notices:
                errors.append(
                    f"THIRD_PARTY_NOTICES.md must mention source {field} {value!r}"
                )
        if isinstance(license_name, str) and license_name.strip().casefold() == "mit":
            for paragraph_name, paragraph in (
                ("permission", MIT_PERMISSION_PARAGRAPH),
                ("warranty", MIT_WARRANTY_PARAGRAPH),
            ):
                if " ".join(paragraph.split()) not in normalized_notices:
                    errors.append(
                        f"THIRD_PARTY_NOTICES.md must include the canonical MIT "
                        f"{paragraph_name} paragraph"
                    )
        adaptations = source.get("adaptations")
        if not isinstance(adaptations, list) or not adaptations:
            errors.append(f"{label} adaptations must be a nonempty list")
            continue
        for adaptation_index, adaptation in enumerate(adaptations):
            item_label = f"{label} adaptation {adaptation_index + 1}"
            if not isinstance(adaptation, dict):
                errors.append(f"{item_label} must be an object")
                continue
            skill = adaptation.get("skill")
            if not isinstance(skill, str) or skill not in skill_names:
                errors.append(f"{item_label} must name an existing packaged skill")
            elif skill in declared_skills:
                errors.append(f"adapted skill {skill} is declared more than once")
            else:
                declared_skills.add(skill)
            source_paths = adaptation.get("source_paths")
            if not isinstance(source_paths, list) or not source_paths:
                errors.append(f"{item_label} source_paths must be a nonempty list")
            else:
                for source_path in source_paths:
                    if not isinstance(source_path, str) or not source_path.strip():
                        errors.append(f"{item_label} source_paths must contain nonempty paths")
                        continue
                    pure = PurePosixPath(source_path)
                    if pure.is_absolute() or ".." in pure.parts:
                        errors.append(f"{item_label} source path must stay within its source repository")
            files = adaptation.get("files")
            if files is not None:
                if not isinstance(files, list) or not files:
                    errors.append(f"{item_label} files must be a nonempty list when present")
                elif isinstance(skill, str) and skill in skill_names:
                    root = PLUGIN_ROOT / "skills" / skill
                    for declared in files:
                        if not isinstance(declared, str) or not declared.strip():
                            errors.append(f"{item_label} files must contain nonempty paths")
                            continue
                        candidate = (root / declared).resolve()
                        try:
                            candidate.relative_to(root.resolve())
                        except ValueError:
                            errors.append(f"{item_label} file escapes skill {skill}: {declared}")
                            continue
                        if not candidate.is_file():
                            errors.append(f"{item_label} declares missing file for {skill}: {declared}")
        for value, field in ((repository, "repository"), (commit, "commit"), (license_name, "license")):
            if isinstance(value, str) and value and value not in notices:
                errors.append(f"THIRD_PARTY_NOTICES.md must mention source {field} {value!r}")
    return errors


def validate_plugin_static() -> list[str]:
    """Check the single-owner-skill package shared by Codex and Claude."""
    errors: list[str] = []
    codex_path = PLUGIN_ROOT / ".codex-plugin/plugin.json"
    claude_path = PLUGIN_ROOT / ".claude-plugin/plugin.json"
    owner_skill = PLUGIN_ROOT / "skills/skiphow/SKILL.md"
    for path in (codex_path, claude_path, owner_skill):
        if not path.is_file():
            relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            errors.append(f"missing plugin file: {relative}")
    if errors:
        return errors

    try:
        codex = json.loads(codex_path.read_text(encoding="utf-8"))
        claude = json.loads(claude_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read plugin manifests: {exc}"]
    for host, manifest in (("Codex", codex), ("Claude", claude)):
        if not isinstance(manifest, dict) or manifest.get("name") != "skiphow":
            errors.append(f"{host} manifest must describe the skiphow plugin")
            continue
        if manifest.get("skills") != "./skills/":
            errors.append(f"{host} manifest must load ./skills/")
        if manifest.get("license") != "MIT":
            errors.append(f"{host} manifest must declare the packaged MIT license")
        if "hooks" in manifest or "agents" in manifest:
            errors.append(f"{host} manifest must rely on the default plugin directories")

    shipped = {
        path.relative_to(PLUGIN_ROOT).as_posix()
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    absent = sorted(CORE_PACKAGE_FILES - shipped)
    if absent:
        errors.append(f"plugin is missing required files: {', '.join(absent)}")
    package_entries = [
        path
        for path in PLUGIN_ROOT.iterdir()
        if path.is_file()
        or path.is_symlink()
        or any(child.is_file() or child.is_symlink() for child in path.rglob("*"))
    ]
    unexpected_top_level = sorted(
        path.name for path in package_entries if path.name not in ALLOWED_PLUGIN_TOP_LEVEL
    )
    if unexpected_top_level:
        errors.append(f"plugin has unexpected top-level entries: {', '.join(unexpected_top_level)}")
    allowed_non_skill_files = {
        relative for relative in CORE_PACKAGE_FILES if not relative.startswith("skills/")
    } | {"SOURCES.json", "THIRD_PARTY_NOTICES.md"}
    unexpected_non_skill = sorted(
        relative
        for relative in shipped
        if not relative.startswith("skills/") and relative not in allowed_non_skill_files
    )
    if unexpected_non_skill:
        errors.append(
            f"plugin ships files outside manifests, hooks, skills, and notices: "
            f"{', '.join(unexpected_non_skill)}"
        )
    links = sorted(
        path.relative_to(PLUGIN_ROOT).as_posix()
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_symlink()
    )
    if links:
        errors.append(f"plugin must ship regular files, not links: {', '.join(links)}")
    package_license = PLUGIN_ROOT / "LICENSE"
    if not package_license.is_file() or package_license.read_bytes() != (ROOT / "LICENSE").read_bytes():
        errors.append("plugin must include the repository MIT license")

    skills_root = PLUGIN_ROOT / "skills"
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    unexpected_skill_entries = sorted(path.name for path in skills_root.iterdir() if not path.is_dir())
    if unexpected_skill_entries:
        errors.append(
            f"plugin skills/ may contain only top-level skill directories: "
            f"{', '.join(unexpected_skill_entries)}"
        )
    direct_skill_files = {path / "SKILL.md" for path in skill_dirs}
    public_skills = {path for path in PLUGIN_ROOT.rglob("SKILL.md") if path.is_file()}
    nested_skills = sorted(
        path.relative_to(PLUGIN_ROOT).as_posix() for path in public_skills - direct_skill_files
    )
    if nested_skills:
        errors.append(f"plugin must not contain nested SKILL.md files: {', '.join(nested_skills)}")
    for skill_dir in skill_dirs:
        errors.extend(validate_skill_directory(skill_dir))
    skill_names = {path.name for path in skill_dirs if (path / "SKILL.md").is_file()}
    if skill_names != {"skiphow"}:
        errors.append("plugin must expose exactly one owner entry at skills/skiphow/SKILL.md")

    errors.extend(model_id_scan())
    errors.extend(validate_plugin_links())
    errors.extend(validate_third_party_sources(skill_names))
    errors.extend(validate_continuity_hook())

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
    commands = [["git", "diff", "--check"], ["git", "diff", "--cached", "--check"]]
    if base:
        commands.append(["git", "diff", "--check", f"{base}...HEAD"])
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
        + validate_plugin_static()
        + validate_release_version_change(base)
    )
    commands = [
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
