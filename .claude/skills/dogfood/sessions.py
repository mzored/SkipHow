#!/usr/bin/env python3
"""Locate and slice sessions containing observable SkipHow evidence.

The audit reads evidence, not multi-megabyte transcripts. This helper finds
candidate sessions, slices one into a digest, and greps back into the raw bytes
on demand. It reports observable host events and exact model-visible text;
causal and conformance rulings belong to the reader.

    sessions.py list [--since YYYY-MM-DD | --on YYYY-MM-DD]
    sessions.py digest <session> [--report-chars N] [--json]
    sessions.py grep <session> <pattern> [--max N]
    sessions.py coverage
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import ntpath
import os
import re
import stat
import subprocess
import sys
import unicodedata
from collections import Counter
from contextvars import ContextVar
from datetime import date, datetime
from pathlib import Path

_RAW_PATH_SEPARATOR = rb"(?:/|\\/|\\{1,2})"
_RAW_SKILL_BOUNDARY = rb"(?![A-Za-z0-9_.-])"
MARKER_LITERAL = b"skiphow"


def _raw_json_ascii(character: str) -> bytes:
    """Match one ASCII character literally or through a valid JSON escape."""
    codepoint = f"{ord(character):04x}".encode("ascii")
    escaped = rb"\\u" + b"".join(
        rb"[" + bytes((value, value - 32)) + rb"]"
        if 97 <= value <= 102
        else bytes((value,))
        for value in codepoint
    )
    return rb"(?:" + re.escape(character.encode("ascii")) + rb"|" + escaped + rb")"


def _raw_json_text(value: str) -> bytes:
    return b"".join(_raw_json_ascii(character) for character in value)


def _raw_json_casefold_text(value: str) -> bytes:
    """Match ASCII text and JSON Unicode escapes without case sensitivity."""
    parts: list[bytes] = []
    for character in value:
        variants = {character.lower(), character.upper()}
        parts.append(
            rb"(?:" + b"|".join(_raw_json_ascii(item) for item in variants) + rb")"
        )
    return b"".join(parts)


_RAW_JSON_SKIPHOW = _raw_json_text("skiphow")
_RAW_JSON_SKIPHOW_CASEFOLD = _raw_json_casefold_text("skiphow")
_RAW_JSON_ATTRIBUTION_PLUGIN = _raw_json_text("attributionPlugin")
_RAW_JSON_COLON = _raw_json_ascii(":")
JSON_MARKER_TOKEN_RE = re.compile(_RAW_JSON_SKIPHOW_CASEFOLD)
JSON_MARKER_TOKEN_MAX_BYTES = 6 * len(MARKER_LITERAL)
MARKER_RES = (
    re.compile(
        rb'"'
        + _RAW_JSON_ATTRIBUTION_PLUGIN
        + rb'"[ \t\r\n]*:[ \t\r\n]*"'
        + _RAW_JSON_SKIPHOW
        + rb'"'
    ),
    re.compile(
        rb"(?<![A-Za-z0-9_.-])"
        + _RAW_JSON_SKIPHOW
        + _RAW_JSON_COLON
        + _RAW_JSON_SKIPHOW
        + rb"(?![A-Za-z0-9_.-])"
    ),
    re.compile(
        rb"(?<![A-Za-z0-9_.-])plugins"
        + _RAW_PATH_SEPARATOR
        + rb"cache"
        + _RAW_PATH_SEPARATOR
        + _RAW_JSON_SKIPHOW_CASEFOLD
        + _RAW_PATH_SEPARATOR
        + _RAW_JSON_SKIPHOW_CASEFOLD
        + _RAW_PATH_SEPARATOR
        + rb"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
        + _RAW_PATH_SEPARATOR
        + rb"skills"
        + _RAW_PATH_SEPARATOR
        + _RAW_JSON_SKIPHOW_CASEFOLD
        + _RAW_SKILL_BOUNDARY,
        re.IGNORECASE,
    ),
    re.compile(
        rb"(?<![A-Za-z0-9_.-])plugins"
        + _RAW_PATH_SEPARATOR
        + _RAW_JSON_SKIPHOW_CASEFOLD
        + _RAW_PATH_SEPARATOR
        + rb"skills"
        + _RAW_PATH_SEPARATOR
        + _RAW_JSON_SKIPHOW_CASEFOLD
        + _RAW_SKILL_BOUNDARY,
        re.IGNORECASE,
    ),
    re.compile(
        rb"(?<![A-Za-z0-9_.-])\.agents"
        + _RAW_PATH_SEPARATOR
        + rb"skills"
        + _RAW_PATH_SEPARATOR
        + _RAW_JSON_SKIPHOW_CASEFOLD
        + _RAW_SKILL_BOUNDARY,
        re.IGNORECASE,
    ),
)
SKILL_BODY = "Base directory for this skill:"
SKILL_NAME_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
PLUGIN_VERSION_PATTERN = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
BASE_DIRECTORY_RE = re.compile(rf"{re.escape(SKILL_BODY)}[ \t]*([^\r\n]+)")
NAMESPACED_SKILL_RE = re.compile(rf"^skiphow:(?P<name>{SKILL_NAME_PATTERN})$")
REFERENCE_ROSTER_LABEL = "(governing reference roster)"
STRUCTURED_WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
CLAUDE_TERMINAL_STOP_REASONS = {"end_turn", "stop_sequence", "refusal"}
CLAUDE_NONTERMINAL_STOP_REASONS = {
    "compaction",
    "tool_use",
    "max_tokens",
    "pause_turn",
    "model_context_window_exceeded",
}
CLAUDE_STOP_REASONS = (
    CLAUDE_TERMINAL_STOP_REASONS | CLAUDE_NONTERMINAL_STOP_REASONS
)
CODEX_STARTED_TOOL_TYPES = {
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "collab_tool_call",
    "web_search",
}
CODEX_TOOL_TYPES = CODEX_STARTED_TOOL_TYPES
CODEX_COLLAB_TOOLS = {"spawn_agent", "send_input", "wait", "close_agent"}
CODEX_COLLAB_AGENT_STATUSES = {
    "pending_init",
    "running",
    "interrupted",
    "completed",
    "errored",
    "shutdown",
    "not_found",
}
CODEX_FILE_CHANGE_KINDS = {"add", "delete", "update"}
CODEX_EVENT_TYPES = {
    "thread.started",
    "turn.started",
    "turn.completed",
    "turn.failed",
    "item.started",
    "item.updated",
    "item.completed",
    "error",
}
CODEX_ITEM_TYPES = {
    "agent_message",
    "reasoning",
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "collab_tool_call",
    "web_search",
    "todo_list",
    "error",
}
CLAUDE_RECORD_TYPES = {
    "agent-name",
    "ai-title",
    "artifact-comment-monitor",
    "assistant",
    "atis-latch",
    "attachment",
    "bridge-session",
    "compacted",
    "cost-state",
    "custom-title",
    "file-history-delta",
    "file-history-snapshot",
    "frame-link",
    "last-prompt",
    "mode",
    "permission-mode",
    "pr-link",
    "progress",
    "queue-operation",
    "relocated",
    "summary",
    "system",
    "user",
    "worktree-state",
}
CODEX_USAGE_REQUIRED_FIELDS = {
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
}
CODEX_USAGE_FIELDS = CODEX_USAGE_REQUIRED_FIELDS | {"cache_write_input_tokens"}
RUST_I64_MIN = -(1 << 63)
RUST_I64_MAX = (1 << 63) - 1
RUST_U64_MAX = (1 << 64) - 1
RUST_I32_MIN = -(1 << 31)
RUST_I32_MAX = (1 << 31) - 1
COMMAND_OWNER_FRAME_RE = re.compile(
    r"\A<command-message>.*?</command-message>\n"
    r"<command-name>(?P<command>/[^<\s]+)</command-name>\n"
    r"<command-args>(?P<arguments>.*)</command-args>\Z",
    re.DOTALL,
)
SHORT_SESSION_RE = re.compile(r"[0-9a-f]{8}")
COVERAGE_SCHEMA = "skiphow.dogfood.coverage/v1"
COVERAGE_SOURCE = "claude-code-project-transcripts"
COVERAGE_SIDECAR_RE = re.compile(
    r"field-audit-(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})\.receipts\.json"
)
COVERAGE_SESSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
COVERAGE_VERSION_RE = re.compile(
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
COVERAGE_FINGERPRINT_RE = re.compile(r"sha256-v1:[0-9a-f]{64}")
AUDIT_HOME: ContextVar[Path | None] = ContextVar("dogfood_audit_home", default=None)


def claude_home() -> Path:
    return Path(
        os.environ.get("CLAUDE_CONFIG_DIR")
        or os.environ.get("CLAUDE_HOME")
        or Path.home() / ".claude"
    )


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def plugin_cache_roots() -> tuple[Path, ...]:
    selected_home = AUDIT_HOME.get()
    if selected_home is not None:
        return (
            canonical_home_path(selected_home) / "plugins/cache/skiphow/skiphow",
        )
    return tuple(
        dict.fromkeys(
            canonical_home_path(home) / "plugins/cache/skiphow/skiphow"
            for home in (claude_home(), codex_home())
        )
    )


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def reference_names() -> tuple[str, ...]:
    """Derive current and historical direct reference names from repository evidence."""
    current = repository_root() / "plugins/skiphow/skills/skiphow/references"
    shipped = {path.stem for path in current.glob("*.md")} if current.is_dir() else set()
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--all",
                "--format=",
                "--name-only",
                "--",
                "plugins/skiphow/skills/skiphow/references",
            ],
            cwd=repository_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        result = None
    historical: set[str] = set()
    if result and result.returncode == 0:
        prefix = "plugins/skiphow/skills/skiphow/references/"
        for line in result.stdout.splitlines():
            if line.startswith(prefix) and line.endswith(".md"):
                historical.add(line[len(prefix) : -len(".md")])
    return tuple(sorted(shipped | historical))


REFERENCES = reference_names()


def raw_json_marker_token_present(value: bytes) -> bool:
    """Find a literal or JSON-Unicode-escaped marker without a large-file regex."""
    if MARKER_LITERAL in value.lower():
        return True
    # A mixed literal/escaped spelling must contain ``\\u``. Search only small
    # windows around those rare candidates; applying the expanded expression to
    # every byte of a multi-gigabyte store made discovery CPU-bound.
    position = 0
    radius = JSON_MARKER_TOKEN_MAX_BYTES - 1
    while True:
        position = value.find(b"\\u", position)
        if position < 0:
            return False
        start = max(0, position - radius)
        end = min(len(value), position + 2 + radius)
        if JSON_MARKER_TOKEN_RE.search(value[start:end]):
            return True
        position += 2


def stream_contains_marker(handle: object) -> bool:
    """Scan one already-open binary transcript with bounded overlap."""
    tail = b""
    overlap = JSON_MARKER_TOKEN_MAX_BYTES - 1
    while chunk := handle.read(1 << 20):
        window = tail + chunk
        if raw_json_marker_token_present(window):
            return True
        tail = window[-overlap:]
    return False


def regular_snapshot(status: os.stat_result) -> tuple[int, int, int, int, int]:
    """Return fields that expose replacement or in-place mutation while reading."""
    return tuple(
        getattr(status, field)
        for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    )


def opened_transcript_stable(path: Path, handle: object, before: os.stat_result) -> bool:
    """Bind consumed bytes to one stable file and the current directory entry."""
    after = os.fstat(handle.fileno())
    if regular_snapshot(before) != regular_snapshot(after):
        return False
    try:
        with open_regular_binary(path) as current:
            return os.path.samestat(before, os.fstat(current.fileno()))
    except OSError:
        return False


def contains_marker(path: Path) -> bool:
    """Conservatively prefilter valid JSON spellings; parsed records attribute."""
    with open_regular_binary(path) as handle:
        before = os.fstat(handle.fileno())
        found = stream_contains_marker(handle)
        if not opened_transcript_stable(path, handle, before):
            raise OSError(f"{path} changed during marker discovery")
        return found


def record_contains_marker(record: dict) -> bool:
    """Return whether one parsed record contains a literal SkipHow marker."""
    encoded = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return any(pattern.search(encoded) for pattern in MARKER_RES)


def local_calendar_date(timestamp: str) -> str | None:
    """Convert an ISO host timestamp to the machine's local calendar date."""
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.astimezone().date().isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def parsed_timestamp(timestamp: str) -> datetime | None:
    """Parse one host timestamp for chronological ordering."""
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.astimezone()
    except (OSError, OverflowError, ValueError):
        return None


def normalize_crlf(text: str) -> str:
    """Treat CRLF and LF as equivalent without normalizing other characters."""
    return text.replace("\r\n", "\n")


def rust_integer_valid(value: object, minimum: int, maximum: int) -> bool:
    """Return whether a JSON integer fits one exact Rust integer type."""
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


def codex_usage_valid(value: object) -> bool:
    """Validate codex-exec's current serialized Usage payload."""
    if not isinstance(value, dict) or not CODEX_USAGE_REQUIRED_FIELDS <= value.keys():
        return False
    return all(
        field not in value
        or rust_integer_valid(value[field], RUST_I64_MIN, RUST_I64_MAX)
        for field in CODEX_USAGE_FIELDS
    )


def codex_web_action_valid(value: object) -> bool:
    """Validate the current codex-exec WebSearchAction wire shape."""
    if not isinstance(value, dict):
        return False
    action_type = value.get("type")
    if action_type == "other":
        return True
    if action_type == "search":
        query = value.get("query")
        queries = value.get("queries")
        return (
            (query is None or isinstance(query, str))
            and (
                queries is None
                or isinstance(queries, list)
                and all(isinstance(query_value, str) for query_value in queries)
            )
        )
    if action_type == "open_page":
        return value.get("url") is None or isinstance(value.get("url"), str)
    if action_type == "find_in_page":
        return all(
            value.get(field) is None or isinstance(value.get(field), str)
            for field in ("url", "pattern")
        )
    return False


def codex_file_changes_valid(value: object) -> bool:
    """Validate every file-change element before treating a patch as observed."""
    if not isinstance(value, list) or not all(
        isinstance(change, dict)
        and isinstance(change.get("path"), str)
        and bool(change["path"])
        and isinstance(change.get("kind"), str)
        and change["kind"] in CODEX_FILE_CHANGE_KINDS
        for change in value
    ):
        return False
    identities = [comparable_path_token(change["path"]) for change in value]
    return all(identity is not None for identity in identities) and len(
        set(identities)
    ) == len(value)


def codex_collab_states_valid(value: object) -> bool:
    """Validate the current codex-exec collab agent-state map."""
    return isinstance(value, dict) and all(
        isinstance(thread_id, str)
        and bool(thread_id)
        and isinstance(state, dict)
        and isinstance(state.get("status"), str)
        and state["status"] in CODEX_COLLAB_AGENT_STATUSES
        and "message" in state
        and (state["message"] is None or isinstance(state["message"], str))
        and (
            state["status"] == "completed"
            or state["status"] == "errored"
            and isinstance(state["message"], str)
            or state["status"] not in {"completed", "errored"}
            and state["message"] is None
        )
        for thread_id, state in value.items()
    )


def json_values_equal(left: object, right: object) -> bool:
    """Compare JSON values without Python's bool/number coercions."""
    if not json_string_values_valid(left) or not json_string_values_valid(right):
        return False
    pending = [(left, right)]
    seen_left: set[int] = set()
    seen_right: set[int] = set()
    scalar_types = (type(None), bool, int, float, str)
    while pending:
        current_left, current_right = pending.pop()
        if type(current_left) is not type(current_right):
            return False
        if isinstance(current_left, dict):
            left_id, right_id = id(current_left), id(current_right)
            if left_id in seen_left or right_id in seen_right:
                return False
            seen_left.add(left_id)
            seen_right.add(right_id)
            if current_left.keys() != current_right.keys():
                return False
            pending.extend(
                (value, current_right[key])
                for key, value in current_left.items()
            )
            continue
        if isinstance(current_left, list):
            left_id, right_id = id(current_left), id(current_right)
            if left_id in seen_left or right_id in seen_right:
                return False
            seen_left.add(left_id)
            seen_right.add(right_id)
            if len(current_left) != len(current_right):
                return False
            pending.extend(zip(current_left, current_right))
            continue
        if type(current_left) not in scalar_types or current_left != current_right:
            return False
    return True


def result_content_parts(value: object) -> tuple[bool, list[str]]:
    """Validate and decode text-bearing Claude ToolResult content blocks."""
    found: list[str] = []
    seen: set[int] = set()

    def valid_image_source(source: object) -> bool:
        if not isinstance(source, dict) or not isinstance(source.get("type"), str):
            return False
        source_type = source["type"]
        if source_type == "base64":
            return (
                source.get("media_type")
                in {"image/jpeg", "image/png", "image/gif", "image/webp"}
                and isinstance(source.get("data"), str)
                and bool(source["data"])
            )
        if source_type == "url":
            return isinstance(source.get("url"), str) and bool(source["url"])
        if source_type == "file":
            return isinstance(source.get("file_id"), str) and bool(source["file_id"])
        return False

    def visit(current: object) -> bool:
        if not isinstance(current, dict):
            return False
        identity = id(current)
        if identity in seen:
            return False
        seen.add(identity)
        if "type" not in current:
            return False
        block_type = current["type"]
        if not isinstance(block_type, str):
            return False
        if block_type == "text":
            text = current.get("text")
            if not isinstance(text, str):
                return False
            if text:
                found.append(text)
            return True
        if block_type == "image":
            return valid_image_source(current.get("source"))
        if block_type == "search_result":
            content = current.get("content")
            if not (
                isinstance(current.get("source"), str)
                and isinstance(current.get("title"), str)
                and isinstance(content, list)
            ):
                return False
            return all(
                isinstance(item, dict)
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
                and visit(item)
                for item in content
            )
        if block_type == "document":
            source = current.get("source")
            if not isinstance(source, dict) or not isinstance(source.get("type"), str):
                return False
            source_type = source["type"]
            if source_type == "text":
                data = source.get("data")
                if source.get("media_type") != "text/plain" or not isinstance(data, str):
                    return False
                if data:
                    found.append(data)
                return True
            if source_type == "content":
                content = source.get("content")
                if isinstance(content, str):
                    if content:
                        found.append(content)
                    return True
                if not isinstance(content, list):
                    return False
                return all(
                    isinstance(item, dict)
                    and item.get("type") in {"text", "image"}
                    and visit(item)
                    for item in content
                )
            if source_type == "base64":
                return (
                    source.get("media_type") == "application/pdf"
                    and isinstance(source.get("data"), str)
                    and bool(source["data"])
                )
            if source_type == "url":
                return isinstance(source.get("url"), str) and bool(source["url"])
            if source_type == "file":
                return isinstance(source.get("file_id"), str) and bool(
                    source["file_id"]
                )
            return False
        # All other typed blocks, including output_text/resource, are opaque.
        return True

    if isinstance(value, str):
        return True, [value] if value else []
    if not isinstance(value, list):
        return False, []
    top_level_types = [
        item.get("type") for item in value if isinstance(item, dict)
    ]
    if "search_result" in top_level_types and any(
        block_type != "search_result" for block_type in top_level_types
    ):
        return False, []
    valid = all(isinstance(item, dict) and visit(item) for item in value)
    return valid, found if valid else []


def result_content_payload_valid(value: object) -> bool:
    """Validate every nested value that model-visible result extraction visits."""
    return result_content_parts(value)[0]


def json_string_values_valid(value: object) -> bool:
    """Validate values representable by serde_json without arbitrary precision."""
    pending = [value]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            if any("\ud800" <= character <= "\udfff" for character in current):
                return False
            continue
        if isinstance(current, float) and not math.isfinite(current):
            return False
        if (
            isinstance(current, int)
            and not isinstance(current, bool)
            and not RUST_I64_MIN <= current <= RUST_U64_MAX
        ):
            return False
        if isinstance(current, (list, dict)):
            identity = id(current)
            if identity in seen:
                return False
            seen.add(identity)
            if isinstance(current, list):
                pending.extend(current)
            else:
                if not all(isinstance(key, str) for key in current):
                    return False
                pending.extend(current.keys())
                pending.extend(current.values())
    return True


def codex_mcp_result_valid(value: object) -> bool:
    """Validate the optional result object emitted for an MCP terminal."""
    return value is None or (
        isinstance(value, dict)
        and isinstance(value.get("content"), list)
        and "structured_content" in value
    )


def codex_mcp_error_valid(value: object) -> bool:
    """Validate the optional error object emitted for an MCP terminal."""
    return value is None or (
        isinstance(value, dict) and isinstance(value.get("message"), str)
    )


def codex_start_valid(item: dict) -> bool:
    """Validate one current codex-exec item.started payload."""
    item_type = item.get("type")
    if item_type == "command_execution":
        return (
            isinstance(item.get("command"), str)
            and bool(item["command"])
            and item.get("aggregated_output") == ""
            and "exit_code" in item
            and item["exit_code"] is None
            and item.get("status") == "in_progress"
        )
    if item_type == "file_change":
        return codex_file_changes_valid(item.get("changes")) and item.get(
            "status"
        ) == "in_progress"
    if item_type == "mcp_tool_call":
        return (
            isinstance(item.get("server"), str)
            and bool(item["server"])
            and isinstance(item.get("tool"), str)
            and bool(item["tool"])
            and "arguments" in item
            and "result" in item
            and item["result"] is None
            and "error" in item
            and item["error"] is None
            and item.get("status") == "in_progress"
        )
    if item_type == "collab_tool_call":
        tool = item.get("tool")
        receivers = item.get("receiver_thread_ids")
        prompt = item.get("prompt")
        states = item.get("agents_states")
        return (
            isinstance(tool, str)
            and tool in CODEX_COLLAB_TOOLS
            and isinstance(item.get("sender_thread_id"), str)
            and bool(item["sender_thread_id"])
            and isinstance(receivers, list)
            and all(
                isinstance(thread_id, str) and bool(thread_id)
                for thread_id in receivers
            )
            and (tool == "wait" or len(set(receivers)) == len(receivers))
            and "prompt" in item
            and (prompt is None or isinstance(prompt, str))
            and codex_collab_states_valid(states)
            and not states
            and (
                tool == "spawn_agent"
                and not receivers
                and isinstance(prompt, str)
                or tool == "send_input"
                and len(receivers) == 1
                and isinstance(prompt, str)
                or tool == "close_agent"
                and len(receivers) == 1
                and prompt is None
                or tool == "wait"
                and prompt is None
            )
            and item.get("status") == "in_progress"
        )
    if item_type == "web_search":
        return (
            isinstance(item.get("query"), str)
            and codex_web_action_valid(item.get("action"))
        )
    return False


def codex_terminal_shape_valid(item: dict) -> bool:
    """Validate one current codex-exec item.completed tool payload."""
    item_type = item.get("type")
    if item_type == "web_search":
        return (
            isinstance(item.get("query"), str)
            and codex_web_action_valid(item.get("action"))
        )
    if item_type == "command_execution":
        exit_code = item.get("exit_code")
        status = item.get("status")
        return (
            isinstance(item.get("command"), str)
            and bool(item["command"])
            and isinstance(item.get("aggregated_output"), str)
            and "exit_code" in item
            and (
                exit_code is None
                or rust_integer_valid(exit_code, RUST_I32_MIN, RUST_I32_MAX)
            )
            and isinstance(status, str)
            and status in {"completed", "failed", "declined"}
            and (
                status == "completed"
                and exit_code == 0
                or status == "failed"
                and exit_code != 0
                or status == "declined"
                and exit_code in {None, -1}
            )
        )
    if item_type == "file_change":
        return (
            codex_file_changes_valid(item.get("changes"))
            and isinstance(item.get("status"), str)
            and item["status"] in {"completed", "failed"}
        )
    if item_type == "mcp_tool_call":
        result = item.get("result")
        error = item.get("error")
        status = item.get("status")
        return (
            isinstance(item.get("server"), str)
            and bool(item["server"])
            and isinstance(item.get("tool"), str)
            and bool(item["tool"])
            and "arguments" in item
            and "result" in item
            and codex_mcp_result_valid(result)
            and "error" in item
            and codex_mcp_error_valid(error)
            and isinstance(status, str)
            and status in {"completed", "failed"}
            and (
                status == "completed"
                and isinstance(result, dict)
                and error is None
                or status == "failed"
                and (
                    isinstance(result, dict)
                    and error is None
                    or result is None
                    and isinstance(error, dict)
                )
            )
        )
    if item_type == "collab_tool_call":
        tool = item.get("tool")
        receivers = item.get("receiver_thread_ids")
        prompt = item.get("prompt")
        status = item.get("status")
        agents_states = item.get("agents_states")
        failed_agent = isinstance(agents_states, dict) and any(
            state.get("status") in {"errored", "not_found"}
            for state in agents_states.values()
            if isinstance(state, dict)
        )
        return (
            isinstance(tool, str)
            and tool in CODEX_COLLAB_TOOLS
            and isinstance(item.get("sender_thread_id"), str)
            and bool(item["sender_thread_id"])
            and isinstance(receivers, list)
            and all(
                isinstance(thread_id, str) and bool(thread_id)
                for thread_id in receivers
            )
            and len(set(receivers)) == len(receivers)
            and "prompt" in item
            and (prompt is None or isinstance(prompt, str))
            and codex_collab_states_valid(agents_states)
            and set(agents_states) == set(receivers)
            and (
                tool == "spawn_agent"
                and len(receivers) <= 1
                and isinstance(prompt, str)
                or tool == "send_input"
                and len(receivers) == 1
                and isinstance(prompt, str)
                or tool == "close_agent"
                and len(receivers) == 1
                and prompt is None
                or tool == "wait"
                and prompt is None
            )
            and isinstance(status, str)
            and status in {"completed", "failed"}
            and (
                tool == "spawn_agent"
                and (
                    status == "completed"
                    and len(receivers) == 1
                    and not failed_agent
                    or status == "failed"
                    and (
                        not receivers
                        or len(receivers) == 1
                        and failed_agent
                    )
                )
                or tool != "spawn_agent"
                and (status == "failed") == failed_agent
            )
        )
    return False


