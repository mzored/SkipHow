"""Focused tests for optional GitHub adapters."""

import importlib.util
import hashlib
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
HEAD = "a" * 40
OTHER_HEAD = "b" * 40


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


issues = load("github_issues", "plugins/skiphow/scripts/github_issues.py")
project = load("github_project", "plugins/skiphow/scripts/github_project.py")


def test_repo_at_parses_github_origins() -> None:
    with patch.object(issues, "run", return_value="git@github.com:owner/repo.git"):
        assert issues.repo_at() == "owner/repo"
    with patch.object(issues, "run", return_value="https://github.com/owner/repo.git"):
        assert issues.repo_at() == "owner/repo"


def test_exact_title_duplicate_returns_existing_issue() -> None:
    payload = json.dumps([{"number": 7, "title": "Weekly export", "url": "https://x/7"}])
    with patch.object(issues, "run", return_value=payload):
        assert issues.find_duplicate("owner/repo", "Weekly export").number == 7


def test_substring_match_is_only_a_candidate() -> None:
    payload = json.dumps(
        [{"number": 7, "title": "Weekly export is slow", "url": "https://x/7"}]
    )
    with patch.object(issues, "run", return_value=payload):
        assert issues.find_candidates("owner/repo", "Weekly export")[0].number == 7
        assert issues.find_duplicate("owner/repo", "Weekly export") is None


def test_candidate_search_uses_evidence_and_deduplicates() -> None:
    payload = json.dumps([{"number": 7, "title": "Export failure", "url": "https://x/7"}])
    with patch.object(issues, "run", return_value=payload) as command:
        rows = issues.find_candidates("owner/repo", "Weekly export", "timeout in exporter")
    assert rows == [issues.Issue(7, "Export failure", "https://x/7")]
    assert command.call_count == 2
    assert command.call_args_list[1].args[0][8] == '"timeout in exporter"'


def test_candidate_search_quotes_qualifiers_and_rejects_empty_input() -> None:
    with patch.object(issues, "run", return_value="[]") as run:
        assert issues.find_candidates("owner/repo", 'export is:closed "failure"') == []
    assert run.call_args.args[0][8] == '"export is:closed  failure " in:title'
    with pytest.raises(issues.GitHubError, match="non-empty"):
        issues.find_candidates("owner/repo", "   ")


def test_persist_uses_native_relationships_when_supported() -> None:
    commands: list[list[str]] = []

    def fake_run(command, *, cwd="."):
        commands.append(list(command))
        return "https://github.com/owner/repo/issues/8"

    with (
        patch.object(issues, "find_duplicate", return_value=None),
        patch.object(
            issues,
            "supported_create_flags",
            return_value={"--type", "--parent", "--blocked-by"},
        ),
        patch.object(issues, "available_issue_types", return_value={"Feature"}),
        patch.object(issues, "run", side_effect=fake_run),
    ):
        url = issues.persist(
            "owner/repo", "Feature", "Weekly export", "body", parent="2", blocked_by="3"
        )
    assert url.endswith("/8")
    command = commands[-1]
    assert "--type" in command
    assert "--parent" in command
    assert "--blocked-by" in command
    assert "--label" not in command


def test_persist_falls_back_when_types_and_relationship_flags_are_unavailable() -> None:
    commands: list[list[str]] = []

    def fake_run(command, *, cwd="."):
        commands.append(list(command))
        return "https://github.com/owner/repo/issues/8"

    with (
        patch.object(issues, "find_duplicate", return_value=None),
        patch.object(issues, "supported_create_flags", return_value=set()),
        patch.object(issues, "available_issue_types", return_value=set()),
        patch.object(issues, "run", side_effect=fake_run),
    ):
        url = issues.persist(
            "owner/repo", "Feature", "Weekly export", "body", parent="2", blocked_by="3"
        )
    assert url.endswith("/8")
    command = commands[-1]
    assert command == [
        "gh",
        "issue",
        "create",
        "--repo",
        "owner/repo",
        "--title",
        "Weekly export",
        "--body",
        "body",
    ]


