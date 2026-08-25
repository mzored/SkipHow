"""Provider-neutral conformance tests without calling a model or provider CLI."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.adapters import (  # noqa: E402
    AgentProviderAdapter,
    Capability,
    ClaudeAdapter,
    CodexAdapter,
    ModelInfo,
    PermissionMode,
    ProviderError,
)
from skiphow.adapters.transports import ClaudeCliTransport, CodexAppServerTransport  # noqa: E402


class FakeCodexTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Any]]] = []
        self.closed: list[str] = []

    async def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append((method, params))
        if method == "model/list":
            return {
                "data": [
                    {
                        "id": "configured-at-runtime",
                        "contextWindow": 64000,
                        "supportedReasoningEfforts": [
                            {"reasoningEffort": "medium", "description": "Balanced"}
                        ],
                    }
                ]
            }
        if method == "thread/start":
            return {"thread": {"id": "codex-new"}}
        if method == "thread/resume":
            return {"thread": {"id": params["threadId"]}}
        if method == "thread/fork":
            return {"thread": {"id": "codex-fork"}}
        if method == "turn/start":
            return {"turn": {"id": "codex-turn"}}
        return {}

    async def notifications(self, session_id: str) -> AsyncIterator[Mapping[str, Any]]:
        yield {
            "method": "item/agentMessage/delta",
            "params": {"turnId": "codex-turn", "delta": "hello"},
        }
        yield {
            "method": "thread/tokenUsage/updated",
            "params": {
                "threadId": session_id,
                "turnId": "codex-turn",
                "tokenUsage": {
                    "total": {
                        "inputTokens": 11,
                        "outputTokens": 7,
                        "cachedInputTokens": 3,
                        "cacheWriteInputTokens": 2,
                    },
                    "last": {"totalTokens": 18},
                    "modelContextWindow": 64000,
                },
            },
        }
        yield {
            "method": "turn/completed",
            "params": {
                "turn": {"id": "codex-turn"},
            },
        }

    async def close_session(self, session_id: str) -> None:
        self.closed.append(session_id)


class FakeClaudeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.closed: list[str] = []

    async def list_models(self) -> list[Mapping[str, Any]]:
        return [{"id": "configured-at-runtime", "context_limit": 64000}]

    async def start(self, options: Mapping[str, Any], prompt: str) -> Mapping[str, Any]:
        self.calls.append(("start", {"options": options, "prompt": prompt}))
        return {"session_id": "claude-new", "message_id": "claude-turn"}

    async def resume(self, session_id: str, options: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(("resume", {"session_id": session_id, "options": options}))
        return {"session_id": session_id}

    async def fork(self, session_id: str, options: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(("fork", {"session_id": session_id, "options": options}))
        return {"session_id": "claude-fork"}

    async def send(self, session_id: str, prompt: str) -> Mapping[str, Any]:
        self.calls.append(("send", {"session_id": session_id, "prompt": prompt}))
        return {"message_id": "claude-turn"}

    async def messages(self, session_id: str) -> AsyncIterator[Mapping[str, Any]]:
        yield {
            "type": "stream_event",
            "message_id": "claude-turn",
            "parent_tool_use_id": "subagent-tool",
        }
        yield {
            "type": "result",
            "usage": {"input_tokens": 11, "output_tokens": 7},
            "total_cost_usd": 0.03,
        }

    async def interrupt(self, session_id: str) -> None:
        self.calls.append(("interrupt", session_id))

    async def compact(self, session_id: str) -> None:
        self.calls.append(("compact", session_id))

    async def close(self, session_id: str) -> None:
        self.closed.append(session_id)


def make_adapter(provider: str) -> tuple[AgentProviderAdapter, Any]:
    if provider == "codex":
        transport = FakeCodexTransport()
        return CodexAdapter(transport), transport
    transport = FakeClaudeTransport()
    return ClaudeAdapter(transport), transport


@pytest.mark.parametrize("provider", ("codex", "claude"))
def test_provider_adapter_conformance(provider: str, tmp_path: Path) -> None:
    async def scenario() -> None:
        adapter, transport = make_adapter(provider)

        capabilities = await adapter.discover_capabilities()
        required = {
            Capability.START,
            Capability.RESUME,
            Capability.FORK,
            Capability.SEND,
            Capability.STREAM,
            Capability.INTERRUPT,
            Capability.COMPACT,
            Capability.USAGE,
            Capability.CLEANUP,
        }
        assert required <= capabilities.supported

        models = await adapter.list_models()
        assert [model.model_id for model in models] == ["configured-at-runtime"]
        if provider == "codex":
            assert models[0].profiles == ("medium",)
            assert models[0].capabilities == frozenset({"text", "image"})

        session = await adapter.start_session(
            "implement the task",
            cwd=tmp_path,
            permissions=PermissionMode.WORKSPACE_WRITE,
            model_profile="medium",
            model_id=models[0].model_id,
            budget_usd=1.25,
        )
        assert session.provider == provider
        assert session.session_id == f"{provider}-new"
        if provider == "codex":
            assert transport.calls[-2] == (
                "thread/start",
                {
                    "cwd": str(tmp_path),
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "model": "configured-at-runtime",
                },
            )
            assert transport.calls[-1][0] == "turn/start"
            assert transport.calls[-1][1]["effort"] == "medium"

        resumed = await adapter.resume_session(
            session.session_id, checkpoint={"checkpoint": "opaque"}
        )
        assert resumed.session_id == session.session_id
        if provider == "codex":
            assert transport.calls[-1] == (
                "thread/resume",
                {"threadId": session.session_id},
            )

        forked = await adapter.fork_session(
            session.session_id, checkpoint={"lastTurnId": session.turn_id}
        )
        assert forked.parent_session_id == session.session_id
        assert forked.session_id == f"{provider}-fork"

        turn = await adapter.send_turn(session.session_id, "verify it")
        assert turn.turn_id == f"{provider}-turn"

        events = [event async for event in adapter.stream_events(session.session_id)]
        assert events
        assert all(event.provider == provider for event in events)
        assert all(event.session_id == session.session_id for event in events)
        usage = await adapter.usage(session.session_id)
        assert usage.input_tokens == 11
        assert usage.output_tokens == 7
        if provider == "codex":
            assert usage.cache_read_tokens == 3
            assert usage.cache_write_tokens == 2
            assert usage.context_tokens == 18
            assert usage.context_limit == 64000

        await adapter.interrupt(session.session_id)
        await adapter.compact(session.session_id)
        await adapter.cleanup(session.session_id)
        assert transport.closed == [session.session_id]
        if provider == "codex":
            assert transport.calls[-3:] == [
                (
                    "turn/interrupt",
                    {"threadId": session.session_id, "turnId": "codex-turn"},
                ),
                ("thread/compact/start", {"threadId": session.session_id}),
                ("thread/unsubscribe", {"threadId": session.session_id}),
            ]

    asyncio.run(scenario())


def test_configured_catalog_is_used_when_discovery_is_unavailable() -> None:
    class OfflineCodex(FakeCodexTransport):
        async def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
            if method == "model/list":
                raise OSError("not installed")
            return await super().request(method, params)

    configured = ModelInfo(provider="codex", model_id="from-user-config")
    adapter = CodexAdapter(OfflineCodex(), configured_models=[configured])
    assert asyncio.run(adapter.list_models()) == (configured,)


@pytest.mark.parametrize(
    ("permission", "sandbox"),
    (
        (PermissionMode.READ_ONLY, "read-only"),
        (PermissionMode.WORKSPACE_WRITE, "workspace-write"),
        (PermissionMode.FULL_ACCESS, "danger-full-access"),
    ),
)
def test_codex_uses_app_server_sandbox_values(
    permission: PermissionMode, sandbox: str, tmp_path: Path
) -> None:
    async def scenario() -> None:
        transport = FakeCodexTransport()
        adapter = CodexAdapter(transport)
        await adapter.start_session("task", cwd=tmp_path, permissions=permission)
        assert transport.calls[0] == (
            "thread/start",
            {
                "cwd": str(tmp_path),
                "approvalPolicy": "never",
                "sandbox": sandbox,
            },
        )

    asyncio.run(scenario())


def test_invalid_provider_response_is_rejected() -> None:
    class BrokenClaude(FakeClaudeTransport):
        async def start(self, options: Mapping[str, Any], prompt: str) -> Mapping[str, Any]:
            return {}

    adapter = ClaudeAdapter(BrokenClaude())
    with pytest.raises(ProviderError, match="no session id"):
        asyncio.run(
            adapter.start_session(
                "task",
                cwd=ROOT,
                permissions=PermissionMode.READ_ONLY,
            )
        )


def test_concrete_codex_subprocess_transport() -> None:
    async def scenario() -> None:
        transport = await CodexAppServerTransport.launch(
            [sys.executable, str(ROOT / "tests/fixtures/fake_provider_process.py"), "codex"]
        )
        adapter = CodexAdapter(transport)
        models = await adapter.list_models()
        assert [model.model_id for model in models] == ["fixture-model"]
        session = await adapter.start_session(
            "test",
            cwd=ROOT,
            permissions=PermissionMode.READ_ONLY,
        )
        events = [event async for event in adapter.stream_events(session.session_id)]
        assert events[-1].kind == "turn/completed"
        assert (await adapter.usage(session.session_id)).total_tokens == 3
        await transport.aclose()

    asyncio.run(scenario())


def test_codex_transport_rejects_unhandled_server_requests() -> None:
    async def scenario() -> None:
        transport = await CodexAppServerTransport.launch(
            [
                sys.executable,
                str(ROOT / "tests/fixtures/fake_provider_process.py"),
                "codex-request",
            ]
        )
        adapter = CodexAdapter(transport)
        session = await adapter.start_session(
            "test",
            cwd=ROOT,
            permissions=PermissionMode.READ_ONLY,
        )
        events = [event async for event in adapter.stream_events(session.session_id)]
        assert events[-1].kind == "turn/completed"
        await transport.aclose()

    asyncio.run(scenario())


def test_concrete_claude_cli_transport() -> None:
    async def scenario() -> None:
        transport = ClaudeCliTransport(
            [sys.executable, str(ROOT / "tests/fixtures/fake_provider_process.py"), "claude"]
        )
        adapter = ClaudeAdapter(transport)
        session = await adapter.start_session(
            "test",
            cwd=ROOT,
            permissions=PermissionMode.READ_ONLY,
            model_profile="high",
        )
        assert session.session_id == "fixture-session"
        events = [event async for event in adapter.stream_events(session.session_id)]
        system = next(event for event in events if event.kind == "system")
        effort_index = system.data["argv"].index("--effort")
        assert system.data["argv"][effort_index + 1] == "high"
        assert events[-1].kind == "result"
        assert (await adapter.usage(session.session_id)).total_tokens == 3

    asyncio.run(scenario())
