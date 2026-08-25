from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
import sys

import pytest

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
from skiphow.execution import CampaignExecutor
from skiphow.runner import DurableRunner


class FakeProvider(AgentProviderAdapter):
    async def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities("fake", frozenset())

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo("fake", "local")]

    async def start_session(
        self,
        input: str,
        *,
        cwd: Path,
        permissions: PermissionMode,
        model_profile: str | None = None,
        model_id: str | None = None,
        budget_usd: float | None = None,
    ) -> SessionRef:
        raise AssertionError("retired executor must not dispatch a provider session")

    async def resume_session(self, session_id: str, *, checkpoint=None) -> SessionRef:
        raise AssertionError("retired executor must not resume a provider session")

    async def fork_session(self, session_id: str, *, checkpoint=None) -> SessionRef:
        raise AssertionError("retired executor must not fork a provider session")

    async def send_turn(self, session_id: str, input: str) -> SessionRef:
        raise AssertionError("retired executor must not send a provider turn")

    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        if False:
            yield StreamEvent("fake", session_id, "result", {})
        raise AssertionError("retired executor must not stream provider events")

    async def interrupt(self, session_id: str) -> None:
        raise AssertionError("retired executor must not interrupt a provider session")

    async def compact(self, session_id: str) -> None:
        raise AssertionError("retired executor must not compact a provider session")

    async def usage(self, session_id: str) -> Usage:
        raise AssertionError("retired executor must not query provider usage")

    async def cleanup(self, session_id: str) -> None:
        raise AssertionError("retired executor must not clean up a provider session")


@pytest.mark.parametrize("permissions", list(PermissionMode))
def test_legacy_executor_is_retired_for_every_permission_mode(
    tmp_path: Path,
    permissions: PermissionMode,
) -> None:
    runner = DurableRunner(tmp_path / "run.sqlite3")

    with pytest.raises(
        RuntimeError,
        match=(
            "CampaignExecutor is retired because it bypasses supervised runtime "
            "controls; use CampaignSupervisor"
        ),
    ):
        CampaignExecutor(
            runner,
            FakeProvider(),
            cwd=tmp_path,
            permissions=permissions,
        )


def test_legacy_executor_default_is_retired(tmp_path: Path) -> None:
    runner = DurableRunner(tmp_path / "run.sqlite3")

    with pytest.raises(RuntimeError, match="durable security audit"):
        CampaignExecutor(runner, FakeProvider(), cwd=tmp_path)
