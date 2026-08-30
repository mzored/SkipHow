#!/usr/bin/env python3
"""Run deterministic checks for the portable SkipHow plugin."""

from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
from html import unescape as html_unescape
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Iterable
import unicodedata
from urllib.parse import unquote, urlsplit
import venv
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins/skiphow"
SITE_ROOT = ROOT / "site"
SITE_BASE_URL = "https://mzored.github.io/SkipHow/"
REPOSITORY_URL = "https://github.com/mzored/SkipHow"
SITE_PAGES = {
    "index.html": SITE_BASE_URL,
    "compare/index.html": f"{SITE_BASE_URL}compare/",
    "evidence/index.html": f"{SITE_BASE_URL}evidence/",
}
REQUIREMENTS = ROOT / "requirements-dev.txt"
PERSONAL_PATH = re.compile(
    r"(?:(?<![\w.])/(?:Users|home)/[^/\s]+/?|"
    + r"(?<![\w.])/root(?:/|(?=$|[\s,;:!?)}\].'\"`]))"
    + r"|[A-Za-z]:[\\/]+(?i:users)[\\/]+[^\\/\s]+[\\/]?"
    + r"|~/\.(?:codex|claude)(?:/|\b)|\$(?:\{)?HOME(?:\})?[\\/]"
    + r"|(?i:%userprofile%)[\\/])"
)
CONCRETE_MODEL_ID = re.compile(
    # A provider name, any number of family words, then a version component. This is a
    # deliberately broad but still finite list of provider-shaped identifiers; decoded
    # and rendered representations are scanned below so escaping cannot bypass it.
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
SAFE_ECHO_COMMAND = re.compile(r"^echo '([A-Za-z0-9][A-Za-z0-9 .,/:_-]*)'$")
HANDOFF_STATE_REFERENCE = re.compile(r"(?:\.skiphow\b|\bhandoff(?:\.[a-z0-9]+)?\b)", re.IGNORECASE)
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
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
COMMON_MANIFEST_METADATA_FIELDS = frozenset(
    {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
    }
)
HOST_MANIFEST_METADATA_FIELDS = {
    "Codex": COMMON_MANIFEST_METADATA_FIELDS | {"interface"},
    "Claude": COMMON_MANIFEST_METADATA_FIELDS | {"$schema", "displayName", "metadata"},
}
HOST_MANIFEST_COMPONENT_FIELDS = {
    "Codex": frozenset({"skills", "apps", "mcpServers"}),
    "Claude": frozenset(
        {
            "skills",
            "commands",
            "agents",
            "workflows",
            "hooks",
            "mcpServers",
            "outputStyles",
            "lspServers",
            "experimental",
            "dependencies",
            "userConfig",
            "channels",
        }
    ),
}
PACKAGE_MANIFEST_COMPONENT_FIELDS = frozenset({"skills"})
MIT_PERMISSION_PARAGRAPH = """\
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:"""
MIT_CONDITION_PARAGRAPH = """\
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software."""
MIT_WARRANTY_PARAGRAPH = """\
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
WINDOWS_DRIVE_DESTINATION = re.compile(r"^[A-Za-z]:")
HTML_ENTITY = re.compile(r"&(?:#[xX][0-9A-Fa-f]+|#[0-9]+|[A-Za-z][A-Za-z0-9]+);")
ALLOWED_REMOTE_LINK_SCHEMES = frozenset({"http", "https", "mailto"})
WINDOWS_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul", "conin$", "conout$"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
    | {f"com{number}" for number in "¹²³"}
    | {f"lpt{number}" for number in "¹²³"}
)


class DuplicateJSONKey(ValueError):
    """Raised when a JSON object would silently replace an earlier field."""


class DisallowedLocalLink(ValueError):
    """Raised for local-file URI forms that must never be treated as remote."""


def display_path(path: Path, base: Path | None = None) -> Path:
    """Return a stable relative label when possible, otherwise the original path."""
    base = ROOT if base is None else base
    try:
        return path.relative_to(base)
    except ValueError:
        return path


def first_symlink_component(path: Path, base: Path | None = None) -> Path | None:
    """Return the first package-relative path component that is a symlink."""
    base = ROOT if base is None else base
    try:
        relative = path.relative_to(base)
    except ValueError:
        return path if path.is_symlink() else None
    current = base
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return current
    return None


def validate_plugin_root_directory() -> list[str]:
    """Require the package root and every repository-relative parent to be real."""
    linked = first_symlink_component(PLUGIN_ROOT)
    if linked is not None:
        return [f"plugin path component must not be a link: {display_path(linked)}"]
    if not PLUGIN_ROOT.is_dir():
        return [f"plugin root is not a directory: {display_path(PLUGIN_ROOT)}"]
    return []


def regular_file_problem(path: Path, label: str) -> str | None:
    """Describe why a control file is not an ordinary non-symlink file."""
    linked = first_symlink_component(path)
    if linked is not None:
        return f"{label} must be a regular non-symlink file"
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        return f"{label} is unavailable: {exc}"
    if not stat.S_ISREG(mode):
        return f"{label} must be a regular non-symlink file"
    return None


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


def checked_null_paths(command: list[str]) -> tuple[bool, set[str] | str]:
    """Run a Git path query without quote or newline ambiguity."""
    command_environment = os.environ.copy()
    command_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=command_environment,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode:
        return False, os.fsdecode(result.stdout + result.stderr).strip()
    return True, {os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw}


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(f"duplicate JSON field: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def load_json_text(text: str) -> object:
    """Decode strict JSON without silently replacing duplicate fields."""
    return json.loads(
        text,
        object_pairs_hook=_unique_json_object,
        parse_constant=_reject_json_constant,
    )


def yaml_library():
    """Import the prepared YAML dependency only after bootstrap has run."""
    import yaml

    return yaml


def load_yaml_text(text: str) -> object:
    """Decode YAML without silently replacing duplicate mapping keys."""
    yaml = yaml_library()

    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node, deep=False):
        loader.flatten_mapping(node)
        mapping: dict[object, object] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable key",
                    key_node.start_mark,
                ) from exc
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping,
    )
    return yaml.load(text, Loader=UniqueKeyLoader)


def nested_strings(value: object, seen: set[int] | None = None) -> Iterable[str]:
    """Yield strings from structured data, including mapping keys."""
    if isinstance(value, str):
        yield value
        return
    if not isinstance(value, (dict, list, tuple, set)):
        return
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return
    seen.add(identity)
    if isinstance(value, dict):
        for key, item in value.items():
            yield from nested_strings(key, seen)
            yield from nested_strings(item, seen)
    else:
        for item in value:
            yield from nested_strings(item, seen)


def is_normalized_relative_posix_path(value: str) -> bool:
    """Return whether a package path is portable, relative, and canonical."""
    if not value.strip() or "\0" in value or "\\" in value or ":" in value:
        return False
    pure = PurePosixPath(value)
    return (
        not pure.is_absolute()
        and pure != PurePosixPath(".")
        and ".." not in pure.parts
        and pure.as_posix() == value
    )


def windows_package_path_key(value: str) -> str | None:
    """Return a Windows comparison key, or None for an unshippable path."""
    parts = PurePosixPath(value).parts
    if not parts:
        return None
    normalized: list[str] = []
    for part in parts:
        try:
            part.encode("utf-8")
        except UnicodeEncodeError:
            return None
        if (
            not part
            or part in {".", ".."}
            or part[-1] in {" ", "."}
            or any(unicodedata.category(character) == "Cs" for character in part)
            or any(ord(character) < 32 or character in '<>:"\\|?*' for character in part)
            or part.rstrip(" .").split(".", 1)[0].casefold() in WINDOWS_RESERVED_NAMES
        ):
            return None
        normalized.append(unicodedata.normalize("NFC", part).casefold())
    return "/".join(normalized)


def validate_package_path_portability(paths: Iterable[str]) -> list[str]:
    """Reject Windows-invalid names and case-fold collisions in package paths."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    keys: dict[str, str] = {}
    directory_prefixes: dict[str, str] = {}
    reported_directory_collisions: set[tuple[str, str]] = set()
    for path in sorted(paths):
        key = windows_package_path_key(path)
        if key is None:
            errors.append(f"plugin has a nonportable file path: {path}")
            continue
        original_parts = PurePosixPath(path).parts
        key_parts = key.split("/")
        for index in range(1, len(original_parts)):
            original_prefix = "/".join(original_parts[:index])
            normalized_prefix = "/".join(key_parts[:index])
            previous_prefix = directory_prefixes.get(normalized_prefix)
            if previous_prefix is not None and previous_prefix != original_prefix:
                collision = (previous_prefix, original_prefix)
                if collision not in reported_directory_collisions:
                    errors.append(
                        "plugin directory paths collide on case-insensitive or "
                        f"Unicode-normalizing filesystems: {previous_prefix}, "
                        f"{original_prefix}"
                    )
                    reported_directory_collisions.add(collision)
            else:
                directory_prefixes[normalized_prefix] = original_prefix
        previous = seen.get(key)
        if previous is not None and previous != path:
            errors.append(
                f"plugin paths collide on case-insensitive filesystems: {previous}, {path}"
            )
        else:
            seen[key] = path
        keys[key] = path
    for key, path in keys.items():
        parts = key.split("/")
        for index in range(1, len(parts)):
            prefix = "/".join(parts[:index])
            if prefix in keys:
                errors.append(
                    f"plugin file conflicts with a directory on case-insensitive filesystems: "
                    f"{keys[prefix]}, {path}"
                )
                break
    return errors


def markdown_rendered_text(text: str) -> Iterable[str]:
    """Yield CommonMark-visible inline text with formatting boundaries removed."""
    from markdown_it import MarkdownIt

    def visible_fragments(tokens) -> Iterable[str]:
        for child in tokens or ():
            if child.type in {"text", "text_special", "code_inline"}:
                yield child.content
            elif child.type == "image":
                yield from visible_fragments(child.children)
            elif child.type in {"softbreak", "hardbreak"}:
                yield "\n"

    for token in MarkdownIt("commonmark").parse(text):
        if token.type != "inline":
            continue
        fragments = list(visible_fragments(token.children))
        if fragments:
            yield "".join(fragments)


def scan_representations(path: Path, text: str) -> Iterable[str]:
    """Yield raw and host-decoded representations of one public file."""
    yield text
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            yield from nested_strings(load_json_text(text))
        except (ValueError, json.JSONDecodeError):
            pass
    elif suffix in {".yml", ".yaml"}:
        try:
            yield from nested_strings(load_yaml_text(text))
        except yaml_library().YAMLError:
            pass
    elif suffix in MARKDOWN_SUFFIXES:
        if path.name == "SKILL.md":
            frontmatter = re.match(
                r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL
            )
            if frontmatter is not None:
                try:
                    yield from nested_strings(load_yaml_text(frontmatter.group(1)))
                except yaml_library().YAMLError:
                    pass
        # A malformed frontmatter block must not suppress independently rendered text.
        yield from markdown_rendered_text(text)
        for attribute in markdown_policy_attributes_text(text):
            yield decode_markup_layers(attribute)


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
        if path.is_symlink():
            errors.append(f"JSON must be a regular file, not a link: {display_path(path)}")
            continue
        try:
            load_json_text(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {display_path(path)}: {exc}")
    return errors


def validate_yaml() -> list[str]:
    yaml = yaml_library()
    errors: list[str] = []
    for path in repository_files({".yml", ".yaml"}):
        try:
            load_yaml_text(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"invalid YAML {display_path(path)}: {exc}")
    return errors


def markdown_targets_text(text: str, *, include_images: bool = True) -> list[str]:
    """Return resource destinations parsed from CommonMark source."""
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark")
    # The normal renderer suppresses unsafe schemes such as file:. Validation must
    # still see those destinations so it can reject them deliberately.
    parser.validateLink = lambda _url: True
    result: list[str] = []
    for token in parser.parse(text):
        for child in token.children or ():
            if child.type == "link_open" and child.attrGet("href"):
                result.append(child.attrGet("href"))
            elif include_images and child.type == "image" and child.attrGet("src"):
                result.append(child.attrGet("src"))
    return result


def markdown_policy_attributes_text(text: str) -> list[str]:
    """Return link/image destinations and titles that hosts decode or display."""
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark")
    parser.validateLink = lambda _url: True
    result: list[str] = []
    for token in parser.parse(text):
        for child in token.children or ():
            if child.type == "link_open":
                for attribute in ("href", "title"):
                    value = child.attrGet(attribute)
                    if value:
                        result.append(value)
            elif child.type == "image":
                for attribute in ("src", "title"):
                    value = child.attrGet(attribute)
                    if value:
                        result.append(value)
    return result


def markdown_targets(path: Path, *, include_images: bool = True) -> list[str]:
    """Return resource destinations parsed as CommonMark."""
    return markdown_targets_text(
        path.read_text(encoding="utf-8"), include_images=include_images
    )


def markdown_contains_raw_html(path: Path) -> bool:
    """Return whether CommonMark treats any shipped source as raw HTML."""
    from markdown_it import MarkdownIt

    for token in MarkdownIt("commonmark").parse(path.read_text(encoding="utf-8")):
        if token.type in {"html_block", "html_inline"}:
            return True
        if any(
            child.type in {"html_block", "html_inline"}
            for child in token.children or ()
        ):
            return True
    return False


def decode_markup_layers(value: str) -> str:
    """Decode URI and HTML escapes to stability without a magic nesting limit."""
    while True:
        expanded = unquote(HTML_ENTITY.sub(lambda match: html_unescape(match.group()), value))
        if expanded == value:
            return value
        value = expanded


def markdown_files(root: Path) -> list[Path]:
    """Return Markdown resources without assuming one spelling or filename case."""
    return sorted(
        path
        for path in root.rglob("*")
        if (path.is_file() or path.is_symlink())
        and path.suffix.lower() in MARKDOWN_SUFFIXES
    )


def local_link(path: Path, target: str) -> Path | None:
    # MarkdownIt has already applied the CommonMark entity layer. Split the URI
    # before decoding its path so encoded ?/# characters remain filename data.
    try:
        parsed = urlsplit(target)
    except ValueError as exc:
        raise DisallowedLocalLink(target) from exc
    scheme = parsed.scheme.casefold()
    if scheme == "file":
        raise DisallowedLocalLink(target)
    if scheme:
        if scheme not in ALLOWED_REMOTE_LINK_SCHEMES:
            raise DisallowedLocalLink(target)
        if scheme in {"http", "https"}:
            try:
                decoded_authority = unquote(parsed.netloc)
                authority = urlsplit(f"{scheme}://{decoded_authority}")
                hostname = authority.hostname
            except ValueError as exc:
                raise DisallowedLocalLink(target) from exc
            if not parsed.netloc or not hostname:
                raise DisallowedLocalLink(target)
        elif not parsed.path:
            raise DisallowedLocalLink(target)
        return None
    if parsed.netloc:
        raise DisallowedLocalLink(target)

    target_path = unquote(parsed.path)
    if (
        "\0" in target_path
        or WINDOWS_DRIVE_DESTINATION.match(target_path)
        or "\\" in target_path
    ):
        raise DisallowedLocalLink(target)
    if not parsed.path and parsed.fragment:
        return None
    if WINDOWS_DRIVE_DESTINATION.match(target_path):
        raise DisallowedLocalLink(target)
    if not target_path:
        return None
    if ":" in target_path:
        raise DisallowedLocalLink(target)
    try:
        return (path.parent / target_path).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise DisallowedLocalLink(target) from exc


def path_exists_with_exact_spelling(path: Path) -> bool:
    """Check every component without filesystem case/normalization forgiveness."""
    absolute = path.absolute()
    parts = absolute.parts
    if not parts:
        return False
    current = Path(parts[0])
    for part in parts[1:]:
        try:
            if part not in {entry.name for entry in current.iterdir()}:
                return False
        except OSError:
            return False
        current /= part
    return current.exists()


def skill_frontmatter(path: Path) -> tuple[dict[str, object] | None, str | None]:
    """Read the metadata block required by the Agent Skills specification."""
    yaml = yaml_library()

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, str(exc)
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if match is None:
        return None, "missing YAML frontmatter"
    try:
        value = load_yaml_text(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter: {exc}"
    if not isinstance(value, dict):
        return None, "frontmatter must be a mapping"
    if not text[match.end():].strip():
        return None, "skill body must not be empty"
    return value, None


def validate_markdown_links() -> list[str]:
    errors: list[str] = []
    for path in repository_files(MARKDOWN_SUFFIXES):
        if path.is_symlink():
            errors.append(f"Markdown must be a regular file, not a link: {display_path(path)}")
            continue
        try:
            targets = markdown_targets(path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read Markdown {display_path(path)}: {exc}")
            continue
        for target in targets:
            try:
                candidate = local_link(path, target)
            except DisallowedLocalLink:
                errors.append(
                    f"local-file link is not allowed: {display_path(path)} -> {target}"
                )
                continue
            if candidate is None:
                continue
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                errors.append(f"link escapes repository: {display_path(path)} -> {target}")
                continue
            if not path_exists_with_exact_spelling(candidate):
                errors.append(f"broken local link: {display_path(path)} -> {target}")
    return errors


class SiteHTML(HTMLParser):
    """Collect the small set of HTML facts the static site contract requires."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.start_tags: list[tuple[str, dict[str, str]]] = []
        self.title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = {key: value or "" for key, value in attrs}
        self.start_tags.append((tag.casefold(), normalized))
        if tag.casefold() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    def attributes(self, tag: str) -> list[dict[str, str]]:
        return [attrs for candidate, attrs in self.start_tags if candidate == tag]


def _site_meta(document: SiteHTML, key: str, value: str) -> list[str]:
    return [
        attrs.get("content", "").strip()
        for attrs in document.attributes("meta")
        if attrs.get(key) == value
    ]


def _site_local_target(page: Path, value: str) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    candidate = (page.parent / unquote(parsed.path)).resolve()
    try:
        candidate.relative_to(SITE_ROOT.resolve())
    except ValueError as exc:
        raise DisallowedLocalLink(value) from exc
    if candidate.is_dir() or parsed.path.endswith("/"):
        candidate /= "index.html"
    return candidate


def validate_site() -> list[str]:
    """Validate the canonical no-runtime GitHub Pages site."""
    errors: list[str] = []
    titles: set[str] = set()
    descriptions: set[str] = set()
    for relative, canonical in SITE_PAGES.items():
        page = SITE_ROOT / relative
        problem = regular_file_problem(page, f"site/{relative}")
        if problem is not None:
            errors.append(problem)
            continue
        try:
            text = page.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read site/{relative}: {exc}")
            continue
        document = SiteHTML()
        try:
            document.feed(text)
        except Exception as exc:
            errors.append(f"cannot parse site/{relative}: {exc}")
            continue

        html_tags = document.attributes("html")
        if len(html_tags) != 1 or html_tags[0].get("lang") != "en":
            errors.append(f"site/{relative} must declare exactly one English html root")
        title = "".join(document.title_parts).strip()
        if not title:
            errors.append(f"site/{relative} must have a nonempty title")
        elif title in titles:
            errors.append(f"site/{relative} duplicates another page title: {title}")
        titles.add(title)

        description = _site_meta(document, "name", "description")
        if len(description) != 1 or not description[0]:
            errors.append(f"site/{relative} must have one nonempty meta description")
        elif description[0] in descriptions:
            errors.append(f"site/{relative} duplicates another meta description")
        descriptions.update(description)
        if _site_meta(document, "name", "robots") != ["index,follow"]:
            errors.append(f"site/{relative} must declare robots index,follow")
        if _site_meta(document, "name", "viewport") != [
            "width=device-width, initial-scale=1, viewport-fit=cover"
        ]:
            errors.append(f"site/{relative} must declare the responsive viewport")

        canonical_links = [
            attrs.get("href")
            for attrs in document.attributes("link")
            if "canonical" in attrs.get("rel", "").split()
        ]
        if canonical_links != [canonical]:
            errors.append(f"site/{relative} canonical URL must be {canonical}")
        if _site_meta(document, "property", "og:url") != [canonical]:
            errors.append(f"site/{relative} Open Graph URL must match its canonical URL")
        for property_name in ("og:title", "og:description", "og:image"):
            values = _site_meta(document, "property", property_name)
            if len(values) != 1 or not values[0]:
                errors.append(f"site/{relative} must have one nonempty {property_name}")
        if _site_meta(document, "property", "og:image:alt") != [
            "SkipHow: own the product, let the agent own the engineering."
        ]:
            errors.append(f"site/{relative} must describe its Open Graph image")

        scripts = document.attributes("script")
        if len(scripts) != 1 or scripts[0].get("type") != "application/ld+json":
            errors.append(
                f"site/{relative} may contain only one JSON-LD script and no client runtime"
            )
        else:
            match = re.search(
                r'<script\s+type="application/ld\+json">(.*?)</script>',
                text,
                re.DOTALL | re.IGNORECASE,
            )
            try:
                structured = load_json_text(match.group(1)) if match else None
            except (ValueError, json.JSONDecodeError):
                structured = None
            if not isinstance(structured, dict):
                errors.append(f"site/{relative} has invalid JSON-LD")
            else:
                if structured.get("@type") != "SoftwareSourceCode":
                    errors.append(f"site/{relative} JSON-LD must use SoftwareSourceCode")
                if structured.get("url") != canonical:
                    errors.append(f"site/{relative} JSON-LD URL must match its canonical URL")

        if len(document.attributes("h1")) != 1:
            errors.append(f"site/{relative} must contain exactly one h1")
        for landmark in ("header", "nav", "main", "footer"):
            if len(document.attributes(landmark)) != 1:
                errors.append(f"site/{relative} must contain exactly one {landmark} landmark")
        repository_links = [
            attrs
            for attrs in document.attributes("a")
            if attrs.get("href") == REPOSITORY_URL
        ]
        if not repository_links:
            errors.append(f"site/{relative} must link directly to the GitHub repository")
        if relative == "index.html" and not any(
            "button" in attrs.get("class", "").split() for attrs in repository_links
        ):
            errors.append("site/index.html must present GitHub as a homepage action")
        for tag in ("div", "pre"):
            for attrs in document.attributes(tag):
                if attrs.get("aria-label") and not attrs.get("role"):
                    errors.append(
                        f"site/{relative} must not name a generic {tag} without a compatible role"
                    )
        for tag, attribute in (("a", "href"), ("link", "href"), ("img", "src")):
            for attrs in document.attributes(tag):
                value = attrs.get(attribute)
                if not value or value.startswith("#"):
                    continue
                try:
                    target = _site_local_target(page, value)
                except DisallowedLocalLink:
                    errors.append(f"site/{relative} link escapes site root: {value}")
                    continue
                if target is not None and not path_exists_with_exact_spelling(target):
                    errors.append(f"broken site link: site/{relative} -> {value}")

    sitemap = SITE_ROOT / "sitemap.xml"
    problem = regular_file_problem(sitemap, "site/sitemap.xml")
    if problem is not None:
        errors.append(problem)
    else:
        try:
            root = ET.parse(sitemap).getroot()
            locations = {
                element.text.strip()
                for element in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if element.text and element.text.strip()
            }
        except (OSError, ET.ParseError) as exc:
            errors.append(f"invalid site/sitemap.xml: {exc}")
        else:
            expected = set(SITE_PAGES.values())
            if locations != expected:
                errors.append("site/sitemap.xml must contain exactly the three canonical pages")

    for relative in ("assets/site.css", "assets/favicon.svg", "assets/social-preview.png", ".nojekyll"):
        path = SITE_ROOT / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"site must contain a regular site/{relative}")
    if (SITE_ROOT / "robots.txt").exists():
        errors.append("project site must not claim control of the account-level robots.txt")
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
        SITE_ROOT,
    )
    errors: list[str] = []
    for path in repository_files():
        if not any(path == root or path.is_relative_to(root) for root in roots):
            continue
        if path.is_symlink() and (
            path.is_relative_to(PLUGIN_ROOT)
            or path == ROOT / ".agents/plugins/marketplace.json"
            or path == ROOT / ".claude-plugin/marketplace.json"
        ):
            errors.append(f"shipped file must not be a link: {display_path(path)}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            if path.suffix.lower() in MARKDOWN_SUFFIXES:
                errors.append(
                    f"shipped Markdown is not valid UTF-8: {display_path(path)}: {exc}"
                )
            continue
        except OSError as exc:
            errors.append(f"cannot read shipped file {display_path(path)}: {exc}")
            continue
        reported: set[str] = set()
        for representation in scan_representations(path, text):
            for match in PERSONAL_PATH.finditer(representation):
                message = (
                    f"personal path {match.group(0)!r} in {display_path(path)}"
                )
                if message not in reported:
                    errors.append(message)
                    reported.add(message)
    return errors


def load_json(relative: str) -> dict[str, object]:
    path = ROOT / relative
    problem = regular_file_problem(path, relative)
    if problem is not None:
        raise ValueError(problem)
    value = load_json_text(path.read_text(encoding="utf-8"))
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
    version_path = ROOT / "VERSION"
    problem = regular_file_problem(version_path, "VERSION")
    if problem is not None:
        raise ValueError(problem)
    release = version_path.read_text(encoding="utf-8").strip()
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
    changelog_path = ROOT / "CHANGELOG.md"
    problem = regular_file_problem(changelog_path, "CHANGELOG.md")
    if problem is not None:
        raise ValueError(problem)
    changelog = changelog_path.read_text(encoding="utf-8")
    released = re.findall(r"^## (\S+) \(\d{4}-\d{2}-\d{2}\)$", changelog, re.MULTILINE)
    if not released:
        errors.append("CHANGELOG.md has no dated release heading")
    elif released[0] != release:
        errors.append(f"CHANGELOG.md leads with {released[0]}, not the released {release}")
    security_path = ROOT / "SECURITY.md"
    problem = regular_file_problem(security_path, "SECURITY.md")
    if problem is not None:
        raise ValueError(problem)
    if f"| {release.rsplit('.', 1)[0]}.x | Yes |" not in security_path.read_text(
        encoding="utf-8"
    ):
        errors.append(f"SECURITY.md does not support {release.rsplit('.', 1)[0]}.x")
    return errors


def infer_stable_release_base() -> tuple[bool, str]:
    """Find the nearest prior reachable exact vMAJOR.MINOR.PATCH release tag."""
    passed, output = checked(["git", "tag", "--merged", "HEAD", "--list", "v*"])
    if not passed:
        return False, output
    stable_tag = re.compile(
        r"^v((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))$"
    )
    candidates: list[tuple[str, tuple[int, int, int]]] = []
    for tag in output.splitlines():
        match = stable_tag.fullmatch(tag)
        if match is None:
            continue
        candidates.append((tag, tuple(int(part) for part in match.group(1).split("."))))
    if not candidates:
        return False, "HEAD has no reachable stable vMAJOR.MINOR.PATCH release tag"

    measured: list[tuple[int, tuple[int, int, int], str]] = []
    for tag, version_parts in candidates:
        passed, distance_text = checked(
            ["git", "rev-list", "--count", f"{tag}..HEAD"]
        )
        if not passed:
            return False, f"cannot measure release tag {tag}: {distance_text}"
        try:
            distance = int(distance_text)
        except ValueError:
            return False, f"release tag {tag} returned an invalid commit distance"
        if distance < 0:
            return False, f"release tag {tag} returned an invalid commit distance"
        if distance == 0:
            continue
        measured.append((distance, tuple(-part for part in version_parts), tag))
    if not measured:
        return False, "HEAD has no prior reachable stable release tag"
    return True, min(measured)[2]


def validate_release_version_change(base: str | None) -> list[str]:
    """Require a monotonic version bump whenever the packaged plugin changes."""
    if not (ROOT / ".git").exists():
        return []
    comparison_base = base
    if comparison_base is None:
        passed, inferred = infer_stable_release_base()
        if not passed:
            return [f"cannot infer stable release baseline: {inferred}"]
        comparison_base = inferred
    changed_paths: set[str] = set()
    if comparison_base:
        passed, changed = checked_null_paths(
            [
                "git",
                "diff",
                "--name-only",
                "--no-renames",
                "-z",
                f"{comparison_base}...HEAD",
            ]
        )
        if not passed:
            return [f"cannot inspect release diff from {comparison_base}: {changed}"]
        if not isinstance(changed, set):
            return [
                f"cannot inspect release diff from {comparison_base}: malformed path output"
            ]
        changed_paths.update(changed)
    passed, changed = checked_null_paths(
        ["git", "diff", "--name-only", "--no-renames", "-z", "HEAD"]
    )
    if not passed:
        return [f"cannot inspect release diff from HEAD: {changed}"]
    if not isinstance(changed, set):
        return ["cannot inspect release diff from HEAD: malformed path output"]
    changed_paths.update(changed)
    passed, untracked = checked_null_paths(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"]
    )
    if not passed:
        return [f"cannot inspect untracked release files: {untracked}"]
    if not isinstance(untracked, set):
        return ["cannot inspect untracked release files: malformed path output"]
    changed_paths.update(untracked)
    if not any(
        path == "plugins/skiphow" or path.startswith("plugins/skiphow/")
        for path in changed_paths
    ):
        return []
    previous_ref = comparison_base
    passed, previous = checked(["git", "show", f"{previous_ref}:VERSION"])
    if not passed:
        return [f"cannot read VERSION at {previous_ref}: {previous}"]
    version_path = ROOT / "VERSION"
    problem = regular_file_problem(version_path, "VERSION")
    if problem is not None:
        return [f"cannot read current VERSION: {problem}"]
    try:
        current = version_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        return [f"cannot read current VERSION: {exc}"]
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
    """Keep recognized provider-shaped model IDs out of portable skill policy."""
    candidates = (
        list(paths)
        if paths is not None
        else [path for path in sorted(PLUGIN_ROOT.rglob("*")) if path.is_file()]
    )
    errors: list[str] = []
    for path in candidates:
        if path.is_symlink():
            errors.append(f"cannot scan linked model policy: {display_path(path)}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            if path.suffix.lower() in MARKDOWN_SUFFIXES:
                errors.append(f"cannot scan non-UTF-8 model policy {path}: {exc}")
            continue
        except OSError as exc:
            errors.append(f"cannot scan model policy {path}: {exc}")
            continue
        reported: set[str] = set()
        for representation in scan_representations(path, content):
            for match in CONCRETE_MODEL_ID.finditer(representation):
                relative = display_path(path)
                message = f"concrete model ID {match.group(0)!r} in {relative}"
                if message not in reported:
                    errors.append(message)
                    reported.add(message)
    return errors


def validate_continuity_hook(path: Path | None = None) -> list[str]:
    """Permit exactly one read-only SessionStart continuity hook."""
    path = path or PLUGIN_ROOT / "hooks/hooks.json"
    if not path.is_file():
        return ["plugin must ship hooks/hooks.json with the continuity hook"]
    if path.is_symlink():
        return ["plugin hooks/hooks.json must be a regular file, not a link"]
    relative = display_path(path)
    try:
        payload = load_json_text(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot read {relative}: {exc}"]
    if not isinstance(payload, dict):
        return [f"{relative} must contain an object"]
    errors: list[str] = []
    unknown_root = sorted(set(payload) - {"description", "hooks"})
    if unknown_root:
        errors.append(
            f"{relative} has unsupported top-level fields: {', '.join(unknown_root)}"
        )
    description = payload.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{relative} description must be a nonempty string")
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict) or set(hooks) != {"SessionStart"}:
        errors.append(f"{relative} must declare only SessionStart hooks")
        return errors
    groups = hooks["SessionStart"]
    if not isinstance(groups, list) or not groups:
        errors.append(f"{relative} must list its SessionStart groups")
        return errors
    if len(groups) != 2:
        errors.append(
            f"{relative} must declare exactly the startup|clear and "
            "compact|resume matcher groups"
        )
    matcher_groups: list[frozenset[str]] = []
    for index, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            errors.append(f"{relative} matcher group {index} must be an object")
            continue
        unknown_group = sorted(set(group) - {"matcher", "hooks"})
        if unknown_group:
            errors.append(
                f"{relative} matcher group {index} has unsupported fields: "
                f"{', '.join(unknown_group)}"
            )
        matcher = group.get("matcher")
        handlers = group.get("hooks")
        if not isinstance(matcher, str) or not matcher:
            errors.append(f"{relative} matcher group {index} matcher must be a nonempty string")
            continue
        sources = matcher.split("|")
        source_group = frozenset(sources)
        if (
            len(sources) != 2
            or matcher not in {"startup|clear", "compact|resume"}
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
        unknown_handler = sorted(set(handler) - {"type", "command", "timeout"})
        if unknown_handler:
            errors.append(
                f"{relative} handler has unsupported fields: {', '.join(unknown_handler)}"
            )
        hook_type = handler.get("type")
        command = handler.get("command")
        timeout = handler.get("timeout")
        if not isinstance(hook_type, str) or hook_type != "command":
            errors.append(f"{relative} handler type must be the string 'command'")
        if not isinstance(command, str) or not command.strip():
            errors.append(f"{relative} handler command must be a nonempty string")
        else:
            if SAFE_ECHO_COMMAND.fullmatch(command) is None:
                errors.append(
                    f"{relative} handler must use the portable safe echo-literal command shape"
                )
            if (
                source_group == frozenset({"compact", "resume"})
                and HANDOFF_STATE_REFERENCE.search(command) is not None
            ):
                errors.append(
                    f"{relative} compact|resume reminder must not select handoff state"
                )
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, int)
            or timeout <= 0
        ):
            errors.append(f"{relative} handler timeout must be a positive integer")
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
    yaml = yaml_library()

    path = skill_dir / "agents/openai.yaml"
    relative = display_path(path)
    if not path.is_file():
        return []
    if path.is_symlink():
        return [f"{relative} must be a regular file, not a link"]
    errors: list[str] = []
    try:
        payload = load_yaml_text(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"cannot read {relative}: {exc}"]
    if not isinstance(payload, dict):
        return [f"{relative} must contain a YAML mapping"]
    if not set(payload) <= {"interface", "policy"}:
        errors.append(f"{relative} may contain only interface and policy")
    interface = payload.get("interface")
    if "interface" in payload and not isinstance(interface, dict):
        errors.append(f"{relative} interface must be a mapping when present")
    elif isinstance(interface, dict):
        expected_interface = {"display_name", "short_description", "default_prompt"}
        if not set(interface) <= expected_interface:
            errors.append(
                f"{relative} interface may contain only display_name, "
                "short_description, and default_prompt"
            )
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
        if not set(policy) <= {"allow_implicit_invocation"}:
            errors.append(
                f"{relative} policy may contain only allow_implicit_invocation"
            )
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
    if skill_file.is_symlink():
        return [f"top-level skill {name} SKILL.md must be a regular file, not a link"]

    metadata, frontmatter_error = skill_frontmatter(skill_file)
    relative = display_path(skill_file)
    if frontmatter_error is not None:
        errors.append(f"invalid skill {relative}: {frontmatter_error}")
    elif metadata is not None:
        invalid_keys = [key for key in metadata if not isinstance(key, str)]
        if invalid_keys:
            errors.append(f"{relative} frontmatter keys must be strings")
        unsupported = sorted(
            key
            for key in metadata
            if isinstance(key, str) and key not in AGENT_SKILL_FIELDS
        )
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
    """Keep Markdown under references/ and require every resource to be reachable."""
    root = skill_dir.resolve()
    skill_file = skill_dir / "SKILL.md"
    references = skill_dir / "references"
    errors: list[str] = []
    if references.is_symlink():
        errors.append(
            f"skill {skill_dir.name} references/ must be a directory, not a link"
        )
        return errors
    references_root = references.resolve()
    resources: list[Path] = []
    for path in markdown_files(skill_dir):
        relative = display_path(path, skill_dir)
        if path.is_symlink():
            errors.append(
                f"skill {skill_dir.name} Markdown must be a regular file, not a link: "
                f"{relative}"
            )
            continue
        resources.append(path)
        resolved = path.resolve()
        if resolved != skill_file.resolve() and not resolved.is_relative_to(references_root):
            errors.append(
                f"skill {skill_dir.name} has Markdown outside SKILL.md and references/: "
                f"{relative}"
            )
    if not references.is_dir():
        return errors

    pending = [skill_file.resolve()]
    seen: set[Path] = set()
    reachable: set[Path] = set()
    while pending:
        source = pending.pop()
        if source in seen or not source.is_file():
            continue
        seen.add(source)
        try:
            targets = markdown_targets(source, include_images=False)
        except (OSError, UnicodeError) as exc:
            relative = display_path(source)
            errors.append(f"cannot inspect skill references from {relative}: {exc}")
            continue
        for target in targets:
            try:
                candidate = local_link(source, target)
            except DisallowedLocalLink:
                relative = display_path(source, root)
                errors.append(
                    f"skill {skill_dir.name} has a disallowed Markdown destination: "
                    f"{relative} -> {target}"
                )
                continue
            if (
                candidate is None
                or candidate.suffix.lower() not in MARKDOWN_SUFFIXES
                or not candidate.is_relative_to(root)
                or not path_exists_with_exact_spelling(candidate)
                or not candidate.is_file()
            ):
                continue
            reachable.add(candidate)
            pending.append(candidate)

    markdown_references = {
        path.resolve()
        for path in resources
        if path.resolve().is_relative_to(references_root)
    }
    orphans = sorted(markdown_references - reachable)
    errors.extend(
        f"skill {skill_dir.name} has unreachable Markdown reference: "
        f"{display_path(path, root)}"
        for path in orphans
    )
    return errors


def validate_plugin_links() -> list[str]:
    """Keep every local Markdown link inside the shipped plugin and resolvable."""
    errors: list[str] = []
    for path in markdown_files(PLUGIN_ROOT):
        relative = display_path(path)
        if path.is_symlink():
            errors.append(
                f"plugin Markdown must be a regular file, not a link: {relative}"
            )
            continue
        try:
            targets = markdown_targets(path)
            contains_html = markdown_contains_raw_html(path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read Markdown {relative}: {exc}")
            continue
        if contains_html:
            errors.append(f"plugin Markdown must not contain raw HTML: {relative}")
        for target in targets:
            try:
                candidate = local_link(path, target)
            except DisallowedLocalLink:
                errors.append(f"plugin local-file link is not allowed: {relative} -> {target}")
                continue
            if candidate is None:
                continue
            try:
                candidate.relative_to(PLUGIN_ROOT.resolve())
            except ValueError:
                errors.append(f"plugin link escapes package: {relative} -> {target}")
                continue
            if not path_exists_with_exact_spelling(candidate):
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
    if sources_path.is_symlink() or notices_path.is_symlink():
        return ["SOURCES.json and THIRD_PARTY_NOTICES.md must be regular files, not links"]

    relative = display_path(sources_path)
    try:
        payload = load_json_text(sources_path.read_text(encoding="utf-8"))
        notices = notices_path.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot read third-party provenance: {exc}"]
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        return [f"{relative} must contain a sources list"]
    errors: list[str] = []
    if set(payload) != {"schema_version", "sources"}:
        errors.append(f"{relative} may contain only schema_version and sources")
    schema_version = payload.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != 1
    ):
        errors.append(f"{relative} schema_version must be the integer 1")
    if not payload["sources"]:
        errors.append(f"{relative} sources must not be empty when the manifest is present")
    if not notices.strip():
        errors.append("THIRD_PARTY_NOTICES.md must not be empty")
    normalized_notices = " ".join(notices.split())
    for index, source in enumerate(payload["sources"]):
        label = f"{relative} source {index + 1}"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        allowed_source_fields = {
            "repository",
            "commit",
            "license",
            "copyright",
            "provenance",
            "adaptations",
        }
        if not set(source) <= allowed_source_fields:
            errors.append(f"{label} has unsupported fields")
        repository = source.get("repository")
        try:
            parsed = urlsplit(repository) if isinstance(repository, str) else None
        except ValueError:
            parsed = None
        if parsed is None or parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{label} repository must be an HTTPS source URL")
        commit = source.get("commit")
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-fA-F]{40}", commit) is None:
            errors.append(f"{label} commit must be a pinned 40-character hexadecimal revision")
        license_name = source.get("license")
        if license_name != "MIT":
            errors.append(f"{label} license must be the exact SPDX identifier MIT")
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
        if license_name == "MIT":
            copyright_notice = source.get("copyright")
            if not isinstance(copyright_notice, str) or not copyright_notice.strip():
                errors.append(f"{label} MIT source copyright must be present")
            for paragraph_name, paragraph in (
                ("permission", MIT_PERMISSION_PARAGRAPH),
                ("condition", MIT_CONDITION_PARAGRAPH),
                ("warranty", MIT_WARRANTY_PARAGRAPH),
            ):
                if " ".join(paragraph.split()) not in normalized_notices:
                    errors.append(
                        f"THIRD_PARTY_NOTICES.md must include the canonical MIT "
                        f"{paragraph_name} paragraph"
                    )
            if isinstance(copyright_notice, str) and copyright_notice.strip():
                complete_notice = " ".join(
                    (
                        "MIT License",
                        copyright_notice.strip(),
                        MIT_PERMISSION_PARAGRAPH,
                        MIT_CONDITION_PARAGRAPH,
                        MIT_WARRANTY_PARAGRAPH,
                    )
                )
                if " ".join(complete_notice.split()) not in normalized_notices:
                    errors.append(
                        f"THIRD_PARTY_NOTICES.md must include one complete canonical MIT "
                        f"notice for {copyright_notice!r}"
                    )
        adaptations = source.get("adaptations")
        if not isinstance(adaptations, list) or not adaptations:
            errors.append(f"{label} adaptations must be a nonempty list")
            continue
        source_skills: set[str] = set()
        for adaptation_index, adaptation in enumerate(adaptations):
            item_label = f"{label} adaptation {adaptation_index + 1}"
            if not isinstance(adaptation, dict):
                errors.append(f"{item_label} must be an object")
                continue
            if set(adaptation) != {"skill", "source_paths", "files"}:
                errors.append(
                    f"{item_label} must contain only skill, source_paths, and files"
                )
            skill = adaptation.get("skill")
            if not isinstance(skill, str) or skill not in skill_names:
                errors.append(f"{item_label} must name an existing packaged skill")
            elif skill in source_skills:
                errors.append(f"adapted skill {skill} is declared more than once for {label}")
            else:
                source_skills.add(skill)
            source_paths = adaptation.get("source_paths")
            if not isinstance(source_paths, list) or not source_paths:
                errors.append(f"{item_label} source_paths must be a nonempty list")
            else:
                for source_path in source_paths:
                    if not isinstance(source_path, str) or not source_path.strip():
                        errors.append(f"{item_label} source_paths must contain nonempty paths")
                        continue
                    if not is_normalized_relative_posix_path(source_path):
                        errors.append(
                            f"{item_label} source path must be one normalized relative POSIX path"
                        )
            files = adaptation.get("files")
            if not isinstance(files, list) or not files:
                errors.append(f"{item_label} files must be a nonempty list")
            elif isinstance(skill, str) and skill in skill_names:
                root = PLUGIN_ROOT / "skills" / skill
                for declared in files:
                    if not isinstance(declared, str) or not declared.strip():
                        errors.append(f"{item_label} files must contain nonempty paths")
                        continue
                    if not is_normalized_relative_posix_path(declared):
                        errors.append(
                            f"{item_label} file must be one normalized relative POSIX path: "
                            f"{declared!r}"
                        )
                        continue
                    try:
                        candidate = (root / declared).resolve()
                        candidate.relative_to(root.resolve())
                    except (OSError, RuntimeError, ValueError):
                        errors.append(f"{item_label} file escapes skill {skill}: {declared}")
                        continue
                    if not path_exists_with_exact_spelling(candidate) or not candidate.is_file():
                        errors.append(f"{item_label} declares missing file for {skill}: {declared}")
        for value, field in ((repository, "repository"), (commit, "commit"), (license_name, "license")):
            if isinstance(value, str) and value and value not in notices:
                errors.append(f"THIRD_PARTY_NOTICES.md must mention source {field} {value!r}")
    return errors


def validate_manifest_component_fields(
    host: str, manifest: dict[str, object]
) -> list[str]:
    """Keep host manifests limited to metadata and this package's one component."""
    metadata_fields = HOST_MANIFEST_METADATA_FIELDS[host]
    host_components = HOST_MANIFEST_COMPONENT_FIELDS[host]
    accepted = metadata_fields | host_components
    errors: list[str] = []
    unknown = sorted(set(manifest) - accepted)
    if unknown:
        errors.append(
            f"{host} manifest has unsupported fields: {', '.join(unknown)}"
        )
    disallowed_components = sorted(
        (set(manifest) & host_components) - PACKAGE_MANIFEST_COMPONENT_FIELDS
    )
    if disallowed_components:
        errors.append(
            f"{host} manifest may declare only the skills component, not: "
            f"{', '.join(disallowed_components)}"
        )
    return errors


def validate_marketplace_catalogs() -> list[str]:
    """Bind each host catalog to one available SkipHow package."""
    errors: list[str] = []
    try:
        codex = load_json(".agents/plugins/marketplace.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read Codex marketplace: {exc}")
    else:
        if set(codex) != {"name", "interface", "plugins"}:
            errors.append("Codex marketplace must contain only name, interface, and plugins")
        if codex.get("name") != "skiphow" or codex.get("interface") != {
            "displayName": "SkipHow"
        }:
            errors.append("Codex marketplace catalog identity must be SkipHow")
        plugins = codex.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1:
            errors.append("Codex marketplace must contain exactly one plugin entry")
        else:
            entry = plugins[0]
            expected = {
                "name": "skiphow",
                "source": {"source": "local", "path": "./plugins/skiphow"},
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                    "products": ["CODEX"],
                },
                "category": "Developer Tools",
            }
            if entry != expected:
                errors.append(
                    "Codex marketplace entry must have the exact SkipHow identity, "
                    "local source, availability policy, product scope, and category"
                )

    try:
        claude = load_json(".claude-plugin/marketplace.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read Claude marketplace: {exc}")
    else:
        if set(claude) != {"name", "owner", "description", "plugins"}:
            errors.append(
                "Claude marketplace must contain only name, owner, description, and plugins"
            )
        if claude.get("name") != "skiphow":
            errors.append("Claude marketplace catalog identity must be skiphow")
        owner = claude.get("owner")
        if owner != {"name": "mzored", "url": "https://github.com/mzored"}:
            errors.append(
                "Claude marketplace owner identity must be mzored at its HTTPS repository URL"
            )
        description = claude.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append("Claude marketplace description must be a nonempty string")
        plugins = claude.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1:
            errors.append("Claude marketplace must contain exactly one plugin entry")
        elif plugins[0] != {"name": "skiphow", "source": "./plugins/skiphow"}:
            errors.append(
                "Claude marketplace entry must have the exact SkipHow identity and local source"
            )
    return errors


def validate_plugin_static() -> list[str]:
    """Check the single-owner-skill package shared by Codex and Claude."""
    errors = validate_plugin_root_directory()
    if errors:
        return errors
    codex_path = PLUGIN_ROOT / ".codex-plugin/plugin.json"
    claude_path = PLUGIN_ROOT / ".claude-plugin/plugin.json"
    owner_skill = PLUGIN_ROOT / "skills/skiphow/SKILL.md"
    for path in (codex_path, claude_path, owner_skill):
        if not path.is_file():
            relative = display_path(path)
            errors.append(f"missing plugin file: {relative}")
        elif path.is_symlink():
            errors.append(f"plugin file must be regular, not a link: {display_path(path)}")
    if errors:
        return errors

    try:
        codex = load_json_text(codex_path.read_text(encoding="utf-8"))
        claude = load_json_text(claude_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot read plugin manifests: {exc}"]
    for host, manifest in (("Codex", codex), ("Claude", claude)):
        if not isinstance(manifest, dict) or manifest.get("name") != "skiphow":
            errors.append(f"{host} manifest must describe the skiphow plugin")
            continue
        errors.extend(validate_manifest_component_fields(host, manifest))
        if manifest.get("skills") != "./skills/":
            errors.append(f"{host} manifest must load ./skills/")
        if manifest.get("license") != "MIT":
            errors.append(f"{host} manifest must declare the packaged MIT license")

    shipped = {
        path.relative_to(PLUGIN_ROOT).as_posix()
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    absent = sorted(CORE_PACKAGE_FILES - shipped)
    if absent:
        errors.append(f"plugin is missing required files: {', '.join(absent)}")
    errors.extend(validate_package_path_portability(shipped))
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
    root_license = ROOT / "LICENSE"
    root_license_problem = regular_file_problem(root_license, "root LICENSE")
    package_license_problem = regular_file_problem(package_license, "plugin LICENSE")
    if root_license_problem is not None:
        errors.append(root_license_problem)
    if package_license_problem is not None:
        errors.append("plugin must include the repository MIT license")
    elif root_license_problem is None:
        try:
            licenses_match = package_license.read_bytes() == root_license.read_bytes()
        except OSError:
            licenses_match = False
        if not licenses_match:
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

    errors.extend(validate_marketplace_catalogs())
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
        + validate_site()
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
