from __future__ import annotations

from collections.abc import AsyncIterator
import asyncio
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.adapters.base import (
    AgentProviderAdapter,
    ModelInfo,
    PermissionMode,
    ProviderCapabilities,
    SessionRef,
    StreamEvent,
    Usage,
)
from skiphow.model_routing import (
    ModelCandidate,
    RouteDecision,
    SemanticProfile,
)
from skiphow.runner import DurableRunner
from skiphow.schemas import TaskStatus
from skiphow.supervisor import CampaignSupervisor, SupervisionLimits


class FakeProvider(AgentProviderAdapter):
    def __init__(self, *, cost: float | None = 0.1) -> None:
        self.cost = cost
        self.started = 0
        self.resumed: list[str] = []
        self.sent: list[str] = []
        self.closed: list[str] = []
        self.interrupted: list[str] = []

    async def discover_capabilities(self):
        return ProviderCapabilities("fake", frozenset())

    async def list_models(self):
        return [ModelInfo("fake", "model", context_limit=10_000)]

    async def start_session(
        self,
        input: str,
        *,
        cwd: Path,
        permissions: PermissionMode,
        model_profile: str | None = None,
        model_id: str | None = None,
        budget_usd: float | None = None,
    ):
        del cwd, permissions, model_profile, budget_usd
        self.started += 1
        self.sent.append(input)
        return SessionRef("fake", f"session-{self.started}", model_id=model_id)

    async def resume_session(self, session_id: str, *, checkpoint=None):
        del checkpoint
        self.resumed.append(session_id)
        return SessionRef("fake", session_id)

    async def fork_session(self, session_id: str, *, checkpoint=None):
        del checkpoint
        return SessionRef("fake", session_id + "-fork")

    async def send_turn(self, session_id: str, input: str):
        self.sent.append(input)
        return SessionRef("fake", session_id)

    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        yield StreamEvent("fake", session_id, "progress", {})
        yield StreamEvent("fake", session_id, "result", {"ok": True})

    async def interrupt(self, session_id: str):
        self.interrupted.append(session_id)

    async def compact(self, session_id: str):
        del session_id

    async def usage(self, session_id: str):
        del session_id
        return Usage(cost_usd=self.cost)

    async def cleanup(self, session_id: str):
        self.closed.append(session_id)


class QuietProvider(FakeProvider):
    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        await asyncio.sleep(10)
        yield StreamEvent("fake", session_id, "result", {"ok": True})


def route() -> RouteDecision:
    candidate = ModelCandidate(
        "fake", "model", "v1", SemanticProfile.BALANCED, 10_000
    )
    return RouteDecision(candidate, candidate.profile, "test route", 0.1, None)


def test_supervisor_runs_dependencies_and_reconciles_terminal_state(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "First", task_id="first")
    runner.add_task(run.run_id, "Second", task_id="second", dependencies=("first",))
    provider = FakeProvider()

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path).run(
            run.run_id, "worker", route()
        )
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert [attempt["status"] for attempt in receipt["attempts"]] == ["DONE", "DONE"]
    assert provider.started == 2
    reasons = {
        checkpoint["reason"]
        for checkpoint in runner.store.export_run(run.run_id)["checkpoints"]
    }
    assert "process_exit" in reasons


def test_supervisor_resumes_provider_session_after_failed_verification(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Retry me", task_id="task")
    provider = FakeProvider()
    supervisor = CampaignSupervisor(runner, provider, cwd=tmp_path)

    first = asyncio.run(
        supervisor.run(run.run_id, "worker-1", route(), lambda events: False, once=True)
    )
    second = asyncio.run(
        supervisor.run(run.run_id, "worker-2", route(), once=True)
    )

    assert first["attempts"][0]["status"] == "READY"
    assert second["attempts"][0]["session_resumed"] is True
    assert provider.resumed == ["session-1"]
    assert runner.store.get_task("task").status is TaskStatus.DONE


def test_supervisor_enforces_reported_cost_ceiling(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Expensive task", task_id="task")
    provider = FakeProvider(cost=1.5)
    limits = SupervisionLimits(max_cost_usd=1.0)

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path, limits=limits).run(
            run.run_id, "worker", route()
        )
    )

    assert receipt["run"]["status"] == "BLOCKED"
    assert receipt["attempts"][0]["status"] == "COST_LIMIT"
    assert receipt["measured_cost_usd"] == 1.5
    assert provider.interrupted == ["session-1"]


def test_supervisor_polls_and_releases_due_external_wait(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Wait then finish", task_id="task")
    claim = runner.frontier(run.run_id, "parking", lease_seconds=10)[0]
    running = runner.store.transition_attempt(
        claim["attempt_id"],
        "parking",
        TaskStatus.RUNNING,
        expected_task_revision=claim["task"].revision,
    )
    runner.store.wait_external(
        claim["attempt_id"],
        "parking",
        expected_task_revision=running.revision,
        due_at=time.time() + 0.02,
        reason="fixture readiness",
    )
    limits = SupervisionLimits(max_duration=1, poll_interval=0.01)

    receipt = asyncio.run(
        CampaignSupervisor(
            runner, FakeProvider(), cwd=tmp_path, limits=limits
        ).run(run.run_id, "worker", route())
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert receipt["attempts"][0]["status"] == "DONE"


def test_duration_limit_interrupts_quiet_provider_and_preserves_retry(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Long task", task_id="task")
    provider = QuietProvider()
    limits = SupervisionLimits(
        max_duration=0.2, lease_seconds=0.2, poll_interval=0.02
    )

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path, limits=limits).run(
            run.run_id, "worker", route()
        )
    )

    assert receipt["exit_reason"] == "duration_limit"
    assert receipt["attempts"][0]["status"] == "DURATION_LIMIT"
    assert runner.store.get_task("task").status is TaskStatus.READY
    assert provider.interrupted == ["session-1"]