def codex_item_wire_valid(item: object) -> bool:
    """Validate one current codex-exec ThreadItem wire payload."""
    if not (
        isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and bool(item["id"])
        and isinstance(item.get("type"), str)
        and item["type"] in CODEX_ITEM_TYPES
    ):
        return False
    item_type = item["type"]
    if item_type in {"agent_message", "reasoning"}:
        return isinstance(item.get("text"), str)
    if item_type == "command_execution":
        exit_code = item.get("exit_code")
        return (
            isinstance(item.get("command"), str)
            and isinstance(item.get("aggregated_output"), str)
            and "exit_code" in item
            and (
                exit_code is None
                or rust_integer_valid(exit_code, RUST_I32_MIN, RUST_I32_MAX)
            )
            and item.get("status")
            in {"in_progress", "completed", "failed", "declined"}
        )
    if item_type == "file_change":
        return codex_file_changes_valid(item.get("changes")) and item.get(
            "status"
        ) in {"in_progress", "completed", "failed"}
    if item_type == "mcp_tool_call":
        return (
            isinstance(item.get("server"), str)
            and isinstance(item.get("tool"), str)
            and "arguments" in item
            and "result" in item
            and codex_mcp_result_valid(item["result"])
            and "error" in item
            and codex_mcp_error_valid(item["error"])
            and item.get("status") in {"in_progress", "completed", "failed"}
        )
    if item_type == "collab_tool_call":
        return (
            isinstance(item.get("tool"), str)
            and item["tool"] in CODEX_COLLAB_TOOLS
            and isinstance(item.get("sender_thread_id"), str)
            and isinstance(item.get("receiver_thread_ids"), list)
            and all(
                isinstance(thread_id, str)
                for thread_id in item["receiver_thread_ids"]
            )
            and "prompt" in item
            and (item["prompt"] is None or isinstance(item["prompt"], str))
            and codex_collab_states_valid(item.get("agents_states"))
            and item.get("status") in {"in_progress", "completed", "failed"}
        )
    if item_type == "web_search":
        return isinstance(item.get("query"), str) and codex_web_action_valid(
            item.get("action")
        )
    if item_type == "todo_list":
        return isinstance(item.get("items"), list) and all(
            isinstance(todo, dict)
            and isinstance(todo.get("text"), str)
            and isinstance(todo.get("completed"), bool)
            for todo in item["items"]
        )
    return item_type == "error" and isinstance(item.get("message"), str)


def codex_event_valid(record: dict) -> bool:
    """Validate one current codex-exec ThreadEvent envelope and lifecycle shape."""
    event_type = record.get("type")
    if event_type == "thread.started":
        return isinstance(record.get("thread_id"), str) and bool(
            record["thread_id"]
        )
    if event_type == "turn.started":
        return True
    if event_type == "turn.completed":
        return codex_usage_valid(record.get("usage"))
    if event_type == "turn.failed":
        error = record.get("error")
        return isinstance(error, dict) and isinstance(error.get("message"), str)
    if event_type == "error":
        return isinstance(record.get("message"), str)
    if event_type not in {"item.started", "item.updated", "item.completed"}:
        return False
    item = record.get("item")
    if not codex_item_wire_valid(item):
        return False
    item_type = item["type"]
    if event_type == "item.started":
        if item_type in CODEX_STARTED_TOOL_TYPES:
            return codex_start_valid(item)
        return item_type == "todo_list"
    if event_type == "item.updated":
        return item_type == "todo_list"
    if item_type == "web_search":
        return True
    if item_type in CODEX_TOOL_TYPES:
        return codex_terminal_shape_valid(item) or codex_start_valid(item)
    return item_type in {"agent_message", "reasoning", "todo_list", "error"}


def transcript_record_valid(record: dict) -> bool:
    """Validate nested fields used for positive or negative transcript claims."""
    if not json_string_values_valid(record):
        return False
    if not isinstance(record.get("type"), str) or not record["type"]:
        return False
    if record["type"] not in CODEX_EVENT_TYPES | CLAUDE_RECORD_TYPES:
        return False
    if any(
        record.get(key) is not None and not isinstance(record[key], dict)
        for key in ("origin", "attachment", "item")
    ):
        return False
    if record.get("toolUseResult") is not None and not isinstance(
        record["toolUseResult"], (str, list, dict)
    ):
        return False
    raw_message = record.get("message")
    if record["type"] == "error":
        if not isinstance(raw_message, str):
            return False
    elif raw_message is not None and not isinstance(raw_message, dict):
        return False
    if record["type"] == "turn.failed":
        error = record.get("error")
        if not (
            isinstance(error, dict) and isinstance(error.get("message"), str)
        ):
            return False
    if any(
        record.get(key) is not None and not isinstance(record[key], bool)
        for key in (
            "isSidechain",
            "isMeta",
            "isCompactSummary",
            "isVisibleInTranscriptOnly",
            "isVirtual",
        )
    ):
        return False
    if any(
        record.get(key) is not None and not isinstance(record[key], str)
        for key in (
            "type",
            "timestamp",
            "cwd",
            "gitBranch",
            "version",
            "thread_id",
            "uuid",
            "parentUuid",
            "sourceToolAssistantUUID",
            "sourceToolUseID",
            "promptSource",
            "userType",
        )
    ):
        return False
    if "\x00" in (record.get("cwd") or ""):
        return False

    origin = record.get("origin") or {}
    if origin.get("kind") is not None and not isinstance(origin["kind"], str):
        return False
    if record["type"] != "user" and origin.get("kind") is not None:
        return False
    attachment = record.get("attachment") or {}
    if any(
        attachment.get(key) is not None and not isinstance(attachment[key], str)
        for key in ("type", "commandMode")
    ):
        return False
    if (
        attachment.get("type") == "queued_command"
        and attachment.get("commandMode") == "prompt"
    ):
        prompt_values = [
            attachment[key]
            for key in ("prompt", "command")
            if key in attachment and attachment[key] is not None
        ]
        if not prompt_values:
            return False
        for prompt in prompt_values:
            if isinstance(prompt, str):
                continue
            if not isinstance(prompt, list) or not all(
                isinstance(block, dict)
                and isinstance(block.get("type"), str)
                and (
                    block["type"] != "text"
                    or isinstance(block.get("text"), str)
                )
                and (
                    block["type"] != "image"
                    or isinstance(block.get("source"), dict)
                    and all(
                        isinstance(block["source"].get(field), str)
                        for field in ("type", "media_type", "data")
                    )
                )
                for block in prompt
            ):
                return False

    message = raw_message if isinstance(raw_message, dict) else {}
    message_role = message.get("role")
    if message_role is not None and (
        not isinstance(message_role, str)
        or record["type"] in {"assistant", "user"}
        and message_role != record["type"]
    ):
        return False
    if "stop_reason" in message:
        if record["type"] != "assistant":
            return False
        if message["stop_reason"] is not None and (
            not isinstance(message["stop_reason"], str)
            or message["stop_reason"] not in CLAUDE_STOP_REASONS
        ):
            return False
    if (
        message.get("usage") is not None
        and not isinstance(message["usage"], dict)
        or message.get("model") is not None
        and not isinstance(message["model"], str)
    ):
        return False
    integer_usage_fields = {
        "input_tokens",
        "cached_input_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    }
    if isinstance(message.get("usage"), dict) and any(
        key in integer_usage_fields
        and (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        )
        for key, value in message["usage"].items()
    ):
        return False
    if record.get("usage") is not None and not isinstance(record["usage"], dict):
        return False
    if record["type"] != "turn.completed" and isinstance(
        record.get("usage"), dict
    ) and any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in record["usage"].values()
    ):
        return False
    content = message.get("content")
    if content is not None and not isinstance(content, (str, list)):
        return False
    if isinstance(content, list):
        if not all(isinstance(block, dict) for block in content):
            return False
        for block in content:
            block_type = block.get("type")
            if not isinstance(block_type, str):
                return False
            if block_type == "text" and not isinstance(block.get("text"), str):
                return False
            if block_type == "tool_use" and not (
                isinstance(block.get("id"), str)
                and bool(block["id"])
                and isinstance(block.get("name"), str)
                and bool(block["name"])
                and isinstance(block.get("input"), dict)
            ):
                return False
            if block_type == "tool_result" and not (
                isinstance(block.get("tool_use_id"), str)
                and bool(block["tool_use_id"])
                and (
                    "is_error" not in block
                    or isinstance(block.get("is_error"), bool)
                )
                and (
                    "content" not in block
                    or result_content_payload_valid(block.get("content"))
                )
            ):
                return False

    if record["type"] in CODEX_EVENT_TYPES:
        return codex_event_valid(record)
    return True


def reject_json_constant(constant: str) -> object:
    """Reject Python's non-standard NaN and Infinity JSON extensions."""
    raise ValueError(f"invalid JSON constant: {constant}")


def reject_duplicate_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build one JSON object while rejecting duplicate keys fail-closed."""
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def parse_record_stream(handle: object) -> tuple[list[dict], int, int]:
    """Parse an already-open transcript and count unreadable marker lines."""
    records: list[dict] = []
    broken = 0
    broken_markers = 0
    for raw_line in handle:
        # A malformed record cannot be semantically attributed. Retain any
        # valid raw-JSON spelling of the product name so discovery fails
        # closed instead of silently losing a possibly relevant candidate.
        raw_has_marker = raw_json_marker_token_present(raw_line)
        try:
            line = raw_line.decode("utf-8").strip()
        except UnicodeDecodeError:
            broken += 1
            broken_markers += int(raw_has_marker)
            continue
        if not line:
            continue
        try:
            value = json.loads(
                line,
                parse_constant=reject_json_constant,
                object_pairs_hook=reject_duplicate_object,
            )
        except (ValueError, RecursionError):
            broken += 1
            broken_markers += int(raw_has_marker)
            continue
        if not isinstance(value, dict) or not transcript_record_valid(value):
            broken += 1
            broken_markers += int(raw_has_marker)
            continue
        records.append(value)
    return records, broken, broken_markers


def iter_records_with_marker_errors(path: Path) -> tuple[list[dict], int, int]:
    """Parse a transcript and separately count unreadable marker-bearing lines."""
    with open_regular_binary(path) as handle:
        before = os.fstat(handle.fileno())
        result = parse_record_stream(handle)
        if not opened_transcript_stable(path, handle, before):
            raise OSError(f"{path} changed while it was parsed")
        return result


def scan_marker_member(
    path: Path,
    expected: tuple[int, int, int, int, int] | None = None,
) -> tuple[tuple[list[dict], int, int] | None, tuple[int, int, int, int, int]]:
    """Prefilter and, on a hit, parse one held stable file identity."""
    with open_regular_binary(path) as handle:
        before = os.fstat(handle.fileno())
        if expected is not None and regular_snapshot(before) != expected:
            raise OSError(f"{path} changed after transcript inventory")
        marker_possible = stream_contains_marker(handle)
        if not marker_possible:
            result = None
        else:
            handle.seek(0)
            result = parse_record_stream(handle)
        if not opened_transcript_stable(path, handle, before):
            raise OSError(f"{path} changed during marker discovery")
        return result, regular_snapshot(before)


def parse_expected_transcript(
    path: Path, expected: tuple[int, int, int, int, int]
) -> tuple[list[dict], int, int]:
    """Parse a markerless candidate member only if its scanned identity remains."""
    with open_regular_binary(path) as handle:
        before = os.fstat(handle.fileno())
        if regular_snapshot(before) != expected:
            raise OSError(f"{path} changed after marker discovery")
        result = parse_record_stream(handle)
        if not opened_transcript_stable(path, handle, before):
            raise OSError(f"{path} changed while it was parsed")
        return result


def iter_records(path: Path) -> tuple[list[dict], int]:
    """Parse a transcript, tolerating lines corrupted by interleaved writes."""
    records, broken, _broken_markers = iter_records_with_marker_errors(path)
    return records, broken


def blocks(record: dict) -> list[dict]:
    message = record.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def model_visible_root(record: dict) -> bool:
    """Exclude sidechain, summary, meta, and transcript-only plumbing."""
    return not (
        record.get("isSidechain")
        or record.get("isMeta")
        or record.get("isCompactSummary")
        or record.get("isVisibleInTranscriptOnly")
        or record.get("isVirtual")
    )


def root_assistant_record(record: dict) -> bool:
    return record.get("type") == "assistant" and model_visible_root(record)


def text_of(record: dict) -> str:
    return "\n".join(b.get("text") or "" for b in blocks(record) if b.get("type") == "text")


def model_visible_skill_frame_record(record: dict) -> bool:
    """Recognize any host-owned skill frame that entered the root context."""
    if not (
        not record.get("isSidechain")
        and not record.get("isVirtual")
        and record.get("type") == "user"
        and record.get("userType") == "external"
        and record.get("isMeta") is True
        and not record.get("isCompactSummary")
        and not record.get("isVisibleInTranscriptOnly")
        and (record.get("origin") or {}).get("kind") != "human"
    ):
        return False
    base = BASE_DIRECTORY_RE.match(normalize_crlf(text_of(record)))
    return bool(base and base.group(1).strip())


def model_visible_meta_input_record(record: dict) -> bool:
    """Recognize host/peer text injected into the root model context."""
    return bool(
        not record.get("isSidechain")
        and not record.get("isVirtual")
        and record.get("type") == "user"
        and record.get("isMeta") is True
        and not record.get("isCompactSummary")
        and not record.get("isVisibleInTranscriptOnly")
        and (record.get("origin") or {}).get("kind") != "human"
        and text_of(record).strip()
        and not any(block.get("type") == "tool_result" for block in blocks(record))
    )


def result_content_text(value: object) -> str:
    """Return only model-visible text from a Claude tool-result payload."""
    valid, found = result_content_parts(value)
    return "\n".join(found) if valid else ""


def skiphow_skill_call_names(records: list[dict]) -> dict[str, str]:
    """Return root Skill calls whose target explicitly names the SkipHow plugin."""
    calls: dict[str, str] = {}
    for record in records:
        if not root_assistant_record(record):
            continue
        for block in blocks(record):
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                data = block.get("input")
                if not isinstance(data, dict):
                    continue
                requested = [data[field] for field in ("skill", "name") if field in data]
                if (
                    not requested
                    or any(not isinstance(value, str) or not value for value in requested)
                    or len(set(requested)) != 1
                ):
                    continue
                invoked = requested[0]
                match = (
                    NAMESPACED_SKILL_RE.fullmatch(invoked)
                    if isinstance(invoked, str)
                    else None
                )
                if not match:
                    continue
                tool_id = block.get("id")
                if isinstance(tool_id, str) and tool_id:
                    name = match.group("name")
                    if tool_id in calls and calls[tool_id] != name:
                        calls[tool_id] = ""
                    else:
                        calls[tool_id] = name
    return {tool_id: name for tool_id, name in calls.items() if name}


def successful_skill_result_ids(records: list[dict]) -> set[str]:
    """Return explicit SkipHow Skill calls with one later successful result."""
    calls = skiphow_skill_call_names(records)
    results = claude_tool_results(records)
    ambiguous = ambiguous_claude_tool_ids(records)
    return {
        tool_id
        for tool_id in calls
        if tool_id not in ambiguous and results.get(tool_id, (False, ""))[0]
    }


def ambiguous_successful_skill_result_ids(records: list[dict]) -> set[str]:
    """Return unbound SkipHow call IDs with a later non-error result.

    Duplicate calls/results and conflicting input aliases cannot be bound to
    one activation. A successful terminal still means another contract may
    have entered the session, so canonical identity retains ``unknown``.
    """
    calls, results = claude_tool_occurrences(records)
    ambiguous = ambiguous_claude_tool_ids(records)
    paired = claude_tool_results(records)
    bound = successful_skill_result_ids(records)

    def explicitly_names_skiphow(call: tuple[int, int, dict]) -> bool:
        block = call[2]
        data = block.get("input")
        return bool(
            block.get("name") == "Skill"
            and isinstance(data, dict)
            and any(
                isinstance(value, str)
                and NAMESPACED_SKILL_RE.fullmatch(value) is not None
                for field in ("skill", "name")
                if (value := data.get(field)) is not None
            )
        )

    explicit_ids = {
        tool_id
        for tool_id, occurrences in calls.items()
        if any(explicitly_names_skiphow(call) for call in occurrences)
    }
    unbound = {
        tool_id
        for tool_id in explicit_ids - bound - ambiguous
        if paired.get(tool_id, (False, ""))[0]
    }
    unbound.update({
        tool_id
        for tool_id in explicit_ids & ambiguous
        if any(
            not bool(result[2].get("is_error"))
            and any(
                call[:2] < result[:2] and explicitly_names_skiphow(call)
                for call in calls.get(tool_id, ())
            )
            for result in results.get(tool_id, ())
        )
    })
    return unbound


def record_descends_from(
    record_index: int,
    ancestor_index: int,
    ancestor_uuid: str,
    records_by_uuid: dict[str, tuple[int, dict]],
) -> bool:
    """Follow a unique, backward-only parent chain."""
    record = records_by_uuid.get(
        next(
            (
                uuid
                for uuid, (index, _record) in records_by_uuid.items()
                if index == record_index
            ),
            "",
        )
    )
    if not record:
        return False
    current_index, current_record = record
    parent = current_record.get("parentUuid")
    seen: set[str] = set()
    while isinstance(parent, str) and parent and parent not in seen:
        if parent == ancestor_uuid and ancestor_index < current_index:
            return True
        seen.add(parent)
        parent_entry = records_by_uuid.get(parent)
        if not parent_entry or parent_entry[0] >= current_index:
            return False
        current_index, current_record = parent_entry
        parent = current_record.get("parentUuid")
    return False


def skill_injection_observations(records: list[dict]) -> dict[str, dict]:
    """Bind Claude's separate meta injection to its exact successful Skill call."""
    allowed = successful_skill_result_ids(records)
    expected_names = skiphow_skill_call_names(records)
    _calls, results = claude_tool_occurrences(records)
    uuid_counts = Counter(
        record["uuid"]
        for record in records
        if isinstance(record.get("uuid"), str) and record["uuid"]
        and not record.get("isSidechain")
        and not record.get("isVirtual")
    )
    records_by_uuid = {
        record["uuid"]: (index, record)
        for index, record in enumerate(records)
        if isinstance(record.get("uuid"), str)
        and record["uuid"]
        and uuid_counts[record["uuid"]] == 1
        and not record.get("isSidechain")
        and not record.get("isVirtual")
    }
    observations: dict[str, dict] = {}
    consumed_injection_indexes: set[int] = set()

    def evaluate(index: int, text: str, expected_name: str, attribution: str) -> dict:
        comparison_text = normalize_crlf(text)
        base = BASE_DIRECTORY_RE.match(comparison_text)
        hits = skill_paths(base.group(1), require_file=False) if base else []
        if not (
            len(hits) == 1
            and hits[0]["name"] == expected_name
            and not (
                attribution == "explicit_skill_call"
                and hits[0]["source"] != "plugin"
            )
        ):
            return {
                "status": "activation_path_mismatch",
                "attribution": attribution,
                "at": records[index].get("timestamp", ""),
            }
        hit = hits[0]
        cache_root = hit.get("_root", "")
        if (
            re.fullmatch(PLUGIN_VERSION_PATTERN, hit["version"])
            and not portable_absolute_path(cache_root)
        ):
            body, artifact_source = "", "contract_bytes_unavailable"
        else:
            body, artifact_source = package_skill(
                hit["version"], expected_name, cache_root
            )
        comparison_body = normalize_crlf(body)
        exact_bodies = [comparison_body]
        if comparison_body.startswith("---\n") and "\n---\n" in comparison_body[4:]:
            exact_bodies.append(
                comparison_body.split("\n---\n", 1)[1].lstrip("\n")
            )
        canonical_body = exact_bodies[-1]
        tail = comparison_text[base.end() :] if base else ""
        observed_body = tail.lstrip("\n")
        exact = False
        body_fingerprint = ""
        if (
            body.strip()
            and canonical_body.strip()
            and hit["source"] == "plugin"
        ):
            for candidate in exact_bodies:
                expected = candidate.rstrip("\n")
                observed = observed_body.rstrip("\n")
                if not expected.strip() or not observed_body.startswith(expected):
                    continue
                wrapper = observed[len(expected) :]
                if not wrapper or re.match(r"^\n+ARGUMENTS:", wrapper):
                    exact = True
                    body_fingerprint = hashlib.sha256(
                        canonical_body.rstrip("\n").encode("utf-8")
                    ).hexdigest()
                    break
        result = {
            "status": "body_observed" if exact else "body_unverified",
            "name": expected_name,
            "text": text,
            "source": hit["source"],
            "version": hit["version"],
            "artifact_source": artifact_source,
            "attribution": attribution,
            "at": records[index].get("timestamp", ""),
        }
        if (
            re.fullmatch(PLUGIN_VERSION_PATTERN, hit["version"])
            and isinstance(hit.get("_root"), str)
            and portable_absolute_path(hit["_root"])
        ):
            result["_cache_root"] = hit["_root"]
        if body_fingerprint:
            result["body_fingerprint"] = body_fingerprint
        return result

    for tool_id in allowed:
        result_occurrences = results.get(tool_id, [])
        if len(result_occurrences) != 1:
            continue
        result_index = result_occurrences[0][0]
        result_record = records[result_index]
        result_uuid = result_record.get("uuid")
        if (
            not isinstance(result_uuid, str)
            or not result_uuid
            or result_uuid not in records_by_uuid
        ):
            continue
        candidates: list[tuple[int, str]] = []
        for index, record in enumerate(records):
            if (
                index <= result_index
                or record.get("isSidechain")
                or record.get("isVirtual")
                or record.get("type") != "user"
                or record.get("userType") != "external"
                or record.get("isMeta") is not True
                or record.get("isCompactSummary")
                or record.get("isVisibleInTranscriptOnly")
                or (record.get("origin") or {}).get("kind") == "human"
                or record.get("sourceToolUseID") != tool_id
                or not isinstance(record.get("uuid"), str)
                or record.get("uuid") not in records_by_uuid
                or not record_descends_from(
                    index, result_index, result_uuid, records_by_uuid
                )
            ):
                continue
            text = text_of(record)
            base = BASE_DIRECTORY_RE.match(text)
            if base:
                candidates.append((index, text))
        if len(candidates) != 1:
            if candidates:
                observations[tool_id] = {"status": "ambiguous_injection"}
            continue
        index, text = candidates[0]
        observation = evaluate(
            index, text, expected_names[tool_id], "explicit_skill_call"
        )
        observations[tool_id] = observation
        if observation.get("status") in {"body_observed", "body_unverified"}:
            consumed_injection_indexes.add(index)

    for index, record in enumerate(records):
        if index in consumed_injection_indexes or not model_visible_skill_frame_record(
            record
        ):
            continue
        text = text_of(record)
        base = BASE_DIRECTORY_RE.match(text)
        hits = skill_paths(base.group(1), require_file=False) if base else []
        key = f"unattributed:{index}"
        while key in observations:
            key += ":frame"
        if len(hits) != 1:
            observations[key] = {
                "status": "activation_path_ambiguous",
                "attribution": "unattributed_meta_injection",
                "at": record.get("timestamp", ""),
            }
            continue
        observations[key] = evaluate(
            index, text, hits[0]["name"], "unattributed_meta_injection"
        )
    return observations


def contract_identity_values(
    records: list[dict],
    observations: dict[str, dict] | None = None,
) -> list[str]:
    """Return one fail-closed contract identity across every consumer.

    A concrete version requires a plugin-cache path in a linked or
    unattributed body injection. A successful Skill call with no such
    injection, and every project-local or otherwise unversioned injection,
    contributes ``unknown`` instead of disappearing beside known evidence.
    """
    injections = (
        observations
        if observations is not None
        else skill_injection_observations(records)
    )

    def observed_version(observation: dict) -> str:
        version = observation.get("version")
        if (
            observation.get("status") in {"body_observed", "body_unverified"}
            and observation.get("source") == "plugin"
            and isinstance(version, str)
            and re.fullmatch(PLUGIN_VERSION_PATTERN, version)
            and portable_absolute_path(observation.get("_cache_root"))
        ):
            return version
        return "unknown"

    values = {
        observed_version(injections.get(tool_id, {}))
        for tool_id in successful_skill_result_ids(records)
    }
    if ambiguous_successful_skill_result_ids(records):
        values.add("unknown")
    values.update(
        observed_version(observation)
        for tool_id, observation in injections.items()
        if tool_id.startswith("unattributed:")
    )
    return sorted(values) or ["unknown"]


def contract_identity_status(values: list[str]) -> str:
    """Classify canonical contract identity values without discarding unknown."""
    known = [value for value in values if value != "unknown"]
    if len(known) > 1:
        return "mixed"
    if known and "unknown" in values:
        return "partially_unknown"
    if len(known) == 1:
        return "single"
    return "unknown"


def contract_body_contributors(
    records: list[dict], observations: dict[str, dict]
) -> list[dict]:
    """Return every body observation that contributes to one identity."""
    contributors = [
        observations.get(tool_id, {})
        for tool_id in successful_skill_result_ids(records)
    ]
    contributors.extend(
        observation
        for tool_id, observation in observations.items()
        if tool_id.startswith("unattributed:")
    )
    return contributors


def contract_body_identity_status(
    records: list[dict], observations: dict[str, dict], version: str
) -> str:
    """Classify governing body evidence without exposing contract bytes."""
    contributors = contract_body_contributors(records, observations)
    if not contributors:
        return "not_observed"
    exact = [
        observation
        for observation in contributors
        if observation.get("status") == "body_observed"
        and observation.get("source") == "plugin"
        and observation.get("version") == version
        and isinstance(observation.get("body_fingerprint"), str)
        and observation["body_fingerprint"]
    ]
    if len(exact) != len(contributors):
        return "partially_unverified"
    return (
        "single"
        if len({observation["body_fingerprint"] for observation in exact}) == 1
        else "mixed"
    )


def governing_contract_roots(
    records: list[dict], observations: dict[str, dict], version: str
) -> tuple[str, ...] | None:
    """Return agreed activation cache roots, or None for mixed provenance."""
    if contract_body_identity_status(records, observations, version) != "single":
        return None
    contributors = contract_body_contributors(records, observations)
    rooted = [
        observation
        for observation in contributors
        if isinstance(observation.get("_cache_root"), str)
    ]
    if not rooted:
        return ()
    if len(rooted) != len(contributors) or any(
        not portable_absolute_path(observation["_cache_root"])
        for observation in rooted
    ):
        return None
    return tuple(sorted({observation["_cache_root"] for observation in rooted}))


