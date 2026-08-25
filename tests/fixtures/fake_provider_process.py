#!/usr/bin/env python3
"""Local protocol fixture. It never calls a model or provider service."""

from __future__ import annotations

import json
import sys


def emit(value: object) -> None:
    print(json.dumps(value), flush=True)


def codex() -> None:
    request_mode = sys.argv[1] == "codex-request"
    for line in sys.stdin:
        request = json.loads(line)
        request_id = request.get("id")
        if request_id is None:
            continue
        method = request["method"]
        if method == "initialize":
            result = {"userAgent": "fixture"}
        elif method == "model/list":
            result = {"data": [{"id": "fixture-model"}]}
        elif method == "thread/start":
            result = {"thread": {"id": "fixture-thread"}}
        elif method == "turn/start":
            result = {"turn": {"id": "fixture-turn"}}
        else:
            result = {}
        emit({"id": request_id, "result": result})
        if method == "turn/start":
            if request_mode:
                emit(
                    {
                        "id": 99,
                        "method": "item/commandExecution/requestApproval",
                        "params": {
                            "threadId": "fixture-thread",
                            "turnId": "fixture-turn",
                        },
                    }
                )
                rejection = json.loads(next(sys.stdin))
                assert rejection["id"] == 99
                assert rejection["error"]["code"] == -32601
            emit(
                {
                    "method": "thread/tokenUsage/updated",
                    "params": {
                        "threadId": "fixture-thread",
                        "turnId": "fixture-turn",
                        "tokenUsage": {
                            "total": {
                                "inputTokens": 2,
                                "outputTokens": 1,
                                "cachedInputTokens": 0,
                                "cacheWriteInputTokens": 0,
                                "reasoningOutputTokens": 0,
                                "totalTokens": 3,
                            },
                            "last": {
                                "inputTokens": 2,
                                "outputTokens": 1,
                                "cachedInputTokens": 0,
                                "cacheWriteInputTokens": 0,
                                "reasoningOutputTokens": 0,
                                "totalTokens": 3,
                            },
                            "modelContextWindow": 1000,
                        },
                    },
                }
            )
            emit(
                {
                    "method": "turn/completed",
                    "params": {
                        "threadId": "fixture-thread",
                        "turn": {"id": "fixture-turn"},
                    },
                }
            )


def claude() -> None:
    resume = None
    if "--resume" in sys.argv:
        resume = sys.argv[sys.argv.index("--resume") + 1]
    session_id = "fixture-fork" if "--fork-session" in sys.argv else resume or "fixture-session"
    emit(
        {
            "type": "system",
            "subtype": "init",
            "session_id": session_id,
            "argv": sys.argv[2:],
        }
    )
    emit(
        {
            "type": "result",
            "session_id": session_id,
            "usage": {"input_tokens": 2, "output_tokens": 1},
        }
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"codex", "codex-request"}:
        codex()
    else:
        claude()
