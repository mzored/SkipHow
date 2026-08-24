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


def test_duplicate_search_returns_existing_issue() -> None:
    payload = json.dumps([{"number": 7, "title": "Weekly export", "url": "https://x/7"}])
    with patch.object(issues, "run", return_value=payload):
        assert issues.find_duplicate("owner/repo", "Weekly export").number == 7


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
