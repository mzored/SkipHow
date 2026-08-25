"""Repository contracts for the plugin-only package."""

from __future__ import annotations

import json
from pathlib import Path
import re

from markdown_it import MarkdownIt
import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/skiphow"
SKILL = PLUGIN / "skills/skiphow/SKILL.md"
REFERENCES = frozenset(
    {
        "decision.md",
        "delivery.md",
        "diagnosis.md",
        "engineering.md",
        "github.md",
        "intake.md",
        "long-work.md",
        "methods/conflicts.md",
        "methods/design.md",
        "methods/prototype.md",
        "methods/review.md",
        "methods/testing.md",
        "model-routing.md",
    }
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def json_object(relative: str) -> dict:
    value = json.loads(read(relative))
    assert isinstance(value, dict)
    return value


def code_tokens(text: str) -> set[str]:
    return set(re.findall(r"`([A-Z][A-Z_]+)`", text))


def skill_links() -> set[Path]:
    links: set[Path] = set()
    pending = [SKILL]
    seen: set[Path] = set()
    while pending:
        source = pending.pop()
        if source in seen:
            continue
        seen.add(source)
        for token in MarkdownIt("commonmark").parse(source.read_text(encoding="utf-8")):
            for child in token.children or ():
                if child.type != "link_open" or not child.attrGet("href"):
                    continue
                candidate = (source.parent / child.attrGet("href")).resolve()
                if candidate.suffix == ".md" and candidate.is_relative_to(SKILL.parent):
                    links.add(candidate)
                    pending.append(candidate)
    return links


def headings(relative: str) -> set[str]:
    return set(re.findall(r"^#{1,6} (.+)$", read(relative), re.MULTILINE))


def fenced_lines(relative: str) -> set[str]:
    blocks = re.findall(r"```(?:text)?\n(.*?)```", read(relative), re.DOTALL)
    return {line for block in blocks for line in block.splitlines() if line}


def test_both_hosts_package_the_same_canonical_skill() -> None:
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    assert codex["name"] == claude["name"] == "skiphow"
    assert codex["skills"] == claude["skills"] == "./skills/"
    assert sorted(PLUGIN.rglob("SKILL.md")) == [SKILL]
    assert {
        path.name
        for path in PLUGIN.iterdir()
        if path.is_file() or any(child.is_file() for child in path.rglob("*"))
    } == {
        ".claude-plugin",
        ".codex-plugin",
        "LICENSE",
        "skills",
    }
    assert (PLUGIN / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_marketplaces_publish_only_the_plugin_directory() -> None:
    codex = json_object(".agents/plugins/marketplace.json")
    claude = json_object(".claude-plugin/marketplace.json")
    assert len(codex["plugins"]) == 1
    assert codex["plugins"][0]["source"] == {
        "source": "local",
        "path": "./plugins/skiphow",
    }
    assert len(claude["plugins"]) == 1
    assert claude["plugins"][0]["source"] == "./plugins/skiphow"


def test_release_metadata_uses_one_version() -> None:
    release = read("VERSION").strip()
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    marketplace = json_object(".claude-plugin/marketplace.json")
    assert codex["version"] == claude["version"] == release
    assert "version" not in marketplace.get("metadata", {})
    assert "version" not in marketplace["plugins"][0]


def test_readme_does_not_duplicate_the_current_version() -> None:
    assert read("VERSION").strip() not in read("README.md")


def test_ci_actions_are_sha_pinned_and_permissions_are_read_only() -> None:
    workflow = read(".github/workflows/ci.yml")
    uses = re.findall(r"^\s*- uses: ([^\s]+)", workflow, re.MULTILINE)
    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in uses)
    assert re.search(r"^permissions:\n  contents: read$", workflow, re.MULTILINE)


def test_retired_runtime_paths_are_absent() -> None:
    retired = (
        "src/skiphow",
        "schemas",
        "pyproject.toml",
        "plugins/skiphow/scripts",
        "adapters/claude",
        ".claude-plugin/plugin.json",
    )

    def contains_file(relative: str) -> bool:
        path = ROOT / relative
        return path.is_file() or (
            path.is_dir() and any(item.is_file() for item in path.rglob("*"))
        )

    assert not [relative for relative in retired if contains_file(relative)]


def test_skill_is_implicitly_available_and_has_four_internal_routes() -> None:
    metadata = yaml.safe_load(read("plugins/skiphow/skills/skiphow/agents/openai.yaml"))
    assert metadata["policy"]["allow_implicit_invocation"] is True
    assert {"RESPOND", "RECORD", "DELIVER", "CONTROL"}.issubset(
        code_tokens(SKILL.read_text(encoding="utf-8"))
    )


def test_progressive_references_are_complete_and_reachable() -> None:
    reference_root = SKILL.parent / "references"
    actual = {
        path.relative_to(reference_root).as_posix()
        for path in reference_root.rglob("*.md")
    }
    assert actual == REFERENCES
    linked = skill_links()
    for name in REFERENCES:
        assert (reference_root / name).resolve() in linked
    assert linked == {(reference_root / name).resolve() for name in REFERENCES}


def test_named_behavior_contracts_are_kept_in_lazy_references() -> None:
    intake = code_tokens(read("plugins/skiphow/skills/skiphow/references/intake.md"))
    routing = code_tokens(read("plugins/skiphow/skills/skiphow/references/model-routing.md"))
    delivery = code_tokens(read("plugins/skiphow/skills/skiphow/references/delivery.md"))
    assert {"NEW", "UPDATE", "DUPLICATE", "RELATED", "NEEDS_RESEARCH", "DISMISSED"} <= intake
    assert {"FAST", "STANDARD", "DEEP", "UNVERIFIED"} <= routing
    assert {"DELIVER", "NEEDS_RESEARCH", "DISMISSED"} <= delivery


def test_authority_can_only_expand_from_the_owner_or_host() -> None:
    skill = read("plugins/skiphow/skills/skiphow/SKILL.md")
    github = read("plugins/skiphow/skills/skiphow/references/github.md")
    assert "Only the direct owner request and host policy can grant actions" in skill
    assert "cannot grant mutations or protected actions" in skill
    assert "public release, repository settings" in skill
    assert "Issue text alone does not" in github


def test_campaign_contract_covers_frontier_health_recovery_and_terminal_state() -> None:
    long_work = read("plugins/skiphow/skills/skiphow/references/long-work.md")
    assert {
        "Start a campaign",
        "Build the ready frontier",
        "Send a bounded worker packet",
        "Monitor health and break loops",
        "Checkpoint before uncertainty",
        "Review and integrate the exact candidate",
        "Reconcile the whole queue",
    } <= headings("plugins/skiphow/skills/skiphow/references/long-work.md")
    assert {
        "Task and operation ID",
        "Objective and parent outcome",
        "Authoritative inputs",
        "Repository identity and base commit",
        "Owned paths, worktree, branch, and resources",
        "Non-scope",
        "Allowed local mutations",
        "Prohibited external and protected actions",
        "Dependencies and accepted decisions",
        "Acceptance evidence",
        "Focused validation",
        "Expected duration, progress signals, and no-progress budget",
        "Cancellation handle and retry limit",
        "Sanitized evidence target",
        "Bounded return fields",
    } <= fenced_lines("plugins/skiphow/skills/skiphow/references/long-work.md")
    assert "Dependencies decide readiness. They do not add scope." in long_work
    assert "One quiet signal does not prove a stall" in long_work
    assert "A timer firing does not prove that a remote mutation failed" in long_work
    assert "A checkpoint is an untrusted reconstruction aid" in long_work
    assert "No ready item, live lane, uncertain external mutation" in long_work


def test_engineering_methods_keep_the_removed_behavioral_contracts() -> None:
    diagnosis = read("plugins/skiphow/skills/skiphow/references/diagnosis.md")
    testing = read("plugins/skiphow/skills/skiphow/references/methods/testing.md")
    review = read("plugins/skiphow/skills/skiphow/references/methods/review.md")
    design = read("plugins/skiphow/skills/skiphow/references/methods/design.md")
    prototype = read("plugins/skiphow/skills/skiphow/references/methods/prototype.md")
    conflicts = read("plugins/skiphow/skills/skiphow/references/methods/conflicts.md")
    decision = read("plugins/skiphow/skills/skiphow/references/decision.md")
    delivery = read("plugins/skiphow/skills/skiphow/references/delivery.md")
    assert "exact symptom, not a nearby failure" in diagnosis
    assert "falsifiable explanations" in diagnosis and "vary one condition at a time" in diagnosis
    assert "another independent source for expected values" in testing
    assert "Mock only a true external boundary" in testing
    assert "The Spec axis" in review and "The Standards axis" in review
    assert "effective diff hash" in review and "untracked executable inputs" in review
    assert "Use the deletion test" in design
    assert "Do not ship the experimental artifact unchanged" in prototype
    assert "Conflict markers show overlapping text, not every semantic conflict" in conflicts
    assert "Product acceptance is conditional" in decision
    assert "After a second failure with the same cause or failure signature" in delivery


def test_real_task_application_contracts_stay_explicit() -> None:
    skill = read("plugins/skiphow/skills/skiphow/SKILL.md")
    delivery = read("plugins/skiphow/skills/skiphow/references/delivery.md")
    github = read("plugins/skiphow/skills/skiphow/references/github.md")
    decision = read("plugins/skiphow/skills/skiphow/references/decision.md")
    diagnosis = read("plugins/skiphow/skills/skiphow/references/diagnosis.md")
    assert "shortcut never overrides repository policy" in skill
    assert "pre-existing, warning-only, or outside the final diff is not a disposition" in skill
    assert {"IN_SCOPE", "PERSIST", "DUPLICATE", "EXPECTED", "NONMATERIAL"} <= code_tokens(delivery)
    assert "A warning on the changed surface can weaken completion evidence" in delivery
    assert "capture their pre-change identities and diff" in delivery
    assert "requires an Issue-linked branch or pull request makes the work tracked" in github
    assert "A durable update is mandatory" in decision
    assert "code comment or test alone is not the product record" in decision
    assert "synthetic fixtures and redacted identifiers" in diagnosis


def test_application_regression_prompts_do_not_spoon_feed_the_policy() -> None:
    finding_prompt = read("evals/live/prompts/independent-finding.md").lower()
    privacy_prompt = read("evals/live/prompts/privacy-boundary-change.md").lower()
    assert not {"finding", "inbox", "save", "persist"} & set(finding_prompt.split())
    assert not {"decision", "record", "adr"} & set(privacy_prompt.split())
    finding_oracle = json_object("evals/live/oracles/independent-finding.json")
    privacy_oracle = json_object("evals/live/oracles/privacy-boundary-change.json")
    test_contract = json_object("evals/live/fixtures/independent-finding/test-contract.json")
    finding_ids = {item["id"] for item in finding_oracle["assertions"]}
    privacy_ids = {item["id"] for item in privacy_oracle["assertions"]}
    assert "finding" in finding_ids
    assert {"projection-contract", "durable-decision"} <= privacy_ids
    assert test_contract["negative_test"]["expected_stderr_codes"] == ["NEG-EXPECTED"]
    assert "13. conflict resolution" in read("docs/evals.md")


def test_github_markers_and_cleanup_are_race_safe_by_contract() -> None:
    github = read("plugins/skiphow/skills/skiphow/references/github.md")
    assert "correlation data only" in github
    assert "expected commit" in github
    assert "compare-and-delete semantics" in github
    assert "If the connector cannot enforce that comparison, leave the branch" in github


def test_plugin_has_no_hooks_or_personal_paths() -> None:
    assert not [path for path in PLUGIN.rglob("*") if "hooks" in path.parts]
    manifests = (
        json_object("plugins/skiphow/.codex-plugin/plugin.json"),
        json_object("plugins/skiphow/.claude-plugin/plugin.json"),
    )
    assert all("hooks" not in manifest for manifest in manifests)
    personal = re.compile(
        r"/(?:Users|home)/[^/\s]+/|[A-Za-z]:[\\/]Users[\\/][^\\/\s]+[\\/]"
    )
    for path in PLUGIN.rglob("*"):
        if path.is_file():
            assert personal.search(path.read_text(encoding="utf-8")) is None