def test_feature_detection_is_cached_and_optional_failures_degrade() -> None:
    issues.available_issue_types.cache_clear()
    issues.supported_create_flags.cache_clear()
    with patch.object(issues, "run", side_effect=issues.GitHubError("unsupported")) as run:
        assert issues.available_issue_types("owner/repo") == set()
        assert issues.available_issue_types("owner/repo") == set()
        assert issues.supported_create_flags() == set()
        assert issues.supported_create_flags() == set()
    assert run.call_count == 2


def test_delivery_branch_creation_and_provenance_are_distinct() -> None:
    with patch.object(issues, "run", side_effect=["", "[]", ""]) as run:
        issues.create_linked_branch("owner/repo", 7, "feature/export")
        issues.record_delivery("owner/repo", 7, "https://github.com/owner/repo/pull/8")
    assert run.call_args_list[0].args[0][:3] == ["gh", "issue", "develop"]
    assert run.call_args_list[1].args[0][:3] == ["gh", "api", "repos/owner/repo/issues/7/comments"]
    assert run.call_args_list[2].args[0][:3] == ["gh", "issue", "comment"]
    assert any(
        "https://github.com/owner/repo/pull/8" in value
        for value in run.call_args_list[2].args[0]
    )


def test_persist_does_not_make_a_duplicate_decision() -> None:
    with (
        patch.object(issues, "find_duplicate") as duplicate,
        patch.object(issues, "supported_create_flags", return_value=set()),
        patch.object(issues, "available_issue_types", return_value=set()),
        patch.object(issues, "run", return_value="https://github.com/owner/repo/issues/8"),
    ):
        assert issues.persist("owner/repo", "Feature", "Export", "body").endswith("/8")
    duplicate.assert_not_called()


def test_ensure_issue_replays_by_operation_marker_and_rejects_payload_reuse() -> None:
    created_body = ""

    def create(repo, kind, title, body, **relationships):
        nonlocal created_body
        created_body = body
        return "https://github.com/owner/repo/issues/8"

    with (
        patch.object(issues, "run", return_value="[]"),
        patch.object(issues, "persist", side_effect=create) as persist,
    ):
        result = issues.ensure_issue(
            "owner/repo",
            "intake:42",
            "Feature",
            "Export",
            "body",
            allow_create=True,
        )
    assert result.status == "CREATED"
    assert "skiphow-operation:intake:42:" in created_body
    persist.assert_called_once()

    existing = json.dumps(
        [{"number": 8, "title": "Export", "body": created_body, "html_url": result.url}]
    )
    with (
        patch.object(issues, "run", return_value=existing),
        patch.object(issues, "persist") as persist,
    ):
        replay = issues.ensure_issue("owner/repo", "intake:42", "Feature", "Export", "body")
    assert replay.status == "UNCHANGED"
    persist.assert_not_called()

    conflicting_body = re.sub(
        r"(skiphow-operation:intake:42:)[0-9a-f]+", r"\1deadbeef", created_body
    )
    conflicting = json.dumps(
        [{"number": 8, "title": "Export", "body": conflicting_body, "html_url": result.url}]
    )
    with patch.object(issues, "run", return_value=conflicting):
        with pytest.raises(issues.GitHubError, match="different payload"):
            issues.ensure_issue("owner/repo", "intake:42", "Feature", "Export", "changed")


