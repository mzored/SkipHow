"""Focused tests for the bundled GitHub lifecycle helper."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "plugins/skiphow/scripts/gh_task_status.py"
SPEC = importlib.util.spec_from_file_location("gh_task_status", HELPER_PATH)
assert SPEC and SPEC.loader
gh_task_status = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gh_task_status
SPEC.loader.exec_module(gh_task_status)


class GitHubLifecycleHelperTests(unittest.TestCase):
    def test_repo_at_parses_https_origin_without_network(self) -> None:
        with patch.object(
            gh_task_status,
            "run",
            return_value="https://github.com/mzored/SkipHow.git",
        ):
            self.assertEqual("mzored/SkipHow", gh_task_status.repo_at("/tmp/repo"))

    def test_pre_hook_ignores_unrelated_project_dump(self) -> None:
        event = {
            "cwd": "/tmp/repo",
            "tool_input": {"command": "gh project item-list 5 --owner mzored"},
        }
        with patch("sys.stdin", io.StringIO(json.dumps(event))):
            self.assertEqual(0, gh_task_status.hook_pre())

    def test_develop_target_uses_explicit_repository(self) -> None:
        target = gh_task_status.develop_target(
            "gh issue develop 42 --repo other/project --checkout",
            "/tmp/repo",
        )
        self.assertEqual(gh_task_status.IssueRef("other/project", 42), target)

    def test_develop_target_rejects_compound_shell_command(self) -> None:
        target = gh_task_status.develop_target(
            "gh issue develop 42 --repo owner/repo || true",
            "/tmp/repo",
        )
        self.assertIsNone(target)

    def test_pre_hook_blocks_develop_when_human_gate_is_set(self) -> None:
        event = {
            "cwd": "/tmp/repo",
            "tool_input": {"command": "gh issue develop 42 --repo owner/repo --checkout"},
        }
        task = gh_task_status.Task(
            repo="owner/repo",
            board=gh_task_status.Board("owner", 5, "main"),
            project_id="project",
            item_id="item",
            values={"Human Gate": "Product decision"},
        )
        stderr = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO(json.dumps(event))),
            patch.object(gh_task_status, "repo_at", return_value="owner/repo"),
            patch.object(gh_task_status, "resolve_task", return_value=(task, {})),
            redirect_stderr(stderr),
        ):
            self.assertEqual(2, gh_task_status.hook_pre())
        self.assertIn("Human Gate=Product decision", stderr.getvalue())

    def test_pre_hook_ignores_untracked_develop_command(self) -> None:
        event = {
            "tool_name": "Bash",
            "cwd": "/tmp/repo",
            "tool_input": {"command": "gh issue develop 42"},
        }
        with (
            patch("sys.stdin", io.StringIO(json.dumps(event))),
            patch.object(
                gh_task_status,
                "resolve_task",
                side_effect=gh_task_status.UntrackedLifecycle(
                    "no Project v2 board contains owner/repo"
                ),
            ),
            patch.object(
                gh_task_status,
                "repo_at",
                return_value="owner/repo",
            ),
        ):
            self.assertEqual(0, gh_task_status.hook_pre())

    def test_pre_hook_blocks_when_lifecycle_verification_fails(self) -> None:
        event = {
            "tool_name": "Bash",
            "cwd": "/tmp/repo",
            "tool_input": {"command": "gh issue develop 42"},
        }
        stderr = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO(json.dumps(event))),
            patch.object(
                gh_task_status,
                "resolve_task",
                side_effect=gh_task_status.LifecycleError("authentication failed"),
            ),
            patch.object(gh_task_status, "repo_at", return_value="owner/repo"),
            redirect_stderr(stderr),
        ):
            self.assertEqual(2, gh_task_status.hook_pre())
        self.assertIn("Cannot verify GitHub lifecycle", stderr.getvalue())

    def test_set_option_never_uses_an_unrelated_field(self) -> None:
        task = gh_task_status.Task(
            repo="owner/repo",
            board=gh_task_status.Board("owner", 5, "main"),
            project_id="project",
            item_id="item",
            values={"Human Gate": "No"},
        )
        unrelated_fields = {
            "Other": ("field", {"In Progress": "option"}),
        }
        with (
            patch.object(
                gh_task_status,
                "resolve_task",
                return_value=(task, unrelated_fields),
            ),
            self.assertRaises(gh_task_status.LifecycleError),
        ):
            gh_task_status.set_option("owner/repo", 42, "In Progress")

    def test_set_in_progress_allows_absent_legacy_gate(self) -> None:
        task = gh_task_status.Task(
            repo="owner/repo",
            board=gh_task_status.Board("owner", 5, "main"),
            project_id="project",
            item_id="item",
            values={},
        )
        fields = {"Status": ("field", {"In progress": "option"})}
        with (
            patch.object(gh_task_status, "resolve_task", return_value=(task, fields)),
            patch.object(gh_task_status, "run") as run,
        ):
            gh_task_status.set_option("owner/repo", 42, "In progress")
        run.assert_called_once()

    def test_candidate_projects_paginates_owner_connection(self) -> None:
        pages = [
            {
                "data": {
                    "organization": {
                        "projectsV2": {
                            "nodes": [{"number": 1}],
                            "pageInfo": {"hasNextPage": True, "endCursor": "next"},
                        }
                    }
                }
            },
            {
                "data": {
                    "organization": {
                        "projectsV2": {
                            "nodes": [{"number": 101}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
        ]
        with patch.object(gh_task_status, "graphql", side_effect=pages):
            self.assertEqual(
                [("owner", 1), ("owner", 101)],
                list(gh_task_status.candidate_projects("owner")),
            )

    def test_stop_hook_blocks_unstarted_task_branch(self) -> None:
        event = {"cwd": "/tmp/repo", "stop_hook_active": False}
        task = gh_task_status.Task(
            repo="owner/repo",
            board=gh_task_status.Board("owner", 5, "main"),
            project_id="project",
            item_id="item",
            values={},
        )
        stdout = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO(json.dumps(event))),
            patch.object(gh_task_status, "branch_name", return_value="42-fix-cache"),
            patch.object(gh_task_status, "repo_at", return_value="owner/repo"),
            patch.object(
                gh_task_status,
                "linked_branch_names",
                return_value={"42-fix-cache"},
            ),
            patch.object(
                gh_task_status,
                "resolve_task",
                return_value=(task, {"Status": ("field", {"In progress": "option"})}),
            ),
            redirect_stdout(stdout),
        ):
            self.assertEqual(0, gh_task_status.hook_stop())
        output = json.loads(stdout.getvalue())
        self.assertEqual("block", output["decision"])
        self.assertIn("Issue #42", output["reason"])

    def test_stop_hook_allows_started_task(self) -> None:
        event = {"cwd": "/tmp/repo", "stop_hook_active": False}
        task = gh_task_status.Task(
            repo="owner/repo",
            board=gh_task_status.Board("owner", 5, "main"),
            project_id="project",
            item_id="item",
            values={"Status": "In progress"},
        )
        stdout = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO(json.dumps(event))),
            patch.object(gh_task_status, "branch_name", return_value="42-fix-cache"),
            patch.object(gh_task_status, "repo_at", return_value="owner/repo"),
            patch.object(
                gh_task_status,
                "linked_branch_names",
                return_value={"42-fix-cache"},
            ),
            patch.object(
                gh_task_status,
                "resolve_task",
                return_value=(task, {"Status": ("field", {"In progress": "option"})}),
            ),
            redirect_stdout(stdout),
        ):
            self.assertEqual(0, gh_task_status.hook_stop())
        self.assertEqual("", stdout.getvalue())

    def test_stop_hook_ignores_unlinked_numeric_branch(self) -> None:
        event = {"cwd": "/tmp/repo", "stop_hook_active": False}
        with (
            patch("sys.stdin", io.StringIO(json.dumps(event))),
            patch.object(gh_task_status, "branch_name", return_value="42-local-scratch"),
            patch.object(gh_task_status, "repo_at", return_value="owner/repo"),
            patch.object(gh_task_status, "linked_branch_names", return_value=set()),
            patch.object(gh_task_status, "resolve_task") as resolve_task,
        ):
            self.assertEqual(0, gh_task_status.hook_stop())
        resolve_task.assert_not_called()


if __name__ == "__main__":
    unittest.main()