def windows_path_semantics(value: object) -> bool:
    """Recognize drive, UNC, or known relative Windows path spelling."""
    if not isinstance(value, str) or not value:
        return False
    windows_drive = bool(re.match(r"^[A-Za-z]:[/\\]", value))
    windows_unc = (
        value.startswith("\\\\") and not value.startswith("\\\\\\")
        or value.startswith("//") and not value.startswith("///")
    )
    folded = windows_ascii_fold(value)
    slashified = folded.replace("\\", "/")
    anchored = slashified[2:] if slashified.startswith("./") else slashified
    known_relative = any(
        anchored.startswith(marker)
        for marker in (
            "plugins/skiphow/skills/",
            ".agents/skills/",
            ".claude/plugins/cache/skiphow/skiphow/",
            ".codex/plugins/cache/skiphow/skiphow/",
        )
    )
    windows_relative = bool(
        "\\" in value
        and (
            known_relative
            or "/" not in value
            and any(
                marker in folded
                for marker in (
                    "plugins\\skiphow\\skills\\",
                    ".agents\\skills\\",
                    ".claude\\plugins\\cache\\skiphow\\skiphow\\",
                    ".codex\\plugins\\cache\\skiphow\\skiphow\\",
                )
            )
        )
    )
    return windows_drive or windows_unc or windows_relative


def windows_ascii_fold(value: str) -> str:
    """Fold Windows path syntax without Unicode length-changing aliases."""
    return value.translate(
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
    )


def canonical_path_token(value: object) -> str | None:
    """Normalize a typed filesystem operand without interpreting shell syntax."""
    if not isinstance(value, str) or not value:
        return None
    normalized = (
        ntpath.normpath(value).replace("\\", "/")
        if windows_path_semantics(value)
        else value
    )
    if any(character in normalized for character in ("\x00", "\n", "\r")):
        return None
    drive = bool(re.match(r"^[A-Za-z]:/", normalized))
    if (":" in normalized and not drive) or ":" in normalized[2:]:
        return None
    if not drive and re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", normalized):
        return None
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def comparable_path_token(value: object) -> str | None:
    """Return an exact path identity with Windows-only case folding."""
    normalized = canonical_path_token(value)
    if normalized is None:
        return None
    if windows_path_semantics(value):
        return f"windows:{windows_ascii_fold(normalized)}"
    return f"native:{normalized}"


def recognized_path_root(value: object) -> tuple[str, str, str, str] | None:
    """Return outer root kind, suffix, version, and exact root path."""
    normalized = canonical_path_token(value)
    if normalized is None:
        return None
    raw_value = value if isinstance(value, str) else ""
    windows_semantics = windows_path_semantics(raw_value)
    compared = windows_ascii_fold(normalized) if windows_semantics else normalized
    source_prefix = "plugins/skiphow/skills/"
    exact_roots: list[tuple[int, str, str]] = []
    root_specs = (
        ("source", repository_root() / "plugins/skiphow/skills"),
        *(("cache", root) for root in plugin_cache_roots()),
    )
    for kind, raw_root in root_specs:
        root_token = canonical_path_token(os.fspath(raw_root))
        if root_token is None:
            continue
        prefix = root_token.rstrip("/") + "/"
        compared_prefix = windows_ascii_fold(prefix) if windows_semantics else prefix
        if compared.startswith(compared_prefix):
            exact_roots.append((len(prefix), kind, prefix))
    if exact_roots:
        _length, kind, prefix = max(
            exact_roots, key=lambda candidate: (candidate[0], candidate[1] == "source")
        )
        remainder = normalized[len(prefix) :]
        if kind == "source":
            return (
                "source",
                windows_ascii_fold(remainder) if windows_semantics else remainder,
                "unknown",
                normalized[: len(prefix)].rstrip("/"),
            )
        version, separator, suffix = remainder.partition("/")
        if separator and re.fullmatch(PLUGIN_VERSION_PATTERN, version):
            return (
                "cache",
                windows_ascii_fold(suffix) if windows_semantics else suffix,
                version,
                normalized[: len(prefix)].rstrip("/"),
            )
        return None
    project_marker = "/.agents/skills/"
    project_index = (
        0
        if compared.startswith(".agents/skills/")
        else compared.find(project_marker)
    )
    source_marker = "/plugins/skiphow/skills/"
    source_index = 0 if compared.startswith(source_prefix) else compared.find(source_marker)
    hidden_cache_markers = (
        "/.claude/plugins/cache/skiphow/skiphow/",
        "/.codex/plugins/cache/skiphow/skiphow/",
    )
    hidden: list[tuple[int, str]] = []
    for marker in hidden_cache_markers:
        relative_marker = marker[1:]
        if compared.startswith(relative_marker):
            hidden.append((0, relative_marker))
        elif compared.count(marker) == 1:
            hidden.append((compared.index(marker), marker))
    candidates = [
        (index, kind, marker)
        for index, kind, marker in (
            (project_index, "project", project_marker),
            (source_index, "source", source_marker),
            *((index, "cache", marker) for index, marker in hidden),
        )
        if index >= 0
    ]
    if not candidates:
        return None
    index, kind, marker = min(candidates, key=lambda candidate: candidate[0])
    if kind == "cache":
        remainder = normalized[index + len(marker) :]
        version, separator, suffix = remainder.partition("/")
        if separator and re.fullmatch(PLUGIN_VERSION_PATTERN, version):
            return (
                "cache",
                windows_ascii_fold(suffix) if windows_semantics else suffix,
                version,
                normalized[: index + len(marker)].rstrip("/"),
            )
        return None
    if kind == "source":
        if compared.startswith(source_prefix):
            suffix = normalized[len(source_prefix) :]
            return (
                "source",
                windows_ascii_fold(suffix) if windows_semantics else suffix,
                "unknown",
                normalized[: len(source_prefix)].rstrip("/"),
            )
        return None
    suffix = (
        normalized[len(".agents/skills/") :]
        if compared.startswith(".agents/skills/")
        else normalized[index + len(project_marker) :]
    )
    compared_suffix = windows_ascii_fold(suffix) if windows_semantics else suffix
    if project_marker in compared_suffix:
        return None
    root = (
        ".agents/skills"
        if compared.startswith(".agents/skills/")
        else normalized[: index + len(project_marker)].rstrip("/")
    )
    return "project", compared_suffix, "unknown", root


def skill_paths(text: str, require_file: bool) -> list[dict[str, str]]:
    """Recognize one exact skill directory or SKILL.md path."""
    rooted = recognized_path_root(text)
    if not rooted:
        return []
    kind, suffix, version, root = rooted
    match_suffix = suffix[:-1] if not require_file and suffix.endswith("/") else suffix
    file_name = "skill\\.md" if windows_path_semantics(text) else "SKILL\\.md"
    if kind == "cache":
        match = re.fullmatch(
            rf"skills/(?P<name>{SKILL_NAME_PATTERN})(?P<file>/{file_name})?",
            match_suffix,
        )
    else:
        match = re.fullmatch(
            rf"(?P<name>{SKILL_NAME_PATTERN})(?P<file>/{file_name})?",
            match_suffix,
        )
    if not match or bool(match.group("file")) != require_file:
        return []
    return [
        {
            "name": match.group("name"),
            "source": "project" if kind == "project" else "plugin",
            "version": version,
            "_root": root,
            "_needle": text,
        }
    ]


def reference_paths(text: str, name: str) -> list[str]:
    """Return a whole semantic path operand when it names this reference."""
    return [text] if reference_name_from_path(text) == name else []


def reference_path_version(path: str) -> str | None:
    """Return the version embedded in an installed-cache reference path."""
    rooted = recognized_path_root(path)
    return rooted[2] if rooted and rooted[0] == "cache" else None


def reference_name_from_path(path: str) -> str | None:
    """Return a direct or nested reference name from an exact SkipHow path."""
    rooted = recognized_path_root(path)
    return reference_name_from_rooted(rooted)


def reference_name_from_rooted(
    rooted: tuple[str, str, str, str] | None,
) -> str | None:
    """Return the reference name from one already-parsed path operand."""
    if not rooted:
        return None
    kind, suffix, _version, _root = rooted
    prefix = "skills/skiphow/references/" if kind == "cache" else "skiphow/references/"
    if not suffix.startswith(prefix):
        return None
    relative = suffix[len(prefix) :]
    if not relative.endswith(".md"):
        return None
    name = relative[:-3]
    rooted_name = f"/{name}/"
    if any(
        marker in rooted_name
        for marker in (
            "/.agents/skills/",
            "/.claude/plugins/cache/",
            "/.codex/plugins/cache/",
            "/plugins/cache/",
            "/plugins/skiphow/skills/",
        )
    ):
        return None
    segment = r"[A-Za-z0-9][A-Za-z0-9._-]*"
    return name if re.fullmatch(rf"{segment}(?:/{segment})*", name) else None


def observed_reference_names(records: list[dict]) -> set[str]:
    """Return reference names appearing in structured semantic path fields."""
    found: set[str] = set()
    for event in terminal_tool_events(records):
        for value in event_path_payloads(event):
            if name := reference_name_from_path(value):
                found.add(name)
    return found


def version_reference_names(version: str) -> set[str]:
    """Return names from the exact tag or installed version cache when available."""
    return version_reference_roster(version)[0]


def claude_tool_occurrences(
    records: list[dict],
) -> tuple[dict[str, list[tuple[int, int, dict]]], dict[str, list[tuple[int, int, dict]]]]:
    """Index root Claude calls and results without pairing by ID alone."""
    calls: dict[str, list[tuple[int, int, dict]]] = {}
    results: dict[str, list[tuple[int, int, dict]]] = {}
    for record_index, record in enumerate(records):
        if record.get("isSidechain"):
            continue
        call_record = root_assistant_record(record)
        result_record = (
            record.get("type") == "user"
            and (record.get("origin") or {}).get("kind") != "human"
            and not record.get("isMeta")
            and not record.get("isCompactSummary")
            and not record.get("isVisibleInTranscriptOnly")
            and not record.get("isVirtual")
        )
        for block_index, block in enumerate(blocks(record)):
            if (
                call_record
                and block.get("type") == "tool_use"
                and isinstance(block.get("id"), str)
                and block["id"]
            ):
                calls.setdefault(block["id"], []).append((record_index, block_index, block))
            elif (
                result_record
                and
                block.get("type") == "tool_result"
                and isinstance(block.get("tool_use_id"), str)
                and block["tool_use_id"]
            ):
                results.setdefault(block["tool_use_id"], []).append(
                    (record_index, block_index, block)
                )
    return calls, results


def claude_pair_lineage_valid(
    records: list[dict],
    call: tuple[int, int, dict],
    result: tuple[int, int, dict],
    unique_record_uuids: set[str] | None = None,
) -> bool:
    """Require the host's call-record lineage on a Claude call/result pair."""
    call_uuid = records[call[0]].get("uuid")
    result_record = records[result[0]]
    result_uuid = result_record.get("uuid")
    if unique_record_uuids is None:
        counts = Counter(
            record["uuid"]
            for record in records
            if not record.get("isSidechain")
            and not record.get("isVirtual")
            and isinstance(record.get("uuid"), str)
            and record["uuid"]
        )
        unique_record_uuids = {
            record_uuid for record_uuid, count in counts.items() if count == 1
        }
    source_tool_id = result_record.get("sourceToolUseID")
    return (
        isinstance(call_uuid, str)
        and bool(call_uuid)
        and call_uuid in unique_record_uuids
        and isinstance(result_uuid, str)
        and bool(result_uuid)
        and result_uuid in unique_record_uuids
        and result_record.get("parentUuid") == call_uuid
        and result_record.get("sourceToolAssistantUUID") == call_uuid
        and (source_tool_id is None or source_tool_id == call[2].get("id"))
    )


def claude_tool_results(records: list[dict]) -> dict[str, tuple[bool, str]]:
    """Pair one root call with one later root result; fail closed otherwise."""
    calls, results = claude_tool_occurrences(records)
    uuid_counts = Counter(
        record["uuid"]
        for record in records
        if not record.get("isSidechain")
        and not record.get("isVirtual")
        and isinstance(record.get("uuid"), str)
        and record["uuid"]
    )
    unique_record_uuids = {
        record_uuid for record_uuid, count in uuid_counts.items() if count == 1
    }
    paired: dict[str, tuple[bool, str]] = {}
    for tool_id in set(calls) & set(results):
        if len(calls[tool_id]) != 1 or len(results[tool_id]) != 1:
            continue
        call_position = calls[tool_id][0][:2]
        result_position = results[tool_id][0][:2]
        if result_position <= call_position or not claude_pair_lineage_valid(
            records,
            calls[tool_id][0],
            results[tool_id][0],
            unique_record_uuids,
        ):
            continue
        block = results[tool_id][0][2]
        paired[tool_id] = (
            not bool(block.get("is_error")),
            result_content_text(block.get("content")),
        )
    return paired


def ambiguous_claude_tool_ids(records: list[dict]) -> set[str]:
    """Return duplicate IDs and unique pairs whose result precedes the call."""
    calls, results = claude_tool_occurrences(records)
    uuid_counts = Counter(
        record["uuid"]
        for record in records
        if not record.get("isSidechain")
        and not record.get("isVirtual")
        and isinstance(record.get("uuid"), str)
        and record["uuid"]
    )
    unique_record_uuids = {
        record_uuid for record_uuid, count in uuid_counts.items() if count == 1
    }
    ambiguous: set[str] = set()
    for tool_id in set(calls) | set(results):
        if len(calls.get(tool_id, [])) > 1 or len(results.get(tool_id, [])) > 1:
            ambiguous.add(tool_id)
        elif calls.get(tool_id) and results.get(tool_id):
            if (
                results[tool_id][0][:2] <= calls[tool_id][0][:2]
                or not claude_pair_lineage_valid(
                    records,
                    calls[tool_id][0],
                    results[tool_id][0],
                    unique_record_uuids,
                )
            ):
                ambiguous.add(tool_id)
    return ambiguous


def codex_turn_memberships(records: list[dict]) -> tuple[bool, dict[int, int]]:
    """Map Codex item records to the active turn that contains them."""
    has_lifecycle = any(
        model_visible_root(record)
        and record.get("type")
        in {"thread.started", "turn.started", "turn.completed", "turn.failed"}
        for record in records
    )
    if not has_lifecycle:
        return False, {}
    memberships: dict[int, int] = {}
    active_turn: int | None = None
    turn_number = 0
    for index, record in enumerate(records):
        if not model_visible_root(record):
            continue
        event_type = record.get("type")
        if event_type == "turn.started":
            turn_number += 1
            active_turn = turn_number
        elif event_type in {"turn.completed", "turn.failed"}:
            active_turn = None
        elif event_type in {"item.started", "item.updated", "item.completed"}:
            if active_turn is not None:
                memberships[index] = active_turn
    return True, memberships


def codex_occurrences_share_turn(
    records: list[dict], left_index: int, right_index: int
) -> bool:
    """Require the same active Codex turn when lifecycle envelopes exist."""
    has_lifecycle, memberships = codex_turn_memberships(records)
    return codex_memberships_share(
        has_lifecycle, memberships, left_index, right_index
    )


def codex_occurrence_has_valid_turn(records: list[dict], index: int) -> bool:
    """Reject an item outside its active turn when envelopes are present."""
    has_lifecycle, memberships = codex_turn_memberships(records)
    return codex_membership_valid(has_lifecycle, memberships, index)


def codex_memberships_share(
    has_lifecycle: bool,
    memberships: dict[int, int],
    left_index: int,
    right_index: int,
) -> bool:
    """Compare two occurrences against one precomputed lifecycle index."""
    if not has_lifecycle:
        return True
    left_turn = memberships.get(left_index)
    return left_turn is not None and memberships.get(right_index) == left_turn


def codex_membership_valid(
    has_lifecycle: bool, memberships: dict[int, int], index: int
) -> bool:
    """Validate one occurrence against one precomputed lifecycle index."""
    return not has_lifecycle or index in memberships


def codex_tool_occurrences(
    records: list[dict],
    lifecycle: tuple[bool, dict[int, int]] | None = None,
) -> tuple[dict[str, list[tuple[int, dict]]], dict[str, list[tuple[int, dict, str]]]]:
    """Index identified root Codex starts and terminal events."""
    starts: dict[str, list[tuple[int, dict]]] = {}
    terminals: dict[str, list[tuple[int, dict, str]]] = {}
    has_lifecycle, turn_memberships = (
        lifecycle if lifecycle is not None else codex_turn_memberships(records)
    )
    for record_index, record in enumerate(records):
        if not model_visible_root(record):
            continue
        item = record.get("item")
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue
        if (
            record.get("type") == "item.started"
            and item["type"] in CODEX_STARTED_TOOL_TYPES
        ):
            starts.setdefault(item_id, []).append((record_index, item))
        elif record.get("type") == "item.completed" and item["type"] in CODEX_TOOL_TYPES:
            if item["type"] != "web_search" and codex_start_valid(item):
                # Turn reconciliation can serialize an in-progress item in an
                # `item.completed` envelope. Coalesce only an identity-equal
                # snapshot before any terminal; every contradiction stays
                # visible as an additional start and therefore ambiguous.
                existing_starts = starts.get(item_id, [])
                existing_terminals = terminals.get(item_id, [])
                if not existing_starts:
                    starts.setdefault(item_id, []).append((record_index, item))
                elif not (
                    len(existing_starts) == 1
                    and not existing_terminals
                    and existing_starts[0][0] < record_index
                    and (
                        not has_lifecycle
                        or turn_memberships.get(existing_starts[0][0]) is not None
                        and turn_memberships.get(existing_starts[0][0])
                        == turn_memberships.get(record_index)
                    )
                    and codex_start_items_share_identity(
                        existing_starts[0][1], item
                    )
                ):
                    starts.setdefault(item_id, []).append((record_index, item))
            else:
                terminals.setdefault(item_id, []).append(
                    (record_index, item, record["type"])
                )
    return starts, terminals


def codex_item_identity_ambiguities(
    records: list[dict],
    tool_occurrences: tuple[
        dict[str, list[tuple[int, dict]]],
        dict[str, list[tuple[int, dict, str]]],
    ]
    | None = None,
    lifecycle: tuple[bool, dict[int, int]] | None = None,
) -> set[str]:
    """Return reused Codex item IDs whose lifecycle cannot name one item."""
    items: dict[str, list[tuple[int, str, dict]]] = {}
    for index, record in enumerate(records):
        if not model_visible_root(record):
            continue
        item = record.get("item")
        item_id = item.get("id") if isinstance(item, dict) else None
        if (
            record.get("type") in {"item.started", "item.updated", "item.completed"}
            and isinstance(item_id, str)
            and item_id
        ):
            items.setdefault(item_id, []).append((index, record["type"], item))

    lifecycle = lifecycle or codex_turn_memberships(records)
    has_lifecycle, memberships = lifecycle
    starts, terminals = (
        tool_occurrences
        if tool_occurrences is not None
        else codex_tool_occurrences(records, lifecycle)
    )
    ambiguous: set[str] = set()
    for item_id, occurrences in items.items():
        item_types = {item.get("type") for _index, _event, item in occurrences}
        if len(item_types) != 1:
            ambiguous.add(item_id)
            continue
        if has_lifecycle and len(
            {memberships.get(index) for index, _event, _item in occurrences}
        ) > 1:
            ambiguous.add(item_id)
            continue
        item_type = next(iter(item_types))
        if item_type in {"agent_message", "reasoning", "error"}:
            if len(occurrences) != 1:
                ambiguous.add(item_id)
            continue
        if item_type == "todo_list":
            event_types = [event for _index, event, _item in occurrences]
            starts_count = event_types.count("item.started")
            completed_count = event_types.count("item.completed")
            if (
                starts_count > 1
                or completed_count > 1
                or starts_count == 1
                and event_types[0] != "item.started"
                or completed_count == 1
                and event_types[-1] != "item.completed"
                or "item.updated" in event_types
                and starts_count == 0
            ):
                ambiguous.add(item_id)
            continue
        if item_type not in CODEX_TOOL_TYPES:
            continue
        call_occurrences = starts.get(item_id, [])
        result_occurrences = terminals.get(item_id, [])
        if len(call_occurrences) > 1 or len(result_occurrences) > 1:
            ambiguous.add(item_id)
            continue
        if call_occurrences and result_occurrences:
            start_index, start_item = call_occurrences[0]
            terminal_index, terminal_item, _terminal_type = result_occurrences[0]
            if not (
                start_index < terminal_index
                and codex_memberships_share(
                    has_lifecycle, memberships, start_index, terminal_index
                )
                and codex_items_share_identity(start_item, terminal_item)
            ):
                ambiguous.add(item_id)
        elif call_occurrences:
            start_index, start_item = call_occurrences[0]
            if not (
                codex_start_valid(start_item)
                and codex_membership_valid(
                    has_lifecycle, memberships, start_index
                )
            ):
                ambiguous.add(item_id)
        elif result_occurrences:
            terminal_index, terminal_item, _terminal_type = result_occurrences[0]
            if not (
                codex_terminal_shape_valid(terminal_item)
                and codex_membership_valid(
                    has_lifecycle, memberships, terminal_index
                )
            ):
                ambiguous.add(item_id)
    return ambiguous


def codex_start_items_share_identity(left: dict, right: dict) -> bool:
    """Compare the stable identity of two in-progress Codex snapshots."""
    if not codex_start_valid(left) or not codex_start_valid(right):
        return False
    item_type = left.get("type")
    if right.get("type") != item_type:
        return False
    if item_type == "command_execution":
        return bool(left.get("command")) and right.get("command") == left.get(
            "command"
        )
    if item_type == "file_change":
        return {
            comparable_path_token(change["path"]): change["kind"]
            for change in left.get("changes", [])
        } == {
            comparable_path_token(change["path"]): change["kind"]
            for change in right.get("changes", [])
        }
    if item_type == "mcp_tool_call":
        return all(
            (
                right.get("server") == left.get("server"),
                right.get("tool") == left.get("tool"),
                json_values_equal(right.get("arguments"), left.get("arguments")),
            )
        )
    if item_type == "collab_tool_call":
        return all(
            (
                right.get("tool") == left.get("tool"),
                right.get("sender_thread_id") == left.get("sender_thread_id"),
                right.get("receiver_thread_ids") == left.get("receiver_thread_ids"),
                right.get("prompt") == left.get("prompt"),
            )
        )
    if item_type == "web_search":
        return right.get("query") == left.get("query")
    return False


def codex_items_share_identity(start: dict, terminal: dict) -> bool:
    """Require stable action identity across a Codex start/terminal pair."""
    if not codex_start_valid(start) or not codex_terminal_shape_valid(terminal):
        return False
    item_type = start.get("type")
    if terminal.get("type") != item_type:
        return False
    if item_type == "command_execution":
        return bool(start.get("command")) and terminal.get("command") == start.get(
            "command"
        )
    if item_type == "file_change":
        return {
            comparable_path_token(change["path"]): change["kind"]
            for change in start.get("changes", [])
        } == {
            comparable_path_token(change["path"]): change["kind"]
            for change in terminal.get("changes", [])
        }
    if item_type == "mcp_tool_call":
        return all(
            (
                terminal.get("server") == start.get("server"),
                terminal.get("tool") == start.get("tool"),
                json_values_equal(
                    terminal.get("arguments"), start.get("arguments")
                ),
            )
        )
    if item_type == "collab_tool_call":
        stable = all(
            (
                terminal.get("tool") == start.get("tool"),
                terminal.get("sender_thread_id") == start.get("sender_thread_id"),
                terminal.get("prompt") == start.get("prompt"),
            )
        )
        if not stable:
            return False
        start_receivers = set(start["receiver_thread_ids"])
        terminal_receivers = set(terminal["receiver_thread_ids"])
        if start["tool"] == "spawn_agent":
            return True
        if start["tool"] == "wait":
            return terminal_receivers <= start_receivers
        return terminal_receivers == start_receivers
    if item_type == "web_search":
        start_query = start.get("query")
        terminal_query = terminal.get("query")
        return "query" in start and isinstance(terminal_query, str) and start_query in (
            "",
            terminal_query,
        )
    return True


def codex_terminal_outcome(terminal_type: str, item: dict) -> str:
    """Classify a structurally valid Codex terminal event."""
    if terminal_type != "item.completed" or not codex_terminal_shape_valid(item):
        return "ambiguous"
    item_type = item.get("type")
    if item_type == "web_search":
        # The flat producer omits WebSearch status. `item.completed` proves the
        # lifecycle event, not whether the underlying search succeeded.
        return "unverified"
    status = item.get("status")
    if item_type == "command_execution":
        exit_code = item.get("exit_code")
        if status in {"failed", "declined"}:
            return "failed"
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            return "ambiguous"
        return "succeeded" if exit_code == 0 else "failed"
    if item_type == "collab_tool_call":
        if item.get("tool") != "spawn_agent":
            return "unverified"
        if item.get("status") == "failed":
            return "failed"
        return "succeeded" if item.get("receiver_thread_ids") else "failed"
    return "succeeded" if status == "completed" else "failed"


def codex_item_output(item: dict) -> str:
    """Return exact model-visible output when the flat event proves it.

    Current Codex flat events do not preserve that form for any mapped tool.
    In particular, MCP model output adds wall-time framing and is truncated
    independently from the larger event result, so reconstructing it here
    would turn event-only bytes into false model-visibility evidence.
    """
    return ""


