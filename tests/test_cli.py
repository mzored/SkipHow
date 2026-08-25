"""End-to-end CLI controls use the durable store, not process memory."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def invoke(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = {"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    import os

    return subprocess.run(
        [sys.executable, "-m", "skiphow", "--project-root", str(project), *args],
        cwd=ROOT,
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def test_cli_start_status_pause_resume_cancel_survive_processes(tmp_path: Path) -> None:
    started = invoke(
        tmp_path,
        "start",
        "Work through the backlog overnight",
        "--run-id",
        "run-1",
        "--task",
        "Deliver the first slice",
    )
    assert started.returncode == 0, started.stderr
    assert json.loads(started.stdout)["status"] == "RUNNING"

    assert invoke(tmp_path, "pause", "run-1").returncode == 0
    status = invoke(tmp_path, "status", "run-1")
    assert json.loads(status.stdout)["status"] == "PAUSED"
    assert invoke(tmp_path, "resume", "run-1").returncode == 0
    cancelled = invoke(tmp_path, "cancel", "run-1")
    assert json.loads(cancelled.stdout)["status"] == "CANCELLED"

    exported = invoke(tmp_path, "export", "run-1")
    receipt = json.loads(exported.stdout)
    assert receipt["run"]["original_request"] == "Work through the backlog overnight"
    assert receipt["events"][0]["kind"] == "run_created"


def test_cli_rejects_database_outside_project(tmp_path: Path) -> None:
    result = invoke(
        tmp_path,
        "--database",
        str(tmp_path.parent / "outside.sqlite3"),
        "status",
        "missing",
    )
    assert result.returncode == 2
    assert "database must remain inside" in result.stderr


def test_cli_intake_dry_run_and_explicit_local_persistence(tmp_path: Path) -> None:
    source = tmp_path / "signals.json"
    source.write_text(json.dumps(["Idea: add reports", "Checkout might fail"]), encoding="utf-8")
    dry = invoke(tmp_path, "intake", str(source))
    assert dry.returncode == 0
    assert json.loads(dry.stdout)["persisted"] is False
    assert not (tmp_path / ".skiphow/intake").exists()

    persisted = invoke(tmp_path, "intake", str(source), "--persist")
    assert persisted.returncode == 0
    assert json.loads(persisted.stdout)["store"]["signals_added"] == 2


def test_cli_intake_runs_grouping_triage_and_idempotent_work_item_pipeline(
    tmp_path: Path,
) -> None:
    source = tmp_path / "signals.json"
    source.write_text(
        json.dumps(
            {
                "signals": [
                    {
                        "verbatim": "- Checkout duplicate charge\n- Duplicate checkout charge",
                        "source": "support-call",
                        "source_record_id": "call-9",
                        "observed_evidence": ["charge ids 1 and 2"],
                        "confidence": 0.9,
                    },
                    "Idea: add saved cards",
                    "The new colors are pleasant",
                    "Could invoices be wrong?",
                ]
            }
        ),
        encoding="utf-8",
    )
    preview = invoke(tmp_path, "intake", str(source))
    assert preview.returncode == 0, preview.stderr
    value = json.loads(preview.stdout)
    assert value["persisted"] is False
    assert value["summary"] == {
        "actionable": 2,
        "dispositions": {"CREATE": 2},
        "groups": 4,
        "observed": 2,
        "recommendations": {"LATER": 1, "NOW": 1},
        "signal_types": {"BUG": 2, "FEEDBACK": 1, "IDEA": 1, "QUESTION": 1},
        "signals": 5,
        "speculative": 3,
    }
    assert not (tmp_path / ".skiphow/intake").exists()

    first = invoke(tmp_path, "intake", str(source), "--persist")
    second = invoke(tmp_path, "intake", str(source), "--persist")
    assert first.returncode == second.returncode == 0
    assert json.loads(first.stdout)["store"]["work_items"] == 2
    replay = json.loads(second.stdout)
    assert replay["store"]["signals_added"] == 0
    assert replay["summary"]["dispositions"] == {"UNCHANGED": 2}


def test_cli_intake_requires_controller_decision_for_candidate_then_merges_provenance(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.json"
    first_path.write_text(json.dumps(["Idea: add weekly report"]), encoding="utf-8")
    assert invoke(tmp_path, "intake", str(first_path), "--persist").returncode == 0

    second_path = tmp_path / "second.json"
    payload = {
        "signals": [
            {
                "verbatim": "Idea: add weekly reports",
                "source_record_id": "request-2",
                "source": "customer-2",
            }
        ]
    }
    second_path.write_text(json.dumps(payload), encoding="utf-8")
    preview = invoke(tmp_path, "intake", str(second_path))
    assert preview.returncode == 0, preview.stderr
    value = json.loads(preview.stdout)
    proposal_id = value["work_items"][0]["item_id"]
    candidate_id = value["candidates"][proposal_id][0]["item_id"]
    assert value["summary"]["dispositions"] == {"UNRESOLVED": 1}

    payload["decisions"] = [
        {
            "item_id": proposal_id,
            "candidate_item_id": candidate_id,
            "disposition": "DUPLICATE",
            "reason": "same affected user and requested outcome",
        }
    ]
    second_path.write_text(json.dumps(payload), encoding="utf-8")
    persisted = invoke(tmp_path, "intake", str(second_path), "--persist")
    assert persisted.returncode == 0, persisted.stderr
    result = json.loads(persisted.stdout)
    assert result["summary"]["dispositions"] == {"DUPLICATE": 1}
    assert result["store"]["work_items"] == 1
    stored = json.loads((tmp_path / ".skiphow/intake/work-items.json").read_text())
    assert len(stored[candidate_id]["signal_ids"]) == 2

    replay = invoke(tmp_path, "intake", str(second_path), "--persist")
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["store"]["signals_added"] == 0


def test_cli_intake_maps_explicit_epic_and_dependencies(tmp_path: Path) -> None:
    source = tmp_path / "epic.json"
    payload: dict[str, object] = {
        "signals": [
            "Idea: instrument checkout latency",
            "Idea: notify on payment failures",
        ]
    }
    source.write_text(json.dumps(payload), encoding="utf-8")
    preview = invoke(tmp_path, "intake", str(source))
    assert preview.returncode == 0, preview.stderr
    child_ids = [item["item_id"] for item in json.loads(preview.stdout)["work_items"]]
    assert len(child_ids) == 2
    payload["epic"] = {
        "item_id": "epic-checkout",
        "title": "Detect checkout failures",
        "outcome": "Operators detect checkout failures before customers report them",
        "why": "Checkout failures cost revenue",
        "acceptance": ["Both independently deliverable checks are live"],
        "children": child_ids,
        "dependencies": {child_ids[1]: [child_ids[0]]},
    }
    source.write_text(json.dumps(payload), encoding="utf-8")
    first = invoke(tmp_path, "intake", str(source), "--persist")
    assert first.returncode == 0, first.stderr
    result = json.loads(first.stdout)
    assert result["epic"]["children"] == child_ids
    assert result["store"]["work_items"] == 3

    replay = invoke(tmp_path, "intake", str(source), "--persist")
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["store"]["work_items"] == 3


def test_cli_intake_honors_explicit_github_and_disabled_trackers(tmp_path: Path) -> None:
    source = tmp_path / "signals.json"
    source.write_text(json.dumps(["Idea: add reports"]), encoding="utf-8")

    configured = invoke(
        tmp_path,
        "setup",
        "--tracker",
        "github",
        "--project",
        "owner/7",
    )
    assert configured.returncode == 0, configured.stderr
    github = invoke(tmp_path, "intake", str(source), "--persist")
    assert github.returncode == 2
    assert "requires the SkipHow plugin Intake workflow" in github.stderr
    assert "will not substitute .skiphow/intake" in github.stderr
    assert not (tmp_path / ".skiphow/intake").exists()

    disabled = invoke(tmp_path, "setup", "--tracker", "none")
    assert disabled.returncode == 0, disabled.stderr
    none = invoke(tmp_path, "intake", str(source), "--persist")
    assert none.returncode == 2
    assert "persistence is disabled by tracker=none" in none.stderr
    assert not (tmp_path / ".skiphow/intake").exists()


def test_cli_setup_migrates_v1_with_backup(tmp_path: Path) -> None:
    config = tmp_path / ".skiphow/config.json"
    config.parent.mkdir()
    config.write_text('{"tracker":"local"}\n', encoding="utf-8")
    result = invoke(tmp_path, "setup", "--tracker", "github", "--project", "owner/7")
    assert result.returncode == 0, result.stderr
    value = json.loads(config.read_text(encoding="utf-8"))
    assert value["schema_version"] == 2
    assert value["tracker"] == {"type": "github", "project": "owner/7"}
    assert config.with_suffix(".json.v1.bak").read_text() == '{"tracker":"local"}\n'
