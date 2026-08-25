"""Optional subprocess transports for the built-in provider adapters."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping, Sequence
import json
from pathlib import Path
import signal
from typing import Any

from .base import ProviderError


_END = object()


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

    def __init__(self, command: Sequence[str] = ("claude",)) -> None:
        self._command = tuple(command)
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._queues: dict[str, asyncio.Queue[object]] = {}
        self._tasks: set[asyncio.Task[None]] = set()

    async def start(self, options: Mapping[str, Any], prompt: str) -> Mapping[str, Any]:
        return await self._launch(prompt, options=options)

    async def resume(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return await self._launch("", options=options, resume=session_id)

    async def fork(
        self, session_id: str, options: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return await self._launch("", options=options, resume=session_id, fork=True)

    async def send(self, session_id: str, prompt: str) -> Mapping[str, Any]:
        return await self._launch(prompt, options={}, resume=session_id)

    async def compact(self, session_id: str) -> None:
        await self._launch("/compact", options={}, resume=session_id)

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
