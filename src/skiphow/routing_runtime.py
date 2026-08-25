"""Durable model-route state shared by execution loops."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .model_routing import (
    LaneRouter,
    LaneState,
    ModelCandidate,
    RouteDecision,
    RoutingPolicy,
    SemanticProfile,
)
from .store import RunnerStore


class DurableRouteCoordinator:
    """Keep a task lane sticky and persist bounded, checkpointed promotions."""

    def __init__(
        self,
        store: RunnerStore,
        *,
        promotion_routes: Sequence[RouteDecision] = (),
        policy: RoutingPolicy | None = None,
    ) -> None:
        self.store = store
        self._promotion_routes = {
            decision.profile: decision for decision in promotion_routes
        }
        self._router = LaneRouter(policy)

    def sticky(
        self, run_id: str, task_id: str, proposed: RouteDecision
    ) -> RouteDecision:
        stored = self.store.ensure_route_lane(
            run_id, task_id, route_lane_payload(proposed)
        )
        return route_from_lane(stored)

    def promote(
        self,
        task_id: str,
        *,
        failure_signature: str,
        checkpoint_id: str,
    ) -> bool:
        stored = self.store.get_route_lane(task_id)
        if stored is None:
            return False
        state = LaneState(
            lane_id=task_id,
            profile=SemanticProfile(stored["profile"]),
            candidate_key=(
                stored["candidate"]["provider"],
                stored["candidate"]["model_id"],
                stored["candidate"]["version"],
            ),
            escalation_count=int(stored.get("escalation_count", 0)),
            failure_signatures=tuple(stored.get("failure_signatures", ())),
            checkpoint_id=stored.get("checkpoint_id"),
        )
        escalation = self._router.escalate(
            state,
            failure_signature=failure_signature,
            checkpoint_id=checkpoint_id,
        )
        if not escalation.changed:
            return False
        promoted = self._promotion_routes.get(escalation.state.profile)
        if promoted is None or promoted.profile is not escalation.state.profile:
            return False
        updated = route_lane_payload(promoted)
        updated.update(
            {
                "escalation_count": escalation.state.escalation_count,
                "failure_signatures": list(escalation.state.failure_signatures),
                "checkpoint_id": checkpoint_id,
                "promotion_reason": escalation.reason,
            }
        )
        self.store.update_route_lane(
            task_id, updated, expected_revision=int(stored["revision"])
        )
        return True

    def promotion_count(self, task_id: str) -> int:
        lane = self.store.get_route_lane(task_id) or {}
        return int(lane.get("escalation_count", 0))


def route_lane_payload(route: RouteDecision) -> dict[str, Any]:
    candidate = route.candidate
    return {
        "profile": route.profile.value,
        "candidate": {
            "provider": candidate.provider,
            "model_id": candidate.model_id,
            "version": candidate.version,
            "profile": candidate.profile.value,
            "context_window": candidate.context_window,
            "input_cost_per_million": candidate.input_cost_per_million,
            "output_cost_per_million": candidate.output_cost_per_million,
            "typical_latency_ms": candidate.typical_latency_ms,
            "context_overhead_tokens": candidate.context_overhead_tokens,
            "capabilities": sorted(candidate.capabilities),
            "enabled": candidate.enabled,
        },
        "reason": route.reason,
        "estimated_cost": route.estimated_cost,
        "calibration_success_rate": route.calibration_success_rate,
        "escalation_count": 0,
        "failure_signatures": [],
        "checkpoint_id": None,
    }


def route_from_lane(payload: dict[str, Any]) -> RouteDecision:
    raw = payload["candidate"]
    candidate = ModelCandidate(
        provider=raw["provider"],
        model_id=raw["model_id"],
        version=raw["version"],
        profile=SemanticProfile(raw["profile"]),
        context_window=int(raw["context_window"]),
        input_cost_per_million=raw.get("input_cost_per_million"),
        output_cost_per_million=raw.get("output_cost_per_million"),
        typical_latency_ms=raw.get("typical_latency_ms"),
        context_overhead_tokens=int(raw.get("context_overhead_tokens", 0)),
        capabilities=frozenset(raw.get("capabilities", ())),
        enabled=bool(raw.get("enabled", True)),
    )
    return RouteDecision(
        candidate=candidate,
        profile=SemanticProfile(payload["profile"]),
        reason=payload["reason"],
        estimated_cost=payload.get("estimated_cost"),
        calibration_success_rate=payload.get("calibration_success_rate"),
    )
