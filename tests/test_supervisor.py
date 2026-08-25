from __future__ import annotations

from collections.abc import AsyncIterator
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.adapters.base import (
    AgentProviderAdapter,
    Capability,
    ContextHealth,
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
    RoutingPolicy,
    SemanticProfile,
)
from skiphow.runner import DurableRunner
from skiphow.runtime_security import (
    DurableSecurityAudit,
    RuntimeSecurityPolicy,
)
from skiphow.security import FilesystemPolicy
from skiphow.schemas import TaskStatus
from skiphow.store import ConflictError
from skiphow.supervisor import (
    CampaignSupervisor,
    SupervisionLimits,
    route_provider_catalog,
    route_provider_models,
    terminal_event_verifier,
)
from skiphow.verification import EnvironmentVerifier


class FakeProvider(AgentProviderAdapter):
    def __init__(self, *, cost: float | None = 0.1) -> None:
        self.cost = cost
        self.started = 0
        self.resumed: list[str] = []
        self.sent: list[str] = []
        self.closed: list[str] = []
        self.interrupted: list[str] = []
        self.started_models: list[str | None] = []
        self.compactions = 0
        self.context_health = ContextHealth.UNKNOWN

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
        self.started_models.append(model_id)
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
        self.compactions += 1

    async def usage(self, session_id: str):
        del session_id
        return Usage(cost_usd=self.cost, context_health=self.context_health)

    async def cleanup(self, session_id: str):
        self.closed.append(session_id)


class QuietProvider(FakeProvider):
    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        await asyncio.sleep(10)
        yield StreamEvent("fake", session_id, "result", {"ok": True})


class CompactingProvider(FakeProvider):
    async def discover_capabilities(self):
        return ProviderCapabilities("fake", frozenset({Capability.COMPACT}))


class ContextBoundaryProvider(FakeProvider):
    async def usage(self, session_id: str):
        return Usage(
            cost_usd=self.cost,
            context_health=(
                ContextHealth.APPROACHING_LIMIT
                if session_id == "session-1"
                else ContextHealth.HEALTHY
            ),
            context_tokens=9_000,
            context_limit=10_000,
        )


class QuietContextBoundaryProvider(ContextBoundaryProvider):
    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        if session_id == "session-1":
            await asyncio.sleep(10)
        yield StreamEvent("fake", session_id, "result", {"ok": True})


class ConcurrencyProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__()
        self.active = 0
        self.max_active = 0

    async def start_session(self, *args, **kwargs):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        return await super().start_session(*args, **kwargs)

    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        await asyncio.sleep(0.02)
        yield StreamEvent("fake", session_id, "result", {"ok": True})

    async def cleanup(self, session_id: str):
        await super().cleanup(session_id)
        self.active -= 1


class RepeatedPressureProvider(CompactingProvider):
    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        if session_id == "session-1":
            yield StreamEvent("fake", session_id, "progress", {})
            yield StreamEvent("fake", session_id, "progress", {})
        else:
            yield StreamEvent("fake", session_id, "result", {"ok": True})

    async def usage(self, session_id: str):
        return Usage(
            cost_usd=self.cost,
            context_health=(
                ContextHealth.APPROACHING_LIMIT
                if session_id == "session-1"
                else ContextHealth.HEALTHY
            ),
            context_tokens=9_000,
            context_limit=10_000,
        )


def route() -> RouteDecision:
    candidate = ModelCandidate(
        "fake", "model", "v1", SemanticProfile.BALANCED, 10_000
    )
    return RouteDecision(candidate, candidate.profile, "test route", 0.1, None)


def test_discovered_catalog_builds_stronger_profile_promotions() -> None:
    models = [
        ModelInfo(
            "fake",
            "discovered",
            model_version="2026-08-25",
            context_limit=20_000,
            pricing={"input": 1.0, "output": 2.0},
        )
    ]

    initial, promotions = route_provider_catalog(
        models,
        provider="fake",
        profile=SemanticProfile.ECONOMY,
    )

    assert initial.profile is SemanticProfile.ECONOMY
    assert [item.profile for item in promotions] == [
        SemanticProfile.BALANCED,
        SemanticProfile.FRONTIER,
    ]
    assert {item.candidate.version for item in (initial, *promotions)} == {
        "2026-08-25"
    }


