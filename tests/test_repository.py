"""Repository contract checks for the SkipHow plugin."""

import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = {
    ".codex-plugin/plugin.json",
    "skills/cto-run/SKILL.md",
    "skills/cto-run/agents/openai.yaml",
    "README.md",
    "LICENSE",
}


def load_json(path: str) -> dict:
    """Load a JSON document from the repository root."""
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_frontmatter(path: str) -> dict:
    """Load YAML frontmatter from a Markdown file in the repository root."""
    contents = (ROOT / path).read_text(encoding="utf-8")
    _, frontmatter, _ = contents.split("---", 2)
    return yaml.safe_load(frontmatter)


class RepositoryContractTests(unittest.TestCase):
    def test_required_structure(self) -> None:
        missing_paths = sorted(
            path for path in REQUIRED_PATHS if not (ROOT / path).is_file()
        )

        self.assertEqual([], missing_paths)
