"""Versioned records and state transitions for the durable runner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping
from uuid import uuid4


SCHEMA_VERSION = 1
FINDING_DISPOSITIONS = frozenset({"RESOLVED", "PERSISTED", "DUPLICATE", "DISMISSED"})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SchemaError(ValueError):
    """Raised when a persisted record does not match its schema."""


class TransitionError(ValueError):
    """Raised for a disallowed state transition."""


class RunStatus(StrEnum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    PAUSED = "PAUSED"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStatus(StrEnum):
    PROPOSED = "PROPOSED"
    READY = "READY"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    VERIFYING = "VERIFYING"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    CIRCUIT_BROKEN = "CIRCUIT_BROKEN"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


RUN_TERMINAL = frozenset(
    {RunStatus.COMPLETED, RunStatus.BLOCKED, RunStatus.FAILED, RunStatus.CANCELLED}
)
TASK_TERMINAL = frozenset(
    {
        TaskStatus.DONE,
        TaskStatus.BLOCKED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.SUPERSEDED,
    }
)

RUN_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.NEW: frozenset({RunStatus.READY, RunStatus.CANCELLED}),
    RunStatus.READY: frozenset({RunStatus.RUNNING, RunStatus.PAUSED, RunStatus.CANCELLED}),
    RunStatus.RUNNING: frozenset(
        {
            RunStatus.WAITING_EXTERNAL,
            RunStatus.PAUSED,
            RunStatus.VERIFYING,
            RunStatus.COMPLETED,
            RunStatus.BLOCKED,
            RunStatus.FAILED,
            RunStatus.CANCELLED,
        }
    ),
    RunStatus.WAITING_EXTERNAL: frozenset(
        {RunStatus.RUNNING, RunStatus.PAUSED, RunStatus.BLOCKED, RunStatus.CANCELLED}
    ),
    RunStatus.PAUSED: frozenset({RunStatus.RUNNING, RunStatus.CANCELLED}),
    RunStatus.VERIFYING: frozenset(
        {RunStatus.RUNNING, RunStatus.COMPLETED, RunStatus.BLOCKED, RunStatus.FAILED, RunStatus.CANCELLED}
    ),
    **{status: frozenset() for status in RUN_TERMINAL},
}

TASK_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PROPOSED: frozenset({TaskStatus.READY, TaskStatus.CANCELLED, TaskStatus.SUPERSEDED}),
    TaskStatus.READY: frozenset({TaskStatus.CLAIMED, TaskStatus.CANCELLED, TaskStatus.SUPERSEDED}),
    TaskStatus.CLAIMED: frozenset({TaskStatus.RUNNING, TaskStatus.READY, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.WAITING_EXTERNAL,
            TaskStatus.VERIFYING,
            TaskStatus.READY,
            TaskStatus.BLOCKED,
            TaskStatus.CIRCUIT_BROKEN,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.WAITING_EXTERNAL: frozenset(
        {TaskStatus.READY, TaskStatus.RUNNING, TaskStatus.BLOCKED, TaskStatus.CANCELLED}
    ),
    TaskStatus.VERIFYING: frozenset(
        {TaskStatus.DONE, TaskStatus.RUNNING, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED}
    ),
    TaskStatus.CIRCUIT_BROKEN: frozenset({TaskStatus.READY, TaskStatus.BLOCKED, TaskStatus.CANCELLED}),
    **{status: frozenset() for status in TASK_TERMINAL},
}


def validate_transition(current: StrEnum, target: StrEnum, transitions: Mapping[StrEnum, frozenset[StrEnum]]) -> None:
    if target == current:
        return
    if target not in transitions[current]:
        raise TransitionError(f"cannot transition {current.value} to {target.value}")


def _require(record: Mapping[str, Any], field_name: str, expected: type) -> Any:
    value = record.get(field_name)
    if not isinstance(value, expected) or expected is int and isinstance(value, bool):
        raise SchemaError(f"{field_name} must be {expected.__name__}")
    return value


def _version(record: Mapping[str, Any]) -> None:
    version = _require(record, "schema_version", int)
    if version != SCHEMA_VERSION:
        raise SchemaError(f"unsupported schema_version {version}")


@dataclass(frozen=True, slots=True)
class Run:
    run_id: str
    original_request: str
    authority: dict[str, Any]
    status: RunStatus = RunStatus.NEW
    revision: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    budget: dict[str, Any] = field(default_factory=dict)
    cancel_requested: bool = False
    next_action: str = ""
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def create(cls, original_request: str, authority: Mapping[str, Any], *, run_id: str | None = None, budget: Mapping[str, Any] | None = None) -> "Run":
        if not original_request.strip():
            raise SchemaError("original_request must not be empty")
        return cls(run_id or uuid4().hex, original_request, dict(authority), budget=dict(budget or {}))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Run":
        _version(value)
        return cls(
            run_id=_require(value, "run_id", str),
            original_request=_require(value, "original_request", str),
            authority=dict(_require(value, "authority", dict)),
            status=RunStatus(_require(value, "status", str)),
            revision=_require(value, "revision", int),
            created_at=_require(value, "created_at", str),
            updated_at=_require(value, "updated_at", str),
            budget=dict(_require(value, "budget", dict)),
            cancel_requested=_require(value, "cancel_requested", bool),
            next_action=_require(value, "next_action", str),
            schema_version=SCHEMA_VERSION,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Task:
    task_id: str
    run_id: str
    outcome: str
    constraints: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    status: TaskStatus = TaskStatus.PROPOSED
    revision: int = 0
    priority: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    next_action: str = ""
    failure_signature: str | None = None
    failure_count: int = 0
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def create(cls, run_id: str, outcome: str, *, task_id: str | None = None, constraints: tuple[str, ...] = (), dependencies: tuple[str, ...] = (), priority: int = 0) -> "Task":
        if not outcome.strip():
            raise SchemaError("outcome must not be empty")
        return cls(task_id or uuid4().hex, run_id, outcome, tuple(constraints), tuple(dependencies), priority=priority)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Task":
        _version(value)
        constraints = _require(value, "constraints", list)
        dependencies = _require(value, "dependencies", list)
        if not all(isinstance(item, str) for item in constraints + dependencies):
            raise SchemaError("constraints and dependencies must contain strings")
        failure_signature = value.get("failure_signature")
        if failure_signature is not None and not isinstance(failure_signature, str):
            raise SchemaError("failure_signature must be string or null")
        return cls(
            task_id=_require(value, "task_id", str), run_id=_require(value, "run_id", str),
            outcome=_require(value, "outcome", str), constraints=tuple(constraints), dependencies=tuple(dependencies),
            status=TaskStatus(_require(value, "status", str)), revision=_require(value, "revision", int),
            priority=_require(value, "priority", int), created_at=_require(value, "created_at", str),
            updated_at=_require(value, "updated_at", str), next_action=_require(value, "next_action", str),
            failure_signature=failure_signature, failure_count=_require(value, "failure_count", int), schema_version=SCHEMA_VERSION,
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["constraints"] = list(self.constraints)
        value["dependencies"] = list(self.dependencies)
        return value


@dataclass(frozen=True, slots=True)
class Event:
    event_id: str
    run_id: str
    kind: str
    occurred_at: str
    data: dict[str, Any]
    task_id: str | None = None
    sequence: int | None = None
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def create(cls, run_id: str, kind: str, data: Mapping[str, Any], *, task_id: str | None = None) -> "Event":
        if not kind.strip():
            raise SchemaError("kind must not be empty")
        return cls(uuid4().hex, run_id, kind, utc_now(), dict(data), task_id)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Event":
        _version(value)
        task_id = value.get("task_id")
        sequence = value.get("sequence")
        if task_id is not None and not isinstance(task_id, str):
            raise SchemaError("task_id must be string or null")
        if sequence is not None and (not isinstance(sequence, int) or isinstance(sequence, bool)):
            raise SchemaError("sequence must be integer or null")
        return cls(
            event_id=_require(value, "event_id", str), run_id=_require(value, "run_id", str),
            kind=_require(value, "kind", str), occurred_at=_require(value, "occurred_at", str),
            data=dict(_require(value, "data", dict)), task_id=task_id, sequence=sequence,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: str
    run_id: str
    summary: str
    disposition: str
    created_at: str = field(default_factory=utc_now)
    task_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def create(cls, run_id: str, summary: str, disposition: str, *, task_id: str | None = None, details: Mapping[str, Any] | None = None) -> "Finding":
        if not summary.strip() or disposition not in FINDING_DISPOSITIONS:
            raise SchemaError(
                "summary must not be empty and disposition must be a terminal finding state"
            )
        return cls(uuid4().hex, run_id, summary, disposition, task_id=task_id, details=dict(details or {}))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Finding":
        _version(value)
        task_id = value.get("task_id")
        if task_id is not None and not isinstance(task_id, str):
            raise SchemaError("task_id must be string or null")
        disposition = _require(value, "disposition", str)
        if disposition not in FINDING_DISPOSITIONS:
            raise SchemaError("invalid finding disposition")
        return cls(
            finding_id=_require(value, "finding_id", str), run_id=_require(value, "run_id", str),
            summary=_require(value, "summary", str), disposition=disposition,
            created_at=_require(value, "created_at", str), task_id=task_id,
            details=dict(_require(value, "details", dict)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