def codex_tool_events(records: list[dict]) -> list[dict]:
    """Normalize unique Codex terminal events and unresolved starts."""
    lifecycle = codex_turn_memberships(records)
    starts, terminals = codex_tool_occurrences(records, lifecycle)
    identity_ambiguities = codex_item_identity_ambiguities(
        records, (starts, terminals), lifecycle
    )
    sequence_ambiguous = (
        codex_turn_status(records, identity_ambiguities) == "ambiguous_sequence"
    )
    events: list[dict] = []
    has_lifecycle, memberships = lifecycle
    occurrence_items_by_id: dict[str, list[dict]] = {}
    for record in records:
        if not model_visible_root(record) or record.get("type") not in {
            "item.started",
            "item.updated",
            "item.completed",
        }:
            continue
        item = record.get("item")
        item_id = item.get("id") if isinstance(item, dict) else None
        if isinstance(item_id, str) and item_id:
            occurrence_items_by_id.setdefault(item_id, []).append(item)
    ids = set(starts) | set(terminals)
    ordered_ids = sorted(
        ids,
        key=lambda item_id: min(
            [index for index, _ in starts.get(item_id, [])]
            + [index for index, _, _ in terminals.get(item_id, [])]
        ),
    )
    for item_id in ordered_ids:
        call_occurrences = starts.get(item_id, [])
        result_occurrences = terminals.get(item_id, [])
        occurrence_items = occurrence_items_by_id.get(item_id, [])
        if len(result_occurrences) == 1:
            terminal_index, terminal_item, terminal_type = result_occurrences[0]
            compatible = (
                not call_occurrences
                and codex_terminal_shape_valid(terminal_item)
                and codex_membership_valid(
                    has_lifecycle, memberships, terminal_index
                )
                or len(call_occurrences) == 1
                and call_occurrences[0][0] < terminal_index
                and codex_memberships_share(
                    has_lifecycle,
                    memberships,
                    call_occurrences[0][0],
                    terminal_index,
                )
                and codex_items_share_identity(call_occurrences[0][1], terminal_item)
            )
            outcome = (
                codex_terminal_outcome(terminal_type, terminal_item)
                if compatible
                and item_id not in identity_ambiguities
                and not sequence_ambiguous
                else "ambiguous"
            )
            event_item = terminal_item
            event_index = terminal_index
            output = codex_item_output(terminal_item) if outcome != "ambiguous" else ""
        else:
            event_index, event_item = (
                call_occurrences[0]
                if call_occurrences
                else (result_occurrences[0][0], result_occurrences[0][1])
            )
            outcome = (
                "unresolved"
                if len(call_occurrences) == 1
                and not result_occurrences
                and codex_start_valid(call_occurrences[0][1])
                and codex_membership_valid(
                    has_lifecycle, memberships, call_occurrences[0][0]
                )
                and item_id not in identity_ambiguities
                and not sequence_ambiguous
                else "ambiguous"
            )
            output = ""
        event = {
                "host": "codex",
                "id": item_id,
                "tool": event_item.get("type") or "?",
                "input": event_item,
                "succeeded": outcome == "succeeded",
                "outcome": outcome,
                "output": output,
                "at": records[event_index].get("timestamp", ""),
            }
        if outcome == "ambiguous" and len(occurrence_items) > 1:
            event["ambiguous_inputs"] = occurrence_items
        events.append(event)
    return events


def terminal_tool_events(records: list[dict]) -> list[dict]:
    """Normalize root terminal tool events while retaining action/output provenance."""
    events: list[dict] = codex_tool_events(records)
    claude_results = claude_tool_results(records)
    _claude_calls, claude_result_occurrences = claude_tool_occurrences(records)
    ambiguous_ids = ambiguous_claude_tool_ids(records)
    for record in records:
        if not root_assistant_record(record):
            continue
        for block in blocks(record):
            if block.get("type") != "tool_use":
                continue
            tool_id = block.get("id")
            paired = claude_results.get(tool_id) if isinstance(tool_id, str) else None
            result_occurrences = (
                claude_result_occurrences.get(tool_id, [])
                if isinstance(tool_id, str)
                else []
            )
            result_record = (
                records[result_occurrences[0][0]]
                if len(result_occurrences) == 1
                else None
            )
            structured_result_present = bool(
                isinstance(result_record, dict) and "toolUseResult" in result_record
            )
            structured_result_associated = bool(
                isinstance(result_record, dict)
                and sum(
                    result_block.get("type") == "tool_result"
                    for result_block in blocks(result_record)
                )
                == 1
            )
            raw_structured_result = (
                result_record.get("toolUseResult")
                if isinstance(result_record, dict)
                else None
            )
            outcome = (
                "ambiguous"
                if not isinstance(tool_id, str) or not tool_id or tool_id in ambiguous_ids
                else "unresolved"
                if paired is None
                else "succeeded"
                if paired[0]
                else "failed"
            )
            events.append(
                {
                    "host": "claude",
                    "id": tool_id or "",
                    "tool": block.get("name") or "?",
                    "input": block.get("input") or {},
                    "succeeded": bool(paired and paired[0]),
                    "outcome": outcome,
                    # Error results are model-visible too. Success controls what
                    # action can be inferred, not whether the output existed.
                    "output": paired[1] if paired else "",
                    "structured_result": (
                        raw_structured_result
                        if structured_result_associated
                        and isinstance(raw_structured_result, dict)
                        else {}
                    ),
                    "structured_result_present": structured_result_present,
                    "structured_result_associated": structured_result_associated,
                    "structured_result_shape": (
                        "dict"
                        if isinstance(raw_structured_result, dict)
                        else type(raw_structured_result).__name__
                        if structured_result_present
                        else "absent"
                    ),
                    "at": record.get("timestamp", ""),
                }
            )
    return events


ECMASCRIPT_TRIM_CHARACTERS = (
    "\u0009\u000b\u000c\u0020\u00a0\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u202f\u205f\u3000\ufeff\u000a\u000d\u2028\u2029"
)


