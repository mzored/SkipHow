#!/usr/bin/env python3
"""Locate and slice Claude Code sessions that ran the SkipHow skill.

The audit reads evidence, not multi-megabyte transcripts. This helper finds
candidate sessions, slices one into a digest, and greps back into the raw bytes
on demand. It never judges: it reports what a run was given, what actually
entered its context, what it changed, and what it said. Every conformance call
belongs to the reader.

    sessions.py list [--since YYYY-MM-DD] [--all]
    sessions.py digest <session> [--report-chars N] [--json]
    sessions.py grep <session> <pattern> [--max N]
    sessions.py coverage
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from collections import Counter
from pathlib import Path

MARKERS = (
    b'"attributionPlugin":"skiphow"',
    b"plugins/skiphow/skills/skiphow/SKILL.md",
    b".agents/skills/skiphow/SKILL.md",
)
SKILL_BODY = "Base directory for this skill:"
SKILL_NAME_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
PLUGIN_VERSION_PATTERN = r"[0-9]+(?:\.[0-9]+)+(?:[-+][0-9A-Za-z.-]+)?"
VERSION_RE = re.compile(
    rf"skiphow[/\\]skiphow[/\\]({PLUGIN_VERSION_PATTERN})[/\\]skills"
)
BASE_DIRECTORY_RE = re.compile(rf"{re.escape(SKILL_BODY)}\s*([^\r\n]+)")
NAMESPACED_SKILL_RE = re.compile(rf"^[/$]?skiphow:(?P<name>{SKILL_NAME_PATTERN})$")
SKILL_PATH_RES = (
    (
        "plugin",
        re.compile(
            rf"(?:^|[/\\])skiphow[/\\]skiphow[/\\]"
            rf"(?P<version>{PLUGIN_VERSION_PATTERN})[/\\]skills[/\\]"
            rf"(?P<name>{SKILL_NAME_PATTERN})(?P<file>[/\\]SKILL\.md)?"
            rf"(?=$|[/\\\s\"'`<>),;\]}}])"
        ),
    ),
    (
        "plugin",
        re.compile(
            rf"(?<![A-Za-z0-9_.-])plugins[/\\]skiphow[/\\]skills[/\\]"
            rf"(?P<name>{SKILL_NAME_PATTERN})(?P<file>[/\\]SKILL\.md)?"
            rf"(?=$|[/\\\s\"'`<>),;\]}}])"
        ),
    ),
    (
        "project",
        re.compile(
            rf"(?<![A-Za-z0-9_.-])\.agents[/\\]skills[/\\]"
            rf"(?P<name>{SKILL_NAME_PATTERN})(?P<file>[/\\]SKILL\.md)?"
            rf"(?=$|[/\\\s\"'`<>),;\]}}])"
        ),
    ),
)
LEGACY_REFERENCES = (
    "decision",
    "delivery",
    "diagnosis",
    "engineering",
    "github",
    "intake",
    "long-work",
    "model-routing",
    "worktrees",
)
HEADINGS = ("Result", "Evidence", "Rulings and findings", "Saved follow-ups", "Limits")
HEADING_RE = re.compile(
    r"^\s{0,3}(?:#{1,4}\s*)?(?:\*\*|__)?\s*"
    r"(Result|Evidence|Rulings and findings|Saved follow-ups|Limits)"
    r"\s*(?:\*\*|__)?\s*[:—–-]?\s*",
    re.MULTILINE,
)
FINDING_TAGS = ("TRACKED", "SAVED", "UNSAVED", "DISMISSED")
# Tokens that are not SKILL.md findings tags; a run using one is worth surfacing.
FOREIGN_TAGS = ("PERSISTED", "RESOLVED", "IN_SCOPE", "EXPECTED", "NONMATERIAL")
READ_VERBS = {"cat", "bat", "head", "tail", "awk", "less", "more", "nl", "cut", "strings", "xxd"}
SEARCH_VERBS = {"grep", "rg", "ag", "ack", "find", "ls", "wc", "stat", "git", "diff"}
WRITE_VERBS = {"rm", "mv", "cp", "tee", "touch"}
STRUCTURED_WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
CODEX_JSON_EVENT_TYPES = {
    "thread.started",
    "turn.started",
    "turn.completed",
    "turn.failed",
    "item.started",
    "item.updated",
    "item.completed",
    "error",
}
CODEX_STARTED_TOOL_TYPES = {
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "collab_tool_call",
    "web_search",
}
AUDITED_RE = re.compile(r"Audited `([0-9a-f]{8})`")


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_HOME") or Path.home() / ".claude")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def reference_names() -> tuple[str, ...]:
    """Return current reference names plus the retired 1.x audit surface."""
    current = repository_root() / "plugins/skiphow/skills/skiphow/references"
    shipped = {path.stem for path in current.glob("*.md")} if current.is_dir() else set()
    return tuple(sorted(shipped | set(LEGACY_REFERENCES)))


REFERENCES = reference_names()


def contains_marker(path: Path) -> bool:
    """Scan for the attribution marker without holding the file in memory."""
    tail = b""
    overlap = max(map(len, MARKERS))
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1 << 20):
                window = tail + chunk
                if any(marker in window for marker in MARKERS):
                    return True
                tail = chunk[-overlap:]
    except OSError:
        return False
    return False


def iter_records(path: Path) -> tuple[list[dict], int]:
    """Parse a transcript, tolerating lines corrupted by interleaved writes."""
    records: list[dict] = []
    broken = 0
    try:
        handle = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return records, broken
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                broken += 1
                continue
            if isinstance(value, dict):
                records.append(value)
    return records, broken


def blocks(record: dict) -> list[dict]:
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def text_of(record: dict) -> str:
    return "\n".join(b.get("text") or "" for b in blocks(record) if b.get("type") == "text")


def nested_strings(value: object):
    """Yield strings from one transcript value without retaining the enclosing payload."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from nested_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_strings(child)


