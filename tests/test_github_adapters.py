"""Focused tests for optional GitHub adapters."""

import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


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
    assert command.call_args_list[1].args[0][8] == "timeout in exporter"


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
    with patch.object(issues, "run") as run:
        issues.create_linked_branch("owner/repo", 7, "feature/export")
        issues.record_delivery("owner/repo", 7, "https://github.com/owner/repo/pull/8")
    assert run.call_args_list[0].args[0][:3] == ["gh", "issue", "develop"]
    assert run.call_args_list[1].args[0][:3] == ["gh", "issue", "comment"]
    assert "Delivery: https://github.com/owner/repo/pull/8" in run.call_args_list[1].args[0]


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