def test_issue_operation_identity_binds_normalized_relationships() -> None:
    created_body = ""

    def create(repo, kind, title, body, **relationships):
        nonlocal created_body
        created_body = body
        return "https://github.com/owner/repo/issues/8"

    with (
        patch.object(issues, "run", return_value="[]"),
        patch.object(issues, "persist", side_effect=create),
        patch.object(issues, "create_relationship", return_value="LINKED"),
    ):
        issues.ensure_issue(
            "owner/repo",
            "intake:relationships",
            "Feature",
            "Export",
            "body",
            allow_create=True,
            blocked_by=3,
            parent=2,
        )

    existing = json.dumps(
        [{"number": 8, "title": "Export", "body": created_body, "html_url": "https://github.com/owner/repo/issues/8"}]
    )
    with patch.object(issues, "run", return_value=existing):
        replay = issues.ensure_issue(
            "owner/repo",
            "intake:relationships",
            "Feature",
            "Export",
            "body",
            parent=2,
            blocked_by=3,
        )
        assert replay.status == "UNCHANGED"
        with pytest.raises(issues.GitHubError, match="different payload"):
            issues.ensure_issue(
                "owner/repo",
                "intake:relationships",
                "Feature",
                "Export",
                "body",
                parent=2,
                blocked_by=4,
            )


def test_issue_recovery_uses_direct_api_listing_not_search_index() -> None:
    with patch.object(issues, "run", return_value="[]") as run:
        result = issues.ensure_issue(
            "owner/repo", "intake:recovery", "Feature", "Export", "body"
        )
    assert result.status == "NOT_FOUND"
    command = run.call_args.args[0]
    assert command[:3] == ["gh", "api", "repos/owner/repo/issues"]
    assert "--paginate" in command
    assert "--slurp" in command
    assert "--search" not in command


def test_provenance_is_idempotent_by_caller_key() -> None:
    canonical = json.dumps(
        {"source": "support", "excerpt": "export failed", "evidence": None},
        ensure_ascii=False,
        sort_keys=True,
    )
    marker = (
        "<!-- skiphow-provenance:signal-7:"
        + hashlib.sha256(canonical.encode()).hexdigest()
        + " -->"
    )
    with patch.object(
        issues, "run", return_value=json.dumps([{"body": f"{marker}\nexisting"}])
    ) as run:
        outcome = issues.record_provenance(
            "owner/repo", 8, "support", "export failed", key="signal-7"
        )
    assert outcome == "UNCHANGED"
    run.assert_called_once()


def test_relationship_is_native_idempotent_or_honestly_unverified() -> None:
    existing = json.dumps([{"number": 8}])
    with patch.object(issues, "run", return_value=existing) as run:
        assert issues.create_relationship("owner/repo", 8, "parent", 2) == "UNCHANGED"
    run.assert_called_once()
    with patch.object(issues, "run", side_effect=issues.GitHubError("unsupported")):
        assert issues.create_relationship("owner/repo", 8, "parent", 2) == "UNVERIFIED"


def test_unavailable_native_relationship_records_marked_reference() -> None:
    responses = iter([issues.GitHubError("unsupported"), "[]", ""])

    def fake_run(command, *, cwd="."):
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response

    with patch.object(issues, "run", side_effect=fake_run) as run:
        outcome = issues.create_relationship("owner/repo", 8, "blocked_by", 2)

    assert outcome == "UNVERIFIED"
    comment = run.call_args_list[2].args[0]
    assert comment[:3] == ["gh", "issue", "comment"]
    body = comment[comment.index("--body") + 1]
    assert "<!-- skiphow-relationship-reference:blocked_by:2 -->" in body
    assert "https://github.com/owner/repo/issues/2" in body
    assert "Native relationship status: UNVERIFIED" in body


def test_relationship_reference_fallback_is_idempotent() -> None:
    marker = "<!-- skiphow-relationship-reference:parent:2 -->"
    with patch.object(
        issues,
        "run",
        side_effect=[
            issues.GitHubError("unsupported"),
            json.dumps([[{"body": f"{marker}\nParent reference: existing"}]]),
        ],
    ) as run:
        outcome = issues.create_relationship("owner/repo", 8, "parent", 2)

    assert outcome == "UNVERIFIED"
    assert run.call_count == 2


