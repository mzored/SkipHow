"""Deterministic contracts for the opt-in GitHub lifecycle gate."""

from __future__ import annotations

import ast
import base64
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location(
        "check_github_e2e", ROOT / "scripts/check_github_e2e.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


e2e = load()


def completed(stdout: str = "", returncode: int = 0, stderr: str = ""):
    return e2e.subprocess.CompletedProcess([], returncode, stdout, stderr)


def state() -> dict[str, object]:
    run_id = "20260825T000000Z-0123456789"
    return {
        "schema_version": 2,
        "harness_version": "2",
        "run_id": run_id,
        "owner": "example",
        "repo": "example/skiphow-e2e-sandbox",
        "repo_id": 42,
        "branch": f"{e2e.BRANCH_PREFIX}{run_id.lower()}",
        "baseline_issue_states": {},
        "workspace": "/tmp/skiphow-test.workspace",
        "completed_phases": [],
        "events": [],
    }


def test_live_gate_requires_two_independent_opt_ins(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv(e2e.ENV_OPT_IN, raising=False)
    assert e2e.main(
        ["--state", str(tmp_path / "state.json"), "--repo", "example/sandbox"]
    ) == 2
    assert e2e.ENV_OPT_IN in capsys.readouterr().err
    assert not (tmp_path / "state.json").exists()


def test_new_state_binds_preprovisioned_sandbox_id_and_unique_branch(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    candidate = {"repository_revision": "a" * 40, "repository_dirty": False}
    with (
        patch.object(e2e, "candidate_identity", return_value=candidate),
        patch.object(e2e, "inspect_sandbox", return_value={"id": 42}),
        patch.object(e2e, "active_sandbox_branches", return_value=[]),
        patch.object(e2e, "issue_state_map", return_value={1: "CLOSED"}),
        patch.object(
            e2e,
            "run",
            return_value=completed("https://github.com/example/source.git\n"),
        ),
    ):
        value = e2e.new_state(path, "example/skiphow-e2e-sandbox")
    assert value["repo"] == "example/skiphow-e2e-sandbox"
    assert value["repo_id"] == 42
    assert value["branch"] == f"{e2e.BRANCH_PREFIX}{value['run_id'].lower()}"
    assert json.loads(path.read_text())["repo"] == value["repo"]


def test_new_state_refuses_candidate_repository(tmp_path: Path) -> None:
    with patch.object(
        e2e,
        "run",
        return_value=completed("https://github.com/example/source.git\n"),
    ):
        with pytest.raises(e2e.GateError, match="candidate repository"):
            e2e.new_state(tmp_path / "state.json", "example/source")


def test_new_state_refuses_an_already_active_sandbox(tmp_path: Path) -> None:
    with (
        patch.object(
            e2e,
            "run",
            return_value=completed("https://github.com/example/source.git\n"),
        ),
        patch.object(e2e, "inspect_sandbox", return_value={"id": 42}),
        patch.object(
            e2e,
            "active_sandbox_branches",
            return_value=["refs/heads/skiphow/e2e-active"],
        ),
    ):
        with pytest.raises(e2e.GateError, match="already has an active E2E branch"):
            e2e.new_state(tmp_path / "state.json", "example/sandbox")


def test_harness_has_no_repository_create_or_delete_command() -> None:
    tree = ast.parse((ROOT / "scripts/check_github_e2e.py").read_text())
    repository_actions = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue
        values = [item.value for item in node.elts if isinstance(item, ast.Constant)]
        if values[:2] == ["gh", "repo"]:
            repository_actions.append(values[2] if len(values) > 2 else "")
    assert not ({"create", "delete"} & set(repository_actions))


def test_remote_ref_treats_an_empty_repository_as_missing() -> None:
    empty = completed(
        returncode=1,
        stderr="gh: Git Repository is empty. (HTTP 409)",
    )
    with patch.object(e2e, "run", return_value=empty):
        assert e2e.remote_ref("example/skiphow-e2e", "main") is None


def test_inspect_sandbox_requires_private_marked_repo_and_workflow() -> None:
    marker = base64.b64encode(json.dumps(e2e.SANDBOX_MARKER).encode()).decode()
    repository = {
        "id": 42,
        "full_name": "example/skiphow-e2e-sandbox",
        "private": True,
        "description": e2e.SANDBOX_DESCRIPTION,
        "default_branch": "main",
        "has_issues": True,
        "archived": False,
    }
    with patch.object(
        e2e,
        "json_output",
        side_effect=[
            repository,
            {"encoding": "base64", "content": marker},
            {
                "encoding": "base64",
                "content": base64.b64encode(e2e.SANDBOX_WORKFLOW.encode()).decode(),
            },
        ],
    ):
        assert e2e.inspect_sandbox("example/skiphow-e2e-sandbox", 42) == repository

    repository["private"] = False
    with patch.object(e2e, "json_output", return_value=repository):
        with pytest.raises(e2e.GateError, match="required private"):
            e2e.inspect_sandbox("example/skiphow-e2e-sandbox")

    repository["private"] = True
    with patch.object(e2e, "json_output", return_value=repository):
        with pytest.raises(e2e.GateError, match="ID changed"):
            e2e.inspect_sandbox("example/skiphow-e2e-sandbox", 99)


def test_transient_remote_error_is_not_treated_as_absence() -> None:
    value = state()
    with patch.object(
        e2e,
        "inspect_sandbox",
        side_effect=e2e.GateError("network down"),
    ):
        with pytest.raises(e2e.GateError, match="network down"):
            e2e.remote_repo(value)


def test_sandbox_marker_declares_fixed_purpose() -> None:
    marker = json.dumps(e2e.SANDBOX_MARKER).encode()
    payload = {"encoding": "base64", "content": base64.b64encode(marker).decode()}
    with patch.object(e2e, "json_output", return_value=payload):
        assert e2e.sandbox_marker("example/sandbox") == e2e.SANDBOX_MARKER
    payload["content"] = base64.b64encode(b'{"purpose":"other"}').decode()
    with patch.object(e2e, "json_output", return_value=payload):
        with pytest.raises(e2e.GateError, match="does not declare"):
            e2e.sandbox_marker("example/sandbox")


def test_issue_replay_uses_marker_before_create() -> None:
    existing = {
        "number": 4,
        "title": "Delivery",
        "body": "<!-- marker -->",
        "state": "OPEN",
        "url": "https://github.com/example/repo/issues/4",
    }
    with (
        patch.object(e2e, "issue_rows", return_value=[existing]),
        patch.object(e2e, "run") as run,
    ):
        assert e2e.ensure_issue(
            "example/repo", marker="marker", title="Delivery", body="body"
        ) == existing
    run.assert_not_called()


def test_existing_workspace_with_another_origin_is_refused(tmp_path: Path) -> None:
    value = state()
    workspace = tmp_path / "workspace"
    value["workspace"] = str(workspace)
    workspace.mkdir()
    (workspace / ".git").mkdir()
    (workspace / ".skiphow-e2e-workspace.json").write_text(
        json.dumps(e2e.workspace_marker(value)), encoding="utf-8"
    )

    def fake_run(command, **kwargs):
        if command == ["git", "remote"]:
            return completed("origin\n")
        if command[:4] == ["git", "remote", "get-url", "origin"]:
            return completed("https://github.com/example/unrelated.git\n")
        return completed()

    with patch.object(e2e, "run", side_effect=fake_run):
        with pytest.raises(e2e.GateError, match="origin does not match"):
            e2e.ensure_workspace(value)


def test_native_dependency_must_be_observed_before_signal_closes() -> None:
    value = state()
    signal = {"number": 1, "state": "OPEN"}
    delivery = {"number": 2, "state": "OPEN", "blockedBy": []}
    with patch.object(e2e, "ensure_issue", side_effect=[signal, delivery]):
        with pytest.raises(e2e.GateError, match="native blocking dependency"):
            e2e.ensure_issues(value)


def test_native_dependency_accepts_graphql_connection_shape() -> None:
    value = state()
    signal = {"number": 1, "state": "CLOSED"}
    delivery = {
        "number": 2,
        "state": "OPEN",
        "blockedBy": {"nodes": [{"number": 1}], "totalCount": 1},
    }
    with patch.object(e2e, "ensure_issue", side_effect=[signal, delivery]):
        observed_signal, observed_delivery = e2e.ensure_issues(value)
    assert observed_signal["number"] == 1
    assert observed_delivery["number"] == 2


def test_checks_bind_success_to_exact_head() -> None:
    head = "a" * 40
    assert e2e.checks_green(
        {"headRefOid": head, "statusCheckRollup": [{"name": "verify", "conclusion": "SUCCESS"}]},
        head,
    )
    assert not e2e.checks_green({"headRefOid": head, "statusCheckRollup": []}, head)
    with pytest.raises(e2e.GateError, match="head changed"):
        e2e.checks_green({"headRefOid": "b" * 40, "statusCheckRollup": []}, head)
    with pytest.raises(e2e.GateError, match="check failed"):
        e2e.checks_green(
            {"headRefOid": head, "statusCheckRollup": [{"name": "verify", "conclusion": "FAILURE"}]},
            head,
        )


def test_branch_cleanup_requires_merged_exact_head() -> None:
    value = state()
    head = "a" * 40
    with patch.object(
        e2e,
        "pr_state",
        return_value={"state": "MERGED", "headRefOid": "b" * 40},
    ):
        with pytest.raises(e2e.GateError, match="exact merged"):
            e2e.cleanup_branch(value, 3, head)


def test_completed_resume_only_reconciles_and_rewrites_receipt(tmp_path: Path) -> None:
    value = state()
    value.update(
        {
            "completed_phases": list(e2e.PHASES),
            "delivery_issue": 2,
            "pull_request": 3,
            "delivery_head": "a" * 40,
        }
    )
    with (
        patch.object(e2e, "remote_repo", return_value={"private": True}),
        patch.object(
            e2e,
            "pr_state",
            return_value={"state": "MERGED", "headRefOid": "a" * 40},
        ),
        patch.object(e2e, "verify_issue_closed", return_value={"state": "CLOSED"}),
        patch.object(e2e, "remote_ref", return_value=None),
        patch.object(e2e, "write_receipt") as write_receipt,
        patch.object(e2e, "ensure_branch") as ensure_branch,
    ):
        e2e.execute(
            tmp_path / "state.json",
            value,
            timeout_seconds=1,
            poll_seconds=0.01,
            receipt_path=tmp_path / "receipt.json",
            crash_after=None,
        )
    write_receipt.assert_called_once()
    ensure_branch.assert_not_called()


def test_receipt_grades_against_github_scenario(tmp_path: Path) -> None:
    value = state()
    value.update(
        {
            "delivery_issue": 2,
            "pull_request": 3,
            "delivery_head": "a" * 40,
            "forced_interruption": {
                "phase": "pull_request",
                "at": "2026-08-25T00:00:00Z",
                "exit_code": 75,
            },
            "resume_count": 1,
            "final_reconciliation": {
                "default_contains_delivery": True,
                "owned_branch_exists": False,
                "unrelated_issues_closed": 0,
            },
            "events": [
                {"phase": phase, "at": "2026-08-25T00:00:00Z", "evidence": {}}
                for phase in ("issues", "pull_request", "ci_success", "merge", "branch_cleanup")
            ],
        }
    )
    receipt = tmp_path / "receipt.json"
    candidate = {"repository_revision": "a" * 40, "repository_dirty": False}
    value["candidate"] = candidate
    with patch.object(e2e, "candidate_identity", return_value=candidate):
        e2e.write_receipt(receipt, value)
    from evals.graders.outcome import grade_files

    report = grade_files(ROOT / "evals/scenarios/github-lifecycle.json", receipt)
    assert report.passed, report.as_dict()
