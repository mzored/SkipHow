"""Provider-neutral conformance tests without calling a model or provider CLI."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
import json
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
    ClaudeAgentSdkTransport,
    CodexAdapter,
    ContextHealth,
    ModelInfo,
    PermissionMode,
    ProviderError,
)
from skiphow.adapters.transports import (  # noqa: E402
    ClaudeCliTransport,
    CodexAppServerTransport,
    create_claude_transport,
)
from skiphow.adapters.codex import _usage_from_payload as codex_usage  # noqa: E402


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
            assert usage.context_health is ContextHealth.HEALTHY

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


def test_codex_derives_approaching_context_limit_from_app_server_usage() -> None:
    usage = codex_usage(
        {
            "tokenUsage": {
                "total": {"inputTokens": 80, "outputTokens": 5},
                "last": {"totalTokens": 80},
                "modelContextWindow": 100,
            }
        }
    )
    assert usage is not None
    assert usage.context_health is ContextHealth.APPROACHING_LIMIT


def test_codex_fork_drops_unsupported_personality_override() -> None:
    async def scenario() -> None:
        transport = FakeCodexTransport()
        adapter = CodexAdapter(transport)
        await adapter.resume_session(
            "thread", checkpoint={"personality": "friendly"}
        )
        assert transport.calls[-1] == (
            "thread/resume",
            {"threadId": "thread", "personality": "friendly"},
        )
        await adapter.fork_session(
            "thread",
            checkpoint={"personality": "friendly", "lastTurnId": "turn"},
        )
        assert transport.calls[-1] == (
            "thread/fork",
            {"threadId": "thread", "lastTurnId": "turn"},
        )

    asyncio.run(scenario())


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
        settings_index = system.data["argv"].index("--settings")
        settings = json.loads(system.data["argv"][settings_index + 1])
        assert settings["sandbox"] == {
            "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": False,
            "enabled": True,
            "failIfUnavailable": True,
            "network": {"allowedDomains": []},
        }
        assert "--safe-mode" in system.data["argv"]
        assert "--strict-mcp-config" in system.data["argv"]
        assert events[-1].kind == "result"
        assert (await adapter.usage(session.session_id)).total_tokens == 3

    asyncio.run(scenario())


def test_claude_cli_resume_is_lazy_and_next_send_is_one_process(tmp_path: Path) -> None:
    async def scenario() -> None:
        record = tmp_path / "resume-invocations.jsonl"
        transport = ClaudeCliTransport(
            [
                sys.executable,
                str(ROOT / "tests/fixtures/fake_provider_process.py"),
                "claude-record",
                str(record),
            ]
        )
        adapter = ClaudeAdapter(transport)
        resumed = await adapter.resume_session(
            "saved-session",
            checkpoint={
                "cwd": str(tmp_path),
                "permission_mode": PermissionMode.READ_ONLY.value,
                "model": "claude-test",
                "model_profile": "frontier",
            },
        )
        assert resumed.session_id == "saved-session"
        assert not record.exists()

        await adapter.send_turn(resumed.session_id, "continue exactly once")
        _ = [event async for event in adapter.stream_events(resumed.session_id)]
        invocations = [json.loads(line) for line in record.read_text().splitlines()]
        assert len(invocations) == 1
        invocation = invocations[0]
        assert invocation["cwd"] == str(tmp_path)
        assert invocation["argv"][-1] == "continue exactly once"
        assert invocation["argv"].count("--resume") == 1
        resume_index = invocation["argv"].index("--resume")
        assert invocation["argv"][resume_index + 1] == "saved-session"
        assert invocation["argv"][invocation["argv"].index("--permission-mode") + 1] == "plan"
        assert invocation["argv"][invocation["argv"].index("--effort") + 1] == "high"
        assert invocation["argv"][invocation["argv"].index("--model") + 1] == "claude-test"

    asyncio.run(scenario())


def test_claude_cli_fork_normalizes_checkpoint_command_shape(tmp_path: Path) -> None:
    async def scenario() -> None:
        record = tmp_path / "fork-invocations.jsonl"
        transport = ClaudeCliTransport(
            [
                sys.executable,
                str(ROOT / "tests/fixtures/fake_provider_process.py"),
                "claude-record",
                str(record),
            ]
        )
        adapter = ClaudeAdapter(transport)
        forked = await adapter.fork_session(
            "saved-session",
            checkpoint={
                "cwd": str(tmp_path),
                "permission_mode": PermissionMode.READ_ONLY.value,
                "model": "claude-test",
                "model_profile": "frontier",
            },
        )
        assert forked.session_id == "fixture-fork"
        invocation = json.loads(record.read_text().strip())
        args = invocation["argv"]
        assert invocation["cwd"] == str(tmp_path)
        assert "--fork-session" in args
        assert args[args.index("--resume") + 1] == "saved-session"
        assert args[args.index("--permission-mode") + 1] == "plan"
        assert args[args.index("--effort") + 1] == "high"
        assert args[args.index("--model") + 1] == "claude-test"
        assert args[-1] == ""
        _ = [event async for event in adapter.stream_events(forked.session_id)]

    asyncio.run(scenario())


class FakeClaudeAgentOptions:
    def __init__(self, **values: Any) -> None:
        self.values = values


class FakeHookMatcher:
    def __init__(self, *, hooks: list[Any]) -> None:
        self.hooks = hooks


class FakeClaudeSdkClient:
    instances: list["FakeClaudeSdkClient"] = []

    def __init__(self, *, options: FakeClaudeAgentOptions) -> None:
        self.options = options
        self.responses: list[Mapping[str, Any]] = []
        self.queries: list[str] = []
        self.interrupted = False
        self.disconnected = False
        self.instances.append(self)

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        self.disconnected = True

    async def interrupt(self) -> None:
        self.interrupted = True

    async def query(self, prompt: str) -> None:
        self.queries.append(prompt)
        session_id = self.options.values.get("resume", "sdk-session")
        if self.options.values.get("fork_session"):
            session_id = "sdk-fork"
        if prompt == "/compact":
            matcher = self.options.values["hooks"]["PreCompact"][0]
            await matcher.hooks[0](
                {
                    "session_id": session_id,
                    "hook_event_name": "PreCompact",
                    "trigger": "manual",
                },
                None,
                None,
            )
        self.responses = [
            {"type": "system", "subtype": "init", "session_id": session_id},
            {
                "type": "assistant",
                "session_id": session_id,
                "message_id": "sdk-message",
                "usage": {
                    "input_tokens": 80,
                    "output_tokens": 5,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                },
            },
            {
                "type": "result",
                "session_id": session_id,
                "usage": {"input_tokens": 80, "output_tokens": 5},
                "model_usage": {"claude-test": {"contextWindow": 100}},
                "total_cost_usd": 0.01,
            },
        ]

    async def receive_response(self) -> AsyncIterator[Mapping[str, Any]]:
        for response in self.responses:
            yield response


class FakeClaudeSdk:
    ClaudeSDKClient = FakeClaudeSdkClient
    ClaudeAgentOptions = FakeClaudeAgentOptions
    HookMatcher = FakeHookMatcher


def test_claude_agent_sdk_transport_and_context_health(tmp_path: Path) -> None:
    async def scenario() -> None:
        FakeClaudeSdkClient.instances.clear()
        transport = ClaudeAgentSdkTransport(FakeClaudeSdk)
        adapter = ClaudeAdapter(transport)
        capabilities = await adapter.discover_capabilities()
        assert capabilities.has(Capability.COMPACT_HOOKS)
        assert capabilities.details["interrupt_mode"] == "typed"
        assert capabilities.details["compact_hooks"] == ("PreCompact",)

        session = await adapter.start_session(
            "task",
            cwd=tmp_path,
            permissions=PermissionMode.WORKSPACE_WRITE,
            model_profile="balanced",
            model_id="claude-test",
            budget_usd=1.5,
        )
        assert session.session_id == "sdk-session"
        client = FakeClaudeSdkClient.instances[0]
        assert client.options.values["effort"] == "medium"
        assert client.options.values["permission_mode"] == "acceptEdits"
        assert client.options.values["max_budget_usd"] == 1.5
        assert client.options.values["setting_sources"] == []
        assert client.options.values["skills"] == []
        assert client.options.values["plugins"] == []
        assert client.options.values["mcp_servers"] == {}
        assert client.options.values["strict_mcp_config"] is True
        events = [event async for event in adapter.stream_events(session.session_id)]
        assert events[-1].kind == "result"
        usage = await adapter.usage(session.session_id)
        assert usage.context_tokens == 80
        assert usage.context_limit == 100
        assert usage.context_health is ContextHealth.APPROACHING_LIMIT

        await adapter.compact(session.session_id)
        compact_events = [
            event async for event in adapter.stream_events(session.session_id)
        ]
        assert compact_events[0].kind == "compact_hook"
        assert compact_events[0].data["phase"] == "pre"
        await adapter.interrupt(session.session_id)
        assert client.interrupted
        await adapter.cleanup(session.session_id)
        assert client.disconnected

    asyncio.run(scenario())


def test_claude_sdk_resume_and_fork(tmp_path: Path) -> None:
    async def scenario() -> None:
        transport = ClaudeAgentSdkTransport(FakeClaudeSdk)
        adapter = ClaudeAdapter(transport)
        resumed = await adapter.resume_session("saved-session")
        assert resumed.session_id == "saved-session"
        turn = await adapter.send_turn(resumed.session_id, "continue")
        assert turn.session_id == "saved-session"
        _ = [event async for event in adapter.stream_events(resumed.session_id)]
        forked = await adapter.fork_session(resumed.session_id)
        assert forked.session_id == "sdk-fork"
        assert forked.parent_session_id == "saved-session"
        await adapter.cleanup(resumed.session_id)
        await adapter.cleanup(forked.session_id)

    asyncio.run(scenario())


def test_claude_transport_factory_falls_back_to_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ClaudeAgentSdkTransport, "available", staticmethod(lambda: False))
    assert isinstance(create_claude_transport(("claude-fixture",)), ClaudeCliTransport)


@pytest.mark.parametrize("provider", ("codex", "claude"))
def test_resume_reapplies_supervisor_security_context(provider: str, tmp_path: Path) -> None:
    async def scenario() -> None:
        adapter, transport = make_adapter(provider)
        await adapter.resume_session(
            f"{provider}-session",
            checkpoint={
                "cwd": str(tmp_path),
                "permission_mode": PermissionMode.READ_ONLY.value,
                "model": "configured-at-runtime",
                "model_profile": "frontier",
            },
        )
        call = transport.calls[-1]
        if provider == "codex":
            assert call == (
                "thread/resume",
                {
                    "threadId": "codex-session",
                    "cwd": str(tmp_path),
                    "model": "configured-at-runtime",
                    "sandbox": "read-only",
                },
            )
        else:
            assert call[0] == "resume"
            assert call[1]["options"] == {
                "cwd": str(tmp_path),
                "permission_mode": "plan",
                "model": "configured-at-runtime",
                "profile": "frontier",
            }

    asyncio.run(scenario())
