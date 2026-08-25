"""Claude Agent SDK or structured CLI adapter.

The transport boundary fits both ``ClaudeSDKClient`` and a long-lived
``claude --input-format stream-json --output-format stream-json`` process.
Provider packages remain optional dependencies of SkipHow.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from .base import (
    AgentProviderAdapter,
    Capability,
    ContextHealth,
    ModelInfo,
    PermissionMode,
    ProviderCapabilities,
    ProviderError,
    SessionRef,
    StreamEvent,
    Usage,
)


class ClaudeTransport(Protocol):
    async def start(self, options: Mapping[str, Any], prompt: str) -> Mapping[str, Any]: ...

    async def resume(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    async def fork(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    async def send(self, session_id: str, prompt: str) -> Mapping[str, Any]: ...

    def messages(self, session_id: str) -> AsyncIterator[Mapping[str, Any]]: ...

    async def interrupt(self, session_id: str) -> None: ...

    async def compact(self, session_id: str) -> None: ...

    async def close(self, session_id: str) -> None: ...


class ClaudeAdapter(AgentProviderAdapter):
    provider = "claude"

    def __init__(
        self,
        transport: ClaudeTransport,
        *,
        configured_models: Sequence[ModelInfo] = (),
        supports_compact: bool = True,
        supports_compact_hooks: bool = False,
    ) -> None:
        self._transport = transport
        self._configured_models = tuple(configured_models)
        self._supports_compact = supports_compact
        self._supports_compact_hooks = supports_compact_hooks
        self._usage: dict[str, Usage] = {}

    async def discover_capabilities(self) -> ProviderCapabilities:
        supported = {
            Capability.START,
            Capability.RESUME,
            Capability.FORK,
            Capability.SEND,
            Capability.STREAM,
            Capability.INTERRUPT,
            Capability.USAGE,
            Capability.CLEANUP,
            Capability.SUBAGENT_ATTRIBUTION,
            Capability.BUDGET,
        }
        if self._supports_compact:
            supported.add(Capability.COMPACT)
        if self._supports_compact_hooks:
            supported.add(Capability.COMPACT_HOOKS)
        if hasattr(self._transport, "list_models"):
            supported.add(Capability.MODEL_DISCOVERY)
        return ProviderCapabilities(
            provider=self.provider,
            supported=frozenset(supported),
            details={
                "transport": "agent-sdk-or-stream-json-cli",
                "catalog": "configuration",
                "interrupt_mode": getattr(self._transport, "interrupt_mode", "typed"),
            },
        )

    async def list_models(self) -> Sequence[ModelInfo]:
        discover = getattr(self._transport, "list_models", None)
        if discover is None:
            return self._configured_models
        try:
            rows = await discover()
        except (OSError, ProviderError):
            return self._configured_models
        models = tuple(_claude_model(row) for row in rows if isinstance(row, Mapping))
        return tuple(model for model in models if model is not None) or self._configured_models

    async def start_session(
        self,
        input: str,
        *,
        cwd: Path,
        permissions: PermissionMode,
        model_profile: str | None = None,
        model_id: str | None = None,
        budget_usd: float | None = None,
    ) -> SessionRef:
        options: dict[str, Any] = {
            "cwd": str(cwd),
            "permission_mode": _claude_permission_mode(permissions),
        }
        if model_id is not None:
            options["model"] = model_id
        if model_profile is not None:
            options["profile"] = model_profile
        if budget_usd is not None:
            options["max_budget_usd"] = budget_usd
        return _claude_session(await self._transport.start(options, input), model_id=model_id)

    async def resume_session(
        self, session_id: str, *, checkpoint: Mapping[str, Any] | None = None
    ) -> SessionRef:
        options = dict(checkpoint or {})
        return _claude_session(await self._transport.resume(session_id, options))

    async def fork_session(
        self, session_id: str, *, checkpoint: Mapping[str, Any] | None = None
    ) -> SessionRef:
        options = dict(checkpoint or {})
        options["fork_session"] = True
        child = _claude_session(await self._transport.fork(session_id, options))
        return SessionRef(
            provider=self.provider,
            session_id=child.session_id,
            model_id=child.model_id,
            parent_session_id=session_id,
            metadata=child.metadata,
        )

    async def send_turn(self, session_id: str, input: str) -> SessionRef:
        result = await self._transport.send(session_id, input)
        return SessionRef(
            provider=self.provider,
            session_id=session_id,
            turn_id=_string(result.get("turn_id", result.get("message_id"))),
            metadata=dict(result),
        )

    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        async for message in self._transport.messages(session_id):
            kind = str(message.get("type", "unknown"))
            measured = _claude_usage(message)
            if measured is not None:
                self._usage[session_id] = measured
            yield StreamEvent(
                provider=self.provider,
                session_id=session_id,
                kind=kind,
                data=dict(message),
                turn_id=_string(message.get("message_id", message.get("turn_id"))),
                subagent_id=_subagent_id(message),
            )

    async def interrupt(self, session_id: str) -> None:
        await self._transport.interrupt(session_id)

    async def compact(self, session_id: str) -> None:
        if not self._supports_compact:
            raise ProviderError("Claude transport does not support explicit compaction")
        await self._transport.compact(session_id)

    async def usage(self, session_id: str) -> Usage:
        return self._usage.get(session_id, Usage())

    async def cleanup(self, session_id: str) -> None:
        await self._transport.close(session_id)


def _claude_session(result: Mapping[str, Any], model_id: str | None = None) -> SessionRef:
    session_id = result.get("session_id", result.get("sessionId"))
    if not isinstance(session_id, str) or not session_id:
        raise ProviderError("Claude session response has no session id")
    return SessionRef(
        provider="claude",
        session_id=session_id,
        model_id=_string(result.get("model")) or model_id,
        turn_id=_string(result.get("message_id", result.get("turn_id"))),
        metadata=dict(result),
    )


def _claude_model(row: Mapping[str, Any]) -> ModelInfo | None:
    model_id = row.get("id", row.get("model"))
    if not isinstance(model_id, str) or not model_id:
        return None
    return ModelInfo(
        provider="claude",
        model_id=model_id,
        model_version=_string(row.get("version")),
        profiles=tuple(str(item) for item in row.get("profiles", ())),
        capabilities=frozenset(str(item) for item in row.get("capabilities", ())),
        context_limit=_integer(row.get("context_limit", row.get("contextWindow"))),
        pricing=row.get("pricing") if isinstance(row.get("pricing"), Mapping) else None,
        latency_class=_string(row.get("latency_class")),
        availability=str(row.get("availability", "unknown")),
        deprecated=bool(row.get("deprecated", False)),
        metadata=dict(row),
    )


def _claude_permission_mode(mode: PermissionMode) -> str:
    return {
        PermissionMode.READ_ONLY: "plan",
        PermissionMode.WORKSPACE_WRITE: "acceptEdits",
        PermissionMode.FULL_ACCESS: "bypassPermissions",
    }[mode]


def _claude_usage(message: Mapping[str, Any]) -> Usage | None:
    raw = message.get("usage")
    if not isinstance(raw, Mapping) and isinstance(message.get("result"), Mapping):
        raw = message["result"].get("usage")
    if not isinstance(raw, Mapping):
        return None
    return Usage(
        input_tokens=_token(raw, "input_tokens", "inputTokens"),
        output_tokens=_token(raw, "output_tokens", "outputTokens"),
        cache_read_tokens=_token(raw, "cache_read_input_tokens", "cacheReadInputTokens"),
        cache_write_tokens=_token(raw, "cache_creation_input_tokens", "cacheCreationInputTokens"),
        cost_usd=_number(message.get("total_cost_usd", raw.get("cost_usd"))),
        context_tokens=_optional_token(raw, "context_tokens", "contextTokens"),
        context_limit=_optional_token(raw, "context_limit", "contextLimit"),
        context_health=_context_health(raw.get("context_health", raw.get("contextHealth"))),
        raw=dict(raw),
    )


def _subagent_id(message: Mapping[str, Any]) -> str | None:
    direct = message.get("parent_tool_use_id", message.get("agent_id"))
    if isinstance(direct, str):
        return direct
    payload = message.get("message")
    if isinstance(payload, Mapping):
        nested = payload.get("parent_tool_use_id")
        return nested if isinstance(nested, str) else None
    return None


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _token(raw: Mapping[str, Any], *keys: str) -> int:
    return _optional_token(raw, *keys) or 0


def _optional_token(raw: Mapping[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _context_health(value: Any) -> ContextHealth:
    try:
        return ContextHealth(value)
    except (TypeError, ValueError):
        return ContextHealth.UNKNOWN
