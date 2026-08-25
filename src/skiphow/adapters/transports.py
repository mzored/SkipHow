"""Optional subprocess transports for the built-in provider adapters."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from importlib import import_module
from importlib.util import find_spec
import json
from pathlib import Path
import signal
from typing import Any

from .base import ProviderError


_END = object()
_ERROR = object()


class CodexAppServerTransport:
    """Newline-delimited JSON-RPC client for ``codex app-server``."""

    def __init__(self, process: asyncio.subprocess.Process) -> None:
        if process.stdin is None or process.stdout is None:
            raise ProviderError("Codex app-server requires piped stdin and stdout")
        self._process = process
        self._stdin = process.stdin
        self._stdout = process.stdout
        self._next_id = 1
        self._pending: dict[int, asyncio.Future[Mapping[str, Any]]] = {}
        self._queues: dict[str, asyncio.Queue[object]] = {}
        self._reader_task = asyncio.create_task(self._read_messages())

    @classmethod
    async def launch(
        cls,
        command: Sequence[str] = ("codex", "app-server"),
        *,
        client_name: str = "skiphow",
        client_version: str = "0",
    ) -> "CodexAppServerTransport":
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        transport = cls(process)
        await transport.request(
            "initialize",
            {
                "clientInfo": {
                    "name": client_name,
                    "title": "SkipHow",
                    "version": client_version,
                }
            },
        )
        await transport._notify("initialized", {})
        return transport

    async def request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        if self._process.returncode is not None:
            raise ProviderError(f"Codex app-server exited with {self._process.returncode}")
        request_id = self._next_id
        self._next_id += 1
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        await self._write({"method": method, "id": request_id, "params": dict(params)})
        try:
            return await future
        finally:
            self._pending.pop(request_id, None)

    async def _notify(self, method: str, params: Mapping[str, Any]) -> None:
        await self._write({"method": method, "params": dict(params)})

    async def _write(self, message: Mapping[str, Any]) -> None:
        self._stdin.write((json.dumps(message, separators=(",", ":")) + "\n").encode())
        await self._stdin.drain()

    async def _read_messages(self) -> None:
        try:
            while line := await self._stdout.readline():
                try:
                    message = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if not isinstance(message, Mapping):
                    continue
                request_id = message.get("id")
                method = message.get("method")
                if isinstance(request_id, int) and isinstance(method, str):
                    await self._write(
                        {
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"SkipHow does not handle server request {method}",
                            },
                        }
                    )
                    continue
                if isinstance(request_id, int) and request_id in self._pending:
                    future = self._pending[request_id]
                    error = message.get("error")
                    if isinstance(error, Mapping):
                        future.set_exception(
                            ProviderError(str(error.get("message", "Codex request failed")))
                        )
                    else:
                        result = message.get("result", {})
                        future.set_result(
                            result if isinstance(result, Mapping) else {"value": result}
                        )
                    continue
                session_id = _codex_notification_session(message)
                if session_id is not None:
                    await self._queue(session_id).put(message)
                else:
                    for queue in tuple(self._queues.values()):
                        await queue.put(message)
        finally:
            error = ProviderError("Codex app-server connection closed")
            for future in tuple(self._pending.values()):
                if not future.done():
                    future.set_exception(error)
            for queue in tuple(self._queues.values()):
                await queue.put(_END)

    def _queue(self, session_id: str) -> asyncio.Queue[object]:
        return self._queues.setdefault(session_id, asyncio.Queue())

    async def notifications(self, session_id: str) -> AsyncIterator[Mapping[str, Any]]:
        queue = self._queue(session_id)
        while True:
            message = await queue.get()
            if message is _END:
                return
            if isinstance(message, Mapping):
                yield message

    async def close_session(self, session_id: str) -> None:
        queue = self._queues.pop(session_id, None)
        if queue is not None:
            await queue.put(_END)

    async def aclose(self) -> None:
        if self._process.returncode is None:
            self._process.terminate()
            await self._process.wait()
        await self._reader_task


class ClaudeCliTransport:
    """Structured ``claude -p`` fallback.

    Each turn starts a bounded print-mode process. Resume and fork retain the
    provider transcript. Interrupt terminates the active process and therefore
    has weaker semantics than Agent SDK ``Query.interrupt()``.
    """

    interrupt_mode = "process-terminate"
    compact_hooks: tuple[str, ...] = ()
    supports_compact_hooks = False

    def __init__(self, command: Sequence[str] = ("claude",)) -> None:
        self._command = tuple(command)
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._queues: dict[str, asyncio.Queue[object]] = {}
        self._tasks: set[asyncio.Task[None]] = set()
        self._options: dict[str, dict[str, Any]] = {}

    async def start(self, options: Mapping[str, Any], prompt: str) -> Mapping[str, Any]:
        result = await self._launch(prompt, options=options)
        self._remember_options(result, options)
        return result

    async def resume(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        merged = {**self._options.get(session_id, {}), **options}
        self._options[session_id] = merged
        return {"session_id": session_id}

    async def fork(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        merged = {**self._options.get(session_id, {}), **options}
        result = await self._launch("", options=merged, resume=session_id, fork=True)
        self._remember_options(result, merged)
        return result

    async def send(self, session_id: str, prompt: str) -> Mapping[str, Any]:
        return await self._launch(
            prompt, options=self._options.get(session_id, {}), resume=session_id
        )

    async def compact(self, session_id: str) -> None:
        process = self._processes.get(session_id)
        if process is not None and process.returncode is None:
            await process.wait()
        await self._launch(
            "/compact", options=self._options.get(session_id, {}), resume=session_id
        )

    def _remember_options(
        self, result: Mapping[str, Any], options: Mapping[str, Any]
    ) -> None:
        session_id = result.get("session_id", result.get("sessionId"))
        if isinstance(session_id, str):
            self._options[session_id] = dict(options)

    async def _launch(
        self,
        prompt: str,
        *,
        options: Mapping[str, Any],
        resume: str | None = None,
        fork: bool = False,
    ) -> Mapping[str, Any]:
        args = [
            *self._command,
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--include-hook-events",
            "--safe-mode",
            "--disable-slash-commands",
            "--no-chrome",
            "--strict-mcp-config",
            "--mcp-config",
            "{}",
            "--disallowedTools",
            "WebFetch,WebSearch",
            "--settings",
            _claude_sandbox_settings(),
        ]
        if resume is not None:
            args.extend(("--resume", resume))
        if fork:
            args.append("--fork-session")
        model = options.get("model")
        if isinstance(model, str):
            args.extend(("--model", model))
        effort = options.get("profile")
        if isinstance(effort, str):
            effort = {
                "economy": "low",
                "balanced": "medium",
                "frontier": "high",
            }.get(effort, effort)
            args.extend(("--effort", effort))
        permission = options.get("permission_mode")
        if isinstance(permission, str):
            args.extend(("--permission-mode", permission))
        budget = options.get("max_budget_usd")
        if isinstance(budget, (int, float)) and not isinstance(budget, bool):
            args.extend(("--max-budget-usd", str(budget)))
        args.append(prompt)
        cwd = options.get("cwd")
        ready: asyncio.Future[Mapping[str, Any]] = asyncio.get_running_loop().create_future()
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(cwd) if isinstance(cwd, (str, Path)) else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        task = asyncio.create_task(self._pump(process, ready, expected_session=resume))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return await ready

    async def _pump(
        self,
        process: asyncio.subprocess.Process,
        ready: asyncio.Future[Mapping[str, Any]],
        *,
        expected_session: str | None,
    ) -> None:
        assert process.stdout is not None
        actual_session = expected_session
        buffered: list[Mapping[str, Any]] = []
        while line := await process.stdout.readline():
            try:
                message = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(message, Mapping):
                continue
            candidate = message.get("session_id", message.get("sessionId"))
            if isinstance(candidate, str):
                actual_session = candidate
            if actual_session is None:
                buffered.append(message)
                continue
            queue = self._queues.setdefault(actual_session, asyncio.Queue())
            if not ready.done():
                self._processes[actual_session] = process
                ready.set_result(
                    {
                        "session_id": actual_session,
                        "message_id": message.get("uuid", message.get("message_id")),
                    }
                )
                for earlier in buffered:
                    await queue.put(earlier)
                buffered.clear()
            await queue.put(message)
        returncode = await process.wait()
        if actual_session is not None:
            await self._queues.setdefault(actual_session, asyncio.Queue()).put(_END)
            self._processes.pop(actual_session, None)
        if not ready.done():
            ready.set_exception(
                ProviderError(
                    f"Claude CLI exited with {returncode} before reporting a session id"
                )
            )

    async def messages(self, session_id: str) -> AsyncIterator[Mapping[str, Any]]:
        queue = self._queues.setdefault(session_id, asyncio.Queue())
        while True:
            message = await queue.get()
            if message is _END:
                return
            if isinstance(message, Mapping):
                yield message

    async def interrupt(self, session_id: str) -> None:
        process = self._processes.get(session_id)
        if process is None or process.returncode is not None:
            raise ProviderError(f"no active Claude CLI process for session {session_id}")
        if hasattr(signal, "SIGINT"):
            process.send_signal(signal.SIGINT)
        else:
            process.terminate()

    async def close(self, session_id: str) -> None:
        process = self._processes.pop(session_id, None)
        if process is not None and process.returncode is None:
            process.terminate()
            await process.wait()
        queue = self._queues.pop(session_id, None)
        if queue is not None:
            await queue.put(_END)
        self._options.pop(session_id, None)


class ClaudeAgentSdkTransport:
    """Optional persistent transport backed by ``claude-agent-sdk``."""

    interrupt_mode = "typed"
    compact_hooks = ("PreCompact",)
    supports_compact_hooks = True

    def __init__(self, sdk: Any | None = None) -> None:
        if sdk is None:
            try:
                sdk = import_module("claude_agent_sdk")
            except ImportError as exc:
                raise ProviderError("claude-agent-sdk is not installed") from exc
        required = ("ClaudeSDKClient", "ClaudeAgentOptions", "HookMatcher")
        if any(not hasattr(sdk, name) for name in required):
            raise ProviderError("installed claude-agent-sdk lacks the required client API")
        self._sdk = sdk
        self._clients: dict[str, Any] = {}
        self._queues: dict[str, asyncio.Queue[object]] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}

    @staticmethod
    def available() -> bool:
        return find_spec("claude_agent_sdk") is not None

    async def start(self, options: Mapping[str, Any], prompt: str) -> Mapping[str, Any]:
        return await self._open(options, prompt)

    async def resume(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if session_id in self._clients:
            return {"session_id": session_id}
        client = self._new_client(options, resume=session_id)
        await client.connect()
        self._clients[session_id] = client
        self._queue(session_id)
        return {"session_id": session_id}

    async def fork(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return await self._open(options, "", resume=session_id, fork=True)

    async def send(self, session_id: str, prompt: str) -> Mapping[str, Any]:
        client = self._clients.get(session_id)
        if client is None:
            raise ProviderError(f"Claude SDK session is not connected: {session_id}")
        await self._wait_turn(session_id)
        await client.query(prompt)
        return await self._start_pump(client, expected_session=session_id)

    async def compact(self, session_id: str) -> None:
        client = self._clients.get(session_id)
        if client is None:
            raise ProviderError(f"Claude SDK session is not connected: {session_id}")
        await self._wait_turn(session_id)
        await client.query("/compact")
        await self._start_pump(client, expected_session=session_id)
        await self._wait_turn(session_id)

    async def messages(self, session_id: str) -> AsyncIterator[Mapping[str, Any]]:
        queue = self._queue(session_id)
        while True:
            message = await queue.get()
            if message is _END:
                return
            if isinstance(message, tuple) and len(message) == 2 and message[0] is _ERROR:
                raise ProviderError(str(message[1]))
            if isinstance(message, Mapping):
                yield message

    async def interrupt(self, session_id: str) -> None:
        client = self._clients.get(session_id)
        if client is None:
            raise ProviderError(f"no active Claude SDK client for session {session_id}")
        await client.interrupt()

    async def close(self, session_id: str) -> None:
        task = self._tasks.pop(session_id, None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        client = self._clients.pop(session_id, None)
        if client is not None:
            await client.disconnect()
        queue = self._queues.pop(session_id, None)
        if queue is not None:
            await queue.put(_END)

    async def _open(
        self,
        options: Mapping[str, Any],
        prompt: str,
        *,
        resume: str | None = None,
        fork: bool = False,
    ) -> Mapping[str, Any]:
        client = self._new_client(options, resume=resume, fork=fork)
        await client.connect()
        await client.query(prompt)
        try:
            return await self._start_pump(
                client,
                expected_session=None if fork else resume,
            )
        except BaseException:
            await client.disconnect()
            raise

    def _new_client(
        self,
        options: Mapping[str, Any],
        *,
        resume: str | None = None,
        fork: bool = False,
    ) -> Any:
        sdk_options: dict[str, Any] = {
            "disallowed_tools": ["WebFetch", "WebSearch"],
            "include_partial_messages": True,
            "include_hook_events": True,
            "mcp_servers": {},
            "plugins": [],
            "setting_sources": [],
            "settings": _claude_sandbox_settings(),
            "skills": [],
            "strict_mcp_config": True,
            "hooks": {
                "PreCompact": [
                    self._sdk.HookMatcher(hooks=[self._pre_compact_hook])
                ]
            },
        }
        for source in ("cwd", "permission_mode", "model", "max_budget_usd"):
            value = options.get(source)
            if value is not None:
                sdk_options[source] = value
        effort = options.get("profile")
        if isinstance(effort, str):
            sdk_options["effort"] = _claude_effort(effort)
        if resume is not None:
            sdk_options["resume"] = resume
        if fork:
            sdk_options["fork_session"] = True
        return self._sdk.ClaudeSDKClient(
            options=self._sdk.ClaudeAgentOptions(**sdk_options)
        )

    async def _pre_compact_hook(
        self,
        input_data: Mapping[str, Any],
        tool_use_id: str | None,
        context: Any,
    ) -> Mapping[str, Any]:
        del tool_use_id, context
        session_id = input_data.get("session_id")
        if isinstance(session_id, str):
            await self._queue(session_id).put(
                {
                    "type": "compact_hook",
                    "phase": "pre",
                    "session_id": session_id,
                    "trigger": input_data.get("trigger"),
                }
            )
        return {}

    async def _start_pump(
        self, client: Any, *, expected_session: str | None
    ) -> Mapping[str, Any]:
        ready: asyncio.Future[Mapping[str, Any]] = asyncio.get_running_loop().create_future()
        task = asyncio.create_task(
            self._pump(client, ready, expected_session=expected_session)
        )
        if expected_session is not None:
            self._tasks[expected_session] = task
        return await ready

    async def _pump(
        self,
        client: Any,
        ready: asyncio.Future[Mapping[str, Any]],
        *,
        expected_session: str | None,
    ) -> None:
        actual_session = expected_session
        try:
            async for sdk_message in client.receive_response():
                message = _sdk_message(sdk_message)
                candidate = _claude_session_id(message)
                if candidate is not None:
                    actual_session = candidate
                if actual_session is None:
                    continue
                self._clients[actual_session] = client
                current = asyncio.current_task()
                if current is not None:
                    self._tasks[actual_session] = current
                if not ready.done():
                    ready.set_result(
                        {
                            "session_id": actual_session,
                            "message_id": message.get("uuid", message.get("message_id")),
                        }
                    )
                await self._queue(actual_session).put(message)
        except BaseException as exc:
            if not ready.done():
                ready.set_exception(exc)
            elif actual_session is not None:
                await self._queue(actual_session).put((_ERROR, exc))
        finally:
            if actual_session is not None:
                await self._queue(actual_session).put(_END)
            if not ready.done():
                ready.set_exception(
                    ProviderError("Claude Agent SDK ended before reporting a session id")
                )

    async def _wait_turn(self, session_id: str) -> None:
        task = self._tasks.get(session_id)
        if task is not None and task is not asyncio.current_task():
            await task

    def _queue(self, session_id: str) -> asyncio.Queue[object]:
        return self._queues.setdefault(session_id, asyncio.Queue())


def create_claude_transport(
    command: Sequence[str] = ("claude",),
) -> ClaudeAgentSdkTransport | ClaudeCliTransport:
    """Prefer the installed Agent SDK and otherwise use structured CLI mode."""
    if ClaudeAgentSdkTransport.available():
        try:
            return ClaudeAgentSdkTransport()
        except ProviderError:
            pass
    return ClaudeCliTransport(command)


def _claude_effort(profile: str) -> str:
    return {
        "economy": "low",
        "balanced": "medium",
        "frontier": "high",
    }.get(profile, profile)


def _sdk_message(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        result = dict(value)
    elif is_dataclass(value):
        result = asdict(value)
    elif hasattr(value, "__dict__"):
        result = dict(vars(value))
    else:
        return {"type": type(value).__name__, "value": repr(value)}
    result.setdefault(
        "type",
        {
            "ResultMessage": "result",
            "SystemMessage": "system",
            "AssistantMessage": "assistant",
            "UserMessage": "user",
            "StreamEvent": "stream_event",
            "RateLimitEvent": "rate_limit_event",
            "ConversationResetMessage": "conversation_reset",
        }.get(type(value).__name__, type(value).__name__),
    )
    data = result.get("data")
    if result["type"] == "system" and isinstance(data, Mapping):
        for key, item in data.items():
            result.setdefault(key, item)
    return result


def _claude_session_id(message: Mapping[str, Any]) -> str | None:
    value = message.get("session_id", message.get("sessionId"))
    return value if isinstance(value, str) and value else None


def _codex_notification_session(message: Mapping[str, Any]) -> str | None:
    params = message.get("params")
    if not isinstance(params, Mapping):
        return None
    direct = params.get("threadId", params.get("sessionId"))
    if isinstance(direct, str):
        return direct
    thread = params.get("thread")
    if isinstance(thread, Mapping) and isinstance(thread.get("id"), str):
        return str(thread["id"])
    return None


def _claude_sandbox_settings() -> str:
    """Return a fail-closed sandbox overlay for unattended CLI workers."""
    return json.dumps(
        {
            "sandbox": {
                "enabled": True,
                "failIfUnavailable": True,
                "autoAllowBashIfSandboxed": False,
                "allowUnsandboxedCommands": False,
                "network": {"allowedDomains": []},
            }
        },
        sort_keys=True,
        separators=(",", ":"),
    )