def claude_read_pages_valid(value: object) -> bool:
    """Mirror Claude's current prefix-decimal, at-most-20-page validator."""
    if not isinstance(value, str) or not (
        text := value.strip(ECMASCRIPT_TRIM_CHARACTERS)
    ):
        return False
    if text.endswith("-"):
        return False

    def parse_prefix(part: str) -> float | None:
        match = re.match(
            r"([+-]?)([0-9]+)", part.lstrip(ECMASCRIPT_TRIM_CHARACTERS)
        )
        if not match:
            return None
        try:
            number = float(match.group(2))
        except (OverflowError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        return -number if match.group(1) == "-" else number

    if "-" in text:
        first_text, last_text = text.split("-", 1)
        first, last = parse_prefix(first_text), parse_prefix(last_text)
    else:
        first = last = parse_prefix(text)
    return bool(
        first is not None
        and last is not None
        and first >= 1
        and last >= first
        and last - first + 1 <= 20
    )


def structured_read_file(event: dict) -> tuple[str, dict | None]:
    """Validate a present Claude Read result before exact provenance use."""
    structured = (
        event.get("structured_result")
        if isinstance(event.get("structured_result"), dict)
        else {}
    )
    present = bool(
        event.get("structured_result_present", bool(structured))
    )
    if not present:
        return "absent", None
    if not event.get("structured_result_associated", True):
        return "invalid", None
    if event.get("structured_result_shape", "dict") != "dict":
        return "invalid", None
    if structured.get("type") != "text":
        return "invalid", None
    artifact_read = structured.get("artifactRead")
    if artifact_read is not None and not (
        isinstance(artifact_read, dict)
        and isinstance(artifact_read.get("slug"), str)
        and isinstance(artifact_read.get("ver"), str)
    ):
        return "invalid", None
    file_result = structured.get("file")
    if not (
        isinstance(file_result, dict)
        and isinstance(file_result.get("filePath"), str)
        and bool(file_result["filePath"])
        and isinstance(file_result.get("content"), str)
    ):
        return "invalid", None

    range_fields = ("startLine", "numLines", "totalLines")
    if not all(field in file_result for field in range_fields):
        return "invalid", None
    start, count, total = (file_result[field] for field in range_fields)
    if not (
        isinstance(start, int)
        and not isinstance(start, bool)
        and start >= 0
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count >= 0
        and isinstance(total, int)
        and not isinstance(total, bool)
        and total >= 0
        and count <= total
        and (count == 0 or start + count - 1 <= total)
    ):
        return "invalid", None
    if "truncatedByTokenCap" in file_result and not isinstance(
        file_result["truncatedByTokenCap"], bool
    ):
        return "invalid", None
    content = normalize_crlf(file_result["content"])
    if count == 0 and content or count > 0 and len(content.split("\n")) != count:
        return "invalid", None

    request = event.get("input")
    if not (
        isinstance(request, dict)
        and isinstance(request.get("file_path"), str)
        and bool(request["file_path"])
    ):
        return "invalid", None
    if "pages" in request and not claude_read_pages_valid(request["pages"]):
        return "invalid", None
    offset = request.get("offset", 1)
    expected_start = (
        max(1, offset)
        if isinstance(offset, int)
        and not isinstance(offset, bool)
        and file_result.get("truncatedByTokenCap") is True
        else offset
    )
    if file_result.get("truncatedByTokenCap") is True and (
        offset not in {0, 1}
        or "limit" in request
        or "pages" in request
    ):
        return "invalid", None
    if not (
        isinstance(offset, int)
        and not isinstance(offset, bool)
        and offset >= 0
        and start == expected_start
    ):
        return "invalid", None
    if "limit" in request:
        limit = request["limit"]
        if not (
            isinstance(limit, int)
            and not isinstance(limit, bool)
            and limit > 0
            and count <= limit
        ):
            return "invalid", None
    return "valid", file_result


def decoded_event_output(event: dict) -> str:
    """Decode a proven complete or partial Claude Read frame."""
    output = event.get("output") if isinstance(event.get("output"), str) else ""
    if not (
        event.get("host") == "claude"
        and event.get("tool") == "Read"
        and event.get("succeeded")
    ):
        return output
    data = event.get("input") if isinstance(event.get("input"), dict) else {}
    requested = data.get("file_path") or data.get("path")
    structured_state, file_result = structured_read_file(event)
    if structured_state != "valid" or file_result is None:
        return output
    observed_path = file_result.get("filePath")
    if not (
        isinstance(requested, str)
        and isinstance(observed_path, str)
        and comparable_path_token(requested) == comparable_path_token(observed_path)
    ):
        return output
    if not all(
        field in file_result for field in ("startLine", "numLines", "totalLines")
    ):
        return output
    start = file_result.get("startLine")
    count = file_result.get("numLines")
    total = file_result.get("totalLines")
    content = file_result.get("content")
    if not (
        isinstance(start, int)
        and not isinstance(start, bool)
        and start >= 0
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count >= 0
        and isinstance(total, int)
        and not isinstance(total, bool)
        and total >= 0
        and (count == 0 or start + count - 1 <= total)
        and isinstance(content, str)
    ):
        return output
    framed = [] if not output else output.split("\n")
    if len(framed) != count:
        return output
    decoded: list[str] = []
    frame_separator: str | None = None
    for expected_number, line in enumerate(framed, start):
        # Current Read frames use one unpadded TAB or COLON separator.  The
        # persisted decoder also accepts the legacy arrow with ASCII padding.
        current = re.fullmatch(r"([0-9]+)([\t:])(.*)", line)
        legacy = re.fullmatch(r" *([0-9]+)(→)(.*)", line)
        match = current or legacy
        if not match or match.group(1) != str(expected_number):
            return output
        separator = match.group(2)
        if frame_separator is None:
            frame_separator = separator
        elif separator != frame_separator:
            return output
        decoded.append(match.group(3))
    reconstructed = "\n".join(decoded)
    if frame_separator == ":" and not (
        content.startswith("\t") or "\n\t" in content
    ):
        return output
    return reconstructed if reconstructed == content else output


def read_result_content_agrees(event: dict, decoded_output: str) -> bool:
    """Reject excerpt provenance contradicted by structured Read content."""
    state, file_result = structured_read_file(event)
    if state == "absent":
        return True
    if state != "valid" or file_result is None:
        return False
    content = file_result.get("content")
    return isinstance(content, str) and normalize_crlf(decoded_output) == normalize_crlf(
        content
    )


def event_path_payloads(event: dict) -> list[str]:
    """Return only tool fields whose semantics identify a filesystem target."""
    ambiguous_inputs = event.get("ambiguous_inputs")
    if event.get("host") == "codex" and isinstance(ambiguous_inputs, list):
        return [
            path
            for item in ambiguous_inputs
            if isinstance(item, dict)
            for path in event_path_payloads(
                {
                    "host": "codex",
                    "tool": item.get("type") or "?",
                    "input": item,
                }
            )
        ]
    tool = event.get("tool")
    data = event.get("input") if isinstance(event.get("input"), dict) else {}
    if tool in {"command_execution", "Bash"}:
        return []
    if tool == "file_change":
        return [
            change["path"]
            for change in data.get("changes") or []
            if isinstance(change, dict) and isinstance(change.get("path"), str)
        ]
    if tool in {"Glob", "Grep"}:
        base = data.get("path")
        selector = data.get("pattern" if tool == "Glob" else "glob")
        paths = [base] if isinstance(base, str) else []
        if isinstance(selector, str):
            if recognized_path_root(selector) is not None:
                paths.append(selector)
            elif isinstance(base, str):
                windows_base = windows_path_semantics(base)
                separator = "\\" if windows_base and "\\" in base else "/"
                normalized_selector = (
                    selector.replace("/", separator).replace("\\", separator)
                    if windows_base
                    else selector
                )
                dot_prefix = f".{separator}"
                if normalized_selector.startswith(dot_prefix):
                    normalized_selector = normalized_selector[len(dot_prefix) :]
                selector_parts = normalized_selector.split(separator)
                if (
                    normalized_selector
                    and not selector.startswith(("/", "\\"))
                    and re.match(r"^[A-Za-z]:[/\\]", normalized_selector) is None
                    and not re.search(r"[*?\[\]{}]", normalized_selector)
                    and all(part not in {"", ".", ".."} for part in selector_parts)
                ):
                    paths.append(base.rstrip("/\\") + separator + normalized_selector)
        return paths
    if tool == "Read":
        paths = [
            data[field]
            for field in ("file_path", "path")
            if isinstance(data.get(field), str)
        ]
        structured = event.get("structured_result")
        file_result = structured.get("file") if isinstance(structured, dict) else None
        if isinstance(file_result, dict) and isinstance(
            file_result.get("filePath"), str
        ):
            paths.append(file_result["filePath"])
        return paths
    fields = {
        "Edit": ("file_path",),
        "Write": ("file_path",),
        "MultiEdit": ("file_path",),
        "NotebookEdit": ("notebook_path",),
    }.get(tool, ())
    return [data[field] for field in fields if isinstance(data.get(field), str)]


def read_path_evidence_conflicts(event: dict) -> bool:
    """Return whether structured Read path operands identify different targets."""
    if event.get("host") != "claude" or event.get("tool") != "Read":
        return False
    normalized = [comparable_path_token(path) for path in event_path_payloads(event)]
    return any(path is None for path in normalized) or len(set(normalized)) > 1


def unambiguous_read_path(event: dict) -> str | None:
    """Return one agreed Read target across structured call/result evidence."""
    if not (
        event.get("host") == "claude"
        and event.get("tool") == "Read"
        and event.get("succeeded")
    ):
        return None
    data = event.get("input") if isinstance(event.get("input"), dict) else {}
    raw_paths = [
        data[field]
        for field in ("file_path", "path")
        if field in data and isinstance(data.get(field), str)
    ]
    if any(
        field in data and not isinstance(data.get(field), str)
        for field in ("file_path", "path")
    ):
        return None
    if not raw_paths:
        return None

    structured_state, file_result = structured_read_file(event)
    if structured_state == "invalid":
        return None
    if structured_state == "valid":
        if file_result is None:
            return None
        raw_paths.append(file_result["filePath"])

    normalized = [comparable_path_token(path) for path in raw_paths]
    if not normalized or any(path is None for path in normalized):
        return None
    unique = set(normalized)
    return raw_paths[0] if len(unique) == 1 else None


def detect_skills(records: list[dict]) -> list[dict]:
    """Summarize observed top-level skill activation and file access.

    The summary contains no raw path. Historical and future sibling names are
    discovered from transcript evidence rather than a package roster.
    """
    evidence: dict[tuple[str, str, str], Counter[str]] = {}
    claude_results = claude_tool_results(records)
    ambiguous_ids = ambiguous_claude_tool_ids(records)
    injections = skill_injection_observations(records)
    call_names = skiphow_skill_call_names(records)

    def add(name: str, source: str, version: str, signal: str) -> None:
        evidence.setdefault((name, source, version), Counter())[signal] += 1

    for record in records:
        if not root_assistant_record(record):
            continue
        for block in blocks(record):
            if block.get("type") != "tool_use" or block.get("name") != "Skill":
                continue
            tool_id = block.get("id")
            if not isinstance(tool_id, str) or tool_id not in call_names:
                continue
            name = call_names[tool_id]
            result = claude_results.get(tool_id) if isinstance(tool_id, str) else None
            observation = injections.get(tool_id, {}) if isinstance(tool_id, str) else {}
            source = str(observation.get("source") or "plugin")
            version = str(observation.get("version") or "unknown")
            status = observation.get("status")
            if tool_id in ambiguous_ids:
                add(name, "plugin", "unknown", "activation_ambiguous")
            elif status in {"body_observed", "body_unverified"}:
                add(name, source, version, "activated")
                add(name, source, version, str(status))
            elif observation:
                add(name, source, version, str(status))
            elif result and result[0]:
                add(name, "plugin", "unknown", "activation_succeeded_body_unobserved")
            else:
                add(name, "plugin", "unknown", "attempted")

    for tool_id, observation in injections.items():
        if not tool_id.startswith("unattributed:"):
            continue
        status = observation.get("status")
        if status not in {"body_observed", "body_unverified"}:
            continue
        add(
            str(observation.get("name") or "skiphow"),
            str(observation.get("source") or "plugin"),
            str(observation.get("version") or "unknown"),
            f"{status}_unattributed",
        )

    for _tool_id in ambiguous_successful_skill_result_ids(records):
        add("unknown", "plugin", "unknown", "activation_ambiguous")

    for event in terminal_tool_events(records):
        tool = event["tool"]
        data = event["input"]
        succeeded = event["succeeded"]
        ambiguous_inputs = event.get("ambiguous_inputs")
        file_change_event = tool == "file_change" or bool(
            event.get("host") == "codex"
            and isinstance(ambiguous_inputs, list)
            and any(
                isinstance(item, dict) and item.get("type") == "file_change"
                for item in ambiguous_inputs
            )
        )
        if file_change_event:
            found: set[tuple[str, str, str]] = set()
            for path in event_path_payloads(event):
                for hit in skill_paths(path, require_file=True):
                    found.add((hit["name"], hit["source"], hit["version"]))
            for name, source, version in found:
                signal = (
                    "path_action_ambiguous"
                    if event["outcome"] == "ambiguous"
                    else "path_action_unresolved"
                    if event["outcome"] == "unresolved"
                    else "write_action_succeeded"
                    if succeeded
                    else "path_action_failed"
                )
                add(
                    name,
                    source,
                    version,
                    signal,
                )
            continue
        if tool == "command_execution":
            continue
        if event["host"] != "claude" or tool == "Skill":
            continue
        found: set[tuple[str, str, str, str]] = set()
        hits = [
            hit
            for value in event_path_payloads(event)
            for hit in skill_paths(value, require_file=True)
        ]
        for hit in hits:
            if event["outcome"] == "ambiguous":
                signal = "path_action_ambiguous"
            elif tool == "Read" and read_path_evidence_conflicts(event):
                signal = "path_action_ambiguous"
            elif event["outcome"] == "unresolved":
                signal = "path_action_unresolved"
            elif not succeeded:
                signal = "path_action_failed"
            elif tool == "Read":
                signal = "read_action_observed"
            elif tool in {"Grep", "Glob"}:
                signal = "search_action_observed"
            elif tool in STRUCTURED_WRITE_TOOLS:
                signal = "write_action_succeeded"
            else:
                signal = "path_action_observed"
            found.add((hit["name"], hit["source"], hit["version"], signal))
        for name, source, version, signal in found:
            add(name, source, version, signal)

    signal_order = {
        name: index
        for index, name in enumerate(
            (
                "activated",
                "activation_ambiguous",
                "activation_path_mismatch",
                "body_unverified",
                "ambiguous_injection",
                "activation_succeeded_body_unobserved",
                "read_action_observed",
                "search_action_observed",
                "write_action_succeeded",
                "path_action_observed",
                "path_action_failed",
                "path_action_ambiguous",
                "path_action_unresolved",
            )
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


def valid_reference_name(name: str) -> bool:
    segment = r"[A-Za-z0-9][A-Za-z0-9._-]*"
    return isinstance(name, str) and bool(re.fullmatch(rf"{segment}(?:/{segment})*", name))


def tagged_artifact(version: str, relative: str) -> tuple[str, str] | None:
    """Return exact tag bytes or a proven exact-path absence."""
    if not re.fullmatch(PLUGIN_VERSION_PATTERN, version):
        return None
    tag = f"v{version}"
    try:
        tagged = subprocess.run(
            ["git", "show", f"{tag}:{relative}"],
            cwd=repository_root(),
            capture_output=True,
            check=False,
        )
        if tagged.returncode == 0:
            return tagged.stdout.decode("utf-8"), "tag"
        listed = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", tag, "--", relative],
            cwd=repository_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        if listed.returncode == 0 and relative not in listed.stdout.splitlines():
            return "", "absent_in_version"
    except (OSError, UnicodeError):
        return None
    return None


def cache_descriptor_walk_supported() -> bool:
    """Require held, descriptor-relative no-follow traversal primitives."""
    return bool(
        hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and os.open in os.supports_dir_fd
        and os.scandir in os.supports_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
    )


def cache_directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def cache_file_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def cache_status_is_plain_directory(status: os.stat_result) -> bool:
    return stat.S_ISDIR(status.st_mode) and not getattr(
        status, "st_reparse_tag", 0
    )


def open_cache_root_descriptor(root: str | Path) -> int:
    """Open and bind one real cache root without following its final node."""
    if not cache_descriptor_walk_supported():
        raise OSError("descriptor-relative cache traversal is unavailable")
    root_path = Path(root)
    descriptor = os.open(root_path, cache_directory_flags())
    try:
        opened = os.fstat(descriptor)
        current = os.lstat(root_path)
        if not (
            cache_status_is_plain_directory(opened)
            and cache_status_is_plain_directory(current)
            and os.path.samestat(opened, current)
        ):
            raise OSError("cache root identity is unstable")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def open_cache_child_directory(parent: int, name: str) -> int:
    descriptor = os.open(name, cache_directory_flags(), dir_fd=parent)
    try:
        opened = os.fstat(descriptor)
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not (
            cache_status_is_plain_directory(opened)
            and cache_status_is_plain_directory(current)
            and os.path.samestat(opened, current)
        ):
            raise OSError("cache child is not a plain directory")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def read_cache_artifact(
    root: str | Path, version: str, relative: str
) -> str | None:
    """Read one UTF-8 artifact through a held no-follow cache descriptor chain."""
    root_text = os.fspath(root)
    if (
        not portable_absolute_path(root_text)
        or windows_path_semantics(root_text) and os.name != "nt"
    ):
        return None
    components = (version, *Path(relative).parts)
    if not components or any(component in {"", ".", ".."} for component in components):
        return None
    directories: list[int] = []
    directory_snapshots: list[tuple[int, int, int, int, int]] = []
    artifact: int | None = None
    try:
        directories.append(open_cache_root_descriptor(root_text))
        directory_snapshots.append(
            regular_snapshot(os.fstat(directories[-1]))
        )
        for component in components[:-1]:
            directories.append(
                open_cache_child_directory(directories[-1], component)
            )
            directory_snapshots.append(
                regular_snapshot(os.fstat(directories[-1]))
            )
        artifact = os.open(
            components[-1], cache_file_flags(), dir_fd=directories[-1]
        )
        before = os.fstat(artifact)
        opened_entry = os.stat(
            components[-1],
            dir_fd=directories[-1],
            follow_symlinks=False,
        )
        if not (
            stat.S_ISREG(before.st_mode)
            and stat.S_ISREG(opened_entry.st_mode)
            and not getattr(before, "st_reparse_tag", 0)
            and not getattr(opened_entry, "st_reparse_tag", 0)
            and os.path.samestat(before, opened_entry)
        ):
            return None
        chunks: list[bytes] = []
        while chunk := os.read(artifact, 1 << 20):
            chunks.append(chunk)
        after = os.fstat(artifact)
        if regular_snapshot(before) != regular_snapshot(after):
            return None
        current_root = os.lstat(root_text)
        opened_root = os.fstat(directories[0])
        if not (
            cache_status_is_plain_directory(current_root)
            and os.path.samestat(opened_root, current_root)
            and regular_snapshot(opened_root) == directory_snapshots[0]
            and regular_snapshot(current_root) == directory_snapshots[0]
        ):
            return None
        for index, component in enumerate(components[:-1]):
            current = os.stat(
                component,
                dir_fd=directories[index],
                follow_symlinks=False,
            )
            opened = os.fstat(directories[index + 1])
            if not (
                cache_status_is_plain_directory(current)
                and os.path.samestat(opened, current)
                and regular_snapshot(opened) == directory_snapshots[index + 1]
                and regular_snapshot(current) == directory_snapshots[index + 1]
            ):
                return None
        current_entry = os.stat(
            components[-1],
            dir_fd=directories[-1],
            follow_symlinks=False,
        )
        if not (
            stat.S_ISREG(current_entry.st_mode)
            and not getattr(current_entry, "st_reparse_tag", 0)
            and os.path.samestat(after, current_entry)
            and regular_snapshot(after) == regular_snapshot(current_entry)
        ):
            return None
        return b"".join(chunks).decode("utf-8")
    except (OSError, UnicodeError):
        return None
    finally:
        if artifact is not None:
            os.close(artifact)
        for directory in reversed(directories):
            os.close(directory)


def cached_artifact(version: str, relative: str) -> tuple[str, str]:
    """Return cache bytes only when every existing host cache agrees."""
    roots: list[Path] = []
    for root in plugin_cache_roots():
        try:
            root_status = root.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            return "", "contract_bytes_unavailable"
        if not cache_status_is_plain_directory(root_status):
            return "", "contract_bytes_unavailable"
        try:
            version_status = (root / version).lstat()
        except FileNotFoundError:
            continue
        except OSError:
            return "", "contract_bytes_unavailable"
        if not cache_status_is_plain_directory(version_status):
            return "", "contract_bytes_unavailable"
        roots.append(root)
    if not roots:
        return "", "contract_bytes_unavailable"
    values = [read_cache_artifact(root, version, relative) for root in roots]
    if any(value is None for value in values) or len(set(values)) != 1:
        return "", "contract_bytes_unavailable"
    return str(values[0]), "cache"


def observed_cache_artifact(
    roots: tuple[str, ...], version: str, relative: str
) -> tuple[str, str] | None:
    """Read the exact observed cache root when it is still available."""
    if not roots or any(not portable_absolute_path(root) for root in roots):
        return None
    values: list[str | None] = []
    any_existing = False
    for root in roots:
        value = read_cache_artifact(root, version, relative)
        any_existing = any_existing or value is not None
        values.append(value)
    if not any_existing:
        return None
    if any(value is None for value in values) or len(set(values)) != 1:
        return "", "observed_cache_roots_disagree_or_are_incomplete"
    return str(values[0]), "observed_cache_path"


def package_reference(
    version: str, name: str, observed_roots: tuple[str, ...] = ()
) -> tuple[str, str]:
    """Read exact tagged or installed-cache bytes; never substitute current HEAD."""
    if not re.fullmatch(PLUGIN_VERSION_PATTERN, version) or not valid_reference_name(name):
        return "", "contract_bytes_unavailable"
    relative = f"plugins/skiphow/skills/skiphow/references/{name}.md"
    observed = observed_cache_artifact(
        observed_roots, version, f"skills/skiphow/references/{name}.md"
    )
    if observed_roots:
        return observed or ("", "observed_cache_roots_disagree_or_are_incomplete")
    if tagged := tagged_artifact(version, relative):
        return tagged
    return cached_artifact(version, f"skills/skiphow/references/{name}.md")


def package_skill(
    version: str, name: str, observed_root: str = ""
) -> tuple[str, str]:
    """Read one exact tagged or installed skill; never substitute current HEAD."""
    if not re.fullmatch(PLUGIN_VERSION_PATTERN, version) or not re.fullmatch(
        SKILL_NAME_PATTERN, name
    ):
        return "", "contract_bytes_unavailable"
    relative = f"plugins/skiphow/skills/{name}/SKILL.md"
    observed = observed_cache_artifact(
        (observed_root,) if observed_root else (),
        version,
        f"skills/{name}/SKILL.md",
    )
    if observed_root:
        return observed or ("", "observed_cache_roots_disagree_or_are_incomplete")
    if tagged := tagged_artifact(version, relative):
        return tagged
    return cached_artifact(version, f"skills/{name}/SKILL.md")


def package_skill_root(version: str) -> tuple[str, str]:
    """Compatibility wrapper for the exact owner skill artifact."""
    return package_skill(version, "skiphow")


def body_lines(body: str) -> list[str]:
    """Return distinct substantive lines after CRLF-to-LF normalization only."""
    normalized = normalize_crlf(body)
    return list(
        dict.fromkeys(line for line in normalized.split("\n") if line.strip())
    )


def cache_reference_roster_at(
    root: str | Path, version: str
) -> tuple[set[str], bool, bool]:
    """Read one cache roster through held, descriptor-relative directories."""
    root_text = os.fspath(root)
    if (
        not portable_absolute_path(root_text)
        or windows_path_semantics(root_text) and os.name != "nt"
    ):
        return set(), False, False
    root_path = Path(root_text)
    try:
        root_status = root_path.lstat()
    except FileNotFoundError:
        return set(), False, False
    except OSError:
        return set(), False, True
    if not cache_status_is_plain_directory(root_status):
        return set(), False, True
    if not cache_descriptor_walk_supported():
        try:
            (root_path / version).lstat()
        except FileNotFoundError:
            return set(), False, False
        except OSError:
            return set(), False, True
        return set(), False, True

    base_directories: list[int] = []
    base_snapshots: list[tuple[int, int, int, int, int]] = []
    references: int | None = None

    def close_base_directories() -> None:
        while base_directories:
            os.close(base_directories.pop())

    try:
        base_directories.append(open_cache_root_descriptor(root_text))
        base_snapshots.append(
            regular_snapshot(os.fstat(base_directories[-1]))
        )
        try:
            child = open_cache_child_directory(base_directories[-1], version)
        except FileNotFoundError:
            close_base_directories()
            return set(), False, False
        base_directories.append(child)
        base_snapshots.append(regular_snapshot(os.fstat(child)))
        for component in ("skills", "skiphow"):
            child = open_cache_child_directory(base_directories[-1], component)
            base_directories.append(child)
            base_snapshots.append(regular_snapshot(os.fstat(child)))
        try:
            references = open_cache_child_directory(
                base_directories[-1], "references"
            )
        except FileNotFoundError:
            close_base_directories()
            return set(), True, True
        base_directories.append(references)
        base_snapshots.append(regular_snapshot(os.fstat(references)))
    except OSError:
        close_base_directories()
        return set(), False, True

    names: set[str] = set()
    complete = True
    worklist: list[tuple[int, tuple[str, ...]]] = []
    traversed: list[
        tuple[int, int, str, tuple[int, int, int, int, int]]
    ] = []
    if references is not None:
        worklist.append((references, ()))
        references = None
    while worklist:
        directory, prefix = worklist.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError:
            complete = False
            continue
        for entry in entries:
            try:
                observed = entry.stat(follow_symlinks=False)
            except OSError:
                complete = False
                continue
            if stat.S_ISLNK(observed.st_mode) or getattr(
                observed, "st_reparse_tag", 0
            ):
                complete = False
                continue
            if stat.S_ISDIR(observed.st_mode):
                child: int | None = None
                try:
                    child = open_cache_child_directory(directory, entry.name)
                    opened = os.fstat(child)
                except OSError:
                    if child is not None:
                        os.close(child)
                    complete = False
                    continue
                if not os.path.samestat(observed, opened):
                    os.close(child)
                    complete = False
                    continue
                traversed.append(
                    (
                        child,
                        directory,
                        entry.name,
                        regular_snapshot(opened),
                    )
                )
                worklist.append((child, (*prefix, entry.name)))
                continue
            if not entry.name.endswith(".md"):
                continue
            artifact: int | None = None
            try:
                artifact = os.open(
                    entry.name, cache_file_flags(), dir_fd=directory
                )
                opened = os.fstat(artifact)
                current = os.stat(
                    entry.name, dir_fd=directory, follow_symlinks=False
                )
                if not (
                    stat.S_ISREG(opened.st_mode)
                    and not getattr(opened, "st_reparse_tag", 0)
                    and os.path.samestat(observed, opened)
                    and os.path.samestat(opened, current)
                ):
                    complete = False
                    continue
            except OSError:
                complete = False
                continue
            finally:
                if artifact is not None:
                    os.close(artifact)
            name = "/".join((*prefix, entry.name[:-3]))
            if valid_reference_name(name):
                names.add(name)
            else:
                complete = False
    tree_stable = True
    for descriptor, parent, name, snapshot in traversed:
        try:
            opened = os.fstat(descriptor)
            current = os.stat(
                name, dir_fd=parent, follow_symlinks=False
            )
            tree_stable = bool(
                tree_stable
                and cache_status_is_plain_directory(opened)
                and cache_status_is_plain_directory(current)
                and os.path.samestat(opened, current)
                and regular_snapshot(opened) == snapshot
                and regular_snapshot(current) == snapshot
            )
        except OSError:
            tree_stable = False
    for descriptor, parent, name, snapshot in reversed(traversed):
        try:
            os.close(descriptor)
            current = os.stat(
                name, dir_fd=parent, follow_symlinks=False
            )
            tree_stable = bool(
                tree_stable
                and cache_status_is_plain_directory(current)
                and regular_snapshot(current) == snapshot
            )
        except OSError:
            tree_stable = False
    base_stable = True
    try:
        current_root = os.lstat(root_text)
        opened_root = os.fstat(base_directories[0])
        base_stable = bool(
            cache_status_is_plain_directory(current_root)
            and os.path.samestat(opened_root, current_root)
            and regular_snapshot(opened_root) == base_snapshots[0]
            and regular_snapshot(current_root) == base_snapshots[0]
        )
        for index, component in enumerate(
            (version, "skills", "skiphow", "references")
        ):
            current = os.stat(
                component,
                dir_fd=base_directories[index],
                follow_symlinks=False,
            )
            opened = os.fstat(base_directories[index + 1])
            base_stable = bool(
                base_stable
                and cache_status_is_plain_directory(current)
                and os.path.samestat(opened, current)
                and regular_snapshot(opened) == base_snapshots[index + 1]
                and regular_snapshot(current) == base_snapshots[index + 1]
            )
    except OSError:
        base_stable = False
    close_base_directories()
    return (
        (names, complete, True)
        if base_stable and tree_stable
        else (set(), False, True)
    )


def version_reference_roster(version: str) -> tuple[set[str], bool]:
    """Return the union exact-version roster and whether its sources agree."""
    if not re.fullmatch(PLUGIN_VERSION_PATTERN, version):
        return set(), False
    prefix = "plugins/skiphow/skills/skiphow/references/"
    try:
        tagged = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", f"v{version}", "--", prefix],
            cwd=repository_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, UnicodeError):
        tagged = None
    if tagged and tagged.returncode == 0:
        return (
            {
                line[len(prefix) : -len(".md")]
                for line in tagged.stdout.splitlines()
                if line.startswith(prefix)
                and line.endswith(".md")
                and valid_reference_name(line[len(prefix) : -len(".md")])
            },
            True,
        )

    rosters: list[set[str]] = []
    complete = True
    for root in plugin_cache_roots():
        roster, roster_complete, exists = cache_reference_roster_at(root, version)
        if not exists:
            continue
        rosters.append(roster)
        complete = complete and roster_complete
    union = set().union(*rosters) if rosters else set()
    return union, bool(
        rosters
        and complete
        and all(roster == rosters[0] for roster in rosters)
    )


def observed_cache_reference_roster(
    roots: tuple[str, ...], version: str
) -> tuple[set[str], bool]:
    """Return the union roster and whether every observed cache root agrees."""
    rosters: list[set[str]] = []
    complete = bool(roots)
    for root in roots:
        roster, roster_complete, exists = cache_reference_roster_at(root, version)
        complete = complete and exists and roster_complete
        rosters.append(roster)
    union = set().union(*rosters) if rosters else set()
    agreed = complete and len(rosters) == len(roots) and all(
        roster == rosters[0] for roster in rosters
    )
    return union, agreed


def detect_references(
    _path: Path,
    records: list[dict],
    version: str,
    governing_roots: tuple[str, ...] | None = (),
) -> dict[str, dict]:
    """Report positive body and path-event observations without inferring a load."""
    events = terminal_tool_events(records)
    path_observations: dict[
        str, tuple[tuple[str, str, str, str] | None, str | None]
    ] = {}

    def observe_path(
        path: str,
    ) -> tuple[tuple[str, str, str, str] | None, str | None]:
        if path not in path_observations:
            rooted = recognized_path_root(path)
            path_observations[path] = (rooted, reference_name_from_rooted(rooted))
        return path_observations[path]

    indexed_events: list[tuple[dict, list[str], dict[str, list[str]]]] = []
    observed_names: set[str] = set()
    for event in events:
        payloads = event_path_payloads(event)
        paths_by_name: dict[str, list[str]] = {}
        for payload in payloads:
            _rooted, reference_name = observe_path(payload)
            if reference_name is not None:
                observed_names.add(reference_name)
                paths_by_name.setdefault(reference_name, []).append(payload)
        indexed_events.append((event, payloads, paths_by_name))

    roster_unverified = governing_roots is None
    if governing_roots:
        roster, roster_agrees = observed_cache_reference_roster(
            governing_roots, version
        )
        roster_unverified = not roster_agrees
        version_names = roster
    elif governing_roots is None:
        version_names = set()
    else:
        if version == "unknown":
            # The production helper returns no roster for an unknown version,
            # while injected test/catalog sources may still provide the names
            # whose path-only evidence must remain visible.  Do not read body
            # bytes for them below.
            version_names = version_reference_names(version)
            roster_unverified = False
        else:
            version_names, roster_agrees = version_reference_roster(version)
            roster_unverified = not roster_agrees
    named = version_names | observed_names
    if roster_unverified:
        named.add(REFERENCE_ROSTER_LABEL)
    names = tuple(sorted(named))

    observed_roots: dict[str, set[str]] = {name: set() for name in names}
    for event, payloads, paths_by_name in indexed_events:
        if not event.get("succeeded"):
            continue
        for reference_name, paths in paths_by_name.items():
            if reference_name not in observed_roots:
                continue
            for payload in paths:
                rooted, _name = observe_path(payload)
                if not rooted or rooted[0] != "cache" or rooted[2] != version:
                    continue
                if portable_absolute_path(rooted[3]):
                    observed_roots[reference_name].add(rooted[3])
    bodies: dict[str, str] = {}
    sources: dict[str, str] = {}
    lines: dict[str, list[str]] = {}
    for name in names:
        roots = (
            set(governing_roots)
            if governing_roots
            else set(observed_roots[name])
        )
        if governing_roots and not roster_unverified and name not in version_names:
            body, source = "", "absent_in_version"
        elif version == "unknown" or roster_unverified:
            body, source = "", "contract_bytes_unavailable"
        else:
            body, source = package_reference(
                version, name, tuple(sorted(roots))
            )
        bodies[name], sources[name] = normalize_crlf(body), source
        lines[name] = body_lines(body) if body else []

    actions: dict[str, set[str]] = {name: set() for name in names}
    mismatched_versions: dict[str, set[str]] = {name: set() for name in names}
    mismatched_sources: dict[str, set[str]] = {name: set() for name in names}
    observed_lines: dict[str, set[str]] = {name: set() for name in names}
    body_observed = {name: False for name in names}
    excerpt_observed = {name: False for name in names}

    def selected_contract_path(path: str) -> bool:
        if version == "unknown":
            return True
        rooted, _name = observe_path(path)
        if not (rooted and rooted[0] == "cache" and rooted[2] == version):
            return False
        if not governing_roots:
            return True
        selected_roots = {
            comparable_path_token(root) for root in governing_roots
        }
        return comparable_path_token(rooted[3]) in selected_roots

    for event, payloads, indexed_paths_by_name in indexed_events:
        tool = event["tool"]
        agreed_read_path = unambiguous_read_path(event)
        paths_by_name = {
            name: indexed_paths_by_name.get(name, []) for name in names
        }

        output = normalize_crlf(decoded_event_output(event))
        excerpt_provenance = bool(
            agreed_read_path is not None
            and read_result_content_agrees(event, output)
        )
        if output:
            output_lines = {line for line in output.split("\n") if line}
            for name in names:
                matching = set(lines[name]) & output_lines
                observed_lines[name].update(matching)
                if (
                    matching
                    and excerpt_provenance
                    and agreed_read_path is not None
                    and observe_path(agreed_read_path)[1] == name
                    and selected_contract_path(agreed_read_path)
                ):
                    excerpt_observed[name] = True
                candidate_body = bodies[name].rstrip("\n")
                if (
                    candidate_body.strip()
                    and candidate_body in output
                ):
                    body_observed[name] = True

        for name, raw_paths in paths_by_name.items():
            for path in raw_paths:
                rooted, _name = observe_path(path)
                path_version = (
                    rooted[2] if rooted and rooted[0] == "cache" else None
                )
                if (
                    version != "unknown"
                    and path_version
                    and path_version != version
                ):
                    mismatched_versions[name].add(path_version)
                    actions[name].add("version_mismatch_path_observed")
                elif (
                    version != "unknown"
                    and rooted
                    and rooted[0] != "cache"
                ):
                    actions[name].add("source_mismatch_path_observed")
                    mismatched_sources[name].add(rooted[0])
                elif (
                    version != "unknown"
                    and rooted
                    and rooted[0] == "cache"
                    and rooted[2] == version
                    and governing_roots
                    and not selected_contract_path(path)
                ):
                    actions[name].add("source_mismatch_path_observed")
                    mismatched_sources[name].add("cache_root")
            paths = [path for path in raw_paths if selected_contract_path(path)]
            if not paths:
                continue
            if event["outcome"] == "ambiguous":
                action = "path_action_ambiguous"
            elif tool == "Read" and read_path_evidence_conflicts(event):
                action = "path_action_ambiguous"
            elif event["outcome"] == "unresolved":
                action = "path_action_unresolved"
            elif not event["succeeded"]:
                action = "path_action_failed"
            elif tool == "Read":
                action = "read_action_observed"
            elif tool in {"Grep", "Glob"}:
                action = "search_action_observed"
            elif tool in STRUCTURED_WRITE_TOOLS or tool == "file_change":
                action = "write_action_succeeded"
            else:
                action = "path_action_observed"
            actions[name].add(action)

    out: dict[str, dict] = {}
    priority = (
        "write_action_succeeded",
        "read_action_observed",
        "search_action_observed",
        "path_action_observed",
        "path_action_failed",
        "path_action_ambiguous",
        "path_action_unresolved",
        "version_mismatch_path_observed",
        "source_mismatch_path_observed",
    )
    for name in names:
        action = actions[name]
        hit = len(observed_lines[name])
        total = len(lines[name])
        if roster_unverified or sources[name] == "observed_cache_roots_disagree_or_are_incomplete":
            verdict, basis = "unverified_contract_provenance", "governing_cache_roots_unsettled"
        elif sources[name] == "absent_in_version":
            verdict, basis = "absent_in_version", "exact_version_artifact"
        elif body_observed[name]:
            verdict, basis = "body_observed", "complete_artifact_text_in_model_output"
        elif excerpt_observed[name]:
            verdict, basis = "exact_excerpt_observed", "exact_path_read_result"
        elif hit:
            verdict, basis = "matching_lines_observed", "matching_decoded_line_text"
        elif action:
            verdict = next(label for label in priority if label in action)
            basis = "tool_event"
        else:
            verdict, basis = "not_observed", "transcript_absence_only"
        out[name] = {
            "verdict": verdict,
            "basis": basis,
            "matching_line_values": f"{hit}/{total}" if total else "unavailable",
            "artifact_source": sources[name],
            "actions": sorted(action) or ["none"],
            "mismatched_path_versions": sorted(mismatched_versions[name]),
            "mismatched_path_sources": sorted(mismatched_sources[name]),
        }
    return out


def host_context_envelope(text: str) -> bool:
    """Recognize exact host-owned markup that is not owner speech."""
    return bool(
        re.match(
            r"^<(?:command-(?:name|message)|local-command-(?:stdout|stderr|caveat)|"
            r"ide_(?:opened_file|selection)|task-notification)\b",
            text.lstrip(),
        )
    )


def portable_absolute_path(value: object) -> bool:
    """Recognize absolute paths in either native POSIX or Windows spelling."""
    return bool(
        isinstance(value, str)
        and value
        and (Path(value).is_absolute() or ntpath.isabs(value))
    )


def owner_command_frame(text: str) -> tuple[str, str] | None:
    """Decode only Claude's complete slash-command wrapper."""
    match = COMMAND_OWNER_FRAME_RE.fullmatch(normalize_crlf(text))
    if not match:
        return None
    return match.group("command"), match.group("arguments")


def owner_input_record_visible(record: dict) -> bool:
    """Return whether a root user record can carry direct owner input."""
    return bool(
        not record.get("isSidechain")
        and not record.get("isVirtual")
        and record.get("type") == "user"
        and not record.get("isMeta")
        and not record.get("isCompactSummary")
        and not record.get("isVisibleInTranscriptOnly")
        and not record.get("sourceToolAssistantUUID")
        and not record.get("sourceToolUseID")
        and not record.get("toolUseResult")
        and not any(block.get("type") == "tool_result" for block in blocks(record))
    )


def owner_input_channel(record: dict) -> str:
    """Return explicit owner provenance even when the input has no text."""
    if not owner_input_record_visible(record):
        return ""
    origin = (record.get("origin") or {}).get("kind")
    attachment = record.get("attachment") or {}
    if origin == "human":
        source = record.get("promptSource")
        return (
            "queued"
            if source == "queued"
            else "typed"
            if source == "typed"
            else "human_origin"
        )
    if (
        attachment.get("type") == "queued_command"
        and attachment.get("commandMode") == "prompt"
    ):
        return "queued_attachment"
    if (
        record.get("userType") == "external"
        and origin is None
        and record.get("promptSource") in {None, "typed", "queued"}
    ):
        return f"external_{record.get('promptSource') or 'unspecified'}"
    return ""


def direct_owner_input(record: dict) -> tuple[str, str]:
    """Return text and explicit provenance for one direct owner-input record."""
    channel = owner_input_channel(record)
    if not channel:
        return "", ""
    origin = (record.get("origin") or {}).get("kind")
    attachment = record.get("attachment") or {}
    said = ""
    decoded_command = False
    if origin == "human":
        said = text_of(record)
        command_frame = owner_command_frame(said)
        if command_frame is not None:
            command, arguments = command_frame
            said = arguments if arguments.strip() else command
            channel = "command_args"
            decoded_command = True
    elif (
        attachment.get("type") == "queued_command"
        and attachment.get("commandMode") == "prompt"
    ):
        for raw in (attachment.get("prompt"), attachment.get("command")):
            if isinstance(raw, list):
                raw = "\n".join(
                    block["text"]
                    for block in raw
                    if isinstance(block, dict)
                    and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                )
            if isinstance(raw, str) and raw.strip():
                said = raw
                break
    else:
        said = text_of(record)
    if not said.strip() or not decoded_command and host_context_envelope(said):
        return "", ""
    return said.strip(), channel


def direct_owner_nontext_activity(record: dict) -> bool:
    """Recognize an explicit visible owner turn carried only by non-text data."""
    if not owner_input_channel(record) or direct_owner_input(record)[0]:
        return False
    attachment = record.get("attachment") or {}
    queued_media = any(
        isinstance(value, list)
        and any(
            isinstance(block, dict) and block.get("type") != "text"
            for block in value
        )
        for key in ("prompt", "command")
        if (value := attachment.get(key)) is not None
    )
    message_media = any(block.get("type") != "text" for block in blocks(record))
    return queued_media or message_media


def queued_attachment_activity(record: dict) -> bool:
    """Recognize every substantive payload in a visible queued owner frame."""
    if not owner_input_record_visible(record):
        return False
    attachment = record.get("attachment") or {}
    if not (
        attachment.get("type") == "queued_command"
        and attachment.get("commandMode") == "prompt"
    ):
        return False
    for field in ("prompt", "command"):
        value = attachment.get(field)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and any(
            isinstance(block, dict)
            and (
                block.get("type") != "text"
                or isinstance(block.get("text"), str)
                and bool(block["text"].strip())
            )
            for block in value
        ):
            return True
    return False


def owner_answer_positions(records: list[dict]) -> set[tuple[int, int]]:
    """Return successful AskUserQuestion result positions in transcript order."""
    calls, results = claude_tool_occurrences(records)
    paired = claude_tool_results(records)
    asked = {
        tool_id
        for tool_id, occurrences in calls.items()
        if len(occurrences) == 1
        and occurrences[0][2].get("name") == "AskUserQuestion"
        and paired.get(tool_id, (False, ""))[0]
    }
    return {
        results[tool_id][0][:2]
        for tool_id in asked
        if len(results.get(tool_id, [])) == 1
    }


def owner_activity_record_indexes(records: list[dict]) -> set[int]:
    """Return record indexes with direct or answered owner input."""
    indexes = {record_index for record_index, _ in owner_answer_positions(records)}
    indexes.update(
        index
        for index, record in enumerate(records)
        if direct_owner_input(record)[0] or direct_owner_nontext_activity(record)
    )
    return indexes


def owner_turns(records: list[dict]) -> list[dict]:
    """Return owner input with the host provenance actually present."""
    answer_positions = owner_answer_positions(records)

    turns: list[dict] = []
    for record_index, record in enumerate(records):
        if record.get("isSidechain") or record.get("isVirtual"):
            continue
        for block_index, block in enumerate(blocks(record)):
            if (
                (record_index, block_index) not in answer_positions
                or block.get("type") != "tool_result"
                or block.get("is_error")
            ):
                continue
            answer = result_content_text(block.get("content"))
            if isinstance(answer, str) and answer.strip():
                turns.append(
                    {"at": record.get("timestamp", ""), "channel": "answered", "said": answer.strip()}
                )
        said, channel = direct_owner_input(record)
        if said:
            turns.append(
                {"at": record.get("timestamp", ""), "channel": channel, "said": said}
            )
        elif direct_owner_nontext_activity(record):
            turns.append(
                {
                    "at": record.get("timestamp", ""),
                    "channel": owner_input_channel(record),
                    "said": "[non-text owner input]",
                }
            )
    return turns


def assistant_text(record: dict) -> str:
    """Return one root assistant message from Claude or Codex JSONL."""
    if not model_visible_root(record):
        return ""
    if record.get("type") == "assistant":
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


def applicable_owner_turn_records(records: list[dict]) -> list[dict]:
    """Return only the record suffix belonging to the latest observed owner turn."""
    owner_activity = owner_activity_record_indexes(records)
    boundary = max(owner_activity) if owner_activity else -1
    return records[boundary + 1 :]


def substantive_visible_root_record(record: dict) -> bool:
    """Recognize model-visible root content without assigning owner provenance."""
    if not model_visible_root(record):
        return False
    if root_assistant_record(record):
        message = record.get("message")
        if isinstance(message, dict) and "stop_reason" in message:
            return True
        return any(
            block.get("type") != "text"
            or isinstance(block.get("text"), str)
            and bool(block["text"].strip())
            for block in blocks(record)
        )
    if record.get("type") != "user":
        return False
    if queued_attachment_activity(record):
        return True
    if any(
        block.get("type") != "text"
        or isinstance(block.get("text"), str)
        and bool(block["text"].strip())
        for block in blocks(record)
    ):
        return True
    return direct_owner_nontext_activity(record)


def record_has_later_root_activity(record: dict) -> bool:
    """Return whether a record is substantive root activity after a response."""
    if (
        record.get("isSidechain")
        or record.get("isVirtual")
        or record.get("isCompactSummary")
        or record.get("isVisibleInTranscriptOnly")
    ):
        return False
    if model_visible_skill_frame_record(record) or model_visible_meta_input_record(
        record
    ):
        return True
    if record.get("isMeta"):
        return False
    if substantive_visible_root_record(record):
        return True
    if any(block.get("type") in {"tool_use", "tool_result"} for block in blocks(record)):
        return True
    event_type = record.get("type")
    if event_type in {"thread.started", "turn.started", "turn.failed", "error"}:
        return True
    if event_type in {"item.started", "item.updated", "item.completed"}:
        return isinstance(record.get("item"), dict)
    return False


def terminal_root_response(records: list[dict]) -> tuple[str, str]:
    """Return the terminal root response for the latest observed owner turn."""
    applicable = applicable_owner_turn_records(records)
    responses = [
        (index, text)
        for index, record in enumerate(applicable)
        if (text := assistant_text(record)).strip()
    ]
    if not responses:
        return "", "no_applicable_assistant_text"
    response_index, response = responses[-1]
    response_record = applicable[response_index]
    applicable_start = len(records) - len(applicable)
    response_record_index = applicable_start + response_index
    if response_record.get("type") == "assistant":
        message = response_record.get("message")
        stop_reason = (
            message.get("stop_reason") if isinstance(message, dict) else None
        )
        if (
            isinstance(message, dict)
            and "stop_reason" in message
            and stop_reason is None
            or stop_reason in CLAUDE_NONTERMINAL_STOP_REASONS
        ):
            return "", "unverified_nonterminal_stop_reason"
        content = blocks(response_record)
        if any(block.get("type") == "tool_use" for block in content):
            return "", "unverified_unresolved_tool_call"
        text_positions = [
            index
            for index, block in enumerate(content)
            if block.get("type") == "text"
            and isinstance(block.get("text"), str)
            and block["text"].strip()
        ]
        if text_positions and any(
            index > max(text_positions)
            and (
                block.get("type") != "text"
                or isinstance(block.get("text"), str)
                and bool(block["text"].strip())
            )
            for index, block in enumerate(content)
        ):
            return "", "unverified_later_activity"
    if any(record_has_later_root_activity(record) for record in applicable[response_index + 1 :]):
        return "", "unverified_later_activity"
    if any(
        applicable_start <= record_index <= response_record_index
        for record_index in unpaired_tool_calls(records).values()
    ):
        return "", "unverified_unresolved_tool_call"
    turn_state = codex_turn_status(records)
    if turn_state not in {"completed", "not_observed"}:
        return "", f"unverified_{turn_state}"
    return response, "terminal_root_response"


def report_text(records: list[dict], _versions: list[str]) -> str:
    """Return only the terminal response for the latest observed owner turn."""
    response, status = terminal_root_response(records)
    return response if status == "terminal_root_response" else ""


def codex_thread_identity(records: list[dict]) -> tuple[str, str]:
    """Return one flat Codex thread identity, failing closed on multiple envelopes."""
    identities = [
        record["thread_id"]
        for record in records
        if model_visible_root(record)
        and record.get("type") == "thread.started"
        and isinstance(record.get("thread_id"), str)
        and record["thread_id"]
    ]
    if not identities:
        return "not_observed", ""
    if len(identities) != 1:
        return "ambiguous_sequence", ""
    return "single", identities[0]


def codex_turn_status(
    records: list[dict], item_ambiguities: set[str] | None = None
) -> str:
    """Return a concrete final state only for a well-formed Codex turn sequence."""
    thread_status, _thread_id = codex_thread_identity(records)
    if thread_status == "ambiguous_sequence":
        return "ambiguous_sequence"
    active = False
    observed_start = False
    last_outcome = "not_observed"
    ambiguous = bool(
        codex_item_identity_ambiguities(records)
        if item_ambiguities is None
        else item_ambiguities
    )
    has_lifecycle = any(
        model_visible_root(record)
        and record.get("type")
        in {"thread.started", "turn.started", "turn.completed", "turn.failed"}
        for record in records
    )
    thread_seen = False
    for record in records:
        if not model_visible_root(record):
            continue
        event_type = record.get("type")
        if event_type == "thread.started":
            ambiguous = ambiguous or observed_start or active or last_outcome != "not_observed"
            thread_seen = True
        elif event_type == "turn.started":
            observed_start = True
            ambiguous = ambiguous or active or (
                thread_status == "single" and not thread_seen
            )
            active = True
        elif event_type in {"turn.completed", "turn.failed"}:
            ambiguous = ambiguous or not active
            active = False
            last_outcome = (
                "completed" if event_type == "turn.completed" else "failed"
            )
        elif (
            has_lifecycle
            and event_type in {"item.started", "item.updated", "item.completed"}
            and not active
        ):
            ambiguous = True
    if ambiguous:
        return "ambiguous_sequence"
    if active:
        return "open_sequence"
    return last_outcome if observed_start else "not_observed"


def compaction_status(records: list[dict]) -> bool | str:
    """Report positive compaction evidence; absence is not a negative receipt."""
    root_records = [
        record
        for record in records
        if not record.get("isSidechain") and not record.get("isVirtual")
    ]
    if any(
        record.get("isCompactSummary")
        or record.get("type") == "compacted"
        or root_assistant_record(record)
        and isinstance(record.get("message"), dict)
        and record["message"].get("stop_reason") == "compaction"
        for record in root_records
    ):
        return True
    return "unknown"


def unpaired_tool_calls(records: list[dict]) -> dict[str, int]:
    """Return every root call lacking one uniquely ordered terminal event."""
    pending: dict[str, int] = {}
    claude_calls, claude_results = claude_tool_occurrences(records)
    lifecycle = codex_turn_memberships(records)
    has_lifecycle, memberships = lifecycle
    codex_starts, codex_terminals = codex_tool_occurrences(records, lifecycle)
    codex_ambiguities = codex_item_identity_ambiguities(
        records, (codex_starts, codex_terminals), lifecycle
    )
    codex_sequence = codex_turn_status(records, codex_ambiguities)
    uuid_counts = Counter(
        record["uuid"]
        for record in records
            if not record.get("isSidechain")
            and not record.get("isVirtual")
        and isinstance(record.get("uuid"), str)
        and record["uuid"]
    )
    unique_record_uuids = {
        record_uuid for record_uuid, count in uuid_counts.items() if count == 1
    }
    codex_start_positions = {
        (item_id, record_index)
        for item_id, occurrences in codex_starts.items()
        for record_index, _item in occurrences
    }
    for record_index, record in enumerate(records):
        if not model_visible_root(record):
            continue
        item = record.get("item")
        if isinstance(item, dict) and (
            (
                item.get("id") if isinstance(item.get("id"), str) else "",
                record_index,
            )
            in codex_start_positions
        ):
            item_id = item.get("id") if isinstance(item.get("id"), str) else ""
            starts = codex_starts.get(item_id, []) if item_id else []
            terminals = codex_terminals.get(item_id, []) if item_id else []
            terminal_item = terminals[0][1] if len(terminals) == 1 else {}
            stable_identity = codex_items_share_identity(item, terminal_item)
            paired = (
                len(starts) == 1
                and len(terminals) == 1
                and terminals[0][0] > record_index
                and codex_memberships_share(
                    has_lifecycle,
                    memberships,
                    record_index,
                    terminals[0][0],
                )
                and stable_identity
                and codex_terminal_outcome(terminals[0][2], terminal_item)
                != "ambiguous"
                and codex_sequence != "ambiguous_sequence"
            )
            if not paired:
                pending[f"codex:{item_id or '<missing>'}:{record_index}"] = record_index
        for block_index, block in enumerate(blocks(record)):
            if not root_assistant_record(record):
                continue
            if block.get("type") == "tool_use":
                tool_id = block.get("id") if isinstance(block.get("id"), str) else ""
                calls = claude_calls.get(tool_id, []) if tool_id else []
                results = claude_results.get(tool_id, []) if tool_id else []
                paired = (
                    len(calls) == 1
                    and len(results) == 1
                    and results[0][:2] > (record_index, block_index)
                    and claude_pair_lineage_valid(
                        records, calls[0], results[0], unique_record_uuids
                    )
                )
                if not paired:
                    key = f"claude:{tool_id or '<missing>'}:{record_index}:{block_index}"
                    pending[key] = record_index
    return pending


def unresolved_tool_calls(records: list[dict]) -> dict[str, int]:
    """Return only genuine root starts for which no terminal was recorded.

    Duplicate or missing IDs, duplicate terminals, invalid terminals, reversed
    order, and identity mismatches are ambiguous evidence. They remain visible
    through ``unpaired_tool_calls`` but must not be relabelled as a transcript
    that simply ended while one known action was open.
    """
    pending: dict[str, int] = {}
    claude_calls, claude_results = claude_tool_occurrences(records)
    for tool_id, calls in claude_calls.items():
        if len(calls) == 1 and not claude_results.get(tool_id):
            record_index, block_index, _block = calls[0]
            pending[f"claude:{tool_id}:{record_index}:{block_index}"] = record_index

    lifecycle = codex_turn_memberships(records)
    has_lifecycle, memberships = lifecycle
    codex_starts, codex_terminals = codex_tool_occurrences(records, lifecycle)
    codex_ambiguities = codex_item_identity_ambiguities(
        records, (codex_starts, codex_terminals), lifecycle
    )
    codex_sequence = codex_turn_status(records, codex_ambiguities)
    for item_id, starts in codex_starts.items():
        if (
            len(starts) == 1
            and not codex_terminals.get(item_id)
            and codex_start_valid(starts[0][1])
            and codex_membership_valid(
                has_lifecycle, memberships, starts[0][0]
            )
            and codex_sequence != "ambiguous_sequence"
        ):
            record_index, _item = starts[0]
            pending[f"codex:{item_id}:{record_index}"] = record_index
    return pending


def ended_mid_tool(records: list[dict]) -> bool:
    """True only when an unresolved call is the final observable activity."""
    pending = unresolved_tool_calls(records)
    if not pending:
        return False
    last_pending = max(pending.values())
    pending_blocks = [
        block_index
        for block_index, block in enumerate(blocks(records[last_pending]))
        if block.get("type") == "tool_use"
        and (
            f"claude:{block.get('id') if isinstance(block.get('id'), str) and block.get('id') else '<missing>'}:"
            f"{last_pending}:{block_index}"
        )
        in pending
    ]
    same_record_activity = bool(pending_blocks) and any(
        block_index > max(pending_blocks)
        and (
            block.get("type") != "text"
            or isinstance(block.get("text"), str)
            and bool(block["text"].strip())
        )
        for block_index, block in enumerate(blocks(records[last_pending]))
    )
    later_completion = same_record_activity or any(
        index > last_pending
        and (
            record.get("type") == "turn.completed"
            and model_visible_root(record)
            or record_has_later_root_activity(record)
            and not (
                record.get("type") == "item.completed"
                and isinstance(record.get("item"), dict)
                and record["item"].get("type") != "web_search"
                and codex_start_valid(record["item"])
            )
        )
        for index, record in enumerate(records)
    )
    return not later_completion


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
        if not model_visible_root(record):
            continue
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


def nested_digest_inventory(path: Path) -> dict[str, object]:
    """Snapshot the complete host-defined nested transcript universe."""
    directory = path.with_suffix("") / "subagents"
    try:
        directory_status = directory.lstat()
    except FileNotFoundError:
        return {"status": "missing"}
    except OSError:
        return {"status": "unreadable"}
    if stat.S_ISLNK(directory_status.st_mode) or getattr(
        directory_status, "st_reparse_tag", 0
    ):
        return {"status": "unreadable"}
    if not stat.S_ISDIR(directory_status.st_mode):
        return {"status": "nonregular"}
    selected: set[Path] = set()
    owner_errors: dict[Path, set[Path]] = {}
    snapshots: dict[Path, tuple[int, int, int, int, int] | None] = {}
    scan_nested_transcripts(
        directory, path, selected, owner_errors, snapshots
    )
    return {
        "status": "directory",
        "directory_snapshot": regular_snapshot(directory_status),
        "selected": tuple(sorted(selected)),
        "errors": frozenset(owner_errors.get(path, set())),
        "snapshots": snapshots,
    }


def nested_digest_evidence(
    path: Path, inventory: dict[str, object] | None = None
) -> tuple[list[dict], int, bool]:
    """Return nested marker records and uncertainty without owning the chat."""
    inventory = inventory or nested_digest_inventory(path)
    status = inventory["status"]
    if status == "missing":
        return [], 0, False
    if status == "unreadable":
        return [], 1, True
    if status == "nonregular":
        return [], 0, False
    selected = inventory["selected"]
    snapshots = inventory["snapshots"]
    errors = inventory["errors"]
    if not isinstance(selected, tuple) or not isinstance(snapshots, dict):
        return [], 1, True
    broken = len(errors) if isinstance(errors, frozenset) else 1
    relevant = bool(broken)
    found: list[dict] = []
    for nested in selected:
        expected = snapshots.get(nested)
        if expected is None:
            broken += 1
            relevant = True
            continue
        try:
            scanned, snapshot = scan_marker_member(nested, expected)
        except OSError:
            broken += 1
            relevant = True
            continue
        try:
            records, member_broken, broken_markers = (
                scanned
                if scanned is not None
                else parse_expected_transcript(nested, snapshot)
            )
        except OSError:
            broken += 1
            relevant = True
            continue
        broken += member_broken
        marker_records = [
            record for record in records if record_contains_marker(record)
        ]
        if marker_records or broken_markers or member_broken:
            relevant = True
        if scanned is not None or marker_records or broken_markers:
            found.extend({**record, "isSidechain": True} for record in records)
    return found, broken, relevant


def _digest(path: Path, report_chars: int) -> dict:
    if report_chars < 0:
        raise SystemExit("--report-chars must be zero or greater")
    safe_path = escaped_render_value(path)
    root_status = transcript_file_status(path)
    nested_inventory = (
        nested_digest_inventory(path) if configured_owner_transcript(path) else None
    )
    nested_records, nested_broken, nested_relevant = (
        nested_digest_evidence(path, nested_inventory)
        if nested_inventory is not None
        else ([], 0, False)
    )
    if root_status == "nonregular" and not nested_relevant:
        raise SystemExit(f"{safe_path} is not a regular transcript")
    root_unavailable = root_status in {
        "missing",
        "dangling",
        "unreadable",
        "nonregular",
    }
    records: list[dict] = []
    broken = 1 if root_status in {"dangling", "unreadable", "nonregular"} else 0
    if root_status == "regular":
        try:
            records, broken = iter_records(path)
        except OSError:
            records = []
            broken = 1
            root_unavailable = True
        else:
            root_unavailable = not records and bool(broken)
    if (
        nested_inventory is not None
        and nested_digest_inventory(path) != nested_inventory
    ):
        nested_records = []
        nested_broken = max(1, nested_broken)
        nested_relevant = True
    root_record_count = len(records)
    if records:
        broken += nested_broken
    elif root_unavailable:
        if root_status == "missing" and not nested_relevant:
            raise SystemExit(f"{safe_path} holds no readable records")
        broken = max(1, broken) + nested_broken
        if nested_relevant:
            records.extend(nested_records)
    elif nested_relevant:
        root_unavailable = True
        broken = 1 + nested_broken
        records.extend(nested_records)
    elif root_status == "missing":
        raise SystemExit(f"{safe_path} holds no readable records")
    if not records and not broken:
        raise SystemExit(f"{safe_path} holds no readable records")
    thread_identity_status, thread_id = codex_thread_identity(records)
    if thread_identity_status == "ambiguous_sequence":
        raise SystemExit(
            f"{safe_path} contains multiple Codex thread envelopes"
        )

    tools: Counter[str] = Counter()
    command_results: Counter[str] = Counter()
    models: Counter[str] = Counter()
    usage: Counter[str] = Counter()
    delegations: list[dict] = []
    write_actions: list[dict] = []
    stamps: list[str] = []
    injections = 0
    cwd = branch = host = ""
    claude_results = claude_tool_results(records)
    injection_observations = skill_injection_observations(records)
    injected = [
        observation
        for observation in injection_observations.values()
        if observation.get("status") == "body_observed"
    ]
    injections = len(injected)
    observed_version_values = contract_identity_values(
        records, injection_observations
    )

    for record in records:
        if not model_visible_root(record):
            continue
        cwd = record.get("cwd") or cwd
        branch = record.get("gitBranch") or branch
        host = record.get("version") or host
        if record.get("timestamp"):
            stamps.append(record["timestamp"])
        if record.get("type") == "turn.completed":
            for key in CODEX_USAGE_FIELDS:
                value = (record.get("usage") or {}).get(key)
                if value is not None:
                    usage[key] += value
        if not root_assistant_record(record):
            continue
        message = record.get("message") or {}
        if message.get("model"):
            models[message["model"]] += 1
        for key, value in (message.get("usage") or {}).items():
            if isinstance(value, int) and not isinstance(value, bool):
                usage[key] += value
        for block in blocks(record):
            if block.get("type") != "tool_use":
                continue
            name = block.get("name") or "?"
            tools[name] += 1
            data = block.get("input")
            data = data if isinstance(data, dict) else {}
            tool_id = block.get("id")
            result = claude_results.get(tool_id) if isinstance(tool_id, str) else None
            role = data.get("subagent_type")
            task = data.get("description")
            if (
                name == "Agent"
                and result
                and result[0]
                and isinstance(role, str)
                and bool(role)
                and isinstance(task, str)
                and bool(task)
            ):
                delegations.append(
                    {
                        "role": role,
                        "task": task,
                    }
                )
            if name in STRUCTURED_WRITE_TOOLS and result and result[0]:
                path_field = "notebook_path" if name == "NotebookEdit" else "file_path"
                target = data.get(path_field)
                if isinstance(target, str) and target and "\x00" not in target:
                    write_actions.append(
                        {
                            "at": record.get("timestamp", ""),
                            "tool": name,
                            "path": target,
                        }
                    )
    for event in terminal_tool_events(records):
        if event["host"] != "codex":
            continue
        item = event["input"]
        item_type = event["tool"]
        ambiguous_inputs = event.get("ambiguous_inputs")
        if isinstance(ambiguous_inputs, list):
            for occurrence in ambiguous_inputs:
                tools[
                    str(occurrence.get("type") or "?")
                    if isinstance(occurrence, dict)
                    else "?"
                ] += 1
        else:
            tools[str(item_type)] += 1
        if item_type == "file_change" and event["succeeded"]:
            for change in item.get("changes") or []:
                if isinstance(change, dict):
                    write_actions.append(
                        {
                            "at": event["at"],
                            "tool": "file_change",
                            "path": change.get("path") or "unknown",
                        }
                    )
        elif (
            item_type == "collab_tool_call"
            and event["succeeded"]
            and item.get("tool") == "spawn_agent"
            and isinstance(item.get("prompt"), str)
            and bool(item["prompt"])
        ):
            delegations.append(
                {
                    "role": "spawn_agent",
                    "task": item["prompt"],
                }
            )
        elif item_type == "command_execution" and event["outcome"] in {
            "succeeded",
            "failed",
        }:
            exit_code = item.get("exit_code")
            result = (
                f"{event['outcome']}:{exit_code}"
                if isinstance(exit_code, int) and not isinstance(exit_code, bool)
                else event["outcome"]
            )
            command_results[result] += 1
    observed_skills = [] if broken else detect_skills(records)
    known_versions = [
        version for version in observed_version_values if version != "unknown"
    ]
    version_identity = contract_identity_status(observed_version_values)
    body_identity = (
        contract_body_identity_status(
            records, injection_observations, known_versions[0]
        )
        if version_identity == "single" and known_versions
        else "unverified_contract_identity"
    )
    if broken:
        injections = "unverified"
        delegations = []
        write_actions = []
        command_results = Counter()
    if broken:
        incomplete_names = observed_reference_names(records) | {
            name
            for version in known_versions
            for name in version_reference_names(version)
        }
        reference_evidence = {
            name: {
                "verdict": "unverified_unparseable_transcript",
                "basis": "contract_sequence_incomplete",
                "matching_line_values": "unavailable",
                "artifact_source": "not_evaluated",
                "actions": ["not_evaluated"],
                "mismatched_path_versions": [],
                "mismatched_path_sources": [],
            }
            for name in sorted(incomplete_names)
        }
    elif version_identity == "single" and known_versions and body_identity == "single":
        roots = governing_contract_roots(
            records, injection_observations, known_versions[0]
        )
        reference_evidence = detect_references(
            path, records, known_versions[0], roots
        )
    else:
        mixed_reference_names = observed_reference_names(records) | {
            name
            for version in known_versions
            for name in version_reference_names(version)
        }
        unresolved = (
            "unverified_contract_identity"
            if version_identity != "single" or not known_versions
            else "unverified_contract_body"
        )
        reference_evidence = {
            name: {
                "verdict": unresolved,
                "basis": version_identity if unresolved.endswith("identity") else body_identity,
                "matching_line_values": "unavailable",
                "artifact_source": (
                    "contract_identity_unsettled"
                    if unresolved.endswith("identity")
                    else "contract_body_unsettled"
                ),
                "actions": ["not_evaluated"],
                "mismatched_path_versions": [],
                "mismatched_path_sources": [],
            }
            for name in sorted(mixed_reference_names)
        }
    turn_state = (
        "unverified_incomplete_transcript" if broken else codex_turn_status(records)
    )
    terminal_response, response_status = terminal_root_response(records)
    if broken:
        response_status = "unverified_incomplete_transcript"
    selected = terminal_response or final_assistant_text(
        applicable_owner_turn_records(records)
    )
    if not selected:
        selected = "(no assistant text found)"
    omitted_report_chars = max(0, len(selected) - report_chars) if report_chars else 0
    return {
        "session": path.stem if broken else thread_id or path.stem,
        "project": (
            "unverified_incomplete_transcript"
            if broken
            else Path(cwd).name or "unknown"
        ),
        "branch": (
            "unverified_incomplete_transcript" if broken else branch or "unknown"
        ),
        "host": (
            "unverified_incomplete_transcript" if broken else host or "unknown"
        ),
        "plugin_version_values_observed": (
            ["unverified_incomplete_transcript"]
            if broken
            else observed_version_values
        ),
        "window": (
            ["unverified_incomplete_transcript"] * 2
            if broken
            else [
                stamps[0] if stamps else "unknown",
                stamps[-1] if stamps else "unknown",
            ]
        ),
        "records": root_record_count,
        "unparseable_lines": broken,
        "skill_body_injections": injections,
        "models": (
            "unverified_incomplete_transcript" if broken else dict(models)
        ),
        "owner_turns": (
            "unverified_incomplete_transcript"
            if broken
            else owner_turns(records)
        ),
        "skills": observed_skills,
        "references": reference_evidence,
        "tools": (
            "unverified_incomplete_transcript"
            if broken
            else dict(tools.most_common())
        ),
        "command_results": dict(command_results),
        "successful_structured_delegations": delegations,
        "successful_structured_write_actions": write_actions,
        "checkout_metadata_observations": (
            "unverified_incomplete_transcript"
            if broken
            else identity_transitions(records)
        ),
        "confounders": {
            "compaction_observed": compaction_status(records),
            "trailing_unresolved_tool_call": (
                "unknown" if broken else ended_mid_tool(records)
            ),
            "unpaired_tool_call_count": (
                "unknown" if broken else len(unpaired_tool_calls(records))
            ),
            "turn_sequence": turn_state,
            "thread_identity": (
                "unverified_incomplete_transcript"
                if broken
                else thread_identity_status
            ),
            "plugin_version_identity": (
                "unverified_incomplete_transcript"
                if broken
                else version_identity
            ),
            "contract_body_identity": (
                "unverified_incomplete_transcript" if broken else body_identity
            ),
            "contract_sequence": (
                "unverified_incomplete_transcript" if broken else "parsed"
            ),
        },
        "usage": (
            "unverified_incomplete_transcript" if broken else dict(usage)
        ),
        "report": {
            "selection_status": response_status,
            "omitted_prefix_chars": omitted_report_chars,
            "text": selected[-report_chars:] if report_chars else selected,
        },
    }


def digest(path: Path, report_chars: int, home: Path | None = None) -> dict:
    """Digest one transcript with cache attribution scoped to its selected home."""
    selected_home = None
    if home is not None:
        configured = configured_path_alias(home, lexical_absolute_path(path))
        if configured is not None:
            if not configured_parent_directories_safe(home, configured):
                raise SystemExit(
                    "configured transcript crosses a linked or unavailable project scope"
                )
            selected_home = canonical_home_path(home)
            path = configured
    if selected_home is None:
        return _digest(path, report_chars)
    token = AUDIT_HOME.set(selected_home)
    try:
        return _digest(path, report_chars)
    finally:
        AUDIT_HOME.reset(token)


def owner_transcript_path(projects: Path, path: Path) -> Path:
    """Map one Claude root or nested subagent log to its owner-chat JSONL."""
    try:
        relative = path.relative_to(projects)
    except ValueError:
        return path
    if len(relative.parts) <= 2:
        return path
    if len(relative.parts) < 4 or relative.parts[2] != "subagents":
        return path
    return projects / relative.parts[0] / f"{relative.parts[1]}.jsonl"


def transcript_file_status(path: Path) -> str:
    """Classify a transcript path without opening non-regular filesystem nodes."""
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "unreadable"
    if stat.S_ISLNK(mode):
        try:
            path.stat()
        except FileNotFoundError:
            return "dangling"
        except OSError:
            return "unreadable"
        return "nonregular"
    return "regular" if stat.S_ISREG(mode) else "nonregular"


def open_configured_directory_descriptor(path: Path) -> int | None:
    """Open a configured transcript directory without following any component."""
    selected_home = AUDIT_HOME.get()
    if selected_home is None:
        return None
    configured = configured_path_alias(selected_home, lexical_absolute_path(path))
    if configured is None:
        return None
    projects = canonical_home_path(selected_home) / "projects"
    try:
        relative = configured.relative_to(projects)
    except ValueError:
        raise OSError(f"{path} is outside the configured transcript store") from None
    if not relative.parts or not cache_descriptor_walk_supported():
        raise OSError(f"{path} cannot be opened through a safe directory walk")
    directory = open_cache_root_descriptor(projects)
    try:
        for component in relative.parts:
            child = open_cache_child_directory(directory, component)
            os.close(directory)
            directory = child
        return directory
    except BaseException:
        os.close(directory)
        raise


def open_regular_binary(path: Path):
    """Open one transcript without following a swapped final link or blocking."""
    selected_home = AUDIT_HOME.get()
    if selected_home is not None:
        configured = configured_path_alias(
            selected_home, lexical_absolute_path(path)
        )
        if configured is not None:
            projects = canonical_home_path(selected_home) / "projects"
            try:
                relative = configured.relative_to(projects)
            except ValueError:
                raise OSError(f"{path} is outside the configured transcript store") from None
            if len(relative.parts) < 2 or not cache_descriptor_walk_supported():
                raise OSError(f"{path} cannot be opened through a safe directory walk")
            directory: int | None = None
            descriptor: int | None = None
            try:
                directory = open_cache_root_descriptor(projects)
                for component in relative.parts[:-1]:
                    child = open_cache_child_directory(directory, component)
                    os.close(directory)
                    directory = child
                descriptor = os.open(
                    relative.parts[-1], cache_file_flags(), dir_fd=directory
                )
                opened_status = os.fstat(descriptor)
                current_status = os.stat(
                    relative.parts[-1],
                    dir_fd=directory,
                    follow_symlinks=False,
                )
                if not (
                    stat.S_ISREG(opened_status.st_mode)
                    and stat.S_ISREG(current_status.st_mode)
                    and not getattr(opened_status, "st_reparse_tag", 0)
                    and os.path.samestat(opened_status, current_status)
                ):
                    raise OSError(f"{path} is not a stable regular transcript")
                handle = os.fdopen(descriptor, "rb")
                descriptor = None
                return handle
            finally:
                if descriptor is not None:
                    os.close(descriptor)
                if directory is not None:
                    os.close(directory)
    flags = os.O_RDONLY
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened_status = os.fstat(descriptor)
        current_status = os.lstat(path)
        if not (
            stat.S_ISREG(opened_status.st_mode)
            and stat.S_ISREG(current_status.st_mode)
            and os.path.samestat(opened_status, current_status)
        ):
            raise OSError(f"{path} is not a regular transcript")
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def scan_nested_transcripts(
    directory: Path,
    owner: Path,
    selected: set[Path],
    errors: dict[Path, set[Path]],
    snapshots: dict[Path, tuple[int, int, int, int, int] | None] | None = None,
) -> None:
    """Walk one host-defined subagents tree through held directory handles."""
    if not cache_descriptor_walk_supported():
        errors.setdefault(owner, set()).add(directory)
        return
    try:
        descriptor = open_configured_directory_descriptor(directory)
        if descriptor is None:
            descriptor = open_cache_root_descriptor(directory)
    except OSError:
        errors.setdefault(owner, set()).add(directory)
        return
    scan_nested_transcript_descriptors(
        descriptor, directory, owner, selected, errors, snapshots
    )


def scan_nested_transcript_descriptors(
    descriptor: int,
    directory: Path,
    owner: Path,
    selected: set[Path],
    errors: dict[Path, set[Path]],
    snapshots: dict[Path, tuple[int, int, int, int, int] | None] | None = None,
) -> None:
    """Consume one held subagents directory without reopening descendants by path."""
    pending = [(descriptor, directory)]
    while pending:
        current_descriptor, current = pending.pop()
        try:
            try:
                with os.scandir(current_descriptor) as scanner:
                    entries = list(scanner)
            except OSError:
                errors.setdefault(owner, set()).add(current)
                continue
            for entry in entries:
                path = current / entry.name
                try:
                    observed = entry.stat(follow_symlinks=False)
                except OSError:
                    errors.setdefault(owner, set()).add(path)
                    continue
                if stat.S_ISLNK(observed.st_mode) or getattr(
                    observed, "st_reparse_tag", 0
                ):
                    errors.setdefault(owner, set()).add(path)
                    continue
                if stat.S_ISDIR(observed.st_mode):
                    try:
                        child = open_cache_child_directory(
                            current_descriptor, entry.name
                        )
                    except OSError:
                        errors.setdefault(owner, set()).add(path)
                        continue
                    if not os.path.samestat(observed, os.fstat(child)):
                        os.close(child)
                        errors.setdefault(owner, set()).add(path)
                        continue
                    pending.append((child, path))
                elif entry.name.endswith(".jsonl"):
                    if stat.S_ISREG(observed.st_mode):
                        selected.add(path)
                        if snapshots is not None:
                            snapshots[path] = regular_snapshot(observed)
                    else:
                        errors.setdefault(owner, set()).add(path)
        finally:
            os.close(current_descriptor)


def open_observed_child_directory(
    parent: int, name: str, observed: os.stat_result
) -> int:
    """Bind a scanned child name to the same held directory entry."""
    child = open_cache_child_directory(parent, name)
    if not os.path.samestat(observed, os.fstat(child)):
        os.close(child)
        raise OSError("directory entry identity changed during discovery")
    return child


def discovery_transcript_inventory(
    projects: Path,
    *,
    expected: bool = False,
) -> tuple[
    list[Path],
    dict[Path, set[Path]],
    dict[Path, tuple[int, int, int, int, int] | None],
]:
    """Return root/nested paths discovered through one held directory tree."""
    selected: set[Path] = set()
    errors: dict[Path, set[Path]] = {}
    snapshots: dict[Path, tuple[int, int, int, int, int] | None] = {}
    if not cache_descriptor_walk_supported():
        try:
            projects.lstat()
        except FileNotFoundError:
            if expected:
                raise SystemExit(
                    "transcript discovery incomplete: configured projects scope disappeared"
                ) from None
            return [], errors, snapshots
        except OSError:
            pass
        raise SystemExit(
            "transcript discovery incomplete: safe directory traversal is unavailable"
        )
    try:
        projects_descriptor = open_cache_root_descriptor(projects)
    except FileNotFoundError:
        if expected:
            raise SystemExit(
                "transcript discovery incomplete: configured projects scope disappeared"
            ) from None
        return [], errors, snapshots
    except OSError:
        raise SystemExit(
            "transcript discovery incomplete: configured projects scope is unreadable"
        ) from None
    try:
        try:
            with os.scandir(projects_descriptor) as scanner:
                projects_entries = list(scanner)
        except OSError:
            raise SystemExit(
                "transcript discovery incomplete: configured projects scope is unreadable"
            ) from None
        for project_entry in projects_entries:
            try:
                project_status = project_entry.stat(follow_symlinks=False)
            except OSError:
                raise SystemExit(
                    "transcript discovery incomplete: a project entry is unreadable"
                ) from None
            if not cache_status_is_plain_directory(project_status):
                continue
            project = projects / project_entry.name
            try:
                project_descriptor = open_observed_child_directory(
                    projects_descriptor, project_entry.name, project_status
                )
            except OSError:
                raise SystemExit(
                    "transcript discovery incomplete: a project directory is unreadable"
                ) from None
            try:
                try:
                    with os.scandir(project_descriptor) as scanner:
                        entries = list(scanner)
                except OSError:
                    raise SystemExit(
                        "transcript discovery incomplete: a project directory is unreadable"
                    ) from None
                for entry in entries:
                    path = project / entry.name
                    try:
                        entry_status = entry.stat(follow_symlinks=False)
                    except OSError:
                        raise SystemExit(
                            "transcript discovery incomplete: a project entry is unreadable"
                        ) from None
                    if entry.name.endswith(".jsonl"):
                        if stat.S_ISREG(entry_status.st_mode):
                            selected.add(path)
                            snapshots[path] = regular_snapshot(entry_status)
                        elif stat.S_ISLNK(entry_status.st_mode):
                            try:
                                os.stat(
                                    entry.name,
                                    dir_fd=project_descriptor,
                                    follow_symlinks=True,
                                )
                            except FileNotFoundError:
                                selected.add(path)
                                snapshots[path] = None
                            except OSError:
                                pass
                        continue
                    if not cache_status_is_plain_directory(entry_status):
                        continue
                    owner = project / f"{entry.name}.jsonl"
                    try:
                        session_descriptor = open_observed_child_directory(
                            project_descriptor, entry.name, entry_status
                        )
                    except OSError:
                        errors.setdefault(owner, set()).add(path)
                        continue
                    try:
                        try:
                            with os.scandir(session_descriptor) as scanner:
                                session_entries = list(scanner)
                        except OSError:
                            errors.setdefault(owner, set()).add(path)
                            continue
                        for session_entry in session_entries:
                            if session_entry.name != "subagents":
                                continue
                            subagents_path = path / session_entry.name
                            try:
                                subagents_status = session_entry.stat(
                                    follow_symlinks=False
                                )
                            except OSError:
                                errors.setdefault(owner, set()).add(subagents_path)
                                continue
                            if cache_status_is_plain_directory(subagents_status):
                                try:
                                    subagents_descriptor = open_observed_child_directory(
                                        session_descriptor,
                                        session_entry.name,
                                        subagents_status,
                                    )
                                except OSError:
                                    errors.setdefault(owner, set()).add(
                                        subagents_path
                                    )
                                    continue
                                scan_nested_transcript_descriptors(
                                    subagents_descriptor,
                                    subagents_path,
                                    owner,
                                    selected,
                                    errors,
                                    snapshots,
                                )
                            elif stat.S_ISLNK(subagents_status.st_mode) or getattr(
                                subagents_status, "st_reparse_tag", 0
                            ):
                                errors.setdefault(owner, set()).add(subagents_path)
                    finally:
                        os.close(session_descriptor)
            finally:
                os.close(project_descriptor)
    finally:
        os.close(projects_descriptor)
    return sorted(selected), errors, snapshots


def discovery_transcript_paths(projects: Path) -> list[Path]:
    """Return safe roots and host-defined nested subagent logs."""
    return discovery_transcript_inventory(projects)[0]


def discovery_session_tokens(root_paths: set[Path]) -> dict[Path, tuple[str, str]]:
    """Choose globally resolvable display and durable receipt identifiers."""
    stem_counts = Counter(path.stem for path in root_paths)
    prefix_counts = Counter(path.stem[:8] for path in root_paths)
    tokens: dict[Path, tuple[str, str]] = {}
    for path in root_paths:
        session = path.stem
        prefix = session[:8]
        unique_short = bool(
            SHORT_SESSION_RE.fullmatch(prefix) and prefix_counts[prefix] == 1
        )
        unique_full = stem_counts[session] == 1
        receipt = prefix if unique_short else session if unique_full else ""
        display = receipt or str(path)
        tokens[path] = display, receipt
    return tokens


def canonical_record_hash(record: dict) -> str:
    """Hash one semantic JSON record without retaining its private text."""
    encoded = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def candidate_evidence_fingerprint(
    session: str,
    root_path: Path,
    parsed_members: dict[Path, tuple[list[dict], int, int]],
    marker_records_with_scope: list[tuple[dict, bool]],
    marker_cwds: list[str],
    observed_cwds: list[str],
    root_status: str,
    marker_scope: str,
    nested_evidence_count: int,
    version_values: list[str],
    root_injections: dict[str, dict],
) -> str:
    """Bind every coverable aggregate fact without rendering private evidence."""
    try:
        root_records = parsed_members.get(root_path, ([], 0, 0))[0]
        nested_members: list[list[str]] = []
        for member_path, (records, _broken, _broken_markers) in parsed_members.items():
            if member_path == root_path:
                continue
            marker_hashes = [
                canonical_record_hash(record)
                for record in records
                if record_contains_marker(record)
            ]
            if marker_hashes:
                nested_members.append(marker_hashes)
        nested_members.sort(
            key=lambda value: json.dumps(value, separators=(",", ":"))
        )
        marker_entries = [
            {
                "record": canonical_record_hash(record),
                "role": "sidechain" if sidechain else "root",
                "timestamp": (
                    record.get("timestamp")
                    if isinstance(record.get("timestamp"), str)
                    else None
                ),
                "local_date": (
                    local_calendar_date(record["timestamp"])
                    if isinstance(record.get("timestamp"), str)
                    else None
                ),
                "cwd": (
                    record.get("cwd")
                    if isinstance(record.get("cwd"), str) and record["cwd"]
                    else None
                ),
            }
            for record, sidechain in marker_records_with_scope
        ]
        marker_entries.sort(
            key=lambda value: json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        injection_evidence = sorted(
            (
                {
                    key: observation[key]
                    for key in (
                        "status",
                        "name",
                        "source",
                        "version",
                        "artifact_source",
                        "attribution",
                        "body_fingerprint",
                    )
                    if key in observation
                }
                for observation in root_injections.values()
            ),
            key=lambda value: json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ),
        )
        known_versions = [value for value in version_values if value != "unknown"]
        version_status = contract_identity_status(version_values)
        body_status = (
            contract_body_identity_status(
                root_records, root_injections, known_versions[0]
            )
            if version_status == "single" and len(set(known_versions)) == 1
            else "unverified_contract_identity"
        )
        envelope = {
            "schema": "skiphow-dogfood-candidate-evidence-v1",
            "session": session,
            "root_records": [canonical_record_hash(record) for record in root_records],
            "nested_marker_members": nested_members,
            "markers": marker_entries,
            "marker_cwds": marker_cwds,
            "observed_root_cwds": observed_cwds,
            "root_marker_records": sum(
                not sidechain for _record, sidechain in marker_records_with_scope
            ),
            "sidechain_marker_records": sum(
                sidechain for _record, sidechain in marker_records_with_scope
            ),
            "root_status": root_status,
            "marker_scope": marker_scope,
            "nested_evidence_members": nested_evidence_count,
            "versions": sorted(set(version_values)),
            "contract_identity_status": version_status,
            "contract_body_status": body_status,
            "root_injections": injection_evidence,
        }
        canonical = json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (KeyError, TypeError, ValueError, RecursionError, UnicodeError):
        return "unverified"
    digest = hashlib.sha256()
    digest.update(b"skiphow-dogfood-candidate-evidence-v1\0")
    digest.update(canonical)
    return f"sha256-v1:{digest.hexdigest()}"


def _discover(
    home: Path,
    since: str | None,
    on: str | None = None,
) -> list[dict]:
    projects = home / "projects"
    rows: list[dict] = []
    try:
        projects_mode = projects.lstat().st_mode
    except FileNotFoundError:
        return rows
    except OSError:
        raise SystemExit(
            "transcript discovery incomplete: configured projects scope is unreadable"
        ) from None
    if not stat.S_ISDIR(projects_mode):
        raise SystemExit(
            "transcript discovery incomplete: configured projects scope is not a directory"
        )
    transcript_paths, traversal_errors, transcript_snapshots = (
        discovery_transcript_inventory(projects, expected=True)
    )
    grouped: dict[Path, list[Path]] = {}
    for transcript_path in transcript_paths:
        grouped.setdefault(
            owner_transcript_path(projects, transcript_path), []
        ).append(transcript_path)
    for owner in traversal_errors:
        grouped.setdefault(owner, [])
    root_paths = set(grouped)
    tokens = discovery_session_tokens(root_paths)

    for path, member_paths in sorted(grouped.items()):
        parsed_members: dict[Path, tuple[list[dict], int, int]] = {}
        scanned_snapshots: dict[Path, tuple[int, int, int, int, int]] = {}
        scan_error_paths: set[Path] = set(traversal_errors.get(path, set()))
        for member_path in member_paths:
            expected_snapshot = transcript_snapshots.get(member_path)
            if expected_snapshot is None:
                scan_error_paths.add(member_path)
                continue
            try:
                scanned, snapshot = scan_marker_member(
                    member_path, expected_snapshot
                )
            except OSError:
                scan_error_paths.add(member_path)
                continue
            scanned_snapshots[member_path] = snapshot
            if scanned is None:
                continue
            parsed_members[member_path] = scanned

        marker_evidence = any(
            any(record_contains_marker(record) for record in records)
            or broken_marker_lines
            for records, _broken, broken_marker_lines in parsed_members.values()
        )
        if not marker_evidence and not scan_error_paths:
            continue

        # A candidate aggregates unreadable nested evidence too. Parse
        # markerless nested logs only after the owner group is known relevant;
        # the retained snapshot makes a replacement fail closed.
        for member_path, snapshot in scanned_snapshots.items():
            if member_path == path or member_path in parsed_members:
                continue
            try:
                parsed_members[member_path] = parse_expected_transcript(
                    member_path, snapshot
                )
            except OSError:
                scan_error_paths.add(member_path)

        root_status = transcript_file_status(path)
        root_status = "readable" if root_status == "regular" else root_status
        if path in member_paths:
            if path in scan_error_paths:
                if root_status != "dangling":
                    root_status = "unreadable"
            elif path not in parsed_members:
                root_status = "readable"
                try:
                    if path in scanned_snapshots:
                        parsed_members[path] = parse_expected_transcript(
                            path, scanned_snapshots[path]
                        )
                    else:
                        parsed_members[path] = iter_records_with_marker_errors(path)
                except OSError:
                    scan_error_paths.add(path)
                    root_status = "unreadable"
            else:
                root_status = "readable"

        root_records_all = parsed_members.get(path, ([], 0, 0))[0]
        if root_status == "readable" and not root_records_all:
            # Reaching this point means marker/uncertainty evidence came from
            # malformed root bytes or nested logs, not a readable owner record.
            root_status = (
                "unreadable"
                if parsed_members.get(path, ([], 0, 0))[1]
                else "empty"
            )
        root_records = [
            record for record in root_records_all if not record.get("isSidechain")
        ]
        marker_records_with_scope: list[tuple[dict, bool]] = []
        # A candidate row names the owner chat. Nested logs only establish
        # candidate/date/scope uncertainty; their contracts belong to other
        # agents and must not be presented as the owner's digest identity.
        root_injections = skill_injection_observations(root_records)
        contributing_version_values = contract_identity_values(
            root_records, root_injections
        )
        contributing_versions = set(contributing_version_values)
        broken = len(scan_error_paths)
        broken_marker_lines = 0
        for member_path, (records, member_broken, member_broken_markers) in (
            parsed_members.items()
        ):
            member_markers = [
                record for record in records if record_contains_marker(record)
            ]
            is_nested = member_path != path
            marker_records_with_scope.extend(
                (record, is_nested or bool(record.get("isSidechain")))
                for record in member_markers
            )
            broken += member_broken
            broken_marker_lines += member_broken_markers

        marker_records = [record for record, _sidechain in marker_records_with_scope]
        root_marker_records = [
            record
            for record, sidechain in marker_records_with_scope
            if not sidechain
        ]
        sidechain_marker_records = [
            record for record, sidechain in marker_records_with_scope if sidechain
        ]
        marker_points = sorted(
            (
                parsed,
                record["timestamp"],
                parsed.date().isoformat(),
            )
            for record in marker_records
            if isinstance(record.get("timestamp"), str)
            and (parsed := parsed_timestamp(record["timestamp"])) is not None
        )
        marker_stamps = [timestamp for _parsed, timestamp, _local in marker_points]
        marker_dates = [local for _parsed, _timestamp, local in marker_points]
        undated_marker_records = len(marker_records) - len(marker_points)
        marker_cwds = sorted(
            {
                record["cwd"]
                for record in marker_records
                if isinstance(record.get("cwd"), str) and record["cwd"]
            }
        )
        observed_cwds = list(
            dict.fromkeys(
                record["cwd"]
                for record in root_records
                if isinstance(record.get("cwd"), str) and record["cwd"]
            )
        )
        cwd = (observed_cwds or [""])[-1]
        timestamp_points = sorted(
            (parsed, record["timestamp"])
            for record in root_records
            if isinstance(record.get("timestamp"), str)
            and (parsed := parsed_timestamp(record["timestamp"])) is not None
        )
        started = timestamp_points[0][1] if timestamp_points else ""
        uncertain_marker_evidence = bool(
            broken_marker_lines
            or scan_error_paths
            or root_status in {"missing", "dangling", "nonregular"}
        )
        if (
            since
            and not uncertain_marker_evidence
            and marker_dates
            and marker_dates[-1] < since
            and not undated_marker_records
        ):
            continue
        if (
            on
            and not uncertain_marker_evidence
            and marker_dates
            and on not in marker_dates
            and not undated_marker_records
        ):
            continue
        marker_scope = (
            "unverified_scan_error"
            if scan_error_paths
            else "unverified_incomplete_scope"
            if broken_marker_lines or root_status != "readable"
            else "mixed"
            if root_marker_records and sidechain_marker_records
            else "root"
            if root_marker_records
            else "sidechain_only"
            if sidechain_marker_records
            else "unverified_missing_marker_scope"
        )
        try:
            with open_regular_binary(path) as size_handle:
                size_status = os.fstat(size_handle.fileno())
                if regular_snapshot(size_status) != transcript_snapshots.get(path):
                    raise OSError(f"{path} changed after transcript inventory")
                megabytes: float | str = round(
                    size_status.st_size / 1e6, 1
                )
        except OSError:
            megabytes = "unknown"
        display_session, receipt_session = tokens[path]
        nested_evidence_paths = {
            member_path
            for member_path, (
                member_records,
                member_broken,
                member_broken_markers,
            ) in parsed_members.items()
            if member_path != path
            and (
                any(record_contains_marker(record) for record in member_records)
                or member_broken
                or member_broken_markers
            )
        } | {member_path for member_path in scan_error_paths if member_path != path}
        nested_evidence_count = len(nested_evidence_paths)
        coverable_evidence = not (
            broken
            or broken_marker_lines
            or scan_error_paths
            or root_status != "readable"
        )
        evidence_fingerprint = (
            candidate_evidence_fingerprint(
                path.stem,
                path,
                parsed_members,
                marker_records_with_scope,
                marker_cwds,
                observed_cwds,
                root_status,
                marker_scope,
                nested_evidence_count,
                contributing_version_values,
                root_injections,
            )
            if coverable_evidence
            else "unverified"
        )
        rows.append(
            {
                "session": path.stem,
                "display_session": display_session,
                "receipt_session": receipt_session,
                "path": str(path),
                "project": Path(cwd).name or "unknown",
                "candidate_marker_cwds": marker_cwds,
                "observed_cwds": observed_cwds,
                "candidate_marker_scope": marker_scope,
                "root_marker_records": len(root_marker_records),
                "sidechain_marker_records": len(sidechain_marker_records),
                "started": started or "unknown",
                "candidate_marker_window": [
                    marker_stamps[0] if marker_stamps else "unknown",
                    marker_stamps[-1] if marker_stamps else "unknown",
                ],
                "candidate_marker_local_dates": [
                    marker_dates[0] if marker_dates else "unknown",
                    marker_dates[-1] if marker_dates else "unknown",
                ],
                "candidate_marker_date_status": (
                    "unverified_scan_error"
                    if scan_error_paths
                    else "unverified_incomplete_transcript"
                    if uncertain_marker_evidence
                    else "unverified_undated_marker_records"
                    if marker_dates and undated_marker_records
                    else "observed"
                    if marker_dates
                    else "unverified_missing_or_invalid_timestamp"
                ),
                "undated_marker_records": (
                    undated_marker_records
                    if not uncertain_marker_evidence
                    else None
                ),
                "records": len(root_records_all),
                "unreadable_lines": broken,
                "unreadable_marker_lines": broken_marker_lines,
                "megabytes": megabytes,
                "root_transcript_status": root_status,
                "candidate_transcript_scope": (
                    "synthetic_parent_from_nested"
                    if root_status in {"missing", "dangling"}
                    and nested_evidence_count
                    else f"root_only_{root_status}"
                    if root_status in {"missing", "dangling"}
                    else "root_with_nested_subagent_evidence"
                    if nested_evidence_count or any(
                        member_path != path for member_path in scan_error_paths
                    )
                    else "root_only"
                ),
                "nested_subagent_logs_with_evidence": nested_evidence_count,
                "evidence_fingerprint": evidence_fingerprint,
                "versions": (
                    ["unknown"]
                    if broken or root_status != "readable"
                    else sorted(contributing_versions) or ["unknown"]
                ),
            }
        )
    final_paths, final_errors, final_snapshots = discovery_transcript_inventory(
        projects, expected=True
    )
    if (
        final_paths != transcript_paths
        or final_errors != traversal_errors
        or final_snapshots != transcript_snapshots
    ):
        raise SystemExit(
            "transcript discovery incomplete: transcript universe changed"
        )
    return sorted(
        rows,
        key=lambda item: (
            item["candidate_marker_local_dates"][1],
            item["candidate_marker_window"][1],
            item["started"],
        ),
    )


def discover(
    home: Path,
    since: str | None,
    on: str | None = None,
) -> list[dict]:
    """Discover candidates with cache attribution scoped to the selected home."""
    selected_home = canonical_home_path(home)
    token = AUDIT_HOME.set(selected_home)
    try:
        return _discover(selected_home, since, on)
    finally:
        AUDIT_HOME.reset(token)


def lexical_absolute_path(path: Path) -> Path:
    """Normalize a local path lexically without following filesystem links."""
    return Path(os.path.abspath(os.fspath(path)))


def canonical_home_path(home: Path) -> Path:
    """Resolve only the configured home alias, never a transcript node."""
    return lexical_absolute_path(Path(os.path.realpath(lexical_absolute_path(home))))


def configured_path_alias(home: Path, candidate: Path) -> Path | None:
    """Map a home/projects alias to its canonical store without resolving a log."""
    alias_projects = lexical_absolute_path(home) / "projects"
    canonical_projects = canonical_home_path(home) / "projects"
    candidate = lexical_absolute_path(candidate)
    for projects in (canonical_projects, alias_projects):
        if path_is_within(candidate, projects):
            return canonical_projects / candidate.relative_to(projects)
    for ancestor in candidate.parents:
        if ancestor.name != "projects":
            continue
        try:
            canonical_ancestor = lexical_absolute_path(
                Path(os.path.realpath(ancestor))
            )
        except OSError:
            continue
        if canonical_ancestor == canonical_projects:
            return canonical_projects / candidate.relative_to(ancestor)
    return None


def configured_parent_directories_safe(home: Path, path: Path) -> bool:
    """Require the configured projects and project nodes to be real directories."""
    configured = configured_path_alias(home, lexical_absolute_path(path))
    if configured is None:
        return False
    projects = canonical_home_path(home) / "projects"
    try:
        relative = configured.relative_to(projects)
    except ValueError:
        return False
    if len(relative.parts) < 2:
        return False
    for directory in (projects, projects / relative.parts[0]):
        try:
            mode = directory.lstat().st_mode
        except OSError:
            return False
        if not stat.S_ISDIR(mode):
            return False
    return True


def configured_owner_transcript(path: Path) -> bool:
    """Return whether the selected path is one configured Claude owner chat."""
    home = AUDIT_HOME.get()
    if home is None:
        return False
    configured = configured_path_alias(home, lexical_absolute_path(path))
    if configured is None:
        return False
    projects = canonical_home_path(home) / "projects"
    try:
        relative = configured.relative_to(projects)
    except ValueError:
        return False
    return len(relative.parts) == 2 and configured.suffix == ".jsonl"


def path_is_within(path: Path, directory: Path) -> bool:
    """Return whether one normalized local path is below another."""
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def resolve(home: Path, target: str) -> Path:
    raw_candidate = Path(target)
    alias_home = lexical_absolute_path(home)
    home = canonical_home_path(alias_home)
    projects = lexical_absolute_path(home / "projects")
    typed_absolute = lexical_absolute_path(raw_candidate)
    configured_absolute = configured_path_alias(alias_home, typed_absolute)
    raw_is_configured = configured_absolute is not None
    raw_absolute = configured_absolute or typed_absolute
    path_shaped = bool(
        raw_candidate.is_absolute()
        or len(raw_candidate.parts) > 1
        or raw_candidate.suffix == ".jsonl"
    )

    # An explicit flat transcript outside the configured Claude store is a
    # complete target by itself. Do not enumerate unrelated private projects
    # before accepting it.
    if (
        (raw_candidate.is_absolute() or path_shaped)
        and not raw_is_configured
        and transcript_file_status(raw_absolute) == "regular"
    ):
        return raw_absolute

    # An exact configured root (or a configured nested path that maps to it)
    # is likewise self-contained.  Do not enumerate unrelated private
    # projects merely to accept a readable transcript the caller named.
    if raw_is_configured:
        configured_owner = owner_transcript_path(projects, raw_absolute)
        if (
            configured_parent_directories_safe(alias_home, configured_owner)
            and transcript_file_status(configured_owner) == "regular"
        ):
            return configured_owner

    transcript_paths, traversal_errors, _snapshots = (
        discovery_transcript_inventory(projects)
    )
    roots = {
        owner_transcript_path(projects, lexical_absolute_path(path))
        for path in transcript_paths
    } | {lexical_absolute_path(path) for path in traversal_errors}
    candidates: list[Path] = []
    if raw_is_configured:
        candidates.append(raw_absolute)
    if not raw_candidate.is_absolute():
        if raw_candidate.parts and raw_candidate.parts[0] == "projects":
            candidates.append(lexical_absolute_path(home / raw_candidate))
        elif len(raw_candidate.parts) > 1:
            candidates.append(lexical_absolute_path(projects / raw_candidate))
    for candidate in candidates:
        if not path_is_within(candidate, projects):
            continue
        configured_owner = owner_transcript_path(projects, candidate)
        if configured_owner != candidate and configured_owner in roots:
            return configured_owner
        if candidate in roots:
            return candidate
    if not path_shaped:
        all_matches = sorted(path for path in roots if path.name.startswith(target))
        exact = [path for path in all_matches if path.stem == target]
        matches = exact or all_matches
        if len(matches) > 1:
            ids = ", ".join(
                escaped_render_value(path.stem) for path in matches[:8]
            )
            safe_target = escaped_render_value(target)
            raise SystemExit(f"ambiguous transcript prefix {safe_target!r}: {ids}")
        if matches:
            return matches[0]
    if not raw_is_configured and transcript_file_status(raw_absolute) == "regular":
        return raw_absolute
    safe_target = escaped_render_value(target)
    raise SystemExit(f"no transcript found for {safe_target!r}")


def strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate JSON keys instead of silently keeping the last value."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def invalid_json_constant(_value: str) -> object:
    """Reject Python's non-standard NaN and infinity JSON extensions."""
    raise ValueError("non-standard JSON number")


def coverage_sidecar_entries(
    path: Path,
    expected_sidecar: tuple[int, int, int, int, int] | None = None,
    expected_report: tuple[int, int, int, int, int] | None = None,
) -> list[tuple[str, int, frozenset[str], str | None]]:
    """Validate one adjacent, versioned coverage sidecar exactly."""
    name = COVERAGE_SIDECAR_RE.fullmatch(path.name)
    if not name or date.fromisoformat(name.group("date")).isoformat() != name.group(
        "date"
    ):
        raise ValueError("invalid coverage sidecar name")
    report = path.with_name(
        path.name[: -len(".receipts.json")] + ".md"
    )
    report_status = report.lstat()
    if not stat.S_ISREG(report_status.st_mode):
        raise ValueError("coverage sidecar has no adjacent report")
    if (
        expected_report is not None
        and regular_snapshot(report_status) != expected_report
    ):
        raise ValueError("coverage report changed after inventory")
    with open_regular_binary(path) as handle:
        before = os.fstat(handle.fileno())
        if (
            expected_sidecar is not None
            and regular_snapshot(before) != expected_sidecar
        ):
            raise ValueError("coverage sidecar changed after inventory")
        raw = handle.read()
        if not opened_transcript_stable(path, handle, before):
            raise ValueError("coverage sidecar changed while reading")
    document = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=strict_json_object,
        parse_constant=invalid_json_constant,
        parse_float=invalid_json_constant,
    )
    if not isinstance(document, dict) or set(document) != {
        "schema",
        "source",
        "receipts",
    }:
        raise ValueError("invalid coverage sidecar envelope")
    if (
        document["schema"] != COVERAGE_SCHEMA
        or document["source"] != COVERAGE_SOURCE
        or not isinstance(document["receipts"], list)
    ):
        raise ValueError("invalid coverage sidecar envelope")
    entries: list[tuple[str, int, frozenset[str], str | None]] = []
    for entry in document["receipts"]:
        if not isinstance(entry, dict) or set(entry) != {
            "session",
            "records",
            "plugin_versions",
            "evidence_fingerprint",
        }:
            raise ValueError("invalid coverage receipt")
        session = entry["session"]
        records = entry["records"]
        versions = entry["plugin_versions"]
        fingerprint = entry["evidence_fingerprint"]
        if not isinstance(session, str) or not COVERAGE_SESSION_RE.fullmatch(session):
            raise ValueError("invalid coverage receipt session")
        if (
            not isinstance(records, int)
            or isinstance(records, bool)
            or records < 0
        ):
            raise ValueError("invalid coverage receipt record count")
        if (
            not isinstance(versions, list)
            or not versions
            or any(not isinstance(version, str) for version in versions)
            or len(set(versions)) != len(versions)
            or any(
                version != "unknown"
                and not COVERAGE_VERSION_RE.fullmatch(version)
                for version in versions
            )
        ):
            raise ValueError("invalid coverage receipt plugin identity")
        if not (
            fingerprint is None
            or fingerprint == "unverified"
            or isinstance(fingerprint, str)
            and COVERAGE_FINGERPRINT_RE.fullmatch(fingerprint)
        ):
            raise ValueError("invalid coverage receipt fingerprint")
        entries.append((session, records, frozenset(versions), fingerprint))
    return entries


def coverage_receipts_snapshot(
    research: Path,
) -> tuple[
    set[tuple[str, int, frozenset[str], str | None]],
    object,
]:
    """Load sidecars plus a stable identity snapshot of their whole scope."""
    seen: set[tuple[str, int, frozenset[str], str | None]] = set()
    base_directories: list[int] = []
    base_snapshots: list[tuple[int, int, int, int, int]] = []

    def close_base_directories() -> None:
        while base_directories:
            os.close(base_directories.pop())

    if research.name != "research" or research.parent.name != "docs":
        raise SystemExit("invalid coverage sidecar")
    try:
        research.lstat()
    except FileNotFoundError:
        return seen, ("missing",)
    except OSError:
        raise SystemExit("invalid coverage sidecar") from None

    try:
        root = research.parent.parent
        base_directories.append(open_cache_root_descriptor(root))
        base_snapshots.append(regular_snapshot(os.fstat(base_directories[-1])))
        for component in ("docs", "research"):
            base_directories.append(
                open_cache_child_directory(base_directories[-1], component)
            )
            base_snapshots.append(
                regular_snapshot(os.fstat(base_directories[-1]))
            )
    except OSError:
        close_base_directories()
        raise SystemExit("invalid coverage sidecar") from None

    def inventory() -> tuple[
        tuple[tuple[str, tuple[int, int, int, int, int]], ...],
        tuple[
            tuple[
                Path,
                tuple[int, int, int, int, int],
                tuple[int, int, int, int, int],
            ],
            ...,
        ],
    ]:
        def walk_error(error: OSError) -> None:
            raise error

        found_directories: list[
            tuple[str, tuple[int, int, int, int, int]]
        ] = []
        found: list[
            tuple[
                Path,
                tuple[int, int, int, int, int],
                tuple[int, int, int, int, int],
            ]
        ] = []
        for directory, child_directories, filenames in os.walk(
            research, topdown=True, onerror=walk_error, followlinks=False
        ):
            parent = Path(directory)
            relative_parent = parent.relative_to(research)
            directory_status = parent.lstat()
            if not cache_status_is_plain_directory(directory_status):
                raise ValueError("coverage directory is not plain")
            found_directories.append(
                (relative_parent.as_posix(), regular_snapshot(directory_status))
            )
            child_directories.sort()
            for child_name in child_directories:
                child_status = (parent / child_name).lstat()
                if not cache_status_is_plain_directory(child_status):
                    raise ValueError("coverage directory is not plain")
                if COVERAGE_SIDECAR_RE.fullmatch(child_name):
                    raise ValueError("coverage sidecar is not regular")
            for filename in sorted(filenames):
                name = COVERAGE_SIDECAR_RE.fullmatch(filename)
                if not name:
                    continue
                sidecar_date = name.group("date")
                if (
                    len(relative_parent.parts) != 1
                    or relative_parent.name != sidecar_date
                    or date.fromisoformat(sidecar_date).isoformat() != sidecar_date
                ):
                    raise ValueError("coverage sidecar is outside its dated directory")
                sidecar = Path(directory) / filename
                sidecar_status = sidecar.lstat()
                report = sidecar.with_name(
                    filename[: -len(".receipts.json")] + ".md"
                )
                report_status = report.lstat()
                if not (
                    stat.S_ISREG(sidecar_status.st_mode)
                    and stat.S_ISREG(report_status.st_mode)
                ):
                    raise ValueError("coverage sidecar pair is not regular")
                found.append(
                    (
                        sidecar,
                        regular_snapshot(sidecar_status),
                        regular_snapshot(report_status),
                    )
                )
        return tuple(found_directories), tuple(found)

    def base_stable() -> bool:
        try:
            root_status = os.lstat(research.parent.parent)
            opened_root = os.fstat(base_directories[0])
            if not (
                cache_status_is_plain_directory(root_status)
                and os.path.samestat(opened_root, root_status)
                and regular_snapshot(opened_root) == base_snapshots[0]
                and regular_snapshot(root_status) == base_snapshots[0]
            ):
                return False
            for index, component in enumerate(("docs", "research")):
                current = os.stat(
                    component,
                    dir_fd=base_directories[index],
                    follow_symlinks=False,
                )
                opened = os.fstat(base_directories[index + 1])
                if not (
                    cache_status_is_plain_directory(current)
                    and os.path.samestat(opened, current)
                    and regular_snapshot(opened) == base_snapshots[index + 1]
                    and regular_snapshot(current) == base_snapshots[index + 1]
                ):
                    return False
            return True
        except OSError:
            return False

    try:
        before = inventory()
        for sidecar, sidecar_status, report_status in before[1]:
            seen.update(
                coverage_sidecar_entries(
                    sidecar, sidecar_status, report_status
                )
            )
        if inventory() != before or not base_stable():
            raise ValueError("coverage sidecar inventory changed")
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        OverflowError,
        json.JSONDecodeError,
    ):
        raise SystemExit("invalid coverage sidecar") from None
    finally:
        close_base_directories()
    return seen, (tuple(base_snapshots), before)


