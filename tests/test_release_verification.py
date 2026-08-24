"""Focused tests for deterministic release verification helpers."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_release.py"
SPEC = importlib.util.spec_from_file_location("verify_release", SCRIPT)
assert SPEC and SPEC.loader
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseVerificationTests(unittest.TestCase):
    def test_repo_metadata_and_local_links_validate(self) -> None:
        self.assertEqual([], release.validate_json())
        self.assertEqual([], release.validate_yaml())
        self.assertEqual([], release.validate_markdown_links())

    def test_source_scan_checks_only_distributable_source(self) -> None:
        self.assertEqual([], release.source_scan())

    def test_repository_scan_uses_only_git_owned_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            owned = root / "owned.yaml"
            owned.write_text("valid: true\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            subprocess.run(["git", "add", "owned.yaml"], cwd=root, check=True)
            external = root / ".worktrees" / "other" / "invalid.yaml"
            external.parent.mkdir(parents=True)
            external.write_text("invalid: [", encoding="utf-8")
            with patch.object(release, "ROOT", root):
                self.assertEqual([owned], list(release.repository_files({".yaml"})))
                self.assertEqual([], release.validate_yaml())

    def test_markdown_links_support_angle_and_reference_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "README.md"
            document.write_text(
                "[angle](<missing file.md>)\n\n[reference][missing]\n\n[missing]: absent.md\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            with patch.object(release, "ROOT", root):
                errors = release.validate_markdown_links()
            self.assertEqual(2, len(errors))
            self.assertTrue(any("missing%20file.md" in error for error in errors))
            self.assertTrue(any("absent.md" in error for error in errors))

    def test_candidate_diff_failure_is_reported(self) -> None:
        with patch.object(
            release,
            "checked",
            side_effect=[(True, ""), (False, "file.md:1: trailing whitespace")],
        ):
            errors = release.validate_diff("base-sha")
        self.assertEqual(1, len(errors))
        self.assertIn("base-sha HEAD", errors[0])

    def test_codex_plugin_validator_failure_is_reported(self) -> None:
        validator = Path("/runtime/validate_plugin.py")
        with (
            patch.object(release, "bundled_codex_plugin_validator", return_value=validator),
            patch.object(release, "checked", return_value=(False, "invalid manifest")) as checked,
        ):
            errors = release.validate_codex_plugin()
        self.assertEqual(["Codex plugin validation failed: invalid manifest"], errors)
        checked.assert_called_once_with(
            [
                release.sys.executable,
                str(validator),
                str(ROOT / "plugins" / "skiphow"),
            ]
        )

    def test_missing_codex_plugin_validator_fails_release_gate(self) -> None:
        with patch.object(release, "bundled_codex_plugin_validator", return_value=None):
            errors = release.validate_codex_plugin()
        self.assertEqual(1, len(errors))
        self.assertIn("Codex plugin validator is unavailable", errors[0])

    def test_configured_codex_plugin_validator_takes_precedence(self) -> None:
        validator = ROOT / "configured-validator.py"
        with (
            patch.dict(release.os.environ, {"CODEX_PLUGIN_VALIDATOR": str(validator)}),
            patch.object(Path, "is_file", return_value=True),
        ):
            self.assertEqual(validator.resolve(), release.bundled_codex_plugin_validator())