def test_persisted_verified_outcomes_change_future_route_scoring() -> None:
    models = [
        ModelInfo(
            "fake", "cheap", model_version="v1", context_limit=10_000,
            pricing={"input": 0.1, "output": 0.1},
        ),
        ModelInfo(
            "fake", "quality", model_version="v2", context_limit=10_000,
            pricing={"input": 2.0, "output": 2.0},
        ),
    ]
    cold = route_provider_models(models, provider="fake")
    recorded_at = datetime.now(timezone.utc).isoformat()
    outcomes = []
    for model_id, version, passed in (
        ("cheap", "v1", False),
        ("quality", "v2", True),
    ):
        outcomes.extend(
            {
                "provider": "fake",
                "model_id": model_id,
                "model_version": version,
                "profile": "balanced",
                "recorded_at": recorded_at,
                "verifier_passed": passed,
                "terminal_outcome": "DONE" if passed else "READY",
                "latency_ms": 10,
                "input_tokens": 100,
                "output_tokens": 10,
                "cost_usd": 0.1,
                "retries": 0,
                "promotions": 0,
            }
            for _ in range(4)
        )

    calibrated = route_provider_models(
        models,
        provider="fake",
        outcomes=outcomes,
    )

    assert cold.candidate.model_id == "cheap"
    assert calibrated.candidate.model_id == "quality"
    assert calibrated.candidate.version == "v2"
    assert calibrated.calibration_success_rate == 1.0


def test_supervisor_runs_dependencies_and_reconciles_terminal_state(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "First", task_id="first")
    runner.add_task(run.run_id, "Second", task_id="second", dependencies=("first",))
    provider = FakeProvider()

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path).run(
            run.run_id, "worker", route(), terminal_event_verifier
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


def test_supervisor_checkpoints_and_compacts_approaching_context(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Compact then finish", task_id="task")
    provider = CompactingProvider()
    provider.context_health = ContextHealth.APPROACHING_LIMIT

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path).run(
            run.run_id, "worker", route(), terminal_event_verifier
        )
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert provider.compactions == 1
    reasons = [
        checkpoint["reason"]
        for checkpoint in runner.store.export_run(run.run_id)["checkpoints"]
    ]
    assert reasons.index("before_compaction") < reasons.index("after_compaction")


def test_unsupported_compaction_uses_fresh_session_recovery_boundary(
    tmp_path: Path,
) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Reset context then finish", task_id="task")
    provider = ContextBoundaryProvider()

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path).run(
            run.run_id, "worker", route(), terminal_event_verifier
        )
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert [item["status"] for item in receipt["attempts"]] == [
        "CONTEXT_RECOVERY",
        "DONE",
    ]
    assert provider.started == 2
    assert provider.resumed == []
    checkpoints = runner.store.export_run(run.run_id)["checkpoints"]
    boundary = next(
        item for item in checkpoints if item["reason"] == "context_recovery_boundary"
    )
    assert boundary["force_new_session"] is True
    assert boundary["context_tokens"] == 9_000


