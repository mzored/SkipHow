#!/usr/bin/env python3
"""Locate and slice sessions containing observable SkipHow evidence.

The audit reads evidence, not multi-megabyte transcripts. This helper finds
candidate sessions, slices one into a digest, and greps back into the raw bytes
on demand. It reports observable host events and exact model-visible text;
causal and conformance rulings belong to the reader.

    sessions.py list [--since YYYY-MM-DD | --on YYYY-MM-DD] [--all]
    sessions.py digest <session> [--report-chars N] [--json]
    sessions.py grep <session> <pattern> [--max N]
    sessions.py coverage
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
from collections import Counter
from contextvars import ContextVar
from datetime import date, datetime
from pathlib import Path

_RAW_PATH_SEPARATOR = rb"(?:/|\\{1,2})"
_RAW_SKILL_BOUNDARY = rb"(?![A-Za-z0-9_.-])"
MARKER_RES = (
    re.compile(rb'"attributionPlugin"[ \t\r\n]*:[ \t\r\n]*"skiphow"'),
    re.compile(rb"(?<![A-Za-z0-9_.-])skiphow:skiphow(?![A-Za-z0-9_.-])"),
    re.compile(
        rb"plugins"
        + _RAW_PATH_SEPARATOR
        + rb"cache"
        + _RAW_PATH_SEPARATOR
        + rb"skiphow"
        + _RAW_PATH_SEPARATOR
        + rb"skiphow"
        + _RAW_PATH_SEPARATOR
        + rb"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
        + _RAW_PATH_SEPARATOR
        + rb"skills"
        + _RAW_PATH_SEPARATOR
        + rb"skiphow"
        + _RAW_SKILL_BOUNDARY
    ),
    re.compile(
        rb"plugins"
        + _RAW_PATH_SEPARATOR
        + rb"skiphow"
        + _RAW_PATH_SEPARATOR
        + rb"skills"
        + _RAW_PATH_SEPARATOR
        + rb"skiphow"
        + _RAW_SKILL_BOUNDARY
    ),
    re.compile(
        rb"\.agents"
        + _RAW_PATH_SEPARATOR
        + rb"skills"
        + _RAW_PATH_SEPARATOR
        + rb"skiphow"
        + _RAW_SKILL_BOUNDARY
    ),
)
SKILL_BODY = "Base directory for this skill:"
SKILL_NAME_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
PLUGIN_VERSION_PATTERN = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
BASE_DIRECTORY_RE = re.compile(rf"{re.escape(SKILL_BODY)}[ \t]*([^\r\n]+)")
NAMESPACED_SKILL_RE = re.compile(rf"^skiphow:(?P<name>{SKILL_NAME_PATTERN})$")
HEADINGS = ("Result", "Evidence", "Rulings and findings", "Saved follow-ups", "Limits")
HEADING_RE = re.compile(
    r"^\s{0,3}(?:#{1,4}\s*)?(?:\*\*|__)?\s*"
    r"(Result|Evidence|Rulings and findings|Saved follow-ups|Limits)"
    r"\s*(?:\*\*|__)?\s*[:—–-]?\s*",
    re.MULTILINE,
)
FINDING_TAGS = ("TRACKED", "SAVED", "UNSAVED", "DISMISSED")
STRUCTURED_WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
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
AUDITED_VERSION_TOKEN = rf"(?:unknown|{PLUGIN_VERSION_PATTERN})"
AUDITED_RE = re.compile(
    rf"\AAudited `(?P<session>[A-Za-z0-9][A-Za-z0-9._-]*)` · "
    rf"(?P<records>(?:0|[1-9][0-9]*)) records · "
    rf"plugin (?P<version>{AUDITED_VERSION_TOKEN}"
    rf"(?:,{AUDITED_VERSION_TOKEN})*) · .+\Z"
)
SHORT_SESSION_RE = re.compile(r"[0-9a-f]{8}")
MARKDOWN_FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")
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
        return (selected_home / "plugins/cache/skiphow/skiphow",)
    return tuple(
        dict.fromkeys(
            home / "plugins/cache/skiphow/skiphow"
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


def contains_marker(path: Path) -> bool:
    """Scan for the attribution marker without holding the file in memory."""
    tail = b""
    overlap = 512
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1 << 20):
                window = tail + chunk
                if any(pattern.search(window) for pattern in MARKER_RES):
                    return True
                tail = chunk[-overlap:]
    except OSError:
        return False
    return False


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
    except ValueError:
        return None
    return parsed.astimezone().date().isoformat()


def parsed_timestamp(timestamp: str) -> datetime | None:
    """Parse one host timestamp for chronological ordering."""
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone()


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
    return (
        isinstance(value, list)
        and all(
            isinstance(change, dict)
            and isinstance(change.get("path"), str)
            and bool(change["path"])
            and isinstance(change.get("kind"), str)
            and change["kind"] in CODEX_FILE_CHANGE_KINDS
            for change in value
        )
        and len({change["path"] for change in value}) == len(value)
    )


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
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_values_equal(value, right[key]) for key, value in left.items()
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_values_equal(left_value, right_value)
            for left_value, right_value in zip(left, right)
        )
    return left == right


def result_content_payload_valid(value: object) -> bool:
    """Validate every nested value that model-visible result extraction visits."""
    pending = [value]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            continue
        if not isinstance(current, (list, dict)):
            return False
        identity = id(current)
        if identity in seen:
            return False
        seen.add(identity)
        if isinstance(current, list):
            pending.extend(current)
            continue
        block_type = current.get("type")
        if block_type is not None and not isinstance(block_type, str):
            return False
        if block_type in {"text", "output_text"} and not isinstance(
            current.get("text"), str
        ):
            return False
        if block_type == "resource":
            resource = current.get("resource")
            if not (
                isinstance(resource, dict)
                and isinstance(resource.get("uri"), str)
                and bool(resource["uri"])
                and (
                    isinstance(resource.get("text"), str)
                    or isinstance(resource.get("blob"), str)
                )
            ):
                return False
        if "content" in current:
            pending.append(current["content"])
    return True


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


def iter_records_with_marker_errors(path: Path) -> tuple[list[dict], int, int]:
    """Parse a transcript and separately count unreadable marker-bearing lines."""
    records: list[dict] = []
    broken = 0
    broken_markers = 0
    try:
        handle = path.open("rb")
    except OSError:
        return records, broken, broken_markers
    with handle:
        for raw_line in handle:
            raw_has_marker = any(pattern.search(raw_line) for pattern in MARKER_RES)
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
    )


def root_assistant_record(record: dict) -> bool:
    return record.get("type") == "assistant" and model_visible_root(record)


def text_of(record: dict) -> str:
    return "\n".join(b.get("text") or "" for b in blocks(record) if b.get("type") == "text")


def result_content_text(value: object) -> str:
    """Return only model-visible text from a Claude tool-result payload."""
    found: list[str] = []
    pending = [value]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            if current:
                found.append(current)
            continue
        if not isinstance(current, (list, dict)):
            continue
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(current, list):
            pending.extend(reversed(current))
        elif current.get("type") in {"text", "output_text"} and isinstance(
            current.get("text"), str
        ):
            if current["text"]:
                found.append(current["text"])
        elif current.get("type") == "resource" and isinstance(
            current.get("resource"), dict
        ):
            text = current["resource"].get("text")
            if isinstance(text, str) and text:
                found.append(text)
        elif "content" in current:
            pending.append(current["content"])
    return "\n".join(found)


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
                requested = [
                    value
                    for field in ("skill", "name")
                    if isinstance((value := data.get(field)), str) and value
                ]
                if not requested or len(set(requested)) != 1:
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
    )
    records_by_uuid = {
        record["uuid"]: (index, record)
        for index, record in enumerate(records)
        if isinstance(record.get("uuid"), str)
        and record["uuid"]
        and uuid_counts[record["uuid"]] == 1
        and not record.get("isSidechain")
    }
    observations: dict[str, dict] = {}

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
        body, artifact_source = package_skill(
            hit["version"], expected_name, hit.get("_root", "")
        )
        comparison_body = normalize_crlf(body)
        exact_bodies = [comparison_body]
        if comparison_body.startswith("---\n") and "\n---\n" in comparison_body[4:]:
            exact_bodies.append(
                comparison_body.split("\n---\n", 1)[1].lstrip("\n")
            )
        tail = comparison_text[base.end() :] if base else ""
        observed_body = tail.lstrip("\n")
        exact = False
        if body and hit["source"] == "plugin":
            for candidate in exact_bodies:
                expected = candidate.rstrip("\n")
                observed = observed_body.rstrip("\n")
                if not expected or not observed_body.startswith(expected):
                    continue
                wrapper = observed[len(expected) :]
                if not wrapper or re.match(r"^\n+ARGUMENTS:", wrapper):
                    exact = True
                    break
        return {
            "status": "body_observed" if exact else "body_unverified",
            "name": expected_name,
            "text": text,
            "source": hit["source"],
            "version": hit["version"],
            "artifact_source": artifact_source,
            "attribution": attribution,
            "at": records[index].get("timestamp", ""),
        }

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
        observations[tool_id] = evaluate(
            index, text, expected_names[tool_id], "explicit_skill_call"
        )

    for index, record in enumerate(records):
        if (
            record.get("isSidechain")
            or record.get("type") != "user"
            or record.get("userType") != "external"
            or record.get("isMeta") is not True
            or record.get("isCompactSummary")
            or record.get("isVisibleInTranscriptOnly")
            or (record.get("origin") or {}).get("kind") == "human"
            or record.get("sourceToolUseID") not in (None, "")
            or not isinstance(record.get("uuid"), str)
            or record.get("uuid") not in records_by_uuid
        ):
            continue
        text = text_of(record)
        base = BASE_DIRECTORY_RE.match(text)
        hits = skill_paths(base.group(1), require_file=False) if base else []
        if len(hits) != 1:
            continue
        key = f"unattributed:{record.get('uuid') or index}"
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
        ):
            return version
        return "unknown"

    values = {
        observed_version(injections.get(tool_id, {}))
        for tool_id in successful_skill_result_ids(records)
    }
    values.update(
        observed_version(observation)
        for tool_id, observation in injections.items()
        if tool_id.startswith("unattributed:")
        and observation.get("status") in {"body_observed", "body_unverified"}
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


def canonical_path_token(value: object) -> str | None:
    """Return a lexical filesystem token, rejecting prose and placeholders."""
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    windows_drive = bool(re.match(r"^[A-Za-z]:[/\\]", value))
    windows_unc = value.startswith("\\\\")
    normalized = value.replace("\\", "/") if windows_drive or windows_unc else value
    if any(character in normalized for character in ("\x00", "\n", "\r", "`", "$", "<", ">")):
        return None
    drive = bool(re.match(r"^[A-Za-z]:/", normalized))
    if normalized.startswith("./"):
        normalized = normalized[2:]
    unc = normalized.startswith("//") and not normalized.startswith("///")
    if drive and ":" in normalized[2:]:
        return None
    if not (drive or normalized.startswith("/") or unc) and ":" in normalized:
        return None
    if not (
        normalized.startswith("/")
        or drive
        or unc
        or normalized.startswith(".agents/skills/")
        or normalized.startswith("plugins/skiphow/skills/")
    ):
        return None
    remainder = (
        normalized[3:]
        if drive
        else normalized[2:]
        if unc
        else normalized[1:]
        if normalized.startswith("/")
        else normalized
    )
    parts = remainder.split("/")
    path_parts = parts[:-1] if normalized.endswith("/") else parts
    if not path_parts or any(part in {"", ".", ".."} for part in path_parts):
        return None
    return normalized


def recognized_path_root(value: object) -> tuple[str, str, str, str] | None:
    """Return outer root kind, suffix, version, and exact root path."""
    normalized = canonical_path_token(value)
    if normalized is None:
        return None
    cache_roots = tuple(
        f"{root.as_posix().rstrip('/')}/" for root in plugin_cache_roots()
    )
    for prefix in cache_roots:
        if normalized.startswith(prefix):
            remainder = normalized[len(prefix) :]
            version, separator, suffix = remainder.partition("/")
            if separator and re.fullmatch(PLUGIN_VERSION_PATTERN, version):
                return "cache", suffix, version, prefix.rstrip("/")
            return None
    source_prefix = "plugins/skiphow/skills/"
    source_absolute = f"{repository_root().as_posix().rstrip('/')}/{source_prefix}"
    project_marker = "/.agents/skills/"
    project_index = (
        0
        if normalized.startswith(".agents/skills/")
        else normalized.find(project_marker)
    )
    source_marker = "/plugins/skiphow/skills/"
    source_index = 0 if normalized.startswith(source_prefix) else normalized.find(source_marker)
    hidden_cache_markers = (
        "/.claude/plugins/cache/skiphow/skiphow/",
        "/.codex/plugins/cache/skiphow/skiphow/",
    )
    hidden = [
        (normalized.index(marker), marker)
        for marker in hidden_cache_markers
        if normalized.count(marker) == 1
    ]
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
            return "cache", suffix, version, normalized[: index + len(marker)].rstrip(
                "/"
            )
        return None
    if kind == "source":
        if normalized.startswith(source_prefix):
            return "source", normalized[len(source_prefix) :], "unknown", source_prefix.rstrip("/")
        if normalized.startswith(source_absolute):
            return "source", normalized[len(source_absolute) :], "unknown", source_absolute.rstrip("/")
        return None
    suffix = (
        normalized[len(".agents/skills/") :]
        if normalized.startswith(".agents/skills/")
        else normalized[index + len(project_marker) :]
    )
    if project_marker in suffix:
        return None
    root = (
        ".agents/skills"
        if normalized.startswith(".agents/skills/")
        else normalized[: index + len(project_marker)].rstrip("/")
    )
    return "project", suffix, "unknown", root


def skill_paths(text: str, require_file: bool) -> list[dict[str, str]]:
    """Recognize one exact skill directory or SKILL.md path."""
    rooted = recognized_path_root(text)
    if not rooted:
        return []
    kind, suffix, version, root = rooted
    match_suffix = suffix[:-1] if not require_file and suffix.endswith("/") else suffix
    if kind == "cache":
        match = re.fullmatch(
            rf"skills/(?P<name>{SKILL_NAME_PATTERN})(?P<file>/SKILL\.md)?",
            match_suffix,
        )
    else:
        match = re.fullmatch(
            rf"(?P<name>{SKILL_NAME_PATTERN})(?P<file>/SKILL\.md)?",
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
    if not re.fullmatch(PLUGIN_VERSION_PATTERN, version):
        return set()
    prefix = "plugins/skiphow/skills/skiphow/references/"
    try:
        tagged = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", f"v{version}", "--", prefix],
            cwd=repository_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        tagged = None
    if tagged and tagged.returncode == 0:
        names = {
            line[len(prefix) : -len(".md")]
            for line in tagged.stdout.splitlines()
            if line.startswith(prefix) and line.endswith(".md")
        }
        return names
    rosters: list[set[str]] = []
    for root in plugin_cache_roots():
        version_root = root / version
        if not version_root.is_dir():
            continue
        cache = version_root / "skills/skiphow/references"
        rosters.append(
            {
                str(path.relative_to(cache).with_suffix(""))
                for path in cache.rglob("*.md")
                if valid_reference_name(str(path.relative_to(cache).with_suffix("")))
            }
            if cache.is_dir()
            else set()
        )
    return rosters[0] if rosters and all(roster == rosters[0] for roster in rosters) else set()


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


def codex_tool_occurrences(
    records: list[dict],
) -> tuple[dict[str, list[tuple[int, dict]]], dict[str, list[tuple[int, dict, str]]]]:
    """Index identified root Codex starts and terminal events."""
    starts: dict[str, list[tuple[int, dict]]] = {}
    terminals: dict[str, list[tuple[int, dict, str]]] = {}
    for record_index, record in enumerate(records):
        if record.get("isSidechain"):
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
                # `item.completed` envelope. It remains open, not terminal.
                if not starts.get(item_id):
                    starts.setdefault(item_id, []).append((record_index, item))
            else:
                terminals.setdefault(item_id, []).append(
                    (record_index, item, record["type"])
                )
    return starts, terminals


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
            change["path"]: change["kind"] for change in start.get("changes", [])
        } == {
            change["path"]: change["kind"]
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
    starts, terminals = codex_tool_occurrences(records)
    events: list[dict] = []
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
        if len(result_occurrences) == 1:
            terminal_index, terminal_item, terminal_type = result_occurrences[0]
            compatible = (
                not call_occurrences
                and codex_terminal_shape_valid(terminal_item)
                or len(call_occurrences) == 1
                and call_occurrences[0][0] < terminal_index
                and codex_items_share_identity(call_occurrences[0][1], terminal_item)
            )
            outcome = (
                codex_terminal_outcome(terminal_type, terminal_item)
                if compatible
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
                else "ambiguous"
            )
            output = ""
        events.append(
            {
                "host": "codex",
                "id": item_id,
                "tool": event_item.get("type") or "?",
                "input": event_item,
                "succeeded": outcome == "succeeded",
                "outcome": outcome,
                "output": output,
                "at": records[event_index].get("timestamp", ""),
            }
        )
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
            structured_result = (
                records[result_occurrences[0][0]].get("toolUseResult")
                if len(result_occurrences) == 1
                and sum(
                    block.get("type") == "tool_result"
                    for block in blocks(records[result_occurrences[0][0]])
                )
                == 1
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
                        structured_result if isinstance(structured_result, dict) else {}
                    ),
                    "at": record.get("timestamp", ""),
                }
            )
    return events


def decoded_event_output(event: dict) -> str:
    """Decode a proven complete Claude Read frame; otherwise preserve raw output."""
    output = event.get("output") if isinstance(event.get("output"), str) else ""
    if not (
        event.get("host") == "claude"
        and event.get("tool") == "Read"
        and event.get("succeeded")
    ):
        return output
    data = event.get("input") if isinstance(event.get("input"), dict) else {}
    requested = data.get("file_path") or data.get("path")
    structured = (
        event.get("structured_result")
        if isinstance(event.get("structured_result"), dict)
        else {}
    )
    file_result = structured.get("file")
    if not isinstance(requested, str) or not isinstance(file_result, dict):
        return output
    observed_path = file_result.get("filePath")
    if not isinstance(observed_path, str) or requested.replace("\\", "/") != observed_path.replace(
        "\\", "/"
    ):
        return output
    start = file_result.get("startLine")
    count = file_result.get("numLines")
    total = file_result.get("totalLines")
    content = file_result.get("content")
    if not (
        isinstance(start, int)
        and not isinstance(start, bool)
        and start == 1
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count >= 0
        and isinstance(total, int)
        and not isinstance(total, bool)
        and total == count
        and isinstance(content, str)
    ):
        return output
    framed = [] if not output else output.split("\n")
    if len(framed) != count:
        return output
    decoded: list[str] = []
    for expected_number, line in enumerate(framed, 1):
        match = re.fullmatch(r"([0-9]+)\t(.*)", line)
        if not match or match.group(1) != str(expected_number):
            return output
        decoded.append(match.group(2))
    reconstructed = "\n".join(decoded)
    return reconstructed if reconstructed == content else output


def event_path_payloads(event: dict) -> list[str]:
    """Return only tool fields whose semantics identify a filesystem target."""
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
    fields = {
        "Read": ("file_path", "path"),
        "Grep": ("path",),
        "Glob": ("path", "pattern"),
        "Edit": ("file_path",),
        "Write": ("file_path",),
        "MultiEdit": ("file_path",),
        "NotebookEdit": ("notebook_path",),
    }.get(tool, ())
    return [data[field] for field in fields if isinstance(data.get(field), str)]


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

    for event in terminal_tool_events(records):
        tool = event["tool"]
        data = event["input"]
        succeeded = event["succeeded"]
        if tool == "command_execution":
            continue
        if tool == "file_change":
            found: set[tuple[str, str, str]] = set()
            for change in data.get("changes") or []:
                if not isinstance(change, dict) or not isinstance(change.get("path"), str):
                    continue
                for hit in skill_paths(change["path"], require_file=True):
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
            text=True,
            check=False,
        )
        if tagged.returncode == 0:
            return tagged.stdout, "tag"
        listed = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", tag, "--", relative],
            cwd=repository_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        if listed.returncode == 0 and relative not in listed.stdout.splitlines():
            return "", "absent_in_version"
    except OSError:
        return None
    return None


def cached_artifact(version: str, relative: str) -> tuple[str, str]:
    """Return cache bytes only when every existing host cache agrees."""
    version_roots = [root / version for root in plugin_cache_roots() if (root / version).is_dir()]
    if not version_roots:
        return "", "contract_bytes_unavailable"
    values: list[str | None] = []
    for root in version_roots:
        try:
            values.append((root / relative).read_text(encoding="utf-8"))
        except OSError:
            values.append(None)
    if any(value is None for value in values) or len(set(values)) != 1:
        return "", "contract_bytes_unavailable"
    return str(values[0]), "cache"


def observed_cache_artifact(
    roots: tuple[str, ...], version: str, relative: str
) -> tuple[str, str] | None:
    """Read the exact observed cache root when it is still available."""
    if not roots:
        return None
    values: list[str | None] = []
    any_existing = False
    for root in roots:
        path = Path(root) / version / relative
        any_existing = any_existing or path.exists()
        try:
            values.append(path.read_text(encoding="utf-8"))
        except OSError:
            values.append(None)
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
    if observed is not None:
        return observed
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
    if observed is not None:
        return observed
    if tagged := tagged_artifact(version, relative):
        return tagged
    return cached_artifact(version, f"skills/{name}/SKILL.md")


def package_skill_root(version: str) -> tuple[str, str]:
    """Compatibility wrapper for the exact owner skill artifact."""
    return package_skill(version, "skiphow")


def body_lines(body: str) -> list[str]:
    """Return distinct non-empty lines after CRLF-to-LF normalization only."""
    normalized = normalize_crlf(body)
    return list(dict.fromkeys(line for line in normalized.split("\n") if line))


def detect_references(_path: Path, records: list[dict], version: str) -> dict[str, dict]:
    """Report positive body and path-event observations without inferring a load."""
    names = tuple(sorted(version_reference_names(version) | observed_reference_names(records)))
    events = terminal_tool_events(records)
    observed_roots: dict[str, set[str]] = {name: set() for name in names}
    for event in events:
        if not event.get("succeeded"):
            continue
        for payload in event_path_payloads(event):
            rooted = recognized_path_root(payload)
            if not rooted or rooted[0] != "cache" or rooted[2] != version:
                continue
            name = reference_name_from_path(payload)
            if name in observed_roots:
                observed_roots[name].add(rooted[3])
    bodies: dict[str, str] = {}
    sources: dict[str, str] = {}
    lines: dict[str, list[str]] = {}
    for name in names:
        if version == "unknown":
            body, source = "", "contract_bytes_unavailable"
        else:
            body, source = package_reference(
                version, name, tuple(sorted(observed_roots[name]))
            )
        bodies[name], sources[name] = normalize_crlf(body), source
        lines[name] = body_lines(body) if body else []

    actions: dict[str, set[str]] = {name: set() for name in names}
    mismatched_versions: dict[str, set[str]] = {name: set() for name in names}
    observed_lines: dict[str, set[str]] = {name: set() for name in names}
    body_observed = {name: False for name in names}

    for event in events:
        tool = event["tool"]
        payloads = event_path_payloads(event)
        paths_by_name = {
            name: [
                path
                for payload in payloads
                for path in reference_paths(payload, name)
            ]
            for name in names
        }

        output = normalize_crlf(decoded_event_output(event))
        if output:
            output_lines = {line for line in output.split("\n") if line}
            for name in names:
                observed_lines[name].update(set(lines[name]) & output_lines)
                candidate_body = bodies[name].rstrip("\n")
                if candidate_body and candidate_body in output:
                    body_observed[name] = True

        for name, raw_paths in paths_by_name.items():
            for path in raw_paths:
                path_version = reference_path_version(path)
                if (
                    version != "unknown"
                    and path_version
                    and path_version != version
                ):
                    mismatched_versions[name].add(path_version)
                    actions[name].add("version_mismatch_path_observed")
            paths = [
                path
                for path in raw_paths
                if version == "unknown"
                or not reference_path_version(path)
                or reference_path_version(path) == version
            ]
            if not paths:
                continue
            if event["outcome"] == "ambiguous":
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
    )
    for name in names:
        action = actions[name]
        hit = len(observed_lines[name])
        total = len(lines[name])
        if sources[name] == "absent_in_version":
            verdict, basis = "absent_in_version", "exact_version_artifact"
        elif body_observed[name]:
            verdict, basis = "body_observed", "complete_artifact_text_in_model_output"
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
        and record.get("type") == "user"
        and not record.get("isMeta")
        and not record.get("isCompactSummary")
        and not record.get("isVisibleInTranscriptOnly")
        and not record.get("sourceToolAssistantUUID")
        and not record.get("sourceToolUseID")
        and not record.get("toolUseResult")
        and not any(block.get("type") == "tool_result" for block in blocks(record))
    )


def direct_owner_input(record: dict) -> tuple[str, str]:
    """Return text and explicit provenance for one direct owner-input record."""
    if not owner_input_record_visible(record):
        return "", ""
    origin = (record.get("origin") or {}).get("kind")
    attachment = record.get("attachment") or {}
    said = ""
    channel = ""
    decoded_command = False
    if origin == "human":
        said = text_of(record)
        command_frame = owner_command_frame(said)
        if command_frame is not None:
            command, arguments = command_frame
            said = arguments if arguments.strip() else command
            channel = "command_args"
            decoded_command = True
        else:
            source = record.get("promptSource")
            channel = (
                "queued"
                if source == "queued"
                else "typed"
                if source == "typed"
                else "human_origin"
            )
    elif (
        attachment.get("type") == "queued_command"
        and attachment.get("commandMode") == "prompt"
    ):
        raw = attachment.get("prompt") or attachment.get("command") or ""
        if isinstance(raw, list):
            raw = "\n".join(
                block["text"]
                for block in raw
                if isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            )
        said = raw if isinstance(raw, str) else ""
        channel = "queued_attachment"
    elif (
        record.get("userType") == "external"
        and origin is None
        and record.get("promptSource") in {None, "typed", "queued"}
    ):
        said = text_of(record)
        channel = f"external_{record.get('promptSource') or 'unspecified'}"
    if not said.strip() or not decoded_command and host_context_envelope(said):
        return "", ""
    return said.strip(), channel


def queued_owner_nontext_activity(record: dict) -> bool:
    """Recognize an explicit queued owner prompt that contains only media."""
    if not owner_input_record_visible(record):
        return False
    attachment = record.get("attachment") or {}
    if not (
        attachment.get("type") == "queued_command"
        and attachment.get("commandMode") == "prompt"
    ):
        return False
    return any(
        isinstance(value, list)
        and any(
            isinstance(block, dict) and block.get("type") == "image"
            for block in value
        )
        for key in ("prompt", "command")
        if (value := attachment.get(key)) is not None
    )


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
        if direct_owner_input(record)[0] or queued_owner_nontext_activity(record)
    )
    return indexes


def owner_turns(records: list[dict]) -> list[dict]:
    """Return owner input with the host provenance actually present."""
    answer_positions = owner_answer_positions(records)

    turns: list[dict] = []
    for record_index, record in enumerate(records):
        if record.get("isSidechain"):
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
    return turns


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


def report_text(records: list[dict], versions: list[str]) -> str:
    """Select the report according to the contract version that produced it."""
    parsed = [
        tuple(int(part) for part in match.group(0).split("."))
        for version in versions
        if (match := re.match(r"[0-9]+(?:\.[0-9]+)*", version))
    ]
    reports = select_reports(records)
    if parsed and (1, 1) <= max(parsed) < (1, 14) and reports:
        return reports[-1]["text"]
    return final_assistant_text(records)


def codex_turn_status(records: list[dict]) -> str:
    """Return a concrete final state only for a well-formed Codex turn sequence."""
    active = False
    observed_start = False
    last_outcome = "not_observed"
    ambiguous = False
    for record in records:
        if record.get("isSidechain"):
            continue
        event_type = record.get("type")
        if event_type == "turn.started":
            observed_start = True
            ambiguous = ambiguous or active
            active = True
        elif event_type in {"turn.completed", "turn.failed"}:
            ambiguous = ambiguous or not active
            active = False
            last_outcome = (
                "completed" if event_type == "turn.completed" else "failed"
            )
    if ambiguous:
        return "ambiguous_sequence"
    if active:
        return "open_sequence"
    return last_outcome if observed_start else "not_observed"


def compaction_status(records: list[dict]) -> bool | str:
    """Report positive compaction evidence; absence is not a negative receipt."""
    root_records = [record for record in records if not record.get("isSidechain")]
    if any(
        record.get("isCompactSummary") or record.get("type") == "compacted"
        for record in root_records
    ):
        return True
    return "unknown"


def unpaired_tool_calls(records: list[dict]) -> dict[str, int]:
    """Return every root call lacking one uniquely ordered terminal event."""
    pending: dict[str, int] = {}
    claude_calls, claude_results = claude_tool_occurrences(records)
    codex_starts, codex_terminals = codex_tool_occurrences(records)
    uuid_counts = Counter(
        record["uuid"]
        for record in records
        if not record.get("isSidechain")
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
        if record.get("isSidechain"):
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
                and stable_identity
                and codex_terminal_outcome(terminals[0][2], terminal_item)
                != "ambiguous"
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

    codex_starts, codex_terminals = codex_tool_occurrences(records)
    for item_id, starts in codex_starts.items():
        if (
            len(starts) == 1
            and not codex_terminals.get(item_id)
            and codex_start_valid(starts[0][1])
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
    owner_activity = owner_activity_record_indexes(records)
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
    same_record_text = bool(pending_blocks) and any(
        block_index > max(pending_blocks)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
        and bool(block["text"].strip())
        for block_index, block in enumerate(blocks(records[last_pending]))
    )
    later_completion = same_record_text or any(
        index > last_pending
        and not record.get("isSidechain")
        and (
            bool(assistant_text(record).strip())
            or record.get("type") in {"turn.completed", "turn.failed", "error"}
            or index in owner_activity
            or record.get("type") in {"item.started", "item.updated", "item.completed"}
            and isinstance(record.get("item"), dict)
            and not (
                record.get("type") == "item.completed"
                and record["item"].get("type") != "web_search"
                and codex_start_valid(record["item"])
            )
            or any(block.get("type") in {"tool_use", "tool_result"} for block in blocks(record))
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
        if record.get("isSidechain"):
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


def _digest(path: Path, report_chars: int) -> dict:
    if report_chars < 0:
        raise SystemExit("--report-chars must be zero or greater")
    records, broken = iter_records(path)
    if not records:
        raise SystemExit(f"{path} holds no readable records")

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
        if record.get("isSidechain"):
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
        elif item_type == "command_execution":
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
            }
            for name in sorted(incomplete_names)
        }
    elif version_identity in {"single", "unknown"}:
        reference_evidence = detect_references(
            path, records, known_versions[0] if known_versions else "unknown"
        )
    else:
        mixed_reference_names = observed_reference_names(records) | {
            name
            for version in known_versions
            for name in version_reference_names(version)
        }
        reference_evidence = {
            name: {
                "verdict": "unverified_contract_identity",
                "basis": version_identity,
                "matching_line_values": "unavailable",
                "artifact_source": "contract_identity_unsettled",
                "actions": ["not_evaluated"],
                "mismatched_path_versions": [],
            }
            for name in sorted(mixed_reference_names)
        }
    turn_state = (
        "unverified_incomplete_transcript" if broken else codex_turn_status(records)
    )
    reports = select_reports(records)
    contract_scoring_status = (
        "unverified_incomplete_transcript"
        if broken
        else "applicable_version_known"
        if version_identity == "single"
        else "unverified_contract_identity"
    )
    selected = (
        report_text(records, observed_version_values)
        if contract_scoring_status == "applicable_version_known"
        else final_assistant_text(records)
    )
    selected_headings = {match.group(1) for match in HEADING_RE.finditer(selected)}
    if not selected:
        selected = "(no assistant text found)"
    omitted_report_chars = max(0, len(selected) - report_chars) if report_chars else 0
    return {
        "session": next(
            (
                record["thread_id"]
                for record in records
                if not record.get("isSidechain")
                and record.get("type") == "thread.started"
                and isinstance(record.get("thread_id"), str)
                and record["thread_id"]
            ),
            path.stem,
        ),
        "project": Path(cwd).name or "unknown",
        "branch": branch or "unknown",
        "host": host or "unknown",
        "plugin_version_values_observed": (
            ["unverified_incomplete_transcript"]
            if broken
            else observed_version_values
        ),
        "window": [stamps[0] if stamps else "unknown", stamps[-1] if stamps else "unknown"],
        "records": len(records),
        "unparseable_lines": broken,
        "skill_body_injections": injections,
        "models": dict(models),
        "owner_turns": [
            turn
            for turn in owner_turns(records)
            if not broken or turn["channel"] != "answered"
        ],
        "skills": observed_skills,
        "references": reference_evidence,
        "tools": dict(tools.most_common()),
        "command_results": dict(command_results),
        "successful_structured_delegations": delegations,
        "successful_structured_write_actions": write_actions,
        "checkout_metadata_observations": identity_transitions(records),
        "confounders": {
            "compaction_observed": compaction_status(records),
            "legacy_reports_observed": len(reports),
            "trailing_unresolved_tool_call": (
                "unknown" if broken else ended_mid_tool(records)
            ),
            "unpaired_tool_call_count": (
                "unknown" if broken else len(unpaired_tool_calls(records))
            ),
            "turn_sequence": turn_state,
            "plugin_version_identity": (
                "unverified_incomplete_transcript"
                if broken
                else version_identity
            ),
            "contract_sequence": (
                "unverified_incomplete_transcript" if broken else "parsed"
            ),
        },
        "usage": dict(usage),
        "report": {
            "selection_status": (
                "unverified_incomplete_transcript"
                if broken
                else "unverified_contract_identity"
                if version_identity != "single"
                else "last_applicable_assistant_text"
            ),
            "legacy_contract_scoring": contract_scoring_status,
            "headings_present": [h for h in HEADINGS if h in selected_headings],
            "headings_not_observed": (
                "unverified_incomplete_transcript"
                if broken
                else "unverified_contract_identity"
                if version_identity != "single"
                else [h for h in HEADINGS if h not in selected_headings]
            ),
            "tag_counts": {t: len(re.findall(rf"\b{t}\b", selected)) for t in FINDING_TAGS},
            "omitted_prefix_chars": omitted_report_chars,
            "text": selected[-report_chars:] if report_chars else selected,
        },
    }


def digest(path: Path, report_chars: int, home: Path | None = None) -> dict:
    """Digest one transcript with cache attribution scoped to its selected home."""
    selected_home = None
    if home is not None:
        try:
            path.resolve().relative_to((home / "projects").resolve())
        except (OSError, RuntimeError, ValueError):
            pass
        else:
            selected_home = home
    if selected_home is None and path.parent.parent.name == "projects":
        selected_home = path.parent.parent.parent
    if selected_home is None:
        return _digest(path, report_chars)
    token = AUDIT_HOME.set(selected_home)
    try:
        return _digest(path, report_chars)
    finally:
        AUDIT_HOME.reset(token)


def _discover(
    home: Path,
    since: str | None,
    on: str | None = None,
) -> list[dict]:
    projects = home / "projects"
    root = str(repository_root())
    rows: list[dict] = []
    if not projects.is_dir():
        return rows
    for path in sorted(projects.glob("*/*.jsonl")):
        if not contains_marker(path):
            continue
        records, broken, broken_marker_lines = iter_records_with_marker_errors(path)
        root_records = [record for record in records if not record.get("isSidechain")]
        marker_records = [
            record for record in root_records if record_contains_marker(record)
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
        cwd = next((r.get("cwd") for r in root_records if r.get("cwd")), "") or ""
        real = os.path.realpath(cwd) if cwd else ""
        reason = None
        if not records:
            reason = "unreadable-transcript"
        elif not cwd:
            reason = "no-cwd"
        elif real == os.path.realpath(root) or real.startswith(os.path.realpath(root) + os.sep):
            reason = "self-development"
        elif any(
            real == scratch or real.startswith(scratch + os.sep)
            for scratch in ("/private/tmp", "/tmp", "/private/var/folders")
        ):
            reason = "scratch-harness"
        timestamp_points = sorted(
            (parsed, record["timestamp"])
            for record in root_records
            if isinstance(record.get("timestamp"), str)
            and (parsed := parsed_timestamp(record["timestamp"])) is not None
        )
        started = timestamp_points[0][1] if timestamp_points else ""
        if (
            since
            and not broken_marker_lines
            and marker_dates
            and marker_dates[-1] < since
            and not undated_marker_records
        ):
            continue
        if (
            on
            and not broken_marker_lines
            and marker_dates
            and on not in marker_dates
            and not undated_marker_records
        ):
            continue
        observed_versions = contract_identity_values(records)
        rows.append(
            {
                "session": path.stem,
                "path": str(path),
                "project": Path(cwd).name or "unknown",
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
                    "unverified_incomplete_transcript"
                    if broken_marker_lines
                    else "unverified_undated_marker_records"
                    if marker_dates and undated_marker_records
                    else "observed"
                    if marker_dates
                    else "unverified_missing_or_invalid_timestamp"
                ),
                "undated_marker_records": undated_marker_records,
                "records": len(records),
                "unreadable_lines": broken,
                "unreadable_marker_lines": broken_marker_lines,
                "megabytes": round(path.stat().st_size / 1e6, 1),
                "versions": (
                    ["unverified_incomplete_transcript"]
                    if broken
                    else observed_versions
                ),
                "excluded": reason,
            }
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
    token = AUDIT_HOME.set(home)
    try:
        return _discover(home, since, on)
    finally:
        AUDIT_HOME.reset(token)


def resolve(home: Path, target: str) -> Path:
    candidate = Path(target)
    if candidate.is_file():
        return candidate
    matches = sorted(
        path
        for path in (home / "projects").glob("*/*.jsonl")
        if path.name.startswith(target)
    )
    if not matches:
        raise SystemExit(f"no transcript found for {target!r}")
    if len(matches) > 1:
        ids = ", ".join(path.stem for path in matches[:8])
        raise SystemExit(f"ambiguous transcript prefix {target!r}: {ids}")
    return matches[0]


def audit_receipts(text: str) -> list[tuple[str, int, frozenset[str]]]:
    """Parse exact receipt lines outside Markdown fenced code blocks."""
    receipts: list[tuple[str, int, frozenset[str]]] = []
    fence_character = ""
    fence_length = 0
    for line in text.splitlines():
        fence = MARKDOWN_FENCE_RE.match(line)
        if fence:
            marker = fence.group("fence")
            trailing = line[fence.end() :]
            if not fence_character:
                fence_character = marker[0]
                fence_length = len(marker)
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and not trailing.strip()
            ):
                fence_character = ""
                fence_length = 0
            continue
        if fence_character:
            continue
        receipt = AUDITED_RE.fullmatch(line)
        if receipt:
            receipts.append(
                (
                    receipt.group("session"),
                    int(receipt.group("records")),
                    frozenset(receipt.group("version").split(",")),
                )
            )
    return receipts


def coverage(home: Path) -> str:
    """Derive audit coverage from the receipts, not from a second ledger."""
    seen: set[tuple[str, int, frozenset[str]]] = set()
    for note in (repository_root() / "docs/research").rglob("*.md"):
        seen.update(
            audit_receipts(note.read_text(encoding="utf-8", errors="replace"))
        )
    rows = [r for r in discover(home, None) if not r["excluded"]]
    session_ids = Counter(row["session"] for row in rows)
    prefixes = Counter(row["session"][:8] for row in rows)
    lines = [
        "Coverage from exact docs/research receipts "
        "(session id, record count, and plugin identity):"
    ]
    for row in rows:
        session_id = row["session"]
        prefix = session_id[:8]
        identity = frozenset(row["versions"])
        full_receipts = {
            (count, versions)
            for receipt_session, count, versions in seen
            if receipt_session == session_id
        }
        short_receipts = {
            (count, versions)
            for receipt_session, count, versions in seen
            if SHORT_SESSION_RE.fullmatch(receipt_session)
            and receipt_session == prefix
        }
        snapshot = (row["records"], identity)
        if session_ids[session_id] > 1:
            state = "AMBIGUOUS_SESSION"
        elif row["unreadable_lines"]:
            state = "UNVERIFIED_UNREADABLE"
        elif snapshot in full_receipts:
            state = "covered"
        elif short_receipts and prefixes[prefix] > 1:
            state = "AMBIGUOUS_PREFIX"
        elif snapshot in short_receipts:
            state = "covered"
        elif full_receipts or short_receipts:
            state = "STALE"
        else:
            state = "UNAUDITED"
        lines.append(
            f"  {session_id}  {row['candidate_marker_local_dates'][1]}  "
            f"{row['project']:<16} {state}"
        )
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
            f"  {row['session'][:8]}  marker local-date "
            f"{row['candidate_marker_local_dates'][1]} "
            f"({row['candidate_marker_date_status']}; "
            f"{row['undated_marker_records']} undated marker records)  "
            f"{row['project']:<{width}}  "
            f"v{','.join(row['versions'])}  {row['megabytes']}MB  {row['records']} rec  "
            f"{row['unreadable_lines']} unreadable{note}"
        )
    return "\n".join(lines)


def render_digest(data: dict) -> str:
    incomplete = bool(data["unparseable_lines"])
    out = [
        f"session {data['session']}  project {data['project']}  branch {data['branch']}",
        "host "
        f"{data['host']}  plugin values observed "
        f"{','.join(data['plugin_version_values_observed'])}  "
        f"exact skill bodies observed {data['skill_body_injections']}",
        f"window {data['window'][0]} .. {data['window'][1]}  {data['records']} records  "
        f"{data['unparseable_lines']} unreadable",
        f"models {data['models']}  confounders {data['confounders']}",
        "",
        "OWNER-VISIBLE USER TURNS",
    ]
    for turn in data["owner_turns"] or []:
        out.append(f"  [{turn['at'][:19]} {turn['channel']}] {' '.join(turn['said'].split())}")
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
        )
    out += [
        "",
        f"PARSED TOOL RECORD COUNTS    {data['tools']}",
        f"OBSERVED COMMAND TERMINALS   {data['command_results']}",
        "OBSERVED SUCCESSFUL STRUCTURED DELEGATIONS "
        f"({'UNVERIFIED' if incomplete else len(data['successful_structured_delegations'])})",
        "",
        "OBSERVED SUCCESSFUL STRUCTURED WRITE ACTIONS "
        f"({'UNVERIFIED' if incomplete else len(data['successful_structured_write_actions'])})",
    ]
    for delegation in data["successful_structured_delegations"]:
        out.append(f"  role {delegation['role']}  task {delegation['task']}")
    if not data["successful_structured_delegations"]:
        out.append(
            "  UNVERIFIED: incomplete transcript; absence cannot be established"
            if incomplete
            else "  none observed"
        )
    for write in data["successful_structured_write_actions"]:
        out.append(f"  [{write['at'][:19]}] {write['tool']} {write['path']}")
    if not data["successful_structured_write_actions"]:
        out.append(
            "  UNVERIFIED: incomplete transcript; absence cannot be established"
            if incomplete
            else "  none observed; shell command semantics are not inferred"
        )
    out += [
        "",
        "OBSERVED CHECKOUT METADATA "
        f"({len(data['checkout_metadata_observations'])})",
    ]
    for change in data["checkout_metadata_observations"]:
        out.append(
            f"  [{change['at'][:19]}] cwd {change['cwd']}  branch {change['branch']}"
        )
    if not data["checkout_metadata_observations"]:
        out.append("  none observed")
    report = data["report"]
    out += [
        "",
        f"REPORT selection status         {report['selection_status']}",
        f"       legacy contract scoring  {report['legacy_contract_scoring']}",
        f"       legacy headings observed {report['headings_present']}",
        f"       headings not observed     {report['headings_not_observed']}",
        f"       legacy tag strings seen  {report['tag_counts']}",
    ]
    if report["omitted_prefix_chars"]:
        out.append(
            f"       final text omitted prefix {report['omitted_prefix_chars']} chars; "
            "use bounded grep before ruling on the omitted text"
        )
    out += [
        "",
        "SELECTED PARSED ASSISTANT TEXT",
        report["text"] or "(no assistant text found)",
    ]
    return "\n".join(out)


def main() -> None:
    def nonnegative(value: str) -> int:
        parsed = int(value)
        if parsed < 0:
            raise argparse.ArgumentTypeError("must be zero or greater")
        return parsed

    def iso_date(value: str) -> str:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as error:
            raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from error

    parser = argparse.ArgumentParser(description=__doc__)
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
    listing.add_argument("--all", action="store_true", help="also show excluded sessions")
    listing.add_argument("--json", action="store_true")

    one = sub.add_parser("digest", help="slice one session into reviewable evidence")
    one.add_argument("target", help="session id, id prefix, or transcript path")
    one.add_argument(
        "--report-chars", type=nonnegative, default=0, help="0 keeps the full final text"
    )
    one.add_argument("--json", action="store_true")

    finder = sub.add_parser("grep", help="search the raw transcript of one session")
    finder.add_argument("target")
    finder.add_argument("pattern")
    finder.add_argument("--max", type=int, default=20)
    finder.add_argument("--chars", type=int, default=240)

    sub.add_parser("coverage", help="which sessions the receipts already cover")

    args = parser.parse_args()
    if args.command == "list":
        rows = discover(args.home, args.since, args.on)
        shown = rows if args.all else [row for row in rows if not row["excluded"]]
        print(
            json.dumps(shown, indent=2)
            if args.json
            else render_list(rows, args.all)
        )
    elif args.command == "digest":
        data = digest(resolve(args.home, args.target), args.report_chars, args.home)
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