def test_failed_native_relationship_mutation_records_reference() -> None:
    with patch.object(
        issues,
        "run",
        side_effect=[
            "[]",
            json.dumps({"id": 22}),
            issues.GitHubError("mutation rejected"),
            "[]",
            "",
        ],
    ) as run:
        outcome = issues.create_relationship("owner/repo", 8, "subissue", 2)

    assert outcome == "UNVERIFIED"
    assert run.call_args_list[-1].args[0][:3] == ["gh", "issue", "comment"]


def test_update_issue_skips_matching_fields() -> None:
    current = json.dumps(
        {"title": "Export", "body": "body", "state": "OPEN", "url": "https://x/8"}
    )
    with patch.object(issues, "run", return_value=current) as run:
        assert issues.update_issue(
            "owner/repo",
            8,
            title="Export",
            body="body",
            state="open",
            expected_title_digest=hashlib.sha256(b"Export").hexdigest(),
            expected_body_digest=hashlib.sha256(b"body").hexdigest(),
        ) == "https://x/8"
    run.assert_called_once()

    with patch.object(issues, "run", return_value=current):
        with pytest.raises(issues.GitHubError, match="changed concurrently"):
            issues.update_issue(
                "owner/repo",
                8,
                body="replacement",
                expected_body_digest=hashlib.sha256(b"stale").hexdigest(),
            )


def test_owned_worktree_refuses_to_claim_user_branch(tmp_path: Path) -> None:
    with (
        patch.object(issues, "_worktrees", return_value=[]),
        patch.object(issues, "_branch_metadata", return_value=(None, None)),
        patch.object(issues, "run", return_value="refs/heads/feature/export"),
        pytest.raises(issues.GitHubError, match="unowned branch"),
    ):
        issues.ensure_owned_worktree(
            str(tmp_path), str(tmp_path / "lane"), "feature/export", "main", "run-7"
        )


def test_owned_worktree_replay_requires_exact_owner_and_path(tmp_path: Path) -> None:
    target = str((tmp_path / "lane").resolve())
    rows = [{"worktree": target, "branch": "refs/heads/feature/export"}]
    with (
        patch.object(issues, "_worktrees", return_value=rows),
        patch.object(issues, "_branch_metadata", return_value=("run-7", target)),
        patch.object(issues, "run") as run,
    ):
        assert (
            issues.ensure_owned_worktree(
                str(tmp_path), target, "feature/export", "main", "run-7"
            )
            == "UNCHANGED"
        )
    run.assert_not_called()


