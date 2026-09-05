#!/usr/bin/env python3
"""Enable, check, or disable SkipHow's default governance in the instruction file a host reads.

The helper resolves the trusted user instruction file the way the host itself
discovers it, so the owned activation block lands where the host will read it:

- Codex reads ``AGENTS.override.md`` in its home when that file exists and is
  not empty, and ``AGENTS.md`` otherwise; ``CODEX_HOME`` relocates the home.
- Claude Code reads ``CLAUDE.md`` and every unconditional ``rules/*.md`` file
  in its configuration directory for every project; ``CLAUDE_CONFIG_DIR``
  relocates that directory. A rule with ``paths:`` frontmatter is conditional.

It reports three facts separately: whether the block is configured in a file
the host reads, whether the plugin appears installed and enabled on the host,
and that loading is only ever observed inside a session. It writes nothing
without ``--apply``, changes only its own block, never writes through a
symbolic link, and preserves every other byte.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import difflib
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import tempfile

try:
    import tomllib
except ImportError:  # Python before 3.11
    tomllib = None


ACTIVATION = (
    "For current-project requests, load the installed SkipHow skill before consequential "
    "action and use it as the adaptive virtual CTO policy. Do not load it for unrelated "
    "conversation or for a request that only discusses SkipHow without adopting it."
)
MARKER = b"<!-- skiphow activation"
END = b"<!-- /skiphow activation -->\n"
START = re.compile(rb"<!-- skiphow activation v1 separator=([01]) created=([01]) -->\n")
HOSTS = ("codex", "claude-code")
PLUGIN_ID = "skiphow@skiphow"
MANAGED_POLICY = {
    "codex": (Path("/etc/codex/requirements.toml"), Path("/etc/codex/config.toml")),
    "claude-code": (
        Path("/Library/Application Support/ClaudeCode/managed-settings.json"),
        Path("/Library/Application Support/ClaudeCode/CLAUDE.md"),
        Path("/etc/claude-code/managed-settings.json"),
        Path("/etc/claude-code/CLAUDE.md"),
    ),
}
LOADING_NOTE = "Runtime loading is observed only in a fresh session; no configuration check proves it."


def locate(data: bytes) -> tuple[int, int, bool] | None:
    """Accept only the exact block we own; leave edits for human inspection."""
    if MARKER not in data and b"<!-- /skiphow activation" not in data:
        return None
    matches = list(START.finditer(data))
    if len(matches) != 1 or data.count(MARKER) != 1 or data.count(b"<!-- /skiphow activation") != 1:
        raise ValueError("Activation markers are edited, incomplete, or duplicated; inspect the file.")
    match = matches[0]
    body = ACTIVATION.encode("utf-8") + b"\n" + END
    end = match.end() + len(body)
    if data[match.end():end] != body:
        raise ValueError("The owned activation block was edited; inspect it before changing it.")
    start = match.start()
    if match.group(1) == b"1":
        if start == 0 or data[start - 1:start] != b"\n":
            raise ValueError("The owned activation separator was edited; inspect the file.")
        start -= 1
    return start, end, match.group(2) == b"1"


def transform(original: bytes | None, action: str) -> bytes | None:
    data = original if original is not None else b""
    data.decode("utf-8")
    block = locate(data)
    if action == "remove":
        if block is None:
            return original
        start, end, created = block
        prefix, suffix = data[:start], data[end:]
        needs_separator = prefix and suffix and not prefix.endswith((b"\n", b"\r")) and not suffix.startswith((b"\n", b"\r"))
        separator = b"\n" if needs_separator else b""
        remaining = prefix + separator + suffix
        return None if created and not remaining else remaining
    if block is not None:
        return original
    separator = bool(data and not data.endswith(b"\n"))
    start = f"<!-- skiphow activation v1 separator={int(separator)} created={int(original is None)} -->\n"
    return data + (b"\n" if separator else b"") + start.encode() + ACTIVATION.encode() + b"\n" + END


def atomic_write(target: Path, original: bytes | None, changed: bytes) -> None:
    """Stage the complete file before publishing it; leave the original on failure."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            if original is not None:
                temporary.chmod(stat.S_IMODE(target.stat().st_mode))
            stream.write(changed)
            stream.flush()
            os.fsync(stream.fileno())
        if target.is_symlink() or (target.read_bytes() if target.exists() else None) != original:
            raise ValueError("The target changed since inspection; rerun the preview.")
        if original is None:
            os.link(temporary, target)  # Publish only if the target is still absent.
        else:
            os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@dataclass
class Layout:
    """Where a host reads trusted user instructions and what else it exposes."""

    host: str | None
    home: Path | None
    effective: Path
    candidates: list[Path]
    read_by_host: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    managed: list[Path] = field(default_factory=list)
    availability: str = "not checked; an explicit target names no host"

    def __post_init__(self) -> None:
        if not self.read_by_host:
            self.read_by_host = [self.effective]


