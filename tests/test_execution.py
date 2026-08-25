from __future__ import annotations

from collections.abc import AsyncIterator
import asyncio
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.adapters.base import AgentProviderAdapter, ContextHealth, ModelInfo, PermissionMode, ProviderCapabilities, SessionRef, StreamEvent, Usage
from skiphow.execution import CampaignExecutor
from skiphow.model_routing import ModelCandidate, RouteDecision, SemanticProfile
from skiphow.runner import DurableRunner
from skiphow.schemas import TaskStatus


class FakeProvider(AgentProviderAdapter):
    started: str = ""
    cleaned: list[str]

    def __init__(self) -> None:
        self.cleaned = []
        self.context_health = ContextHealth.UNKNOWN
        self.compactions = 0

    async def discover_capabilities(self): return ProviderCapabilities("fake", frozenset())
    async def list_models(self): return [ModelInfo("fake", "local")]
    async def start_session(self, input: str, *, cwd: Path, permissions: PermissionMode, model_profile: str | None = None, model_id: str | None = None, budget_usd: float | None = None):
        self.started = input
        return SessionRef("fake", "session-1", model_id=model_id)
    async def resume_session(self, session_id: str, *, checkpoint=None): return SessionRef("fake", session_id)
    async def fork_session(self, session_id: str, *, checkpoint=None): return SessionRef("fake", "fork")
    async def send_turn(self, session_id: str, input: str): return SessionRef("fake", session_id)
    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        yield StreamEvent("fake", session_id, "progress", {})
        yield StreamEvent("fake", session_id, "result", {"ok": True})
    async def interrupt(self, session_id: str): return None
    async def compact(self, session_id: str): self.compactions += 1
    async def usage(self, session_id: str): return Usage(context_health=self.context_health)
    async def cleanup(self, session_id: str): self.cleaned.append(session_id)


class BlockingProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__()
        self.release = asyncio.Event()
        self.started_sessions: list[str] = []

    async def start_session(self, input: str, *, cwd: Path, permissions: PermissionMode, model_profile: str | None = None, model_id: str | None = None, budget_usd: float | None = None):
        session_id = f"session-{len(self.started_sessions) + 1}"
        self.started_sessions.append(session_id)
        return SessionRef("fake", session_id, model_id=model_id)

    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        await self.release.wait()
        yield StreamEvent("fake", session_id, "result", {"ok": True})


def test_executor_binds_claim_provider_checkpoint_and_verifier(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "run.sqlite3")
    run = runner.start("Ship the requested outcome", {"local_mutation": True}, run_id="run")
    runner.add_task(run.run_id, "Implement slice", task_id="task")
    candidate = ModelCandidate("fake", "local", "v1", SemanticProfile.BALANCED, 10000)
    route = RouteDecision(candidate, SemanticProfile.BALANCED, "balanced: test", 0.0, None)
    provider = FakeProvider()
    result = asyncio.run(
        CampaignExecutor(runner, provider, cwd=tmp_path).execute_frontier(
            run.run_id, "worker", route, lambda events: events[-1].kind == "result"
        )
    )
    assert result[0]["status"] == "DONE"
    assert runner.status(run.run_id)["status"] == "COMPLETED"
    assert "Immutable outcome: Ship the requested outcome" in provider.started
    assert provider.cleaned == ["session-1"]
    export = runner.store.export_run(run.run_id)
    assert {item["reason"] for item in export["checkpoints"]} >= {
        "before_provider_dispatch", "after_verification"
    }


def test_executor_checkpoints_once_before_provider_compaction(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "run.sqlite3")
    run = runner.start("Keep the outcome", {}, run_id="run")
    runner.add_task(run.run_id, "Long task", task_id="task")
    candidate = ModelCandidate("fake", "local", "v1", SemanticProfile.BALANCED, 10000)
    route = RouteDecision(candidate, SemanticProfile.BALANCED, "balanced: test", 0.0, None)
    provider = FakeProvider()
    provider.context_health = ContextHealth.APPROACHING_LIMIT
    asyncio.run(
        CampaignExecutor(runner, provider, cwd=tmp_path).execute_frontier(
            run.run_id, "worker", route, lambda events: True
        )
    )
    assert provider.compactions == 1
    reasons = {item["reason"] for item in runner.store.export_run(run.run_id)["checkpoints"]}
    assert "before_compaction" in reasons


def test_executor_renews_leases_and_starts_claimed_tasks_concurrently(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "run.sqlite3", parallelism=2)
    run = runner.start("Ship both slices", {}, run_id="run")
    runner.add_task(run.run_id, "First slice", task_id="first")
    runner.add_task(run.run_id, "Second slice", task_id="second")
    candidate = ModelCandidate("fake", "local", "v1", SemanticProfile.BALANCED, 10000)
    route = RouteDecision(candidate, SemanticProfile.BALANCED, "balanced: test", 0.0, None)
    provider = BlockingProvider()

    async def exercise() -> list[dict[str, object]]:
        execution = asyncio.create_task(
            CampaignExecutor(runner, provider, cwd=tmp_path).execute_frontier(
                run.run_id, "worker", route, lambda events: True,
                lease_seconds=0.2,
            )
        )
        for _ in range(100):
            if len(provider.started_sessions) == 2:
                break
            await asyncio.sleep(0.001)
        assert len(provider.started_sessions) == 2
        await asyncio.sleep(0.3)
        assert DurableRunner(tmp_path / "run.sqlite3", parallelism=2).frontier(
            run.run_id, "duplicate", lease_seconds=1
        ) == []
        provider.release.set()
        return await execution

    results = asyncio.run(exercise())

    assert {item["status"] for item in results} == {"DONE"}


def test_verifier_exception_requeues_task_instead_of_stranding_verification(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "run.sqlite3")
    run = runner.start("Recover verifier", {}, run_id="run")
    runner.add_task(run.run_id, "Verify slice", task_id="task")
    candidate = ModelCandidate("fake", "local", "v1", SemanticProfile.BALANCED, 10000)
    route = RouteDecision(candidate, SemanticProfile.BALANCED, "balanced: test", 0.0, None)

    def broken_verifier(events):
        raise RuntimeError("verifier crashed")

    with pytest.raises(RuntimeError, match="verifier crashed"):
        asyncio.run(
            CampaignExecutor(runner, FakeProvider(), cwd=tmp_path).execute_frontier(
                run.run_id, "worker", route, broken_verifier
            )
        )

    task = runner.store.get_task("task")
    assert task.status == TaskStatus.READY
    assert task.failure_signature == "provider:RuntimeError"
