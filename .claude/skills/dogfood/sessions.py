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

MARKER = b'"attributionPlugin":"skiphow"'
SKILL_BODY = "Base directory for this skill:"
VERSION_RE = re.compile(r"skiphow/skiphow/([0-9]+(?:\.[0-9]+)*)/skills")
REFERENCES = (
    "decision",
    "delivery",
    "diagnosis",
    "engineering",
    "github",
    "intake",
    "long-work",
    "model-routing",
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
MUTATION = re.compile(
    r"\b(git\s+(?:commit|push|merge|rebase|reset|tag|branch\s+-[dD])"
    r"|gh\s+(?:issue|pr)\s+(?:create|edit|close|reopen|comment|delete|merge|ready|lock)"
    r"|gh\s+(?:release|repo)\s+(?:create|edit|delete|upload)"
    r"|gh\s+api\s+(?:-X\s*)?(?:POST|PATCH|PUT|DELETE)"
    r"|npm\s+publish|rm\s+-[rf]|sed\s+-i"
    r"|>>?\s*(?!/dev/|&)[\w./~$-]+"
    r"|tee\s+(?!-a\b)[\w./-]+)",
    re.IGNORECASE,
)
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
AUDITED_RE = re.compile(r"Audited `([0-9a-f]{8})`")


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_HOME") or Path.home() / ".claude")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def contains_marker(path: Path) -> bool:
    """Scan for the attribution marker without holding the file in memory."""
    tail = b""
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1 << 20):
                if MARKER in tail + chunk:
                    return True
                tail = chunk[-len(MARKER) :]
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


def package_reference(version: str, name: str) -> tuple[str, str]:
    """Read a reference as it shipped. Says which bytes it got, so a fallback is visible."""
    root = repository_root()
    relative = f"plugins/skiphow/skills/skiphow/references/{name}.md"
    for ref, source in ((f"v{version}:{relative}", "tag"), (f"HEAD:{relative}", "HEAD")):
        try:
            out = subprocess.run(
                ["git", "show", ref], cwd=root, capture_output=True, text=True, check=False
            )
        except OSError:
            break
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout, source
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
        if probe_count and hit == probe_count:
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
        # Probes taken from anything but the run's own tag are weaker evidence.
        if sources[name] != "tag" and confidence == "high" and verdict != "not_loaded":
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
        if record.get("type") != "assistant" or record.get("isSidechain"):
            continue
        text = text_of(record)
        names = {m.group(1) for m in HEADING_RE.finditer(text)}
        if len(names) >= 2:
            found.append({"at": record.get("timestamp", ""), "text": text, "headings": sorted(names)})
    return found


def ended_mid_tool(records: list[dict]) -> bool:
    """True when the final tool call never received a result."""
    pending: set[str] = set()
    for record in records:
        if record.get("isSidechain"):
            continue
        for block in blocks(record):
            if block.get("type") == "tool_use":
                pending.add(block.get("id") or "")
            elif block.get("type") == "tool_result":
                pending.discard(block.get("tool_use_id") or "")
    return bool(pending)


def in_flight(path: Path, minutes: int = 15) -> bool:
    """A session written to recently is probably still running."""
    try:
        return (time.time() - path.stat().st_mtime) < minutes * 60
    except OSError:
        return False


def digest(path: Path, report_chars: int) -> dict:
    records, broken = iter_records(path)
    if not records:
        raise SystemExit(f"{path} holds no readable records")

    tools: Counter[str] = Counter()
    models: Counter[str] = Counter()
    usage: Counter[str] = Counter()
    mutations: list[dict] = []
    delegations: list[dict] = []
    stamps: list[str] = []
    injections = 0
    compaction = False
    cwd = branch = host = ""
    skill_text = ""

    for record in records:
        cwd = record.get("cwd") or cwd
        branch = record.get("gitBranch") or branch
        host = record.get("version") or host
        if record.get("timestamp"):
            stamps.append(record["timestamp"])
        if record.get("isCompactSummary"):
            compaction = True
        text = text_of(record)
        if SKILL_BODY in text:
            injections += 1
            skill_text += text
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
            if name in WRITE_TOOLS:
                mutations.append({"tool": name, "detail": data.get("file_path", "?")})
            elif name == "Bash":
                command = data.get("command", "")
                hits = [" ".join(m.split()) for m in MUTATION.findall(command)]
                if hits:
                    tally = Counter(hits)
                    verbs = ", ".join(
                        verb if count == 1 else f"{verb} x{count}" for verb, count in tally.items()
                    )
                    mutations.append(
                        {
                            "tool": "Bash",
                            "verb": verbs[:90],
                            "detail": " ".join(command.split())[:400],
                        }
                    )

    versions = sorted(set(VERSION_RE.findall(skill_text))) or ["unknown"]
    reports = select_reports(records)
    selected = reports[-1]["text"] if reports else ""
    if not reports:
        # No report-shaped message: show how the session actually ended, so the
        # reader can tell an abandoned run from one that answered off-format.
        trailing = [
            text_of(r)
            for r in records
            if r.get("type") == "assistant" and not r.get("isSidechain") and text_of(r).strip()
        ]
        selected = (
            "(no report-shaped message found; last assistant text follows)\n\n" + trailing[-1]
            if trailing
            else "(no report-shaped message and no assistant text found)"
        )
    return {
        "session": path.stem,
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
        "references": detect_references(path, records, versions[0]),
        "tools": dict(tools.most_common()),
        "delegations": delegations,
        "mutations": mutations,
        "confounders": {
            "compaction": compaction,
            "reports_found": len(reports),
            "ended_mid_tool": ended_mid_tool(records),
            # A transcript still being appended to owes no report yet.
            "in_flight": in_flight(path),
        },
        "usage": dict(usage),
        "report": {
            "headings_present": [h for h in HEADINGS if h in (reports[-1]["headings"] if reports else [])],
            "headings_missing": [h for h in HEADINGS if h not in (reports[-1]["headings"] if reports else [])],
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
        body = "\n".join(t for r in records if SKILL_BODY in (t := text_of(r)))
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
        f"DELEGATIONS  {data['delegations'] or 'none'}",
        "",
        f"MUTATIONS ({len(data['mutations'])})",
    ]
    for mutation in data["mutations"]:
        prefix = f"Bash [{mutation['verb']}]" if mutation["tool"] == "Bash" else mutation["tool"]
        out.append(f"  {prefix} {mutation['detail']}")
    if not data["mutations"]:
        out.append("  none")
    report = data["report"]
    out += [
        "",
        f"REPORT headings present {report['headings_present']}",
        f"       headings missing {report['headings_missing']}",
        f"       finding tags     {report['tag_counts']}",
    ]
    if report["foreign_tags"]:
        out.append(f"       undefined tokens {report['foreign_tags']}")
    out += ["", "REPORT TEXT", report["text"] or "(no report-shaped message found)"]
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
                print(f"L{number}: ...{line[start : start + args.chars]}...")
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