def _codex_availability(home: Path) -> str:
    cache = home / "plugins" / "cache" / "skiphow" / "skiphow"
    versions = sorted(item.name for item in cache.iterdir() if item.is_dir()) if cache.is_dir() else []
    if not versions:
        return "not installed: no plugin cache for skiphow in this Codex home"
    config = home / "config.toml"
    cached = f"cached versions {', '.join(versions)}"
    if not config.is_file():
        return f"installed: {cached}; no config.toml"
    if tomllib is None:
        return f"installed, enablement unknown: this interpreter cannot parse config.toml (Python 3.11 or later can); {cached}"
    try:
        enabled = tomllib.loads(config.read_text(encoding="utf-8")).get("plugins", {}).get(PLUGIN_ID, {}).get("enabled")
    except (OSError, UnicodeError, ValueError):
        return f"installed, enablement unknown: config.toml could not be parsed; {cached}"
    state = "installed" if enabled is not False else "installed but disabled in config.toml"
    return f"{state}: {cached}"


def _claude_availability(home: Path) -> str:
    inventory = home / "plugins" / "installed_plugins.json"
    if not inventory.is_file():
        return "not installed: no plugin inventory in this Claude Code configuration directory"
    try:
        entries = json.loads(inventory.read_text(encoding="utf-8")).get("plugins", {}).get(PLUGIN_ID, [])
    except (OSError, UnicodeError, ValueError):
        return "unknown: the plugin inventory could not be read"
    if not isinstance(entries, list) or not entries:
        return "not installed: the inventory lists no skiphow entry"
    scopes = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        scope = entry.get("scope", "?")
        version = entry.get("version", "?")
        scopes.append(f"{scope} {version}" if scope != "project" else f"project {version} ({entry.get('projectPath', '?')})")
    state = "installed"
    settings = home / "settings.json"
    if settings.is_file():
        try:
            if json.loads(settings.read_text(encoding="utf-8")).get("enabledPlugins", {}).get(PLUGIN_ID) is False:
                state = "installed but disabled in settings.json"
        except (OSError, UnicodeError, ValueError):
            state = "installed, enablement unknown: settings.json could not be read"
    if not any(scope.startswith("user ") for scope in scopes):
        state += " for specific projects only"
    return f"{state}: {'; '.join(scopes)}"


