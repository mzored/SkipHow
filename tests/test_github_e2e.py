"""Deterministic contracts for the opt-in GitHub lifecycle gate."""

from __future__ import annotations

import importlib.util
import base64
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
        "schema_version": 1,
        "harness_version": "1",
        "run_id": run_id,
        "owner": "example",
        "repo": f"example/{e2e.REPO_PREFIX}{run_id.lower()}",
        "ownership_marker": f"skiphow-github-e2e:{run_id}",
        "workspace": "/tmp/skiphow-test.workspace",
        "completed_phases": [],
        "events": [],
    }


def test_live_gate_requires_two_independent_opt_ins(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv(e2e.ENV_OPT_IN, raising=False)
    assert e2e.main(["--state", str(tmp_path / "state.json"), "--owner", "example"]) == 2
    assert e2e.ENV_OPT_IN in capsys.readouterr().err
    assert not (tmp_path / "state.json").exists()


def test_new_state_uses_private_disposable_identity(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    with patch.object(
        e2e,
        "candidate_identity",
        return_value={"repository_revision": "a" * 40, "repository_dirty": False},
    ):
        value = e2e.new_state(path, "example")
    assert value["repo"].startswith(f"example/{e2e.REPO_PREFIX}")
    assert value["ownership_marker"].endswith(value["run_id"])
    assert e2e.repo_name_is_owned(value)
    assert json.loads(path.read_text())["repo"] == value["repo"]


def test_repository_creation_is_private_and_reconciles_after_crash() -> None:
    value = state()
    absent = completed(returncode=1, stderr="gh: Not Found (HTTP 404)")
    present = completed(
        json.dumps(
            {
                "full_name": value["repo"],
                "private": True,
                "description": value["ownership_marker"],
                "archived": False,
                "html_url": "https://github.com/example/sandbox",
            }
        )
    )
    with patch.object(e2e, "run", side_effect=[absent, completed(), present]) as run:
        result = e2e.ensure_repository(value)
    assert result["private"] is True
    creation = run.call_args_list[1].args[0]
    assert creation[:3] == ["gh", "repo", "create"]
    assert "--private" in creation
    assert "--public" not in creation


def test_remote_ref_treats_an_empty_repository_as_missing() -> None:
    empty = completed(
        returncode=1,
        stderr="gh: Git Repository is empty. (HTTP 409)",
    )
    with patch.object(e2e, "run", return_value=empty):
        assert e2e.remote_ref("example/skiphow-e2e", "main") is None


def test_repository_ownership_refuses_public_or_mismatched_remote() -> None:
    value = state()
    payload = {
        "full_name": value["repo"],
        "private": False,
        "description": value["ownership_marker"],
        "archived": False,
    }
    with patch.object(e2e, "run", return_value=completed(json.dumps(payload))):
        with pytest.raises(e2e.GateError, match="ownership marker"):
            e2e.remote_repo(value)
    value["repo"] = "example/not-owned"
    with pytest.raises(e2e.GateError, match="owned disposable"):
        e2e.remote_repo(value)


def test_transient_remote_error_is_not_treated_as_absence() -> None:
    value = state()
    with patch.object(
        e2e,
        "run",
        return_value=completed(returncode=1, stderr="network down"),
    ):
        with pytest.raises(e2e.GateError, match="network down"):
            e2e.remote_repo(value, missing_ok=True)


def test_repository_marker_file_binds_cleanup_to_run_identity() -> None:
    value = state()
    marker = json.dumps(
        {
            "run_id": value["run_id"],
            "ownership_marker": value["ownership_marker"],
        }
    ).encode()
    payload = {"encoding": "base64", "content": base64.b64encode(marker).decode()}
    with patch.object(e2e, "json_output", return_value=payload):
        e2e.verify_repository_marker_file(value)
    payload["content"] = base64.b64encode(b'{"run_id":"other"}').decode()
    with patch.object(e2e, "json_output", return_value=payload):
        with pytest.raises(e2e.GateError, match="does not match"):
            e2e.verify_repository_marker_file(value)


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


def test_initial_commit_writes_a_noninteractive_pull_request_workflow(tmp_path: Path) -> None:
    value = state()
    value["workspace"] = str(tmp_path / "workspace")

    def fake_run(command, **kwargs):
        if command[:4] == ["git", "remote", "get-url", "origin"]:
            return completed(f"https://github.com/{value['repo']}.git\n")
        if command == ["git", "remote"]:
            return completed("origin\n")
        if command[:3] == ["git", "diff", "--cached"]:
            return completed(returncode=1)
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return completed("a" * 40 + "\n")
        return completed()

    with (
        patch.object(e2e, "remote_ref", return_value=None),
        patch.object(e2e, "run", side_effect=fake_run),
    ):
        assert e2e.ensure_initial_commit(value) == "a" * 40
    workflow = (Path(str(value["workspace"])) / ".github/workflows/e2e.yml").read_text()
    assert workflow.startswith("name: SkipHow E2E\non:\n  pull_request:\n")
    assert 'run: test -n "$GITHUB_SHA"' in workflow
    assert '\n"' not in workflow


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


def test_repository_cleanup_requires_completion_and_exact_confirmation(tmp_path: Path) -> None:
    value = state()
    path = tmp_path / "state.json"
    e2e.atomic_json(path, value)
    with pytest.raises(e2e.GateError, match="confirm-delete"):
        e2e.cleanup_repository(path, value, "example/wrong")
    with pytest.raises(e2e.GateError, match="completed lifecycle"):
        e2e.cleanup_repository(path, value, str(value["repo"]))


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
        patch.object(e2e, "ensure_repository") as ensure_repository,
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
    ensure_repository.assert_not_called()
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
