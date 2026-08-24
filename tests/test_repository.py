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

CAPABILITY_ROLES = {"MECHANICAL", "IMPLEMENTATION", "CTO_REVIEW"}
DURABLE_FILES = {"state.json", "journal.jsonl", "briefing.md", "FINAL.md"}
AUTHORITY_ORDER = (
    "1. System, safety, legal, sandbox, and tool constraints.",
    "2. Repository instructions that apply to the current scope.",
    "3. The project runbook, accepted specifications, and approved architecture decisions.",
    "4. This operating policy.",
    "5. Task-local plans and worker briefs.",
)
DEPENDENCY_CHECKS = (
    "release within the last 12 months",
    "more than one maintainer",
    "declared pre-1.0 risk",
    "license compatibility",
    "known high-severity CVEs",
    "`unverified`",
)
FORBIDDEN_TEXT = {
    "/Users/",
    "~/.codex",
    "~/.claude",
    "run-journal",
    "launch.sh",
    "gpt-",
    "opus",
    "sonnet",
    "haiku",
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

    def test_portable_policy(self) -> None:
        """The shipped cto-run policy stays portable and complete."""
        policy_paths = sorted(
            path for path in (ROOT / "skills/cto-run").rglob("*") if path.is_file()
        )
        policy_text = "\n".join(
            path.read_text(encoding="utf-8") for path in policy_paths
        )

        self.assertTrue(policy_paths)
        for role in CAPABILITY_ROLES:
            self.assertIn(role, policy_text)
        for durable_file in DURABLE_FILES:
            self.assertIn(durable_file, policy_text)
        self.assertIn("Host policy takes priority.", policy_text)
        for forbidden_text in FORBIDDEN_TEXT:
            self.assertNotIn(forbidden_text, policy_text)

        operating_policy = (
            ROOT / "skills/cto-run/references/operating-policy.md"
        ).read_text(encoding="utf-8")
        state_contract = (
            ROOT / "skills/cto-run/references/state-contract.md"
        ).read_text(encoding="utf-8")

        for authority in AUTHORITY_ORDER:
            self.assertIn(authority, operating_policy)
        self.assertIn(
            "Specificity breaks ties only within one authority tier.", operating_policy
        )
        self.assertIn(
            "product-owner decision, missing authority, protected action, or external prerequisite",
            operating_policy,
        )
        self.assertIn(
            "No executable lane or unaccounted mutable state may remain.",
            operating_policy,
        )
        self.assertNotIn("irreducible blocker", operating_policy)
        for dependency_check in DEPENDENCY_CHECKS:
            self.assertIn(dependency_check, operating_policy)
        self.assertIn(
            "`reuse_check` with `n/a` when the gate does not apply", operating_policy
        )
        self.assertIn(
            "`reuse_check` as the verdict or `n/a`", state_contract
        )
