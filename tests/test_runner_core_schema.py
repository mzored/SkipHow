"""Focused schema and transition checks for the durable runner."""

from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skiphow.schemas import (  # noqa: E402
    RUN_TERMINAL,
    RUN_TRANSITIONS,
    TASK_TERMINAL,
    TASK_TRANSITIONS,
    Run,
    RunStatus,
    Event,
    Finding,
    SchemaError,
    Task,
    TaskStatus,
    TransitionError,
    validate_transition,
)


def test_records_round_trip_and_reject_unknown_versions() -> None:
    run = Run.create("  preserve this request byte-for-byte\n", {"mutation": True}, run_id="run-1")
    assert Run.from_dict(json.loads(json.dumps(run.to_dict()))) == run
    assert run.original_request == "  preserve this request byte-for-byte\n"

    task = Task.create("run-1", "Ship the result", task_id="task-1", constraints=("local only",))
    assert Task.from_dict(json.loads(json.dumps(task.to_dict()))) == task
    event = Event.create("run-1", "checked", {"ok": True}, task_id="task-1")
    assert Event.from_dict(json.loads(json.dumps(event.to_dict()))) == event
    finding = Finding.create("run-1", "Found it", "PERSISTED", task_id="task-1")
    assert Finding.from_dict(json.loads(json.dumps(finding.to_dict()))) == finding

    invalid = run.to_dict()
    invalid["schema_version"] = 99
    with pytest.raises(SchemaError, match="unsupported schema_version 99"):
        Run.from_dict(invalid)


@pytest.mark.parametrize("status", RUN_TERMINAL)
def test_run_terminal_states_are_absorbing(status: RunStatus) -> None:
    for target in RunStatus:
        if target == status:
            continue
        with pytest.raises(TransitionError):
            validate_transition(status, target, RUN_TRANSITIONS)


@pytest.mark.parametrize("status", TASK_TERMINAL)
def test_task_terminal_states_are_absorbing(status: TaskStatus) -> None:
    for target in TaskStatus:
        if target == status:
            continue
        with pytest.raises(TransitionError):
            validate_transition(status, target, TASK_TRANSITIONS)


def test_transition_maps_accept_only_declared_edges() -> None:
    for current in RunStatus:
        for target in RunStatus:
            if target == current or target in RUN_TRANSITIONS[current]:
                validate_transition(current, target, RUN_TRANSITIONS)
            else:
                with pytest.raises(TransitionError):
                    validate_transition(current, target, RUN_TRANSITIONS)

    for current in TaskStatus:
        for target in TaskStatus:
            if target == current or target in TASK_TRANSITIONS[current]:
                validate_transition(current, target, TASK_TRANSITIONS)
            else:
                with pytest.raises(TransitionError):
                    validate_transition(current, target, TASK_TRANSITIONS)
