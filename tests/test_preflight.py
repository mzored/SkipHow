"""Focused checks for read-only preflight behavior."""

import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "plugins/skiphow/scripts/gh_task_status.py"
SPEC = importlib.util.spec_from_file_location("preflight_helper", HELPER)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preflight
SPEC.loader.exec_module(preflight)


class PreflightTests(unittest.TestCase):
    def test_version_parts_accepts_and_rejects_versions(self) -> None:
        self.assertEqual((2, 93, 0), preflight.version_parts("gh version 2.93.0"))
        self.assertIsNone(preflight.version_parts("development build"))

    def test_hook_config_rejects_empty_lifecycle_hooks(self) -> None:
        with self.assertRaisesRegex(ValueError, "PreToolUse must contain"):
            preflight.validate_hook_config(
                {"hooks": {"PreToolUse": [], "Stop": []}}
            )

    def test_repository_hook_config_is_functional(self) -> None:
        hook_path = ROOT / "plugins/skiphow/hooks/hooks.json"
        preflight.validate_hook_config(json.loads(hook_path.read_text(encoding="utf-8")))

    def test_missing_gh_is_actionable_and_avoids_board_reads(self) -> None:
        with (
            patch.object(preflight.shutil, "which", side_effect=lambda name: None if name == "gh" else "/bin/tool"),
            patch.object(preflight, "run", return_value="/tmp/repo"),
            patch.object(preflight, "board_for") as board_for,
        ):
            failures, _ = preflight.preflight_report(cwd="/tmp/repo")
        self.assertTrue(any("GitHub CLI 2.93.0" in failure for failure in failures))
        board_for.assert_not_called()

    def test_preflight_reports_required_board_options_without_mutating(self) -> None:
        board = preflight.Board("owner", 5, "main")
        fields = {
            "Status": ("status", {"Todo": "todo"}),
            "Human Gate": ("gate", {"No": "no"}),
        }
        with (
            patch.object(preflight.shutil, "which", return_value="/bin/tool"),
            patch.object(preflight, "run", side_effect=["/tmp/repo", "gh version 2.98.0", "authenticated", "codex 1", "claude 1"]),
            patch.object(preflight, "repo_at", return_value="owner/repo"),
            patch.object(preflight, "board_for", return_value=board),
            patch.object(preflight, "project_fields", return_value=("project", fields)),
        ):
            failures, notes = preflight.preflight_report(cwd="/tmp/repo")
        self.assertTrue(any("missing options" in failure for failure in failures))
        self.assertIn("shared lifecycle hooks are present", notes)

    def test_preflight_reports_missing_codex_plugin_command(self) -> None:
        def run(args, *, cwd=None):
            if args[0] == "/bin/codex":
                self.assertEqual(["/bin/codex", "plugin", "--help"], args)
                raise preflight.LifecycleError("unknown command: plugin")
            return "/tmp/repo"

        with (
            patch.object(
                preflight.shutil,
                "which",
                side_effect=lambda name: {"git": "/bin/git", "codex": "/bin/codex"}.get(name),
            ),
            patch.object(preflight, "run", side_effect=run),
        ):
            failures, _ = preflight.preflight_report(cwd="/tmp/repo")
        self.assertTrue(any("repair codex" in failure for failure in failures))