def resolve(host: str, environ: dict[str, str] | None = None) -> Layout:
    """Resolve the effective trusted instruction file the way the host discovers it."""
    environ = os.environ if environ is None else environ
    if host == "codex":
        home = Path(environ.get("CODEX_HOME") or (Path.home() / ".codex")).expanduser().absolute()
        override, agents = home / "AGENTS.override.md", home / "AGENTS.md"
        layout = Layout("codex", home, agents, [agents], availability=_codex_availability(home) if home.is_dir() else "not installed: the Codex home does not exist")
        layout.notes.append("Codex reads AGENTS.override.md in its home when that file exists and is not empty, and AGENTS.md otherwise; CODEX_HOME relocates the home.")
        if override.exists():
            if _nonempty(override):
                layout.effective, layout.candidates, layout.read_by_host = override, [override, agents], [override]
                layout.notes.append(f"{override.name} has content, so Codex does not read {agents.name} here.")
            else:
                layout.candidates = [agents, override]
                layout.notes.append(f"{override.name} exists but is empty, so Codex skips it and reads {agents.name}; the empty file is left alone.")
    elif host == "claude-code":
        home = Path(environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")).expanduser().absolute()
        primary = home / "CLAUDE.md"
        candidates, read_by_host = [primary], [primary]
        rules = home / "rules"
        if rules.is_dir():
            for path in sorted(path for path in rules.rglob("*.md") if path.is_file()):
                candidates.append(path)
                if not _conditional(path):
                    read_by_host.append(path)
        layout = Layout("claude-code", home, primary, candidates, read_by_host, availability=_claude_availability(home) if home.is_dir() else "not installed: the Claude Code configuration directory does not exist")
        layout.notes.append("Claude Code reads CLAUDE.md and every unconditional rules/*.md file in its configuration directory for every project; a rule with paths: frontmatter applies only to matching files; CLAUDE_CONFIG_DIR relocates that directory.")
    else:
        raise ValueError(f"unknown host {host!r}; choose one of {', '.join(HOSTS)}")
    layout.managed = [path for path in MANAGED_POLICY[host] if path.exists()]
    return layout


def explicit(target: Path) -> Layout:
    return Layout(None, None, target, [target])


def _nonempty(path: Path) -> bool:
    try:
        return bool(path.read_bytes().strip())
    except OSError:
        return False


def _conditional(path: Path) -> bool:
    """A Claude rule whose frontmatter names ``paths:`` applies only to matching files."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    return end != -1 and re.search(r"^paths:", text[3:end], re.MULTILINE) is not None


def linked(target: Path) -> bool:
    return target.is_symlink() or any(parent.is_symlink() for parent in target.parents)


def read(target: Path) -> bytes | None:
    if linked(target):
        raise ValueError(f"Use an ordinary path without symbolic links: {target}")
    return target.read_bytes() if target.exists() else None


def block_state(target: Path) -> str:
    """Inspect a file, following a link for inspection only; writes never follow links."""
    if not target.exists():
        return "missing"
    try:
        data = target.read_bytes()
        return "present" if locate(data) else "absent"
    except (OSError, ValueError, UnicodeError):
        return "edited"


def status_report(layout: Layout) -> dict:
    states = {str(path): block_state(path) for path in layout.candidates}
    read_paths = {str(path) for path in layout.read_by_host}
    present = [path for path, state in states.items() if state == "present"]
    active = [path for path in present if path in read_paths]
    return {
        "host": layout.host,
        "home": str(layout.home) if layout.home else None,
        "effective_file": str(layout.effective),
        "read_by_host": sorted(read_paths),
        "block": states,
        "configured": bool(active),
        "active_blocks": active,
        "duplicate_blocks": active[1:] if len(active) > 1 else [],
        "shadowed_blocks": [path for path in present if path not in read_paths],
        "edited_blocks": [path for path, state in states.items() if state == "edited"],
        "linked_files": [str(path) for path in layout.candidates if linked(path)],
        "availability": layout.availability,
        "managed_policy": [str(path) for path in layout.managed],
        "notes": layout.notes,
        "loading": LOADING_NOTE,
    }


def print_status(report: dict) -> None:
    if report["host"]:
        print(f"host: {report['host']} (home {report['home']})")
    print(f"effective file: {report['effective_file']}")
    for path, state in report["block"].items():
        suffix = "" if path in report["read_by_host"] else " (not read by the host for every project)"
        print(f"{path}: owned activation block {state}{suffix}.")
    if report["shadowed_blocks"]:
        print("A block exists in a file the host does not read; run install to move it, or remove to delete it.")
    if report["duplicate_blocks"]:
        print("More than one file the host reads holds the block; install consolidates it into the effective file.")
    if report["edited_blocks"]:
        print("An edited or duplicated block needs inspection before the helper will change that file.")
    if report["linked_files"]:
        print("Linked files are inspected but never edited by the helper: " + ", ".join(report["linked_files"]))
    print(f"configured in a file the host reads: {'yes' if report['configured'] else 'no'}")
    print(f"plugin availability: {report['availability']}")
    for path in report["managed_policy"]:
        print(f"managed policy present: {path} (loads before user instructions and may restrict plugins; not evaluated here)")
    for note in report["notes"]:
        print(f"note: {note}")
    print("Installed package availability and runtime loading are UNVERIFIED by this check. " + LOADING_NOTE)


def plan(layout: Layout, action: str) -> list[tuple[Path, bytes | None, bytes | None]]:
    """Return (path, original, changed) for every file the action touches."""
    changes = []
    for path in layout.candidates:
        wanted = action if path == layout.effective else "remove"
        if path != layout.effective and linked(path):
            if block_state(path) == "present":
                print(f"{path}: linked file holds the block and is left in place; edit its target yourself.", file=sys.stderr)
            continue
        original = read(path)
        changed = transform(original, wanted)
        if changed != original:
            changes.append((path, original, changed))
    return changes


def show_diff(path: Path, original: bytes | None, changed: bytes | None) -> None:
    diff = difflib.unified_diff(
        (original or b"").decode().splitlines(keepends=True),
        (changed or b"").decode().splitlines(keepends=True),
        fromfile=str(path) if original is not None else "/dev/null",
        tofile=str(path) if changed is not None else "/dev/null",
    )
    for line in diff:
        sys.stdout.write(line)
        if not line.endswith("\n"):
            sys.stdout.write("\n\\ No newline at end of file\n")


def apply(path: Path, original: bytes | None, changed: bytes | None) -> None:
    if not path.parent.is_dir():
        raise ValueError(f"The parent directory must already exist: {path.parent}")
    if read(path) != original:
        raise ValueError("The target changed since inspection; rerun the preview.")
    if changed is None:
        path.unlink()
    else:
        atomic_write(path, original, changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("install", "status", "remove"))
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--host", choices=HOSTS, help="Resolve the file this host reads")
    where.add_argument("--target", type=Path, help="Explicit trusted user instruction file")
    parser.add_argument("--apply", action="store_true", help="Apply the displayed change; default is preview only")
    parser.add_argument("--json", action="store_true", help="Print the status report as JSON")
    args = parser.parse_args(argv)
    if args.action != "status" and args.json:
        parser.error("--json applies to status only")
    if args.action == "status" and args.apply:
        parser.error("status is read-only")
    try:
        layout = resolve(args.host) if args.host else explicit(args.target.expanduser().absolute())
        if args.action == "status":
            report = status_report(layout)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                print_status(report)
            return 0
        changes = plan(layout, args.action)
        if not changes:
            print(f"{layout.effective}: no change.")
            return 0
        for path, original, changed in changes:
            show_diff(path, original, changed)
        if args.apply:
            for path, original, changed in changes:
                apply(path, original, changed)
            print("Applied.")
        else:
            print("Preview only. Add --apply to write this change.")
        print(LOADING_NOTE)
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    # Convert normal process cancellation into unwinding so staged files are removed.
    def terminate(signum, _frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, terminate)
    raise SystemExit(main())