def coverage_receipts(
    research: Path,
) -> set[tuple[str, int, frozenset[str], str | None]]:
    """Load only strict field-audit sidecars and fail closed on any malformed one."""
    return coverage_receipts_snapshot(research)[0]


def coverage(home: Path) -> str:
    """Derive coverage from strict sidecars adjacent to their audit reports."""
    research = repository_root() / "docs/research"
    seen, coverage_snapshot = coverage_receipts_snapshot(research)
    rows = discover(home, None)
    confirmed_seen, confirmed_snapshot = coverage_receipts_snapshot(research)
    if confirmed_seen != seen or confirmed_snapshot != coverage_snapshot:
        raise SystemExit("invalid coverage sidecar")
    session_ids = Counter(row["session"] for row in rows)
    prefixes = Counter(row["session"][:8] for row in rows)
    lines = [
        "Coverage from strict docs/research sidecars "
        "(session id, root record count, plugin identity, and evidence fingerprint):"
    ]
    for row in rows:
        session_id = row["session"]
        prefix = session_id[:8]
        receipt_session = row.get("receipt_session")
        if receipt_session is None:
            receipt_session = (
                prefix
                if SHORT_SESSION_RE.fullmatch(prefix) and prefixes[prefix] == 1
                else session_id
                if session_ids[session_id] == 1
                else ""
            )
        identity = frozenset(row["versions"])
        full_receipts = {
            (count, versions, evidence)
            for receipt_session, count, versions, evidence in seen
            if receipt_session == session_id
        }
        short_receipts = {
            (count, versions, evidence)
            for receipt_session, count, versions, evidence in seen
            if SHORT_SESSION_RE.fullmatch(receipt_session)
            and receipt_session == prefix
        }
        fingerprint = row.get("evidence_fingerprint", "unverified")
        snapshot = (row["records"], identity, fingerprint)
        fingerprint_coverable = bool(
            isinstance(fingerprint, str)
            and COVERAGE_FINGERPRINT_RE.fullmatch(fingerprint)
        )
        if not receipt_session or session_ids[session_id] > 1:
            state = "AMBIGUOUS_SESSION"
        elif row.get("root_transcript_status") in {
            "missing",
            "dangling",
            "empty",
            "nonregular",
            "unreadable",
        }:
            state = "UNVERIFIED_UNREADABLE"
        elif row["unreadable_lines"]:
            state = "UNVERIFIED_UNREADABLE"
        elif fingerprint_coverable and snapshot in full_receipts:
            state = "covered"
        elif short_receipts and receipt_session != prefix:
            state = "AMBIGUOUS_PREFIX"
        elif (
            fingerprint_coverable
            and receipt_session == prefix
            and snapshot in short_receipts
        ):
            state = "covered"
        elif full_receipts or short_receipts:
            state = "STALE"
        else:
            state = "UNAUDITED"
        lines.append(
            f"  {escaped_render_value(session_id)}  "
            f"{escaped_render_value(row['candidate_marker_local_dates'][1])}  "
            f"{escaped_render_value(row['project'])} {state}"
        )
    return "\n".join(lines) if rows else "No sessions found."