def test_branch_metadata_reads_the_owned_lane_keys(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    branch = "release/0.8.0-external"
    target = str((tmp_path / "lane").resolve())
    issues.run(["git", "init"], cwd=str(repository))
    issues.run(
        ["git", "config", "--local", f"branch.{branch}.skiphow-owner", "run-7"],
        cwd=str(repository),
    )
    issues.run(
        ["git", "config", "--local", f"branch.{branch}.skiphow-worktree", target],
        cwd=str(repository),
    )

    assert issues._branch_metadata(str(repository), branch) == ("run-7", target)


def test_existing_pull_request_is_reused() -> None:
    existing = json.dumps(
        [{"url": "https://github.com/owner/repo/pull/8", "headRefOid": HEAD}]
    )
    with patch.object(issues, "run", return_value=existing) as run:
        assert issues.ensure_pull_request(
            "owner/repo",
            "feature/export",
            "main",
            "Export",
            "body",
            expected_head=HEAD,
        ).endswith("/8")
    run.assert_called_once()


def test_pull_request_gate_rejects_stale_head() -> None:
    payload = json.dumps(
        {
            "headRefOid": OTHER_HEAD,
            "mergeable": "MERGEABLE",
            "reviewDecision": "APPROVED",
            "statusCheckRollup": [],
        }
    )
    with patch.object(issues, "run", return_value=payload):
        with pytest.raises(issues.GitHubError, match="head changed"):
            issues.pull_request_gate("owner/repo", 8, HEAD, [])


def test_pull_request_gate_requires_named_checks_on_exact_head() -> None:
    payload = json.dumps(
        {
            "headRefOid": HEAD,
            "mergeable": "MERGEABLE",
            "reviewDecision": "APPROVED",
            "statusCheckRollup": [
                {"name": "test", "conclusion": "SUCCESS"},
                {"context": "lint", "state": "PENDING"},
            ],
        }
    )
    with patch.object(issues, "run", return_value=payload):
        gate = issues.pull_request_gate("owner/repo", 8, HEAD, ["test", "lint"])
    assert gate.checks_green is False
    assert gate.missing_checks == ("lint",)


def test_merge_policy_defaults_closed_and_uses_exact_head_guard() -> None:
    with patch.object(issues, "run") as run:
        assert (
            issues.merge_pull_request(
                "owner/repo", 8, policy="never", expected_head=HEAD
            )
            == "NOT_AUTHORIZED"
        )
    run.assert_not_called()

    with patch.object(issues, "pull_request_gate") as gate:
        assert (
            issues.merge_pull_request(
                "owner/repo", 8, policy="when_green", expected_head=HEAD
            )
            == "UNVERIFIED"
        )
    gate.assert_not_called()

    gate = issues.PullRequestGate(HEAD, True, True, True, ())
    with (
        patch.object(issues, "pull_request_gate", return_value=gate),
        patch.object(issues, "run") as run,
    ):
        assert (
            issues.merge_pull_request(
                "owner/repo",
                8,
                policy="when_green_and_approved",
                expected_head=HEAD,
                required_checks=["test"],
                checks_verified=True,
            )
            == "MERGE_REQUESTED"
        )
    assert "--match-head-commit" in run.call_args.args[0]
    assert HEAD in run.call_args.args[0]
    assert "--delete-branch" not in run.call_args.args[0]


def test_cleanup_refuses_dirty_or_unique_owned_worktree(tmp_path: Path) -> None:
    target = str((tmp_path / "lane").resolve())
    rows = [{"worktree": target, "branch": "refs/heads/feature/export"}]
    with (
        patch.object(issues, "_worktrees", return_value=rows),
        patch.object(issues, "_branch_metadata", return_value=("run-7", target)),
        patch.object(issues, "run", side_effect=[HEAD, " M user.txt"]),
        pytest.raises(issues.GitHubError, match="dirty worktree"),
    ):
        issues.cleanup_owned_worktree(
            str(tmp_path),
            target,
            "feature/export",
            "run-7",
            expected_head=HEAD,
            merged_into="main",
        )

    with (
        patch.object(issues, "_worktrees", return_value=rows),
        patch.object(issues, "_branch_metadata", return_value=("run-7", target)),
        patch.object(issues, "run", side_effect=[HEAD, "", "unique"]),
        pytest.raises(issues.GitHubError, match="commits absent"),
    ):
        issues.cleanup_owned_worktree(
            str(tmp_path),
            target,
            "feature/export",
            "run-7",
            expected_head=HEAD,
            merged_into="main",
        )


def test_cleanup_remote_branch_refuses_changed_oid(tmp_path: Path) -> None:
    merged = json.dumps(
        {
            "headRefName": "feature/export",
            "headRefOid": HEAD,
            "headRepository": {"name": "repo"},
            "headRepositoryOwner": {"login": "owner"},
            "mergedAt": "now",
        }
    )
    with (
        patch.object(issues, "_branch_metadata", return_value=("run-7", "/lane")),
        patch.object(
            issues,
            "run",
            side_effect=[
                "git@github.com:owner/repo.git",
                merged,
                f"{OTHER_HEAD} refs/heads/feature/export",
            ],
        ),
        pytest.raises(issues.GitHubError, match="remote branch head changed"),
    ):
        issues.cleanup_owned_remote_branch(
            str(tmp_path),
            "owner/repo",
            "origin",
            "feature/export",
            "run-7",
            expected_head=HEAD,
            merged_pull_request=8,
        )


def test_remote_cleanup_refuses_a_different_repository(tmp_path: Path) -> None:
    merged = json.dumps(
        {
            "headRefName": "feature/export",
            "headRefOid": HEAD,
            "headRepository": {"name": "fork"},
            "headRepositoryOwner": {"login": "owner"},
            "mergedAt": "now",
        }
    )
    with (
        patch.object(
            issues,
            "run",
            side_effect=["git@github.com:owner/repo.git", merged],
        ) as run,
        pytest.raises(issues.GitHubError, match="head repository"),
    ):
        issues.cleanup_owned_remote_branch(
            str(tmp_path),
            "owner/base",
            "origin",
            "feature/export",
            "run-7",
            expected_head=HEAD,
            merged_pull_request=8,
        )
    assert all(command.args[0][:2] != ["git", "push"] for command in run.call_args_list)


def test_repeated_local_cleanup_is_unchanged(tmp_path: Path) -> None:
    with (
        patch.object(issues, "_worktrees", return_value=[]),
        patch.object(issues, "run", return_value="") as run,
    ):
        assert (
            issues.cleanup_owned_worktree(
                str(tmp_path),
                str(tmp_path / "lane"),
                "feature/export",
                "run-7",
                expected_head=HEAD,
                merged_into="main",
            )
            == "UNCHANGED"
        )
    assert run.call_args.args[0][:3] == ["git", "for-each-ref", "--format=%(refname)"]


def test_project_requires_explicit_owner_and_number() -> None:
    assert project.Project.parse("owner/12") == project.Project("owner", 12)
    with pytest.raises(project.ProjectError):
        project.Project.parse("auto")


def test_project_module_contains_no_legacy_gate_or_discovery() -> None:
    source = (ROOT / "plugins/skiphow/scripts/github_project.py").read_text(encoding="utf-8")
    forbidden = "Human" + " Gate"
    assert forbidden not in source
    assert "candidate_projects" not in source
    assert "projectsV2(first" not in source


def test_project_without_explicit_status_mapping_is_unverified() -> None:
    with patch.object(project, "run_json") as run_json:
        outcome = project.update_optional_view(
            project.Project("owner", 12), "https://x/7", "done"
        )
    assert outcome == "UNVERIFIED"
    run_json.assert_not_called()


def test_project_lists_all_items_and_fields_and_avoids_duplicate_item() -> None:
    calls: list[list[str]] = []

    def fake_json(command):
        calls.append(list(command))
        if command[2] == "view":
            return {"id": "PVT_1"}
        if command[2] == "item-list":
            return {
                "items": [
                    {"id": "PVTI_1", "content": {"url": "https://x/7"}, "Flow": "Doing"}
                ]
            }
        if command[2] == "field-list":
            return {
                "fields": [
                    {
                        "id": "PVTF_1",
                        "name": "Flow",
                        "options": [{"id": "OPT_1", "name": "Done"}],
                    }
                ]
            }
        raise AssertionError(command)

    with (
        patch.object(project, "run_json", side_effect=fake_json),
        patch.object(project, "run") as run,
    ):
        outcome = project.update_optional_view(
            project.Project("owner", 12),
            "https://x/7",
            "closed",
            status_field="Flow",
            status_mapping={"closed": "Done"},
        )
    assert outcome == "UPDATED"
    assert not any(command[2] == "item-add" for command in calls)
    list_commands = [command for command in calls if command[2] in {"item-list", "field-list"}]
    assert all(str(project.LIST_LIMIT) in command for command in list_commands)
    run.assert_called_once()


def test_project_matching_status_is_noop() -> None:
    responses = iter(
        [
            {"id": "PVT_1"},
            {
                "items": [
                    {"id": "PVTI_1", "content": {"url": "https://x/7"}, "Flow": "Done"}
                ]
            },
        ]
    )
    with (
        patch.object(project, "run_json", side_effect=lambda command: next(responses)),
        patch.object(project, "run") as run,
    ):
        outcome = project.update_optional_view(
            project.Project("owner", 12),
            "https://x/7",
            "closed",
            status_field="Flow",
            status_mapping={"closed": "Done"},
        )
    assert outcome == "UNCHANGED"
    run.assert_not_called()


def test_optional_project_failure_is_nonblocking(capsys: pytest.CaptureFixture[str]) -> None:
    with patch.object(project, "update_optional_view", side_effect=project.ProjectError("down")):
        status = project.main(
            [
                "owner/12",
                "https://x/7",
                "closed",
                "--status-field",
                "Flow",
                "--status-map",
                '{"closed":"Done"}',
            ]
        )
    assert status == 0
    assert capsys.readouterr().out == "UNVERIFIED: down\n"


def test_incomplete_project_items_do_not_create_a_duplicate() -> None:
    responses = iter(
        [
            {"id": "PVT_1"},
            {"totalCount": 101, "items": [{"id": "PVTI_1"}] * 100},
        ]
    )
    with (
        patch.object(project, "run_json", side_effect=lambda command: next(responses)),
        patch.object(project, "run") as run,
        pytest.raises(project.ProjectError, match="incomplete"),
    ):
        project.update_optional_view(
            project.Project("owner", 12),
            "https://x/101",
            "closed",
            status_field="Flow",
            status_mapping={"closed": "Done"},
        )
    run.assert_not_called()


def test_invalid_optional_mapping_is_nonblocking(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        project.main(
            [
                "owner/12",
                "https://x/7",
                "closed",
                "--status-field",
                "Flow",
                "--status-map",
                "[]",
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.startswith("UNVERIFIED: ")


@pytest.mark.parametrize(
    ("missing", "message"),
    (
        ("field", "field 'Flow' has no id"),
        ("option", "field 'Flow' option 'Done' has no id"),
    ),
)
def test_missing_project_field_or_option_id_is_unverified(
    capsys: pytest.CaptureFixture[str], missing: str, message: str
) -> None:
    field = {
        "name": "Flow",
        "options": [{"id": "OPT_1", "name": "Done"}],
    }
    if missing != "field":
        field["id"] = "PVTF_1"
    if missing == "option":
        field["options"] = [{"name": "Done"}]

    def fake_json(command):
        if command[2] == "view":
            return {"id": "PVT_1"}
        if command[2] == "item-list":
            return {"items": [{"id": "PVTI_1", "content": {"url": "https://x/7"}}]}
        if command[2] == "field-list":
            return {"fields": [field]}
        raise AssertionError(command)

    with patch.object(project, "run_json", side_effect=fake_json):
        status = project.main(
            [
                "owner/12",
                "https://x/7",
                "closed",
                "--status-field",
                "Flow",
                "--status-map",
                '{"closed":"Done"}',
            ]
        )
    assert status == 0
    assert capsys.readouterr().out == f"UNVERIFIED: configured Project {message}\n"


def test_missing_added_project_item_id_is_unverified(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_json(command):
        if command[2] == "view":
            return {"id": "PVT_1"}
        if command[2] == "item-list":
            return {"items": []}
        if command[2] == "field-list":
            return {
                "fields": [
                    {
                        "id": "PVTF_1",
                        "name": "Flow",
                        "options": [{"id": "OPT_1", "name": "Done"}],
                    }
                ]
            }
        if command[2] == "item-add":
            return {}
        raise AssertionError(command)

    with patch.object(project, "run_json", side_effect=fake_json):
        status = project.main(
            [
                "owner/12",
                "https://x/7",
                "closed",
                "--status-field",
                "Flow",
                "--status-map",
                '{"closed":"Done"}',
            ]
        )
    assert status == 0
    assert capsys.readouterr().out == "UNVERIFIED: Project item has no id\n"
