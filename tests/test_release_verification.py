"""Focused tests for deterministic release verification helpers."""

import importlib.util
from pathlib import Path
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

    def test_candidate_diff_failure_is_reported(self) -> None:
        with patch.object(
            release,
            "checked",
            side_effect=[(True, ""), (False, "file.md:1: trailing whitespace")],
        ):
            errors = release.validate_diff("base-sha")
        self.assertEqual(1, len(errors))
        self.assertIn("base-sha HEAD", errors[0])
