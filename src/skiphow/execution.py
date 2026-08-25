"""Compatibility stub for the retired legacy campaign executor."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .adapters.base import AgentProviderAdapter, PermissionMode
from .model_routing import RouteDecision, RoutingPolicy
from .runner import DurableRunner


class CampaignExecutor:
    """Reject legacy execution that bypasses supervised runtime controls."""

    def __init__(
        self,
        runner: DurableRunner,
        provider: AgentProviderAdapter,
        *,
        cwd: Path,
        permissions: PermissionMode = PermissionMode.WORKSPACE_WRITE,
        promotion_routes: Sequence[RouteDecision] = (),
        routing_policy: RoutingPolicy | None = None,
    ) -> None:
        del runner, provider, cwd, permissions, promotion_routes, routing_policy
        raise RuntimeError(
            "CampaignExecutor is retired because it bypasses supervised runtime "
            "controls; use CampaignSupervisor with runtime security policy, durable "
            "security audit, and environment verification"
        )
