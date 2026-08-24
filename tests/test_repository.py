"""Repository contract checks for the SkipHow plugin."""

import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = {
    "plugins/skiphow/.codex-plugin/plugin.json",
    "plugins/skiphow/skills/cto-run/SKILL.md",
    "plugins/skiphow/skills/cto-run/agents/openai.yaml",
    "README.md",
    "LICENSE",
}

PACKAGE_FILES = {
    ".agents/plugins/marketplace.json",
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
    "plugins/skiphow/.codex-plugin/plugin.json",
}
PACKAGE_VERSION = "0.1.0"
PACKAGE_REPOSITORY = "https://github.com/mzored/SkipHow"
PUBLIC_POLICY_FILES = {
    "docs/architecture.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "LICENSE",
}
PORTABLE_POLICY_HEADINGS = {
    "# Operating policy",
    "## Authority and ownership",
    "## Recovery and control loop",
    "## Readiness, risk, and decisions",
    "## Build versus reuse",
    "## Delegation and execution health",
    "## Validation, scope, and handoff",
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
COMPLETION_CLAIM_STATEMENT = (
    "Bind every completion claim to the exact candidate commit, acceptance criteria, "
    "command or procedure, environment, duration, result, and evidence location."
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
            path
            for path in (ROOT / "plugins/skiphow/skills/cto-run").rglob("*")
            if path.is_file()
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
            ROOT / "plugins/skiphow/skills/cto-run/references/operating-policy.md"
        ).read_text(encoding="utf-8")
        state_contract = (
            ROOT / "plugins/skiphow/skills/cto-run/references/state-contract.md"
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
        self.assertIn(COMPLETION_CLAIM_STATEMENT, operating_policy)

    def test_manifest_contract(self) -> None:
        """Both hosts publish the same plugin with public metadata."""
        missing_paths = sorted(
            path for path in PACKAGE_FILES if not (ROOT / path).is_file()
        )
        self.assertEqual([], missing_paths)

        codex_manifest = load_json("plugins/skiphow/.codex-plugin/plugin.json")
        codex_marketplace = load_json(".agents/plugins/marketplace.json")
        claude_manifest = load_json(".claude-plugin/plugin.json")
        claude_marketplace = load_json(".claude-plugin/marketplace.json")

        for manifest in (codex_manifest, claude_manifest):
            self.assertEqual("skiphow", manifest["name"])
            self.assertEqual(PACKAGE_REPOSITORY, manifest["repository"])
            self.assertEqual("MIT", manifest["license"])
            self.assertTrue(manifest["author"]["name"])
            self.assertTrue(manifest["homepage"].startswith("https://"))
            self.assertTrue(manifest["keywords"])

        for marketplace in (codex_marketplace, claude_marketplace):
            self.assertEqual("skiphow", marketplace["name"])
            self.assertEqual("skiphow", marketplace["plugins"][0]["name"])

        self.assertEqual("./skills/", codex_manifest["skills"])
        self.assertFalse((ROOT / "skills").exists())
        self.assertEqual(3, len(codex_manifest["interface"]["defaultPrompt"]))
        self.assertTrue(
            {"hooks", "apps", "mcpServers"}.isdisjoint(codex_manifest)
        )
        self.assertEqual(
            {"source": "local", "path": "./plugins/skiphow"},
            codex_marketplace["plugins"][0]["source"],
        )
        self.assertEqual(
            "./adapters/claude/skills/cto-run", claude_manifest["skills"]
        )
        self.assertEqual(
            "./",
            claude_marketplace["plugins"][0]["source"],
        )
        self.assertEqual(
            PACKAGE_REPOSITORY, claude_marketplace["plugins"][0]["repository"]
        )
        self.assertEqual("MIT", claude_marketplace["plugins"][0]["license"])

    def test_versions_match(self) -> None:
        """Every versioned package record ships the release version."""
        required_paths = (
            "plugins/skiphow/.codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
        )
        missing_paths = [path for path in required_paths if not (ROOT / path).is_file()]
        self.assertEqual([], missing_paths)
        if missing_paths:
            return

        codex_manifest = load_json("plugins/skiphow/.codex-plugin/plugin.json")
        claude_manifest = load_json(".claude-plugin/plugin.json")
        claude_marketplace = load_json(".claude-plugin/marketplace.json")

        self.assertEqual(PACKAGE_VERSION, codex_manifest["version"])
        self.assertEqual(PACKAGE_VERSION, claude_manifest["version"])
        self.assertEqual(PACKAGE_VERSION, claude_marketplace["metadata"]["version"])
        self.assertEqual(PACKAGE_VERSION, claude_marketplace["plugins"][0]["version"])

    def test_claude_adapter(self) -> None:
        """Claude uses an explicit adapter instead of a copied policy."""
        adapter_path = ROOT / "adapters/claude/skills/cto-run/SKILL.md"
        self.assertTrue(adapter_path.is_file())
        if not adapter_path.is_file():
            return

        adapter_text = adapter_path.read_text(encoding="utf-8")
        _, frontmatter, body = adapter_text.split("---", 2)

        self.assertTrue(yaml.safe_load(frontmatter)["disable-model-invocation"])
        self.assertIn("plugins/skiphow/skills/cto-run/SKILL.md", body)
        for heading in PORTABLE_POLICY_HEADINGS:
            self.assertNotIn(heading, body)

    def test_documentation_contract(self) -> None:
        """Public documentation describes use, support, and repository policy."""
        missing_paths = sorted(
            path for path in PUBLIC_POLICY_FILES if not (ROOT / path).is_file()
        )
        self.assertEqual([], missing_paths)
        if missing_paths:
            return

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for heading in (
            "## Install with Codex",
            "## Install with Claude Code",
            "## Run cto-run",
            "## Support policy",
            "## Limitations",
            "## Contributing",
            "## Security",
            "## License",
        ):
            self.assertIn(heading, readme)
        for path in sorted(PUBLIC_POLICY_FILES):
            self.assertIn(f"]({path})", readme)
        self.assertIn(
            "$cto-run docs/runbooks/release.md .skiphow/runs/release-0.1.0 main",
            readme,
        )
        self.assertIn(
            "/skiphow:cto-run docs/runbooks/release.md .skiphow/runs/release-0.1.0 main",
            readme,
        )

        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("ubuntu-latest", ci)
        self.assertIn("3.11", ci)
        self.assertIn("pip install -r requirements-dev.txt", ci)
        self.assertIn("python -m unittest discover -s tests -v", ci)
        self.assertIn("git diff --check", ci)

        dependabot = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("pip", dependabot)
        self.assertIn("github-actions", dependabot)
        self.assertIn("weekly", dependabot)