def skill_injection_texts(record: dict) -> list[str]:
    """Return injected skill bodies from text and tool-result blocks."""
    if record.get("isSidechain"):
        return []
    found: list[str] = []
    for block in blocks(record):
        if block.get("type") == "text":
            candidates = [block.get("text") or ""]
        elif block.get("type") == "tool_result":
            candidates = list(nested_strings(block.get("content")))
        else:
            continue
        found.extend(text for text in candidates if SKILL_BODY in text)
    return found


def skill_paths(text: str, require_file: bool) -> list[dict[str, str]]:
    """Recognize package and project skill paths without returning the private path."""
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for source, pattern in SKILL_PATH_RES:
        for match in pattern.finditer(text):
            if require_file and not match.group("file"):
                continue
            version = match.groupdict().get("version") or "unknown"
            key = (match.group("name"), source, version)
            if key in seen:
                continue
            seen.add(key)
            found.append(
                {
                    "name": match.group("name"),
                    "source": source,
                    "version": version,
                    "_needle": match.group(0),
                }
            )
    return found


def skiphow_attributed(value: object) -> bool:
    """Find Claude's plugin attribution without assuming where the host nests it."""
    if isinstance(value, dict):
        if value.get("attributionPlugin") == "skiphow":
            return True
        return any(skiphow_attributed(child) for child in value.values())
    if isinstance(value, list):
        return any(skiphow_attributed(child) for child in value)
    return False


