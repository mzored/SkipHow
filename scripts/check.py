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
        "model-routing.md",
        "worktrees.md",
    }
)
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
AGENT_ROLES = {"scout": "haiku", "builder": "sonnet", "reviewer": "inherit"}
AGENT_MODELS = frozenset({"haiku", "sonnet", "opus", "inherit"})
AGENT_EFFORTS = frozenset({"low", "medium", "high"})
AGENT_FIELDS = frozenset({"name", "description", "model", "effort", "tools", "isolation", "maxTurns"})
CONTINUITY_MATCHERS = frozenset({"startup", "clear", "compact", "resume"})
PACKAGE_FILES = frozenset(
    {
        "LICENSE",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "agents/builder.md",
        "agents/reviewer.md",
        "agents/scout.md",
        "hooks/hooks.json",
        "skills/skiphow/SKILL.md",
        "skills/skiphow/agents/openai.yaml",
    }
    | {f"skills/skiphow/references/{name}" for name in REQUIRED_REFERENCES}
)
HOOK_COMMAND = re.compile(
    r"""^sh -c 'printf "%s\\n" "[^"'$`\\]+"; """
    r"""if \[ -f \.skiphow/handoff\.md \]; then tail -n \d{1,3} \.skiphow/handoff\.md; fi; exit 0'$"""
)
ROOT_SKILL_LIMITS = {"bytes": 9500, "words": 1400}
REFERENCE_LIMITS = {"total_words": 5200, "file_words": 750}


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


def agent_frontmatter(path: Path) -> dict[str, object]:
    """Parse the YAML frontmatter of one host agent definition."""
    import yaml

    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        raise ValueError(f"{path} has no YAML frontmatter")
    value = yaml.safe_load(match.group(1))
    if not isinstance(value, dict):
        raise ValueError(f"{path} frontmatter must be a mapping")
    return value


def validate_agents(agents_dir: Path = PLUGIN_ROOT / "agents") -> list[str]:
    """Require exactly the three role adapters with host-family aliases only."""
    errors: list[str] = []
    found = {path.stem: path for path in agents_dir.glob("*.md")} if agents_dir.is_dir() else {}
    if set(found) != set(AGENT_ROLES):
        errors.append(
            "plugin agents must be exactly scout, builder, reviewer; found: "
            + (", ".join(sorted(found)) or "none")
        )
    for role, path in sorted(found.items()):
        try:
            meta = agent_frontmatter(path)
        except (OSError, ValueError, ImportError) as exc:
            errors.append(str(exc))
            continue
        relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        unexpected = sorted(set(meta) - AGENT_FIELDS)
        if unexpected:
            errors.append(f"{relative} uses unsupported plugin agent fields: {', '.join(unexpected)}")
        if meta.get("name") != role:
            errors.append(f"{relative} must be named {role}")
        if not isinstance(meta.get("description"), str) or not meta["description"].strip():
            errors.append(f"{relative} needs a description for host auto-delegation")
        model = meta.get("model", "inherit")
        if model not in AGENT_MODELS:
            errors.append(f"{relative} model must be a family alias or inherit, not {model!r}")
        elif role in AGENT_ROLES and model != AGENT_ROLES[role]:
            errors.append(f"{relative} must route {role} to the {AGENT_ROLES[role]} tier")
        if "effort" in meta and meta["effort"] not in AGENT_EFFORTS:
            errors.append(f"{relative} effort must be one of {sorted(AGENT_EFFORTS)}")
        if role == "builder" and meta.get("isolation") != "worktree":
            errors.append(f"{relative} must run in an isolated worktree")
        if role != "builder" and any(tool in str(meta.get("tools", "")) for tool in ("Edit", "Write")):
            errors.append(f"{relative} must stay read-only")
        errors.extend(model_id_scan([path]))
    return errors