def test_context_health_is_polled_while_provider_stream_is_quiet(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Recover quiet context", task_id="task")
    provider = QuietContextBoundaryProvider()
    limits = SupervisionLimits(
        max_duration=1, lease_seconds=0.3, poll_interval=0.01
    )

    receipt = asyncio.run(
        CampaignSupervisor(
            runner, provider, cwd=tmp_path, limits=limits
        ).run(run.run_id, "worker", route(), terminal_event_verifier)
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert receipt["attempts"][0]["status"] == "CONTEXT_RECOVERY"
    assert provider.interrupted == ["session-1"]


def test_repeated_pressure_after_compaction_starts_fresh_session(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Compact or recover", task_id="task")
    provider = RepeatedPressureProvider()

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path).run(
            run.run_id, "worker", route(), terminal_event_verifier
        )
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert [item["status"] for item in receipt["attempts"]] == [
        "CONTEXT_RECOVERY",
        "DONE",
    ]
    assert provider.compactions == 1
    assert provider.resumed == []
    reasons = [
        item["reason"] for item in runner.store.export_run(run.run_id)["checkpoints"]
    ]
    assert "repeated_context_pressure" in reasons


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
        supervisor.run(
            run.run_id, "worker-2", route(), terminal_event_verifier, once=True
        )
    )

    assert first["attempts"][0]["status"] == "READY"
    assert second["attempts"][0]["session_resumed"] is True
    assert provider.resumed == ["session-1"]
    assert runner.store.get_task("task").status is TaskStatus.DONE


def test_supervisor_persists_sticky_exact_version_and_bounded_promotion(tmp_path: Path) -> None:
    database = tmp_path / "runner.sqlite3"
    runner = DurableRunner(database, circuit_threshold=4)
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Retry with promotion", task_id="task")
    provider = FakeProvider(cost=0.2)
    balanced = RouteDecision(
        ModelCandidate("fake", "balanced", "2026-08-01", SemanticProfile.BALANCED, 10_000),
        SemanticProfile.BALANCED,
        "balanced initial route",
        0.1,
        None,
    )
    frontier = RouteDecision(
        ModelCandidate("fake", "frontier", "2026-08-20", SemanticProfile.FRONTIER, 20_000),
        SemanticProfile.FRONTIER,
        "frontier verifier promotion",
        0.3,
        None,
    )

    receipts = []
    for index, passed in enumerate((False, False, True)):
        reopened = DurableRunner(database, circuit_threshold=4)
        supervisor = CampaignSupervisor(
            reopened,
            provider,
            cwd=tmp_path,
            promotion_routes=(frontier,),
            routing_policy=RoutingPolicy(max_escalations=1),
        )
        receipts.append(
            asyncio.run(
                supervisor.run(
                    run.run_id,
                    f"worker-{index}",
                    balanced,
                    lambda events, result=passed: result,
                    once=True,
                )
            )
        )

    reopened_store = DurableRunner(database).store
    export = reopened_store.export_run(run.run_id)
    lane = export["route_lanes"][0]
    outcomes = export["route_outcomes"]

    assert [item["attempts"][0]["status"] for item in receipts] == [
        "READY", "READY", "DONE"
    ]
    assert provider.started_models == ["balanced", "frontier"]
    assert receipts[1]["attempts"][0]["session_resumed"] is False
    assert receipts[2]["attempts"][0]["session_resumed"] is True
    assert lane["profile"] == "frontier"
    assert lane["candidate"]["version"] == "2026-08-20"
    assert lane["escalation_count"] == 1
    assert [item["model_version"] for item in outcomes] == [
        "2026-08-01", "2026-08-20", "2026-08-20"
    ]
    assert [item["verifier_passed"] for item in outcomes] == [False, False, True]
    assert reopened_store.list_route_outcomes() == outcomes


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


def test_cost_ceiling_serializes_parallel_claim_admission(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3", parallelism=2)
    run = runner.start("Inspect", {}, run_id="run")
    runner.add_task(run.run_id, "Inspect first", task_id="first")
    runner.add_task(run.run_id, "Inspect second", task_id="second")
    provider = ConcurrencyProvider()

    receipt = asyncio.run(
        CampaignSupervisor(
            runner,
            provider,
            cwd=tmp_path,
            permissions=PermissionMode.READ_ONLY,
            limits=SupervisionLimits(max_cost_usd=1.0),
        ).run(run.run_id, "worker", route(), terminal_event_verifier)
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert provider.max_active == 1


def test_cost_ceiling_stops_admission_when_provider_cost_is_unknown(
    tmp_path: Path,
) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3", parallelism=2)
    run = runner.start("Inspect", {}, run_id="run")
    runner.add_task(run.run_id, "Inspect first", task_id="first")
    runner.add_task(run.run_id, "Inspect second", task_id="second")
    provider = FakeProvider(cost=None)

    receipt = asyncio.run(
        CampaignSupervisor(
            runner,
            provider,
            cwd=tmp_path,
            permissions=PermissionMode.READ_ONLY,
            limits=SupervisionLimits(max_cost_usd=1.0),
        ).run(run.run_id, "worker", route(), terminal_event_verifier)
    )

    assert receipt["exit_reason"] == "cost_unverified"
    assert receipt["cost_ceiling_enforced"] is False
    assert provider.started == 1
    assert sum(
        task.status is TaskStatus.READY
        for task in runner.store.list_tasks(run.run_id)
    ) == 1


def test_shared_write_checkout_serializes_parallel_claims(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3", parallelism=2)
    run = runner.start("Change both", {}, run_id="run")
    runner.add_task(run.run_id, "Change first", task_id="first")
    runner.add_task(run.run_id, "Change second", task_id="second")
    provider = ConcurrencyProvider()

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path).run(
            run.run_id, "worker", route(), terminal_event_verifier
        )
    )

    assert receipt["run"]["status"] == "COMPLETED"
    assert provider.max_active == 1


def test_full_access_provider_mode_is_blocked_before_dispatch(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver it", {}, run_id="run")
    runner.add_task(run.run_id, "Unsafe task", task_id="task")
    provider = FakeProvider()

    receipt = asyncio.run(
        CampaignSupervisor(
            runner,
            provider,
            cwd=tmp_path,
            permissions=PermissionMode.FULL_ACCESS,
        ).run(run.run_id, "worker", route())
    )

    assert receipt["run"]["status"] == "BLOCKED"
    assert receipt["attempts"][0]["status"] == "SECURITY_BLOCKED"
    assert provider.started == 0
    audits = DurableSecurityAudit(runner.store).events(run.run_id)
    assert audits[-1]["outcome"] == "denied"
    assert DurableSecurityAudit(runner.store).verify(run.run_id)


def test_protected_action_requires_exact_run_authority(tmp_path: Path) -> None:
    denied_runner = DurableRunner(tmp_path / "denied.sqlite3")
    denied = denied_runner.start("Release", {}, run_id="denied")
    denied_runner.add_task(
        denied.run_id,
        "Publish",
        task_id="publish-denied",
        constraints=("protected-action:public-release",),
    )
    denied_provider = FakeProvider()
    denied_receipt = asyncio.run(
        CampaignSupervisor(denied_runner, denied_provider, cwd=tmp_path).run(
            denied.run_id, "worker", route()
        )
    )

    allowed_runner = DurableRunner(tmp_path / "allowed.sqlite3")
    allowed = allowed_runner.start(
        "Release",
        {"protected_actions": ["public-release"], "actor": "owner"},
        run_id="allowed",
    )
    allowed_runner.add_task(
        allowed.run_id,
        "Publish",
        task_id="publish-allowed",
        constraints=("protected-action:public-release",),
    )
    allowed_provider = FakeProvider()
    allowed_receipt = asyncio.run(
        CampaignSupervisor(allowed_runner, allowed_provider, cwd=tmp_path).run(
            allowed.run_id, "worker", route(), terminal_event_verifier
        )
    )

    assert denied_receipt["run"]["status"] == "BLOCKED"
    assert denied_provider.started == 0
    assert allowed_receipt["run"]["status"] == "COMPLETED"
    assert allowed_provider.started == 1


def test_protected_action_is_classified_from_mutation_outcome(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Release", {}, run_id="run")
    runner.add_task(
        run.run_id,
        "Deploy the current build to production",
        task_id="deploy",
    )
    provider = FakeProvider()

    receipt = asyncio.run(
        CampaignSupervisor(runner, provider, cwd=tmp_path).run(
            run.run_id, "worker", route(), terminal_event_verifier
        )
    )

    assert receipt["attempts"][0]["status"] == "SECURITY_BLOCKED"
    assert provider.started == 0
    audit = DurableSecurityAudit(runner.store).events(run.run_id)[-1]
    assert audit["details"]["protected_actions"] == ["production-deployment"]


def test_saved_read_only_profile_cannot_be_escalated_by_cli_mode(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start(
        "Inspect only", {"permission_profile": "read-only"}, run_id="run"
    )
    runner.add_task(run.run_id, "Inspect", task_id="task")
    provider = FakeProvider()

    receipt = asyncio.run(
        CampaignSupervisor(
            runner,
            provider,
            cwd=tmp_path,
            permissions=PermissionMode.WORKSPACE_WRITE,
        ).run(run.run_id, "worker", route())
    )

    assert receipt["attempts"][0]["status"] == "SECURITY_BLOCKED"
    assert provider.started == 0


def test_filesystem_policy_rejects_dispatch_outside_allowlist(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    allowed = tmp_path / "different-root"
    workspace.mkdir()
    allowed.mkdir()
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Deliver", {}, run_id="run")
    runner.add_task(run.run_id, "Write", task_id="task")
    policy = RuntimeSecurityPolicy(
        workspace,
        filesystem=FilesystemPolicy(read_roots=(allowed,), write_roots=(allowed,)),
    )
    provider = FakeProvider()

    receipt = asyncio.run(
        CampaignSupervisor(
            runner, provider, cwd=workspace, security_policy=policy
        ).run(run.run_id, "worker", route())
    )

    assert receipt["attempts"][0]["status"] == "SECURITY_BLOCKED"
    assert provider.started == 0


def test_security_policy_cannot_validate_a_different_provider_cwd(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    different = tmp_path / "different"
    workspace.mkdir()
    different.mkdir()
    runner = DurableRunner(tmp_path / "runner.sqlite3")

    with pytest.raises(ValueError, match="must match"):
        CampaignSupervisor(
            runner,
            FakeProvider(),
            cwd=workspace,
            security_policy=RuntimeSecurityPolicy(different),
        )


def test_durable_security_audit_redacts_secret_details(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Audit", {}, run_id="run")
    audit = DurableSecurityAudit(runner.store)
    secret = "ghp_abcdefghijklmnopqrstuvwx"

    audit.append(
        run.run_id,
        actor="controller",
        action="authority-check",
        target="release",
        outcome="denied",
        details={"authorization": secret, "diagnostic": f"token={secret}"},
    )

    persisted = audit.events(run.run_id)[0]
    assert secret not in repr(persisted)
    assert persisted["details"]["authorization"] == "[REDACTED]"
    assert audit.verify(run.run_id)


def test_security_audit_cas_serializes_concurrent_store_connections(tmp_path: Path) -> None:
    database = tmp_path / "runner.sqlite3"
    runner = DurableRunner(database)
    run = runner.start("Audit", {}, run_id="run")

    def append(index: int) -> None:
        audit = DurableSecurityAudit(DurableRunner(database).store)
        audit.append(
            run.run_id,
            actor=f"worker-{index % 2}",
            action="dispatch-check",
            target=f"task-{index}",
            outcome="allowed",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(append, range(40)))

    audit = DurableSecurityAudit(runner.store)
    assert len(audit.events(run.run_id)) == 40
    assert audit.verify(run.run_id)


def test_security_audit_retries_sustained_cas_contention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ContendedStore:
        def __init__(self) -> None:
            self.attempts = 0

        def list_security_audit(self, run_id: str) -> list[dict[str, object]]:
            return []

        def append_security_audit(self, run_id, payload, **kwargs):
            self.attempts += 1
            if self.attempts <= 20:
                raise ConflictError("simulated contention")
            return dict(payload)

    store = ContendedStore()
    monkeypatch.setattr(time, "sleep", lambda delay: None)
    event = DurableSecurityAudit(store).append(
        "run",
        actor="worker",
        action="dispatch-check",
        target="task",
        outcome="allowed",
    )

    assert store.attempts == 21
    assert event["sequence"] == 1


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
        ).run(run.run_id, "worker", route(), terminal_event_verifier)
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


def test_write_capable_supervisor_fails_closed_without_environment_verifier(
    tmp_path: Path,
) -> None:
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Change the project", {}, run_id="run")
    runner.add_task(run.run_id, "Write output", task_id="task")

    receipt = asyncio.run(
        CampaignSupervisor(runner, FakeProvider(), cwd=tmp_path).run(
            run.run_id, "worker", route(), once=True
        )
    )

    assert receipt["attempts"][0]["status"] == "READY"
    checkpoint = runner.store.export_run(run.run_id)["checkpoints"][-2]
    assert checkpoint["reason"] == "after_verification"
    result = checkpoint["environment_verification"]
    assert result["passed"] is False
    assert "no environment verifier" in result["checks"][0]["reason"]


def test_async_object_verifier_result_is_awaited(tmp_path: Path) -> None:
    class AsyncVerifier:
        async def verify(self, task, events, baseline):
            del task, events, baseline
            return False

    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Inspect", {}, run_id="run")
    runner.add_task(run.run_id, "Inspect output", task_id="task")

    receipt = asyncio.run(
        CampaignSupervisor(
            runner,
            FakeProvider(),
            cwd=tmp_path,
            permissions=PermissionMode.READ_ONLY,
        ).run(run.run_id, "worker", route(), AsyncVerifier(), once=True)
    )

    assert receipt["attempts"][0]["status"] == "READY"


def test_verifier_prepare_error_does_not_strand_claim(tmp_path: Path) -> None:
    class BrokenPrepare:
        def prepare(self, task):
            del task
            raise RuntimeError("baseline failed")

    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Inspect", {}, run_id="run")
    runner.add_task(run.run_id, "Inspect output", task_id="task")

    with pytest.raises(RuntimeError, match="baseline failed"):
        asyncio.run(
            CampaignSupervisor(
                runner,
                FakeProvider(),
                cwd=tmp_path,
                permissions=PermissionMode.READ_ONLY,
            ).run(run.run_id, "worker", route(), BrokenPrepare(), once=True)
        )

    assert runner.store.get_task("task").status is TaskStatus.READY


def test_environment_verifier_checks_files_commands_evidence_and_forbidden_paths(
    tmp_path: Path,
) -> None:
    protected = tmp_path / "protected.txt"
    protected.write_text("unchanged", encoding="utf-8")
    output = tmp_path / "result.txt"
    output.write_text("verified output", encoding="utf-8")
    evidence = tmp_path / "evidence.log"
    evidence.write_text("test receipt", encoding="utf-8")
    verifier_script = tmp_path / "verify.py"
    verifier_script.write_text("print('command proof')\n", encoding="utf-8")
    runner = DurableRunner(tmp_path / "runner.sqlite3")
    run = runner.start("Change the project", {}, run_id="run")
    task = runner.add_task(run.run_id, "Write output", task_id="task")
    verifier = EnvironmentVerifier(
        tmp_path,
        {
            task.task_id: {
                "expected_filesystem": [
                    {"path": "result.txt", "kind": "file", "contains": "verified"}
                ],
                "forbidden_mutations": ["protected.txt"],
                "commands": [
                    {
                        "argv": [sys.executable, "verify.py"],
                        "trusted_artifacts": ["verify.py"],
                        "stdout_contains": "command proof",
                        "timeout_seconds": 5,
                    }
                ],
                "evidence": ["evidence.log"],
            }
        },
    )

    receipt = asyncio.run(
        CampaignSupervisor(runner, FakeProvider(), cwd=tmp_path).run(
            run.run_id, "worker", route(), verifier
        )
    )

    assert receipt["run"]["status"] == "COMPLETED"
    checkpoint = next(
        item
        for item in runner.store.export_run(run.run_id)["checkpoints"]
        if item["reason"] == "after_verification"
    )
    verification = checkpoint["environment_verification"]
    assert verification["passed"] is True
    assert verification["evidence"] == ["evidence.log"]
    assert {item["kind"] for item in verification["checks"]} == {
        "forbidden_mutation",
        "filesystem",
        "command",
        "evidence",
    }