def detect_skills(records: list[dict]) -> list[dict]:
    """Summarize observed top-level skill activation and file access.

    The summary contains no raw path. Historical and future sibling names are
    discovered from transcript evidence rather than a package roster.
    """
    evidence: dict[tuple[str, str, str], Counter[str]] = {}

    def add(name: str, source: str, version: str, signal: str) -> None:
        evidence.setdefault((name, source, version), Counter())[signal] += 1

    for record in records:
        for injected in skill_injection_texts(record):
            for line in BASE_DIRECTORY_RE.findall(injected):
                for hit in skill_paths(line, require_file=False):
                    add(hit["name"], hit["source"], hit["version"], "activated")

        item = record.get("item") if isinstance(record.get("item"), dict) else record
        if (
            item.get("type") == "command_execution"
            and record.get("type") == "item.completed"
        ):
            command = item.get("command") or ""
            if isinstance(command, list):
                command = " ".join(str(part) for part in command)
            succeeded = item.get("status") == "completed" and item.get("exit_code") in (None, 0)
            command_hits: set[tuple[str, str, str, str]] = set()
            for hit in skill_paths(command, require_file=True):
                signal = (
                    classify_command(command, hit["_needle"])
                    if succeeded
                    else "attempted"
                )
                command_hits.add(
                    (hit["name"], hit["source"], hit["version"], signal)
                )
            for name, source, version, signal in command_hits:
                add(name, source, version, signal)
        elif item.get("type") == "file_change" and record.get("type") == "item.completed":
            change_hits: set[tuple[str, str, str]] = set()
            for change in item.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                path = change.get("path")
                if not isinstance(path, str):
                    continue
                for hit in skill_paths(path, require_file=True):
                    change_hits.add((hit["name"], hit["source"], hit["version"]))
            signal = "authored" if item.get("status") == "completed" else "attempted"
            for name, source, version in change_hits:
                add(name, source, version, signal)

        if record.get("type") != "assistant" or record.get("isSidechain"):
            continue
        for block in blocks(record):
            if block.get("type") != "tool_use":
                continue
            tool = block.get("name") or "?"
            data = block.get("input") or {}
            if tool == "Skill":
                invoked = data.get("skill") or data.get("name") or ""
                match = NAMESPACED_SKILL_RE.fullmatch(invoked) if isinstance(invoked, str) else None
                if match:
                    add(match.group("name"), "plugin", "unknown", "activated")
                elif (
                    isinstance(invoked, str)
                    and re.fullmatch(SKILL_NAME_PATTERN, invoked)
                    and skiphow_attributed(block)
                ):
                    add(invoked, "plugin", "unknown", "activated")

            block_hits: set[tuple[str, str, str, str]] = set()
            for value in nested_strings(data):
                for hit in skill_paths(value, require_file=True):
                    if tool == "Read":
                        signal = "read"
                    elif tool == "Bash":
                        signal = classify_command(data.get("command", ""), hit["_needle"])
                    elif tool in {"Grep", "Glob"}:
                        signal = "searched"
                    elif tool in STRUCTURED_WRITE_TOOLS:
                        signal = "authored"
                    else:
                        signal = "mentioned"
                    block_hits.add((hit["name"], hit["source"], hit["version"], signal))
            for name, source, version, signal in block_hits:
                add(name, source, version, signal)

    # A Skill call often precedes a versioned read or injected body. Attach its
    # activation signal to that version when the evidence is unambiguous.
    for (name, source, version), signals in list(evidence.items()):
        if version != "unknown" or "activated" not in signals:
            continue
        known = [
            other_signals
            for (other_name, other_source, other_version), other_signals in evidence.items()
            if other_name == name and other_source == source and other_version != "unknown"
            and ({"activated", "read"} & set(other_signals))
        ]
        if len(known) == 1:
            known[0]["activated"] = max(known[0]["activated"], signals["activated"])
            del signals["activated"]
        if not signals:
            del evidence[(name, source, version)]

    signal_order = {
        name: index
        for index, name in enumerate(
            ("activated", "read", "searched", "authored", "attempted", "mentioned")
        )
    }
    return [
        {
            "name": name,
            "source": source,
            "version": version,
            "signals": {
                signal: count
                for signal, count in sorted(
                    signals.items(), key=lambda item: (signal_order.get(item[0], 99), item[0])
                )
            },
        }
        for (name, source, version), signals in sorted(evidence.items())
    ]