def render_list(rows: list[dict]) -> str:
    if not rows:
        return "No sessions found."
    width = max(len(escaped_render_value(r["project"])) for r in rows)
    prefixes = Counter(row["session"][:8] for row in rows)
    session_counts = Counter(row["session"] for row in rows)
    lines = [f"{len(rows)} candidate session(s)."]
    for row in rows:
        session = row["session"]
        displayed_session = row.get("display_session") or (
            session[:8]
            if SHORT_SESSION_RE.fullmatch(session[:8])
            and prefixes[session[:8]] == 1
            else session
            if session_counts[session] == 1
            else row.get("path", session)
        )
        first_date, last_date = row["candidate_marker_local_dates"]
        marker_dates = first_date if first_date == last_date else f"{first_date}..{last_date}"
        undated = row.get("undated_marker_records")
        undated_text = "unknown" if undated is None else str(undated)
        megabytes = row["megabytes"]
        size = f"{megabytes}MB" if isinstance(megabytes, (int, float)) else str(megabytes)
        records = (
            "UNVERIFIED"
            if row.get("root_transcript_status") in {
                "missing",
                "dangling",
                "empty",
                "nonregular",
                "unreadable",
            }
            or not row["records"]
            and row["unreadable_lines"]
            else row["records"]
        )
        rendered_session = escaped_render_value(displayed_session)
        rendered_project = escaped_render_value(row["project"])
        lines.append(
            f"  {rendered_session}  marker local-date "
            f"{escaped_render_value(marker_dates)} "
            f"({escaped_render_value(row['candidate_marker_date_status'])}; "
            f"{undated_text} undated marker records)  "
            f"scope {escaped_render_value(row.get('candidate_marker_scope', 'unknown'))}  "
            f"logs {escaped_render_value(row.get('candidate_transcript_scope', 'root_only'))}  "
            f"{rendered_project:<{width}}  "
            f"plugin {escaped_render_value(','.join(row['versions']))}  "
            f"{escaped_render_value(size)}  {records} rec  "
            f"{row['unreadable_lines']} unreadable"
        )
    return "\n".join(lines)


