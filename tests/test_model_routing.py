from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skiphow.model_routing import (  # noqa: E402
    CostPreference,
    HeuristicRouter,
    LaneRouter,
    LaneState,
    ModelCandidate,
    ModelCatalog,
    OutcomeCalibrationStore,
    OutcomeRecord,
    RoutingPolicy,
    SemanticProfile,
    TaskFeatures,
)


def model(name: str, profile: SemanticProfile, *, cost: float, context: int = 100_000):
    return ModelCandidate(
        provider="test-provider",
        model_id=name,
        version="test-version",
        profile=profile,
        context_window=context,
        input_cost_per_million=cost,
        output_cost_per_million=cost,
        typical_latency_ms=int(cost * 100),
        capabilities=frozenset({"tools"}),
    )


def test_router_enforces_high_impact_floor_and_explains_it() -> None:
    catalog = ModelCatalog(
        [
            model("cheap-runtime-value", SemanticProfile.ECONOMY, cost=1),
            model("strong-runtime-value", SemanticProfile.FRONTIER, cost=10),
        ]
    )
    decision = HeuristicRouter(catalog).route(
        TaskFeatures(taxonomy="security-review", security_sensitive=True)
    )
    assert decision.profile is SemanticProfile.FRONTIER
    assert "safety floor for security" in decision.reason


@pytest.mark.parametrize("feature", ["campaign_decomposition", "final_integration"])
def test_campaign_judgment_boundaries_use_frontier(feature: str) -> None:
    catalog = ModelCatalog(
        [
            model("balanced-runtime-value", SemanticProfile.BALANCED, cost=1),
            model("frontier-runtime-value", SemanticProfile.FRONTIER, cost=5),
        ]
    )
    task = TaskFeatures(taxonomy="campaign", **{feature: True})
    assert HeuristicRouter(catalog).route(task).profile is SemanticProfile.FRONTIER


def test_router_uses_economy_for_read_only_work_when_configured() -> None:
    catalog = ModelCatalog(
        [
            model("economy-runtime-value", SemanticProfile.ECONOMY, cost=1),
            model("balanced-runtime-value", SemanticProfile.BALANCED, cost=3),
        ]
    )
    policy = RoutingPolicy(safety_floor=SemanticProfile.ECONOMY)
    decision = HeuristicRouter(catalog, policy).route(
        TaskFeatures(taxonomy="inventory", read_only=True, strong_verifier=True),
        CostPreference.ECONOMY,
    )
    assert decision.profile is SemanticProfile.ECONOMY
    assert "read-only task" in decision.reason


def test_missing_history_keeps_mutating_work_at_conservative_floor() -> None:
    catalog = ModelCatalog(
        [
            model("economy-runtime-value", SemanticProfile.ECONOMY, cost=1),
            model("balanced-runtime-value", SemanticProfile.BALANCED, cost=2),
        ]
    )
    policy = RoutingPolicy(
        safety_floor=SemanticProfile.ECONOMY,
        unknown_data_floor=SemanticProfile.BALANCED,
    )
    decision = HeuristicRouter(catalog, policy).route(TaskFeatures(taxonomy="implementation"))
    assert decision.profile is SemanticProfile.BALANCED
    assert "no trusted outcome history" in decision.reason


def test_read_only_work_without_strong_verifier_stays_balanced() -> None:
    catalog = ModelCatalog(
        [
            model("economy-runtime-value", SemanticProfile.ECONOMY, cost=1),
            model("balanced-runtime-value", SemanticProfile.BALANCED, cost=2),
        ]
    )
    decision = HeuristicRouter(catalog).route(
        TaskFeatures(taxonomy="ambiguous-extraction", read_only=True)
    )
    assert decision.profile is SemanticProfile.BALANCED


def test_router_filters_capabilities_and_context() -> None:
    no_tools = model("missing-capability", SemanticProfile.BALANCED, cost=1)
    no_tools = ModelCandidate(
        provider=no_tools.provider,
        model_id=no_tools.model_id,
        version=no_tools.version,
        profile=no_tools.profile,
        context_window=no_tools.context_window,
        input_cost_per_million=1,
    )
    enough = model("adequate-runtime-value", SemanticProfile.BALANCED, cost=2, context=50_000)
    catalog = ModelCatalog([no_tools, enough])
    decision = HeuristicRouter(catalog).route(
        TaskFeatures(
            taxonomy="implementation",
            expected_input_tokens=20_000,
            expected_output_tokens=5_000,
            required_capabilities=frozenset({"tools"}),
        )
    )
    assert decision.candidate is enough


