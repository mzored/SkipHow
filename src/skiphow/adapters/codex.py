"""Codex App Server adapter.

The adapter speaks the documented JSON-RPC method names but owns no process or
credentials. A host supplies a connected transport, which also makes the
adapter deterministic in tests.
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


class CodexTransport(Protocol):
    async def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def notifications(self, session_id: str) -> AsyncIterator[Mapping[str, Any]]: ...

    async def close_session(self, session_id: str) -> None: ...


class CodexAdapter(AgentProviderAdapter):
    provider = "codex"

    def __init__(
        self,
        transport: CodexTransport,
        *,
        configured_models: Sequence[ModelInfo] = (),
    ) -> None:
        self._transport = transport
        self._configured_models = tuple(configured_models)
        self._active_turns: dict[str, str] = {}
        self._usage: dict[str, Usage] = {}

    async def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self.provider,
            supported=frozenset(
                {
                    Capability.START,
                    Capability.RESUME,
                    Capability.FORK,
                    Capability.SEND,
                    Capability.STREAM,
                    Capability.INTERRUPT,
                    Capability.COMPACT,
                    Capability.USAGE,
                    Capability.CLEANUP,
                    Capability.MODEL_DISCOVERY,
                }
            ),
            details={"transport": "app-server-json-rpc", "catalog": "model/list"},
        )

    async def list_models(self) -> Sequence[ModelInfo]:
        try:
            result = await self._transport.request("model/list", {})
        except (OSError, ProviderError):
            return self._configured_models
        rows = result.get("data", result.get("models", ()))
        discovered: list[ModelInfo] = []
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                model_id = row.get("id") or row.get("model")
                if not isinstance(model_id, str) or not model_id:
                    continue
                efforts = row.get("supportedReasoningEfforts", row.get("reasoningEfforts", ()))
                profiles = tuple(
                    effort
                    for value in efforts or ()
                    if (effort := _reasoning_effort(value)) is not None
                )
                modalities = row.get("inputModalities")
                if modalities is None:
                    modalities = ("text", "image")
                discovered.append(
                    ModelInfo(
                        provider=self.provider,
                        model_id=model_id,
                        model_version=_string(row.get("version")),
                        profiles=profiles,
                        capabilities=frozenset(str(value) for value in modalities),
                        context_limit=_integer(row.get("contextWindow")),
                        availability="available",
                        deprecated=bool(row.get("deprecated", False)),
                        metadata=dict(row),
                    )
                )
        return tuple(discovered) or self._configured_models

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
        del budget_usd
        params: dict[str, Any] = {
            "cwd": str(cwd),
            "approvalPolicy": "never",
            "sandbox": _codex_sandbox(permissions),
        }
        if model_id is not None:
            params["model"] = model_id
        result = await self._transport.request("thread/start", params)
        session = _codex_session(result)
        turn = await self._start_turn(
            session.session_id, input, effort=_codex_effort(model_profile)
        )
        return SessionRef(
            provider=self.provider,
            session_id=session.session_id,
            model_id=model_id,
            turn_id=turn.turn_id,
            metadata=session.metadata,
        )

    async def resume_session(
        self, session_id: str, *, checkpoint: Mapping[str, Any] | None = None
    ) -> SessionRef:
        params: dict[str, Any] = {"threadId": session_id}
        _copy_codex_fields(params, checkpoint, _THREAD_RESUME_FIELDS)
        return _codex_session(await self._transport.request("thread/resume", params))

    async def fork_session(
        self, session_id: str, *, checkpoint: Mapping[str, Any] | None = None
    ) -> SessionRef:
        params: dict[str, Any] = {"threadId": session_id}
        _copy_codex_fields(params, checkpoint, _THREAD_FORK_FIELDS)
        child = _codex_session(await self._transport.request("thread/fork", params))
        return SessionRef(
            provider=self.provider,
            session_id=child.session_id,
            model_id=child.model_id,
            parent_session_id=session_id,
            metadata=child.metadata,
        )

    async def send_turn(self, session_id: str, input: str) -> SessionRef:
        return await self._start_turn(session_id, input)

    async def _start_turn(
        self, session_id: str, input: str, *, effort: str | None = None
    ) -> SessionRef:
        params: dict[str, Any] = {
            "threadId": session_id,
            "input": [{"type": "text", "text": input}],
        }
        if effort is not None:
            params["effort"] = effort
        result = await self._transport.request(
            "turn/start",
            params,
        )
        turn = result.get("turn", result)
        if not isinstance(turn, Mapping) or not isinstance(turn.get("id"), str):
            raise ProviderError("Codex turn/start response has no turn id")
        turn_id = str(turn["id"])
        self._active_turns[session_id] = turn_id
        return SessionRef(provider=self.provider, session_id=session_id, turn_id=turn_id)

    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        async for message in self._transport.notifications(session_id):
            method = str(message.get("method", "unknown"))
            params = message.get("params", {})
            data = dict(params) if isinstance(params, Mapping) else {"value": params}
            turn_id = _nested_string(data, "turn", "id") or _string(data.get("turnId"))
            measured = _usage_from_payload(data)
            if measured is not None:
                self._usage[session_id] = measured
            yield StreamEvent(
                provider=self.provider,
                session_id=session_id,
                kind=method,
                data=data,
                turn_id=turn_id,
            )
            if method == "turn/completed":
                return

    async def interrupt(self, session_id: str) -> None:
        turn_id = self._active_turns.get(session_id)
        if turn_id is None:
            raise ProviderError(f"no active turn for Codex session {session_id}")
        await self._transport.request(
            "turn/interrupt", {"threadId": session_id, "turnId": turn_id}
        )

    async def compact(self, session_id: str) -> None:
        await self._transport.request("thread/compact/start", {"threadId": session_id})

    async def usage(self, session_id: str) -> Usage:
        return self._usage.get(session_id, Usage())

    async def cleanup(self, session_id: str) -> None:
        try:
            await self._transport.request("thread/unsubscribe", {"threadId": session_id})
        finally:
            await self._transport.close_session(session_id)
            self._active_turns.pop(session_id, None)


def _codex_session(result: Mapping[str, Any]) -> SessionRef:
    thread = result.get("thread", result)
    if not isinstance(thread, Mapping) or not isinstance(thread.get("id"), str):
        raise ProviderError("Codex thread response has no thread id")
    return SessionRef(
        provider="codex",
        session_id=str(thread["id"]),
        model_id=_string(thread.get("model")),
        metadata=dict(thread),
    )


def _codex_sandbox(mode: PermissionMode) -> str:
    # thread/start's legacy ``sandbox`` field uses CLI config spellings. The
    # structured ``sandboxPolicy.type`` field uses readOnly/workspaceWrite,
    # but sending those values here fails on Codex CLI 0.149.
    return {
        PermissionMode.READ_ONLY: "read-only",
        PermissionMode.WORKSPACE_WRITE: "workspace-write",
        PermissionMode.FULL_ACCESS: "danger-full-access",
    }[mode]


def _codex_effort(profile: str | None) -> str | None:
    """Translate provider-neutral profiles while preserving explicit provider efforts."""
    return {
        "economy": "low",
        "balanced": "medium",
        "frontier": "high",
    }.get(profile, profile)


_THREAD_RESUME_FIELDS = frozenset(
    {
        "approvalPolicy",
        "cwd",
        "model",
        "modelProvider",
        "personality",
        "sandbox",
        "serviceTier",
    }
)
_THREAD_FORK_FIELDS = _THREAD_RESUME_FIELDS | {"ephemeral", "lastTurnId"}


def _copy_codex_fields(
    target: dict[str, Any],
    source: Mapping[str, Any] | None,
    allowed: frozenset[str],
) -> None:
    if source is not None:
        target.update((key, value) for key, value in source.items() if key in allowed)


def _reasoning_effort(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return _string(value.get("reasoningEffort"))
    return None


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _nested_string(data: Mapping[str, Any], key: str, nested: str) -> str | None:
    value = data.get(key)
    return _string(value.get(nested)) if isinstance(value, Mapping) else None


def _usage_from_payload(payload: Mapping[str, Any]) -> Usage | None:
    raw = payload.get("usage") or payload.get("tokenUsage")
    if raw is None and isinstance(payload.get("turn"), Mapping):
        turn = payload["turn"]
        raw = turn.get("usage") or turn.get("tokenUsage")
    if not isinstance(raw, Mapping):
        return None
    breakdown = raw.get("total", raw)
    if not isinstance(breakdown, Mapping):
        return None
    last = raw.get("last")
    context_tokens = None
    if isinstance(last, Mapping):
        context_tokens = _optional_token(last, "totalTokens")
    return Usage(
        input_tokens=_token(breakdown, "input_tokens", "inputTokens"),
        output_tokens=_token(breakdown, "output_tokens", "outputTokens"),
        cache_read_tokens=_token(breakdown, "cache_read_tokens", "cachedInputTokens"),
        cache_write_tokens=_token(
            breakdown, "cache_write_tokens", "cacheWriteInputTokens", "cacheWriteTokens"
        ),
        cost_usd=_number(breakdown.get("cost_usd", breakdown.get("costUsd"))),
        context_tokens=context_tokens or _optional_token(
            breakdown, "context_tokens", "contextTokens"
        ),
        context_limit=_optional_token(
            raw, "modelContextWindow", "context_limit", "contextLimit"
        ),
        context_health=_context_health(
            breakdown.get("context_health", breakdown.get("contextHealth"))
        ),
        raw=dict(raw),
    )


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