def package_reference(version: str, name: str) -> tuple[str, str]:
    """Read exact tagged or cached bytes before a visibly weaker HEAD fallback."""
    root = repository_root()
    relative = f"plugins/skiphow/skills/skiphow/references/{name}.md"
    tag = f"v{version}"
    try:
        tagged = subprocess.run(
            ["git", "show", f"{tag}:{relative}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if tagged.returncode == 0 and tagged.stdout.strip():
            return tagged.stdout, "tag"
        tag_exists = subprocess.run(
            ["git", "rev-parse", "--verify", f"{tag}^{{commit}}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if tag_exists.returncode == 0:
            return "", "absent_in_version"
    except OSError:
        pass
    cached = (
        claude_home()
        / "plugins/cache/skiphow/skiphow"
        / version
        / "skills/skiphow/references"
        / f"{name}.md"
    )
    try:
        return cached.read_text(encoding="utf-8"), "cache"
    except OSError:
        pass
    for ref, source in ((f"HEAD:{relative}", "HEAD"),):
        try:
            out = subprocess.run(
                ["git", "show", ref], cwd=root, capture_output=True, text=True, check=False
            )
        except OSError:
            break
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout, source
    return "", "missing"


def fingerprints(body: str, exclude: str) -> list[str]:
    """Pick fragments that only appear if the reference itself entered context."""
    parts: list[str] = []
    for sentence in re.split(r"(?<=[.;:])\s+|\n", body):
        fragment = " ".join(sentence.split())
        if not 60 <= len(fragment) <= 120 or '"' in fragment or "\\" in fragment:
            continue
        if fragment in exclude:
            continue
        parts.append(fragment)
    if not parts:
        return []
    return list(dict.fromkeys([parts[0], parts[len(parts) // 2], parts[-1]]))


def classify_command(command: str, needle: str) -> str:
    """Say whether a shell command read a file, searched it, or wrote it.

    The governing verb is the last known command word before the path, so a
    pipeline and a quoted pattern containing separators both classify correctly.
    """
    known = READ_VERBS | SEARCH_VERBS | WRITE_VERBS | {"sed"}
    for segment in re.split(r";|&&|\|\||\n", command):
        position = segment.find(needle)
        if position < 0:
            continue
        if re.search(r">>?\s*\S*" + re.escape(needle), segment) or "sed -i" in segment:
            return "authored"
        verb = ""
        for word in segment[:position].split():
            token = Path(word.split("=")[-1].strip("\"'`")).name
            if token in known:
                verb = token
        if verb in WRITE_VERBS:
            return "authored"
        if verb in READ_VERBS:
            return "read"
        if verb == "sed":
            return "read" if re.search(r"-n|\d+p", segment) else "searched"
        if verb in SEARCH_VERBS:
            return "searched"
    return "mentioned"


def detect_references(path: Path, records: list[dict], version: str) -> dict[str, dict]:
    """Two signals: reference bytes present in context, and how a command touched it."""
    skill_body = "\n".join(t for r in records if SKILL_BODY in (t := text_of(r)))
    probes: dict[str, list[str]] = {}
    sources: dict[str, str] = {}
    for name in REFERENCES:
        body, sources[name] = package_reference(version, name)
        probes[name] = fingerprints(body, skill_body) if body else []

    hits = {name: 0 for name in REFERENCES}
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if SKILL_BODY in line:
                    continue
                for name, fragments in probes.items():
                    if hits[name] >= len(fragments) or not fragments:
                        continue
                    hits[name] = sum(1 for f in fragments if f in line) or hits[name]
    except OSError:
        pass

    verbs: dict[str, set[str]] = {name: set() for name in REFERENCES}
    for record in records:
        if record.get("type") != "assistant":
            continue
        for block in blocks(record):
            if block.get("type") != "tool_use":
                continue
            data = block.get("input") or {}
            payload = json.dumps(data, ensure_ascii=False)
            for name in REFERENCES:
                needle = f"references/{name}.md"
                if needle not in payload:
                    continue
                if block.get("name") == "Read":
                    verbs[name].add("read")
                elif block.get("name") == "Bash":
                    verbs[name].add(classify_command(data.get("command", ""), needle))
                else:
                    verbs[name].add("mentioned")

    out: dict[str, dict] = {}
    for name in REFERENCES:
        probe_count = len(probes[name])
        hit = hits[name]
        action = verbs[name]
        if sources[name] == "absent_in_version":
            verdict, confidence = "absent_in_version", "n/a"
        elif probe_count and hit == probe_count:
            verdict, confidence = "loaded", "high"
        elif probe_count and hit:
            verdict, confidence = "partially_loaded", "medium"
        elif "read" in action:
            verdict, confidence = "likely_loaded", "medium" if probe_count else "low"
        elif "authored" in action:
            verdict, confidence = "authored", "high"
        elif "searched" in action:
            verdict, confidence = "searched", "high"
        elif action:
            verdict, confidence = "mentioned", "low"
        else:
            verdict, confidence = "not_loaded", "high" if probe_count else "low"
        # Tagged and installed version caches identify the bytes the run had.
        if (
            sources[name] not in {"tag", "cache"}
            and confidence == "high"
            and verdict in {"loaded", "not_loaded"}
        ):
            confidence = "medium"
        out[name] = {
            "verdict": verdict,
            "confidence": confidence,
            "fingerprints": f"{hit}/{probe_count}" if probe_count else "unavailable",
            "probe_source": sources[name],
            "commands": sorted(action) or ["none"],
        }
    return out


def owner_turns(records: list[dict]) -> list[dict]:
    """Owner speech arrives four ways.

    Typed prompts and queued commands are obvious. An answer to AskUserQuestion is
    an owner decision that only exists as a tool result, and missing it hides the
    moment a run's scope was widened or settled.
    """
    asked: set[str] = set()
    for record in records:
        if record.get("type") != "assistant" or record.get("isSidechain"):
            continue
        for block in blocks(record):
            if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                asked.add(block.get("id") or "")

    turns: list[dict] = []
    for record in records:
        for block in blocks(record):
            if block.get("type") != "tool_result" or block.get("tool_use_id") not in asked:
                continue
            answer = block.get("content")
            if isinstance(answer, list):
                answer = " ".join(
                    b.get("text") or "" for b in answer if isinstance(b, dict)
                )
            if isinstance(answer, str) and answer.strip():
                turns.append(
                    {"at": record.get("timestamp", ""), "channel": "answered", "said": answer.strip()}
                )
        if record.get("isSidechain"):
            continue
        origin = (record.get("origin") or {}).get("kind")
        attachment = record.get("attachment") or {}
        said = ""
        channel = ""
        if origin == "human":
            said, channel = text_of(record), "typed"
        elif attachment.get("type") == "queued_command":
            raw = attachment.get("prompt") or attachment.get("command") or ""
            if isinstance(raw, list):
                raw = "\n".join(
                    b.get("text") or "" for b in raw if isinstance(b, dict) and b.get("type") == "text"
                )
            said = raw if isinstance(raw, str) else ""
            channel = "queued"
            # Host plumbing arrives on the same channel; it is not owner speech.
            if said.lstrip().startswith(("<task-notification", "<local-command", "<command-name")):
                continue
        if not said.strip():
            continue
        turns.append({"at": record.get("timestamp", ""), "channel": channel, "said": said.strip()})
    return sorted(turns, key=lambda turn: turn["at"])


def select_reports(records: list[dict]) -> list[dict]:
    """A report is an assistant block carrying at least two of the five headings."""
    found: list[dict] = []
    for record in records:
        text = assistant_text(record)
        if not text:
            continue
        names = {m.group(1) for m in HEADING_RE.finditer(text)}
        if len(names) >= 2:
            found.append({"at": record.get("timestamp", ""), "text": text, "headings": sorted(names)})
    return found


def assistant_text(record: dict) -> str:
    """Return one root assistant message from Claude or Codex JSONL."""
    if record.get("type") == "assistant" and not record.get("isSidechain"):
        return text_of(record)
    item = record.get("item")
    if (
        record.get("type") == "item.completed"
        and isinstance(item, dict)
        and item.get("type") == "agent_message"
        and isinstance(item.get("text"), str)
    ):
        return item["text"]
    return ""


def final_assistant_text(records: list[dict]) -> str:
    """Return what the root actually said last, independent of report formatting."""
    trailing = [text for record in records if (text := assistant_text(record)).strip()]
    return trailing[-1] if trailing else ""


def report_text(records: list[dict], versions: list[str]) -> str:
    """Select the report according to the contract version that produced it."""
    parsed = [
        tuple(int(part) for part in match.group(0).split("."))
        for version in versions
        if (match := re.match(r"[0-9]+(?:\.[0-9]+)*", version))
    ]
    reports = select_reports(records)
    if parsed and max(parsed) < (1, 14) and reports:
        return reports[-1]["text"]
    return final_assistant_text(records)


def codex_turn_status(records: list[dict]) -> str:
    """Return the final observed Codex turn state without using file age."""
    last_started = max(
        (index for index, record in enumerate(records) if record.get("type") == "turn.started"),
        default=-1,
    )
    if last_started < 0:
        return "not_observed"
    terminal = [
        (index, record["type"])
        for index, record in enumerate(records)
        if index > last_started and record.get("type") in {"turn.completed", "turn.failed"}
    ]
    if not terminal:
        return "unfinished"
    return "failed" if terminal[-1][1] == "turn.failed" else "completed"


def compaction_status(records: list[dict]) -> bool | str:
    """Report only observable compaction; Codex exec JSONL does not expose it."""
    if any(record.get("isCompactSummary") or record.get("type") == "compacted" for record in records):
        return True
    if any(record.get("type") in CODEX_JSON_EVENT_TYPES for record in records):
        return "unknown"
    return False


def ended_mid_tool(records: list[dict]) -> bool:
    """True when the final tool call never received a result."""
    pending: set[str] = set()
    for record in records:
        if record.get("isSidechain"):
            continue
        item = record.get("item")
        if isinstance(item, dict) and item.get("id"):
            item_type = item.get("type")
            if item_type in CODEX_STARTED_TOOL_TYPES:
                if record.get("type") == "item.started":
                    pending.add(item["id"])
                elif record.get("type") in {"item.completed", "item.failed"}:
                    pending.discard(item["id"])
        for block in blocks(record):
            if block.get("type") == "tool_use":
                pending.add(block.get("id") or "")
            elif block.get("type") == "tool_result":
                pending.discard(block.get("tool_use_id") or "")
    return bool(pending)


def in_flight(path: Path, records: list[dict] | None = None, minutes: int = 15) -> bool:
    """A session written to recently is probably still running."""
    if records:
        if codex_turn_status(records) in {"completed", "failed"}:
            return False
    try:
        return (time.time() - path.stat().st_mtime) < minutes * 60
    except OSError:
        return False


def checkout_root(cwd: str) -> str:
    """Normalize a live path to its Git worktree root, retaining stale paths as given."""
    if not cwd:
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return os.path.normpath(cwd)
    return os.path.realpath(result.stdout.strip()) if result.returncode == 0 else os.path.normpath(cwd)


def identity_transitions(records: list[dict]) -> list[dict]:
    """Return the observed checkout identity timeline without judging it."""
    found: list[dict] = []
    roots: dict[str, str] = {}
    cwd = branch = ""
    for record in records:
        raw_cwd = record.get("cwd")
        if raw_cwd and raw_cwd not in roots:
            roots[raw_cwd] = checkout_root(raw_cwd)
        next_cwd = roots[raw_cwd] if raw_cwd else cwd
        next_branch = record.get("gitBranch") or branch
        if (next_cwd, next_branch) != (cwd, branch) and (next_cwd or next_branch):
            found.append(
                {
                    "at": record.get("timestamp", ""),
                    "cwd": next_cwd or "unknown",
                    "branch": next_branch or "unknown",
                }
            )
        cwd, branch = next_cwd, next_branch
    return found


def digest(path: Path, report_chars: int) -> dict:
    records, broken = iter_records(path)
    if not records:
        raise SystemExit(f"{path} holds no readable records")

    tools: Counter[str] = Counter()
    command_results: Counter[str] = Counter()
    models: Counter[str] = Counter()
    usage: Counter[str] = Counter()
    delegations: list[dict] = []
    structured_writes: list[dict] = []
    stamps: list[str] = []
    injections = 0
    cwd = branch = host = ""
    skill_text = ""

    for record in records:
        cwd = record.get("cwd") or cwd
        branch = record.get("gitBranch") or branch
        host = record.get("version") or host
        if record.get("timestamp"):
            stamps.append(record["timestamp"])
        if record.get("type") == "turn.completed":
            for key, value in (record.get("usage") or {}).items():
                if isinstance(value, int):
                    usage[key] += value
        item = record.get("item")
        if record.get("type") == "item.completed" and isinstance(item, dict):
            item_type = item.get("type")
            if item_type in CODEX_STARTED_TOOL_TYPES:
                tools[str(item_type)] += 1
            if item_type == "file_change" and item.get("status") == "completed":
                for change in item.get("changes") or []:
                    if isinstance(change, dict):
                        structured_writes.append(
                            {
                                "at": record.get("timestamp", ""),
                                "tool": "file_change",
                                "path": change.get("path") or "unknown",
                            }
                        )
            elif item_type == "command_execution":
                status = str(item.get("status") or "unknown")
                exit_code = item.get("exit_code")
                result = f"{status}:{exit_code}" if isinstance(exit_code, int) else status
                command_results[result] += 1
        injected = skill_injection_texts(record)
        if injected:
            injections += 1
            skill_text += "\n".join(injected)
        if record.get("type") != "assistant" or record.get("isSidechain"):
            continue
        message = record.get("message") or {}
        if message.get("model"):
            models[message["model"]] += 1
        for key, value in (message.get("usage") or {}).items():
            if isinstance(value, int):
                usage[key] += value
        for block in blocks(record):
            if block.get("type") != "tool_use":
                continue
            name = block.get("name") or "?"
            tools[name] += 1
            data = block.get("input") or {}
            if name == "Agent":
                delegations.append(
                    {
                        "role": data.get("subagent_type") or "unnamed",
                        "task": (data.get("description") or "")[:80],
                    }
                )
            if name in STRUCTURED_WRITE_TOOLS:
                structured_writes.append(
                    {
                        "at": record.get("timestamp", ""),
                        "tool": name,
                        "path": data.get("file_path") or data.get("notebook_path") or "unknown",
                    }
                )
    observed_skills = detect_skills(records)
    injected_versions = set(VERSION_RE.findall(skill_text))
    read_versions = {
        skill["version"]
        for skill in observed_skills
        if skill["version"] != "unknown"
        and ({"activated", "read"} & set(skill["signals"]))
    }
    versions = sorted(injected_versions | read_versions) or ["unknown"]
    if len(versions) == 1:
        reference_evidence = detect_references(path, records, versions[0])
    else:
        reference_evidence = {
            name: {
                "verdict": "unverified_mixed_version",
                "confidence": "n/a",
                "fingerprints": "unavailable",
                "probe_source": "mixed_versions",
                "commands": ["not_evaluated"],
            }
            for name in REFERENCES
        }
    turn_state = codex_turn_status(records)
    reports = select_reports(records)
    selected = report_text(records, versions)
    selected_headings = {match.group(1) for match in HEADING_RE.finditer(selected)}
    if not selected:
        selected = "(no assistant text found)"
    return {
        "session": next(
            (
                record["thread_id"]
                for record in records
                if record.get("type") == "thread.started"
                and isinstance(record.get("thread_id"), str)
                and record["thread_id"]
            ),
            path.stem,
        ),
        "project": Path(cwd).name or "unknown",
        "branch": branch or "unknown",
        "host": host or "unknown",
        "plugin_versions": versions,
        "window": [stamps[0] if stamps else "unknown", stamps[-1] if stamps else "unknown"],
        "records": len(records),
        "unparseable_lines": broken,
        "skill_injections": injections,
        "models": dict(models),
        "owner_turns": owner_turns(records),
        "skills": observed_skills,
        "references": reference_evidence,
        "tools": dict(tools.most_common()),
        "command_results": dict(command_results),
        "delegations": delegations,
        "structured_writes": structured_writes,
        "identity_changes": identity_transitions(records),
        "confounders": {
            "compaction": compaction_status(records),
            "reports_found": len(reports),
            "ended_mid_tool": ended_mid_tool(records),
            "unfinished_turn": turn_state == "unfinished",
            "turn_failed": turn_state == "failed",
            "mixed_plugin_versions": len(versions) > 1,
            # A transcript still being appended to owes no report yet.
            "in_flight": in_flight(path, records),
        },
        "usage": dict(usage),
        "report": {
            "headings_present": [h for h in HEADINGS if h in selected_headings],
            "headings_missing": [h for h in HEADINGS if h not in selected_headings],
            "tag_counts": {t: len(re.findall(rf"\b{t}\b", selected)) for t in FINDING_TAGS},
            "foreign_tags": {
                t: n for t in FOREIGN_TAGS if (n := len(re.findall(rf"\b{t}\b", selected)))
            },
            "text": selected[-report_chars:] if report_chars else selected,
        },
    }


def discover(home: Path, since: str | None) -> list[dict]:
    projects = home / "projects"
    root = str(repository_root())
    rows: list[dict] = []
    if not projects.is_dir():
        return rows
    for path in sorted(projects.glob("*/*.jsonl")):
        if not contains_marker(path):
            continue
        records, _ = iter_records(path)
        if not records:
            continue
        cwd = next((r.get("cwd") for r in records if r.get("cwd")), "") or ""
        real = os.path.realpath(cwd) if cwd else ""
        reason = None
        if not cwd:
            reason = "no-cwd"
        elif real == os.path.realpath(root) or real.startswith(os.path.realpath(root) + os.sep):
            reason = "self-development"
        elif real.startswith(("/private/tmp", "/tmp", "/private/var/folders")):
            reason = "scratch-harness"
        stamps = sorted(r["timestamp"] for r in records if r.get("timestamp"))
        started = stamps[0] if stamps else ""
        if since and started[:10] and started[:10] < since:
            continue
        body = "\n".join(text for record in records for text in skill_injection_texts(record))
        rows.append(
            {
                "session": path.stem,
                "path": str(path),
                "project": Path(cwd).name or "unknown",
                "started": started or "unknown",
                "records": len(records),
                "megabytes": round(path.stat().st_size / 1e6, 1),
                "versions": sorted(set(VERSION_RE.findall(body))) or ["unknown"],
                "excluded": reason,
            }
        )
    return sorted(rows, key=lambda item: item["started"])


def resolve(home: Path, target: str) -> Path:
    candidate = Path(target)
    if candidate.is_file():
        return candidate
    matches = sorted((home / "projects").glob(f"*/{target}*.jsonl"))
    if not matches:
        raise SystemExit(f"no transcript found for {target!r}")
    return matches[0]


def coverage(home: Path) -> str:
    """Derive audit coverage from the receipts, not from a second ledger."""
    seen: set[str] = set()
    for note in (repository_root() / "docs/research").rglob("*.md"):
        seen |= set(AUDITED_RE.findall(note.read_text(encoding="utf-8", errors="replace")))
    rows = [r for r in discover(home, None) if not r["excluded"]]
    lines = ["Coverage from docs/research (marker: Audited `<8-char session>`):"]
    for row in rows:
        state = "covered" if row["session"][:8] in seen else "UNAUDITED"
        lines.append(f"  {row['session'][:8]}  {row['started'][:10]}  {row['project']:<16} {state}")
    return "\n".join(lines) if rows else "No sessions found."


def render_list(rows: list[dict], show_all: bool) -> str:
    included = [r for r in rows if not r["excluded"]]
    shown = rows if show_all else included
    if not shown:
        return "No sessions found."
    width = max(len(r["project"]) for r in shown)
    lines = [f"{len(included)} external session(s); {len(rows) - len(included)} excluded."]
    for row in shown:
        note = f"  [{row['excluded']}]" if row["excluded"] else ""
        lines.append(
            f"  {row['session'][:8]}  {row['started'][:19]}  {row['project']:<{width}}  "
            f"v{','.join(row['versions'])}  {row['megabytes']}MB  {row['records']} rec{note}"
        )
    return "\n".join(lines)


def render_digest(data: dict) -> str:
    out = [
        f"session {data['session']}  project {data['project']}  branch {data['branch']}",
        f"host {data['host']}  plugin {','.join(data['plugin_versions'])}  "
        f"skill injected {data['skill_injections']}x",
        f"window {data['window'][0]} .. {data['window'][1]}  {data['records']} records  "
        f"{data['unparseable_lines']} unreadable",
        f"models {data['models']}  confounders {data['confounders']}",
        "",
        "OWNER TURNS",
    ]
    for turn in data["owner_turns"] or []:
        out.append(f"  [{turn['at'][:19]} {turn['channel']}] {' '.join(turn['said'].split())[:600]}")
    if not data["owner_turns"]:
        out.append("  none captured")
    out += ["", "SKILLS"]
    for skill in data["skills"]:
        signals = ",".join(
            f"{name}:{count}" for name, count in skill["signals"].items()
        )
        out.append(
            f"  {skill['name']:<24} source {skill['source']:<7} "
            f"version {skill['version']:<12} signals {signals}"
        )
    if not data["skills"]:
        out.append("  none observed")
    out += ["", "REFERENCES"]
    for name, info in data["references"].items():
        out.append(
            f"  {name:<14} {info['verdict']:<16} confidence {info['confidence']:<6} "
            f"fingerprints {info['fingerprints']:<6} from {info['probe_source']:<7} "
            f"commands {','.join(info['commands'])}"
        )
    out += [
        "",
        f"TOOLS        {data['tools']}",
        f"COMMANDS     {data['command_results']}",
        f"DELEGATIONS  {data['delegations'] or 'none'}",
        "",
        f"STRUCTURED WRITES ({len(data['structured_writes'])})",
    ]
    for write in data["structured_writes"]:
        out.append(f"  [{write['at'][:19]}] {write['tool']} {write['path']}")
    if not data["structured_writes"]:
        out.append("  none")
    out += [
        "",
        f"IDENTITY CHANGES ({len(data['identity_changes'])})",
    ]
    for change in data["identity_changes"]:
        out.append(
            f"  [{change['at'][:19]}] cwd {change['cwd']}  branch {change['branch']}"
        )
    if not data["identity_changes"]:
        out.append("  none")
    report = data["report"]
    out += [
        "",
        f"REPORT legacy headings observed {report['headings_present']}",
        f"       legacy headings absent   {report['headings_missing']}",
        f"       legacy finding tags      {report['tag_counts']}",
    ]
    if report["foreign_tags"]:
        out.append(f"       undefined tokens {report['foreign_tags']}")
    out += ["", "FINAL ASSISTANT TEXT", report["text"] or "(no assistant text found)"]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=claude_home())
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", help="find sessions that ran the SkipHow skill")
    listing.add_argument("--since", help="ISO date; skip sessions that started earlier")
    listing.add_argument("--all", action="store_true", help="also show excluded sessions")
    listing.add_argument("--json", action="store_true")

    one = sub.add_parser("digest", help="slice one session into reviewable evidence")
    one.add_argument("target", help="session id, id prefix, or transcript path")
    one.add_argument("--report-chars", type=int, default=4000)
    one.add_argument("--json", action="store_true")

    finder = sub.add_parser("grep", help="search the raw transcript of one session")
    finder.add_argument("target")
    finder.add_argument("pattern")
    finder.add_argument("--max", type=int, default=20)
    finder.add_argument("--chars", type=int, default=240)

    sub.add_parser("coverage", help="which sessions the receipts already cover")

    args = parser.parse_args()
    if args.command == "list":
        rows = discover(args.home, args.since)
        print(json.dumps(rows, indent=2) if args.json else render_list(rows, args.all))
    elif args.command == "digest":
        data = digest(resolve(args.home, args.target), args.report_chars)
        print(json.dumps(data, indent=2, ensure_ascii=False) if args.json else render_digest(data))
    elif args.command == "grep":
        path = resolve(args.home, args.target)
        pattern = re.compile(args.pattern)
        shown = 0
        with path.open(encoding="utf-8", errors="replace") as handle:
            for number, line in enumerate(handle, 1):
                match = pattern.search(line)
                if not match:
                    continue
                start = max(0, match.start() - args.chars // 2)
                try:
                    at = (json.loads(line) or {}).get("timestamp", "")
                except (json.JSONDecodeError, AttributeError):
                    at = ""
                print(f"L{number} [{at}]: ...{line[start : start + args.chars]}...")
                shown += 1
                if shown >= args.max:
                    print(f"(stopped at {args.max} matches)")
                    break
        if not shown:
            print("no matches")
    else:
        print(coverage(args.home))


if __name__ == "__main__":
    main()
