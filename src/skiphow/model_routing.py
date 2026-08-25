"""Provider-neutral model selection and outcome calibration.

The catalog contains provider model identifiers supplied by adapters or local
configuration.  This module deliberately defines no concrete model names.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Iterable, Mapping, Sequence


class SemanticProfile(str, Enum):
    """Stable capability classes understood by the controller."""

    ECONOMY = "economy"
    BALANCED = "balanced"
    FRONTIER = "frontier"


class CostPreference(str, Enum):
    """The only model-routing preference exposed to product users."""

    AUTO = "auto"
    ECONOMY = "economy"
    BALANCED = "balanced"
    QUALITY = "quality"


_PROFILE_RANK = {
    SemanticProfile.ECONOMY: 0,
    SemanticProfile.BALANCED: 1,
    SemanticProfile.FRONTIER: 2,
}


@dataclass(frozen=True)
class ModelCandidate:
    """One adapter-supplied model and the facts needed for routing."""

    provider: str
    model_id: str
    version: str
    profile: SemanticProfile
    context_window: int
    input_cost_per_million: float | None = None
    output_cost_per_million: float | None = None
    typical_latency_ms: int | None = None
    context_overhead_tokens: int = 0
    capabilities: frozenset[str] = frozenset()
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.model_id.strip() or not self.version.strip():
            raise ValueError("provider, model_id, and version must be non-empty")
        if self.context_window <= 0:
            raise ValueError("context_window must be positive")
        if self.context_overhead_tokens < 0:
            raise ValueError("context_overhead_tokens cannot be negative")
        for value in (self.input_cost_per_million, self.output_cost_per_million):
            if value is not None and value < 0:
                raise ValueError("model cost cannot be negative")
        if self.typical_latency_ms is not None and self.typical_latency_ms < 0:
            raise ValueError("typical_latency_ms cannot be negative")

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.provider, self.model_id, self.version)


class ModelCatalog:
    """An immutable-by-convention registry populated at runtime."""

    def __init__(self, candidates: Iterable[ModelCandidate] = ()) -> None:
        self._candidates: dict[tuple[str, str, str], ModelCandidate] = {}
        for candidate in candidates:
            self.add(candidate)

    def add(self, candidate: ModelCandidate) -> None:
        if candidate.key in self._candidates:
            raise ValueError(f"duplicate model catalog entry: {candidate.key!r}")
        self._candidates[candidate.key] = candidate

    def available(self) -> tuple[ModelCandidate, ...]:
        return tuple(candidate for candidate in self._candidates.values() if candidate.enabled)

    def get(self, provider: str, model_id: str, version: str) -> ModelCandidate:
        return self._candidates[(provider, model_id, version)]


@dataclass(frozen=True)
class TaskFeatures:
    """Facts derived by the controller without a separate router-model call."""

    taxonomy: str
    repository: str | None = None
    read_only: bool = False
    architecture: bool = False
    campaign_decomposition: bool = False
    final_integration: bool = False
    security_sensitive: bool = False
    money_sensitive: bool = False
    public_contract: bool = False
    external_side_effect: bool = False
    strong_verifier: bool = False
    weak_verifier: bool = False
    expected_input_tokens: int = 0
    expected_output_tokens: int = 0
    required_capabilities: frozenset[str] = frozenset()
    latency_sensitive: bool = False

    def __post_init__(self) -> None:
        if not self.taxonomy.strip():
            raise ValueError("taxonomy must be non-empty")
        if self.expected_input_tokens < 0 or self.expected_output_tokens < 0:
            raise ValueError("expected token counts cannot be negative")
        if self.strong_verifier and self.weak_verifier:
            raise ValueError("a verifier cannot be both strong and weak")

    @property
    def high_impact_reasons(self) -> tuple[str, ...]:
        labels: list[str] = []
        if self.architecture:
            labels.append("architecture")
        if self.campaign_decomposition:
            labels.append("campaign decomposition")
        if self.final_integration:
            labels.append("final integration")
        if self.security_sensitive:
            labels.append("security")
        if self.money_sensitive:
            labels.append("money")
        if self.public_contract:
            labels.append("public contract")
        if self.external_side_effect:
            labels.append("external side effect")
        if self.weak_verifier:
            labels.append("weak verifier")
        return tuple(labels)


@dataclass(frozen=True)
class RoutingPolicy:
    """Local routing limits; it never contains provider model identifiers."""

    safety_floor: SemanticProfile = SemanticProfile.ECONOMY
    high_impact_floor: SemanticProfile = SemanticProfile.FRONTIER
    unknown_data_floor: SemanticProfile = SemanticProfile.BALANCED
    context_headroom_ratio: float = 0.1
    calibration_min_weight: float = 3.0
    max_escalations: int = 2

    def __post_init__(self) -> None:
        if not 0 <= self.context_headroom_ratio < 1:
            raise ValueError("context_headroom_ratio must be in [0, 1)")
        if self.calibration_min_weight < 0:
            raise ValueError("calibration_min_weight cannot be negative")
        if self.max_escalations < 0:
            raise ValueError("max_escalations cannot be negative")


@dataclass(frozen=True)
class RouteDecision:
    candidate: ModelCandidate
    profile: SemanticProfile
    reason: str
    estimated_cost: float | None
    calibration_success_rate: float | None


@dataclass(frozen=True)
class CalibrationEstimate:
    success_rate: float
    effective_weight: float


@dataclass(frozen=True)
class OutcomeRecord:
    """Execution facts only. Prompts and generated content have no fields here."""

    provider: str
    model_id: str
    version: str
    profile: SemanticProfile
    taxonomy: str
    repository: str | None
    recorded_at: datetime
    verifier_passed: bool
    terminal_success: bool
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: float | None = None
    retries: int = 0
    promotions: int = 0

    def __post_init__(self) -> None:
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware")
        for name in ("latency_ms", "input_tokens", "output_tokens", "retries", "promotions"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.estimated_cost is not None and self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")


class OutcomeCalibrationStore:
    """Version-aware, recency-weighted routing outcomes."""

    def __init__(self, half_life_days: float = 30.0) -> None:
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        self.half_life_days = half_life_days
        self._records: list[OutcomeRecord] = []

    def record(self, outcome: OutcomeRecord) -> None:
        self._records.append(outcome)

    def records(self) -> tuple[OutcomeRecord, ...]:
        return tuple(self._records)

    def estimate(
        self,
        candidate: ModelCandidate,
        features: TaskFeatures,
        *,
        now: datetime | None = None,
    ) -> CalibrationEstimate | None:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        weighted_success = 0.0
        total_weight = 0.0
        for record in self._records:
            if (record.provider, record.model_id, record.version) != candidate.key:
                continue
            if record.profile is not candidate.profile:
                continue
            if record.taxonomy != features.taxonomy:
                continue
            repository_weight = 1.0 if record.repository == features.repository else 0.5
            age_days = max(0.0, (current - record.recorded_at).total_seconds() / 86_400)
            recency_weight = math.pow(0.5, age_days / self.half_life_days)
            weight = repository_weight * recency_weight
            verified_success = record.verifier_passed and record.terminal_success
            weighted_success += weight if verified_success else 0.0
            total_weight += weight
        if total_weight == 0:
            return None
        return CalibrationEstimate(weighted_success / total_weight, total_weight)


class HeuristicRouter:
    """Select the cheapest adequate catalog entry and explain the choice."""

    def __init__(
        self,
        catalog: ModelCatalog,
        policy: RoutingPolicy | None = None,
        calibration: OutcomeCalibrationStore | None = None,
    ) -> None:
        self.catalog = catalog
        self.policy = policy or RoutingPolicy()
        self.calibration = calibration

    def route(
        self,
        features: TaskFeatures,
        preference: CostPreference = CostPreference.AUTO,
    ) -> RouteDecision:
        floor, floor_reason = self._required_floor(features, preference)
        candidates = [
            candidate
            for candidate in self.catalog.available()
            if _PROFILE_RANK[candidate.profile] >= _PROFILE_RANK[floor]
            and features.required_capabilities.issubset(candidate.capabilities)
            and self._fits_context(candidate, features)
        ]
        if not candidates:
            raise LookupError(
                f"no enabled model satisfies {floor.value} floor, capabilities, and context"
            )

        estimates = {candidate.key: self._estimate(candidate, features) for candidate in candidates}
        candidates.sort(key=lambda candidate: self._score(candidate, features, estimates[candidate.key]))
        selected = candidates[0]
        estimate = estimates[selected.key]
        rate = None if estimate is None else estimate.success_rate
        data_note = "no trusted outcome history" if estimate is None else f"calibrated success {rate:.0%}"
        reason = f"{selected.profile.value}: {floor_reason}; {data_note}"
        return RouteDecision(
            candidate=selected,
            profile=selected.profile,
            reason=reason,
            estimated_cost=self._estimated_cost(selected, features),
            calibration_success_rate=rate,
        )

    def _required_floor(
        self, features: TaskFeatures, preference: CostPreference
    ) -> tuple[SemanticProfile, str]:
        if features.high_impact_reasons:
            reasons = ", ".join(features.high_impact_reasons)
            return self.policy.high_impact_floor, f"safety floor for {reasons}"
        desired = {
            CostPreference.ECONOMY: SemanticProfile.ECONOMY,
            CostPreference.BALANCED: SemanticProfile.BALANCED,
            CostPreference.QUALITY: SemanticProfile.FRONTIER,
        }.get(
            preference,
            SemanticProfile.ECONOMY
            if features.read_only and features.strong_verifier
            else self.policy.unknown_data_floor,
        )
        configured_floors = [self.policy.safety_floor, desired]
        if not (features.read_only and features.strong_verifier):
            configured_floors.append(self.policy.unknown_data_floor)
        floor = max(configured_floors, key=_PROFILE_RANK.__getitem__)
        if preference is CostPreference.QUALITY:
            return floor, "quality preference"
        if features.read_only and features.strong_verifier and floor is SemanticProfile.ECONOMY:
            return floor, "read-only task with a strong verifier"
        return floor, "configured safety floor"

    def _fits_context(self, candidate: ModelCandidate, features: TaskFeatures) -> bool:
        required = (
            features.expected_input_tokens
            + features.expected_output_tokens
            + candidate.context_overhead_tokens
        )
        usable = candidate.context_window * (1 - self.policy.context_headroom_ratio)
        return required <= usable

    def _estimate(
        self, candidate: ModelCandidate, features: TaskFeatures
    ) -> CalibrationEstimate | None:
        if self.calibration is None:
            return None
        estimate = self.calibration.estimate(candidate, features)
        if estimate is None or estimate.effective_weight < self.policy.calibration_min_weight:
            return None
        return estimate

    @staticmethod
    def _estimated_cost(candidate: ModelCandidate, features: TaskFeatures) -> float | None:
        if candidate.input_cost_per_million is None or candidate.output_cost_per_million is None:
            return None
        return (
            (features.expected_input_tokens + candidate.context_overhead_tokens)
            * candidate.input_cost_per_million
            + features.expected_output_tokens * candidate.output_cost_per_million
        ) / 1_000_000

    def _score(
        self,
        candidate: ModelCandidate,
        features: TaskFeatures,
        estimate: CalibrationEstimate | None,
    ) -> tuple[float, int, int, str, str]:
        cost = self._estimated_cost(candidate, features)
        unknown_cost_penalty = 10_000.0 if cost is None else cost
        latency = candidate.typical_latency_ms
        latency_score = latency if latency is not None else 10_000_000
        # With no execution-verified history, assume only an even chance of
        # success.  An unknown model must not outrank a proven model merely
        # because its missing data looked like a zero penalty.
        reliability = 0.5 if estimate is None else estimate.success_rate
        failure_penalty = (1 - reliability) * 1_000
        if features.latency_sensitive:
            primary = latency_score / 1_000 + unknown_cost_penalty + failure_penalty
        else:
            primary = unknown_cost_penalty + latency_score / 1_000_000 + failure_penalty
        return (
            primary,
            _PROFILE_RANK[candidate.profile],
            candidate.context_overhead_tokens,
            candidate.provider,
            candidate.model_id,
        )


@dataclass(frozen=True)
class LaneState:
    """Sticky routing state for one coherent mutable lane."""

    lane_id: str
    profile: SemanticProfile
    candidate_key: tuple[str, str, str] | None
    escalation_count: int = 0
    failure_signatures: tuple[str, ...] = ()
    checkpoint_id: str | None = None


@dataclass(frozen=True)
class EscalationDecision:
    state: LaneState
    changed: bool
    reason: str


class LaneRouter:
    """Keep a lane sticky and make profile changes explicit and bounded."""

    def __init__(self, policy: RoutingPolicy | None = None) -> None:
        self.policy = policy or RoutingPolicy()

    def continue_lane(self, state: LaneState) -> EscalationDecision:
        return EscalationDecision(state, False, "sticky lane retains its current profile")

    def escalate(
        self,
        state: LaneState,
        *,
        failure_signature: str,
        checkpoint_id: str | None,
        reason: str = "verifier failure",
    ) -> EscalationDecision:
        if not failure_signature.strip():
            raise ValueError("failure_signature must be non-empty")
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required before a profile switch")
        if state.escalation_count >= self.policy.max_escalations:
            return EscalationDecision(state, False, "escalation limit reached")
        current_rank = _PROFILE_RANK[state.profile]
        if current_rank >= _PROFILE_RANK[SemanticProfile.FRONTIER]:
            return EscalationDecision(state, False, "lane already uses the frontier profile")
        next_profile = (SemanticProfile.BALANCED, SemanticProfile.FRONTIER)[current_rank]
        new_state = LaneState(
            lane_id=state.lane_id,
            profile=next_profile,
            candidate_key=None,
            escalation_count=state.escalation_count + 1,
            failure_signatures=state.failure_signatures + (failure_signature,),
            checkpoint_id=checkpoint_id,
        )
        return EscalationDecision(new_state, True, f"{reason}; promoted to {next_profile.value}")

    def bind_candidate(
        self, state: LaneState, candidate: ModelCandidate, *, checkpoint_id: str
    ) -> LaneState:
        if candidate.profile is not state.profile:
            raise ValueError("candidate profile must match the lane profile")
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required before changing candidates")
        return LaneState(
            lane_id=state.lane_id,
            profile=state.profile,
            candidate_key=candidate.key,
            escalation_count=state.escalation_count,
            failure_signatures=state.failure_signatures,
            checkpoint_id=checkpoint_id,
        )
