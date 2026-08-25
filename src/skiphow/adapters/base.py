"""Provider-neutral contract for durable agent sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Capability(StrEnum):
    START = "start"
    RESUME = "resume"
    FORK = "fork"
    SEND = "send"
    STREAM = "stream"
    INTERRUPT = "interrupt"
    COMPACT = "compact"
    USAGE = "usage"
    CLEANUP = "cleanup"
    MODEL_DISCOVERY = "model_discovery"
    SUBAGENT_ATTRIBUTION = "subagent_attribution"
    BUDGET = "budget"
    COMPACT_HOOKS = "compact_hooks"


class PermissionMode(StrEnum):
    READ_ONLY = "read_only"
    WORKSPACE_WRITE = "workspace_write"
    FULL_ACCESS = "full_access"


class ContextHealth(StrEnum):
    HEALTHY = "HEALTHY"
    APPROACHING_LIMIT = "APPROACHING_LIMIT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    provider: str
    supported: frozenset[Capability]
    details: Mapping[str, Any] = field(default_factory=dict)

    def has(self, capability: Capability) -> bool:
        return capability in self.supported


@dataclass(frozen=True, slots=True)
class ModelInfo:
    provider: str
    model_id: str
    model_version: str | None = None
    profiles: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset()
    context_limit: int | None = None
    pricing: Mapping[str, float] | None = None
    latency_class: str | None = None
    availability: str = "unknown"
    deprecated: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SessionRef:
    provider: str
    session_id: str
    model_id: str | None = None
    turn_id: str | None = None
    parent_session_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StreamEvent:
    provider: str
    session_id: str
    kind: str
    data: Mapping[str, Any]
    turn_id: str | None = None
    subagent_id: str | None = None


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float | None = None
    context_tokens: int | None = None
    context_limit: int | None = None
    context_health: ContextHealth = ContextHealth.UNKNOWN
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ProviderError(RuntimeError):
    """A provider operation failed or returned an invalid response."""


class AgentProviderAdapter(ABC):
    """The only provider session interface used by the runner."""

    @abstractmethod
    async def discover_capabilities(self) -> ProviderCapabilities: ...

    @abstractmethod
    async def list_models(self) -> Sequence[ModelInfo]: ...

    @abstractmethod
    async def start_session(
        self,
        input: str,
        *,
        cwd: Path,
        permissions: PermissionMode,
        model_profile: str | None = None,
        model_id: str | None = None,
        budget_usd: float | None = None,
    ) -> SessionRef: ...

    @abstractmethod
    async def resume_session(
        self, session_id: str, *, checkpoint: Mapping[str, Any] | None = None
    ) -> SessionRef: ...

    @abstractmethod
    async def fork_session(
        self, session_id: str, *, checkpoint: Mapping[str, Any] | None = None
    ) -> SessionRef: ...

    @abstractmethod
    async def send_turn(self, session_id: str, input: str) -> SessionRef: ...

    @abstractmethod
    def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]: ...

    @abstractmethod
    async def interrupt(self, session_id: str) -> None: ...

    @abstractmethod
    async def compact(self, session_id: str) -> None: ...

    @abstractmethod
    async def usage(self, session_id: str) -> Usage: ...

    @abstractmethod
    async def cleanup(self, session_id: str) -> None: ...