def test_version_and_recency_bound_calibration() -> None:
    now = datetime(2026, 8, 25, tzinfo=timezone.utc)
    candidate = model("runtime-configured-id", SemanticProfile.BALANCED, cost=2)
    store = OutcomeCalibrationStore(half_life_days=10)
    for version, age, success in (
        ("test-version", 0, True),
        ("test-version", 10, False),
        ("old-version", 0, False),
    ):
        store.record(
            OutcomeRecord(
                provider=candidate.provider,
                model_id=candidate.model_id,
                version=version,
                profile=candidate.profile,
                taxonomy="change",
                repository="repo",
                recorded_at=now - timedelta(days=age),
                verifier_passed=success,
                terminal_success=success,
            )
        )
    estimate = store.estimate(
        candidate, TaskFeatures(taxonomy="change", repository="repo"), now=now
    )
    assert estimate is not None
    assert estimate.success_rate == pytest.approx(2 / 3)
    assert estimate.effective_weight == pytest.approx(1.5)


def test_verified_history_beats_a_cheaper_untested_candidate() -> None:
    proven = model("proven-runtime-value", SemanticProfile.BALANCED, cost=2)
    untested = model("untested-runtime-value", SemanticProfile.BALANCED, cost=1)
    store = OutcomeCalibrationStore()
    now = datetime.now(timezone.utc)
    for _ in range(10):
        store.record(
            OutcomeRecord(
                provider=proven.provider,
                model_id=proven.model_id,
                version=proven.version,
                profile=proven.profile,
                taxonomy="change",
                repository=None,
                recorded_at=now,
                verifier_passed=True,
                terminal_success=True,
            )
        )
    router = HeuristicRouter(ModelCatalog([untested, proven]), calibration=store)
    assert router.route(TaskFeatures(taxonomy="change")).candidate is proven


def test_context_overhead_is_included_in_estimated_cost() -> None:
    candidate = ModelCandidate(
        provider="provider",
        model_id="runtime-value",
        version="version",
        profile=SemanticProfile.BALANCED,
        context_window=100_000,
        context_overhead_tokens=10_000,
        input_cost_per_million=2,
        output_cost_per_million=4,
    )
    decision = HeuristicRouter(ModelCatalog([candidate])).route(
        TaskFeatures(taxonomy="change", expected_input_tokens=5_000, expected_output_tokens=1_000)
    )
    assert decision.estimated_cost == pytest.approx(0.034)


def test_outcome_schema_has_no_prompt_or_content_field() -> None:
    fields = OutcomeRecord.__dataclass_fields__
    assert "prompt" not in fields
    assert "output" not in fields
    assert "content" not in fields


def test_lane_is_sticky_and_escalation_needs_checkpoint() -> None:
    state = LaneState(
        lane_id="writer-1",
        profile=SemanticProfile.ECONOMY,
        candidate_key=("provider", "runtime-id", "version"),
    )
    router = LaneRouter()
    assert router.continue_lane(state).state is state
    with pytest.raises(ValueError, match="checkpoint"):
        router.escalate(state, failure_signature="tests-failed", checkpoint_id=None)
    promoted = router.escalate(
        state, failure_signature="tests-failed", checkpoint_id="checkpoint-1"
    )
    assert promoted.changed
    assert promoted.state.profile is SemanticProfile.BALANCED
    assert promoted.state.candidate_key is None
    assert promoted.state.failure_signatures == ("tests-failed",)


def test_lane_escalation_is_bounded_without_downgrade() -> None:
    router = LaneRouter(RoutingPolicy(max_escalations=1))
    state = LaneState("lane", SemanticProfile.ECONOMY, ("p", "m", "v"))
    first = router.escalate(state, failure_signature="one", checkpoint_id="cp-1")
    second = router.escalate(
        first.state, failure_signature="two", checkpoint_id="cp-2"
    )
    assert first.state.profile is SemanticProfile.BALANCED
    assert not second.changed
    assert second.state.profile is SemanticProfile.BALANCED


def test_catalog_rejects_duplicate_runtime_identity() -> None:
    candidate = model("runtime-value", SemanticProfile.BALANCED, cost=1)
    with pytest.raises(ValueError, match="duplicate"):
        ModelCatalog([candidate, candidate])