def escaped_render_value(value: object) -> str:
    """Keep one untrusted value on one renderer line."""
    encoded = json.dumps(str(value), ensure_ascii=True)
    return encoded[1:-1].replace("\x7f", r"\u007f")


def safe_multiline_render(value: object) -> str:
    """Preserve intentional LF layout while neutralizing terminal controls."""
    rendered: list[str] = []
    for character in str(value):
        codepoint = ord(character)
        if character == "\n":
            rendered.append(character)
        elif (
            codepoint < 0x20
            or 0x7F <= codepoint <= 0x9F
            or unicodedata.category(character) == "Cf"
            or character in {
                "\u2028",
                "\u2029",
            }
        ):
            rendered.append(
                f"\\u{codepoint:04x}"
                if codepoint <= 0xFFFF
                else f"\\U{codepoint:08x}"
            )
        else:
            rendered.append(character)
    return "".join(rendered)


def render_digest(data: dict) -> str:
    incomplete = bool(data["unparseable_lines"])
    rendered_records = "UNVERIFIED" if incomplete else data["records"]
    out = [
        f"session {escaped_render_value(data['session'])}  "
        f"project {escaped_render_value(data['project'])}  "
        f"branch {escaped_render_value(data['branch'])}",
        "host "
        f"{escaped_render_value(data['host'])}  plugin values observed "
        f"{escaped_render_value(','.join(data['plugin_version_values_observed']))}  "
        f"exact skill bodies observed {data['skill_body_injections']}",
        f"window {escaped_render_value(data['window'][0])} .. "
        f"{escaped_render_value(data['window'][1])}  {rendered_records} records  "
        f"{data['unparseable_lines']} unreadable",
        f"models {escaped_render_value(data['models'])}  "
        f"confounders {escaped_render_value(data['confounders'])}",
        "",
        "OWNER-VISIBLE USER TURNS",
    ]
    owner_turn_values = data["owner_turns"] if isinstance(data["owner_turns"], list) else []
    for turn in owner_turn_values:
        out.append(
            f"  [{escaped_render_value(turn['at'][:19])} "
            f"{escaped_render_value(turn['channel'])}] "
            f"{escaped_render_value(' '.join(turn['said'].split()))}"
        )
    if incomplete:
        out.append("  UNVERIFIED: incomplete transcript")
    elif not owner_turn_values:
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
        out.append(
            "  UNVERIFIED: incomplete transcript; absence cannot be established"
            if incomplete
            else "  none observed"
        )
    out += ["", "REFERENCES"]
    for name, info in data["references"].items():
        out.append(
            f"  {name:<14} {info['verdict']:<24} basis {info['basis']:<26} "
            f"matching-lines {info['matching_line_values']:<10} "
            f"artifact {info['artifact_source']:<26} "
            f"actions {','.join(info['actions'])}"
            + (
                f" mismatched-path-versions {','.join(info['mismatched_path_versions'])}"
                if info["mismatched_path_versions"]
                else ""
            )
            + (
                f" mismatched-path-sources {','.join(info['mismatched_path_sources'])}"
                if info["mismatched_path_sources"]
                else ""
            )
        )
    if not data["references"]:
        out.append(
            "  UNVERIFIED: incomplete transcript; reference absence cannot be established"
            if incomplete
            else "  none named by exact contract or structured path evidence"
        )
    out += [
        "",
        f"NORMALIZED TOOL EVENTS       {escaped_render_value(data['tools'])}",
        "OBSERVED COMMAND TERMINALS   "
        f"{'UNVERIFIED' if incomplete else data['command_results']}",
        "OBSERVED SUCCESSFUL STRUCTURED DELEGATIONS "
        f"({'UNVERIFIED' if incomplete else len(data['successful_structured_delegations'])})",
    ]
    for delegation in data["successful_structured_delegations"]:
        out.append(
            f"  role {escaped_render_value(delegation['role'])}  "
            f"task {escaped_render_value(delegation['task'])}"
        )
    if not data["successful_structured_delegations"]:
        out.append(
            "  UNVERIFIED: incomplete transcript; absence cannot be established"
            if incomplete
            else "  none observed"
        )
    out += [
        "",
        "OBSERVED SUCCESSFUL STRUCTURED WRITE ACTIONS "
        f"({'UNVERIFIED' if incomplete else len(data['successful_structured_write_actions'])})",
    ]
    for write in data["successful_structured_write_actions"]:
        out.append(
            f"  [{escaped_render_value(write['at'][:19])}] "
            f"{escaped_render_value(write['tool'])} "
            f"{escaped_render_value(write['path'])}"
        )
    if not data["successful_structured_write_actions"]:
        out.append(
            "  UNVERIFIED: incomplete transcript; absence cannot be established"
            if incomplete
            else "  none observed; shell command semantics are not inferred"
        )
    out += [
        "",
        "OBSERVED CHECKOUT METADATA "
        f"({'UNVERIFIED' if incomplete else len(data['checkout_metadata_observations'])})",
    ]
    checkout_values = (
        data["checkout_metadata_observations"]
        if isinstance(data["checkout_metadata_observations"], list)
        else []
    )
    for change in checkout_values:
        out.append(
            f"  [{escaped_render_value(change['at'][:19])}] "
            f"cwd {escaped_render_value(change['cwd'])}  "
            f"branch {escaped_render_value(change['branch'])}"
        )
    if incomplete:
        out.append("  UNVERIFIED: incomplete transcript")
    elif not checkout_values:
        out.append("  none observed")
    report = data["report"]
    out += [
        "",
        f"REPORT selection status         {report['selection_status']}",
    ]
    if report["omitted_prefix_chars"]:
        out.append(
            f"       final text omitted prefix {report['omitted_prefix_chars']} chars; "
            "use bounded grep before ruling on the omitted text"
        )
    out += [
        "",
        (
            "SELECTED TERMINAL ASSISTANT TEXT"
            if report["selection_status"] == "terminal_root_response"
            else "UNVERIFIED FALLBACK ASSISTANT TEXT"
        ),
        safe_multiline_render(report["text"] or "(no assistant text found)"),
    ]
    return "\n".join(out)


def main() -> None:
    class PrivateArgumentParser(argparse.ArgumentParser):
        def error(self, message: str) -> None:
            if "argument pattern:" in message:
                message = "argument pattern: invalid regular expression"
            for option in ("--max", "--chars", "--report-chars"):
                if f"argument {option}:" in message:
                    message = f"argument {option}: invalid bounded integer"
                    break
            if message.startswith("unrecognized arguments:"):
                message = "unrecognized arguments"
            elif "invalid choice:" in message:
                message = "invalid command choice"
            else:
                message = escaped_render_value(message)
            super().error(message)

    def nonnegative(value: str) -> int:
        try:
            parsed = int(value)
        except (ValueError, OverflowError):
            raise argparse.ArgumentTypeError("invalid bounded integer") from None
        if parsed < 0:
            raise argparse.ArgumentTypeError("must be zero or greater")
        return parsed

    def iso_date(value: str) -> str:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as error:
            raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from error

    def positive(value: str) -> int:
        try:
            parsed = int(value)
        except (ValueError, OverflowError):
            raise argparse.ArgumentTypeError("invalid bounded integer") from None
        if parsed <= 0:
            raise argparse.ArgumentTypeError("must be greater than zero")
        return parsed

    def regular_expression(value: str) -> re.Pattern[str]:
        try:
            return re.compile(value)
        except (re.error, RecursionError, OverflowError):
            raise argparse.ArgumentTypeError("invalid regular expression") from None

    parser = PrivateArgumentParser(prog=Path(sys.argv[0]).name, description=__doc__)
    parser.add_argument("--home", type=Path, default=claude_home())
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", help="find sessions containing SkipHow evidence")
    date_filter = listing.add_mutually_exclusive_group()
    date_filter.add_argument(
        "--since",
        type=iso_date,
        help="local ISO date; skip candidates whose last marker is earlier",
    )
    date_filter.add_argument(
        "--on",
        type=iso_date,
        help=(
            "local ISO date; keep exact-day markers plus candidates whose "
            "undated or unreadable markers prevent safe exclusion"
        ),
    )
    listing.add_argument("--json", action="store_true")

    one = sub.add_parser("digest", help="slice one session into reviewable evidence")
    one.add_argument("target", help="session id, id prefix, or transcript path")
    one.add_argument(
        "--report-chars", type=nonnegative, default=0, help="0 keeps the full final text"
    )
    one.add_argument("--json", action="store_true")

    finder = sub.add_parser("grep", help="search the raw transcript of one session")
    finder.add_argument("target")
    finder.add_argument("pattern", type=regular_expression)
    finder.add_argument("--max", type=positive, default=20)
    finder.add_argument("--chars", type=nonnegative, default=240)

    sub.add_parser("coverage", help="which sessions the receipts already cover")

    args = parser.parse_args()
    if args.command == "list":
        rows = discover(args.home, args.since, args.on)
        print(
            json.dumps(rows, indent=2)
            if args.json
            else render_list(rows)
        )
    elif args.command == "digest":
        data = digest(resolve(args.home, args.target), args.report_chars, args.home)
        print(json.dumps(data, indent=2, ensure_ascii=True) if args.json else render_digest(data))
    elif args.command == "grep":
        path = resolve(args.home, args.target)
        if transcript_file_status(path) != "regular":
            raise SystemExit("raw transcript is unavailable for bounded grep")
        buffered: list[str] = []
        stopped = False
        token = AUDIT_HOME.set(canonical_home_path(args.home))
        try:
            with open_regular_binary(path) as handle:
                before = os.fstat(handle.fileno())
                for number, raw_line in enumerate(handle, 1):
                    line = raw_line.decode("utf-8", errors="replace")
                    match = args.pattern.search(line)
                    if not match:
                        continue
                    if args.chars == 0:
                        buffered.append(f"L{number}: [content omitted]")
                    else:
                        start = max(0, match.start() - args.chars // 2)
                        excerpt = escaped_render_value(
                            line[start : start + args.chars]
                        )[: args.chars]
                        buffered.append(
                            f"L{number}: ...{excerpt}..."
                        )
                    if len(buffered) >= args.max:
                        stopped = True
                        break
                if not opened_transcript_stable(path, handle, before):
                    raise OSError(f"{path} changed during bounded grep")
        except OSError:
            raise SystemExit("raw transcript is unavailable for bounded grep") from None
        finally:
            AUDIT_HOME.reset(token)
        for rendered in buffered:
            print(rendered)
        if stopped:
            print(f"(stopped at {args.max} matches)")
        if not buffered:
            print("no matches")
    else:
        print(coverage(args.home))


if __name__ == "__main__":
    main()