def validate_continuity_hook(path: Path = PLUGIN_ROOT / "hooks/hooks.json") -> list[str]:
    """Permit exactly one read-only SessionStart continuity hook."""
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
    if not isinstance(hooks["SessionStart"], list) or not hooks["SessionStart"]:
        return [f"{relative} must list its SessionStart groups"]
    errors: list[str] = []
    matchers: list[str] = []
    for group in hooks["SessionStart"]:
        matcher = group.get("matcher", "") if isinstance(group, dict) else ""
        handlers = group.get("hooks") if isinstance(group, dict) else None
        sources = [item.strip() for item in re.split(r"[|,]", str(matcher)) if item.strip()]
        if not sources or not set(sources) <= CONTINUITY_MATCHERS or not isinstance(handlers, list) or len(handlers) != 1:
            errors.append(f"{relative} may only match startup, clear, compact, and resume with one handler per group")
            continue
        matchers.extend(sources)
        handler = handlers[0]
        if not isinstance(handler, dict):
            errors.append(f"{relative} handler must be an object")
            continue
        command = handler.get("command", "")
        command = command if isinstance(command, str) else ""
        if handler.get("type") != "command" or not command.startswith("sh -c "):
            errors.append(f"{relative} handler must be a portable sh command")
        if ".skiphow/handoff.md" not in command:
            errors.append(f"{relative} handler must surface .skiphow/handoff.md")
        forbidden = ("curl", "wget", "http", ">", "rm ", "mv ", "git ", "python", "node", "$(", "`")
        if any(token in command for token in forbidden):
            errors.append(f"{relative} handler must not write, fetch, or run programs")
        elif not HOOK_COMMAND.fullmatch(command):
            # A denylist of program names cannot be complete; the accepted command is
            # one fixed shape -- print a notice, then tail the checkpoint if it exists.
            errors.append(f"{relative} handler must match the accepted read-only command shape")
        if {"compact", "resume"} & set(sources):
            anchors = (
                "owner request", "repository instructions", "active host tasks", "live Git",
                "GitHub", "checkout", "branch", "HEAD", "candidate",
            )
            missing = [anchor for anchor in anchors if anchor not in command]
            if missing:
                errors.append(
                    f"{relative} compact/resume notice must require recovery of: {', '.join(missing)}"
                )
    if sorted(matchers) != sorted(CONTINUITY_MATCHERS):
        errors.append(f"{relative} must match startup, clear, compact, and resume exactly once each")
    other = [item for item in path.parent.rglob("*") if item.is_file() and item != path]
    if other:
        errors.append("plugin hooks/ may contain only hooks.json")
    return errors


def validate_budget() -> list[str]:
    """Bound the always-loaded skill and each lazy reference.

    These budgets catch unbounded growth; they are not a target to compress toward.
    The root carries what must apply on every request, so when a budget binds, the
    question is whether the rule belongs in the root, not which words to shave.
    """
    errors: list[str] = []
    try:
        root_text = CANONICAL_SKILL.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot measure the root skill: {exc}"]
    measured = {"bytes": len(root_text.encode("utf-8")), "words": len(root_text.split())}
    for unit, limit in ROOT_SKILL_LIMITS.items():
        if measured[unit] > limit:
            errors.append(f"root skill {unit} exceed the limit: {measured[unit]} > {limit}")
    words = {
        path.relative_to(SKILL_ROOT / "references").as_posix(): len(path.read_text(encoding="utf-8").split())
        for path in sorted((SKILL_ROOT / "references").rglob("*.md"))
    }
    if sum(words.values()) > REFERENCE_LIMITS["total_words"]:
        errors.append(f"references words exceed the limit: {sum(words.values())} > {REFERENCE_LIMITS['total_words']}")
    for name, count in words.items():
        if count > REFERENCE_LIMITS["file_words"]:
            errors.append(f"reference {name} words exceed the limit: {count} > {REFERENCE_LIMITS['file_words']}")
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
        if "hooks" in manifest or "agents" in manifest:
            errors.append(f"{host} manifest must rely on the default agents/ and hooks/ directories")

    public_skills = sorted(PLUGIN_ROOT.rglob("SKILL.md"))
    if public_skills != [CANONICAL_SKILL]:
        found = ", ".join(path.relative_to(PLUGIN_ROOT).as_posix() for path in public_skills)
        errors.append(f"plugin must contain one canonical SKILL.md, found: {found or 'none'}")

    shipped = {
        path.relative_to(PLUGIN_ROOT).as_posix()
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    unexpected = sorted(shipped - PACKAGE_FILES)
    if unexpected:
        errors.append(f"plugin ships files outside the accepted shape: {', '.join(unexpected)}")
    absent = sorted(PACKAGE_FILES - shipped)
    if absent:
        errors.append(f"plugin is missing accepted files: {', '.join(absent)}")
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

    errors.extend(validate_agents())
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
        + validate_plugin_static()
        + validate_budget()
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
