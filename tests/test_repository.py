"""Repository-level contracts for the current package."""

import json
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_only_skiphow_is_a_public_skill_for_both_hosts() -> None:
    codex = sorted(path.parent.name for path in (ROOT / "plugins/skiphow/skills").glob("*/SKILL.md"))
    claude = sorted(path.parent.name for path in (ROOT / "adapters/claude/skills").glob("*/SKILL.md"))
    assert codex == ["skiphow"]
    assert claude == ["skiphow"]
    metadata = yaml.safe_load(read("plugins/skiphow/skills/skiphow/agents/openai.yaml"))
    assert metadata["policy"]["allow_implicit_invocation"] is True
    assert not list((ROOT / "plugins/skiphow/skills/skiphow/references").rglob("openai.yaml"))


def test_claude_controller_can_reach_internal_campaign_policy() -> None:
    adapter = read("adapters/claude/skills/skiphow/SKILL.md")
    controller_path = (
        ROOT / "plugins/skiphow/skills/skiphow/references/engineering/cto/SKILL.md"
    )
    controller = controller_path.read_text(encoding="utf-8")
    campaign = (controller_path.parent / "../../campaign/cto-run/SKILL.md").resolve()
    assert "plugins/skiphow/skills/skiphow/SKILL.md" in adapter
    assert "../../campaign/cto-run/SKILL.md" in controller
    assert campaign.is_file()
    assert "disable-model-invocation" not in campaign.read_text(encoding="utf-8")


def test_router_owns_intent_and_mutation_policy() -> None:
    router = read("plugins/skiphow/skills/skiphow/SKILL.md")
    assert "project answers, inspection, research, review" in router
    for intent in ("ANSWER", "CAPTURE", "DECIDE", "CHANGE", "REPAIR", "CONTINUE"):
        assert f"`{intent}`" in router
    assert "Analysis, research, review, diagnosis-only, and planning requests are read-only" in router
    assert "lightweight delivery brief" in router
    assert "Do not require shaping" in router
    assert "`CAMPAIGN` is an internal execution shape" in router


def test_internal_reference_paths_resolve() -> None:
    root = ROOT / "plugins/skiphow/skills/skiphow"
    for source in root.rglob("*.md"):
        if "upstream" in source.parts:
            continue
        for target in re.findall(r"`([^`]*?(?:SKILL\.md|references/[^`]+\.md))`", source.read_text(encoding="utf-8")):
            candidate = (source.parent / target).resolve()
            assert candidate.is_file(), f"{source.relative_to(ROOT)} -> {target}"


def test_product_records_and_acceptance_are_triggered() -> None:
    product = read("plugins/skiphow/skills/skiphow/references/product/shape/references/product-contract.md")
    acceptance = read("plugins/skiphow/skills/skiphow/references/product/shape/references/product-acceptance.md")
    reviewer = read("plugins/skiphow/skills/skiphow/references/product/shape/references/reviewer.md")
    assert "Lightweight delivery brief" in product
    assert "Extended product decision record" in product
    assert "Do not create an acceptance receipt for an ordinary clear change" in acceptance
    assert "Ordinary clear features" in reviewer


def test_tracking_is_optional_and_issues_first() -> None:
    tracker = read("plugins/skiphow/skills/skiphow/references/trackers/github-task/SKILL.md")
    setup = read("plugins/skiphow/skills/skiphow/references/trackers/setup/SKILL.md")
    capture = read("plugins/skiphow/skills/skiphow/references/product/intake/SKILL.md")
    assert "An Issue is the canonical tracked unit" in tracker
    assert "Project absence is `NOT_CONFIGURED`" in tracker
    assert "Never scan Projects to guess" in tracker
    assert "Core SkipHow needs no setup" in setup
    assert ".skiphow/config.json" in setup
    assert ".skiphow/config.yml" not in setup
    assert "strict_lifecycle" not in setup
    assert ".skiphow/inbox.md" in capture


def test_default_package_has_no_hooks_or_legacy_gate_policy() -> None:
    claude = json.loads(read(".claude-plugin/plugin.json"))
    codex = json.loads(read("plugins/skiphow/.codex-plugin/plugin.json"))
    assert "hooks" not in claude
    assert "hooks" not in codex
    assert not (ROOT / "plugins/skiphow/hooks/hooks.json").exists()
    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "plugins/skiphow/scripts").glob("*.py")
    )
    assert "Human" + " Gate" not in runtime


def test_metadata_and_version_contract() -> None:
    version = read("VERSION").strip()
    manifest = json.loads(read("plugins/skiphow/.codex-plugin/plugin.json"))
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert manifest["version"] == version
    assert len(manifest["interface"]["shortDescription"]) <= 30
    assert len(manifest["interface"]["defaultPrompt"]) <= 3
    assert all("setup" not in prompt.lower() for prompt in manifest["interface"]["defaultPrompt"])
    marketplace = json.loads(read(".agents/plugins/marketplace.json"))
    assert marketplace["plugins"][0]["policy"]["products"] == ["CODEX"]


def test_campaign_state_is_sparse() -> None:
    state = read("plugins/skiphow/skills/skiphow/references/campaign/cto-run/references/state-contract.md")
    policy = read("plugins/skiphow/skills/skiphow/references/campaign/cto-run/references/operating-policy.md")
    assert "Keep only fields used by the campaign" in state
    assert "Add `reuse_check` only" in state
    assert "Generate `FINAL.md`" in policy
    assert "After three consecutive failures" not in policy


def test_host_capability_vocabulary_stays_in_sync() -> None:
    canonical = read(
        "plugins/skiphow/skills/skiphow/references/host-capabilities.md"
    )
    architecture = read("docs/architecture.md")
    architecture_section = architecture.split("## Host capability contract", 1)[1].split(
        "## Campaign state", 1
    )[0]
    canonical_names = set(re.findall(r"^- `([^`]+)`:", canonical, re.MULTILINE))
    documented_names = set(re.findall(r"^- `([^`]+)`$", architecture_section, re.MULTILINE))
    assert canonical_names == documented_names


def test_campaign_and_authority_boundaries_are_explicit() -> None:
    controller = read("plugins/skiphow/skills/skiphow/references/engineering/cto/SKILL.md")
    technical = read("plugins/skiphow/skills/skiphow/references/engineering/cto/references/technical-policy.md")
    campaign = read("plugins/skiphow/skills/skiphow/references/campaign/cto-run/SKILL.md")
    acceptance = read("plugins/skiphow/skills/skiphow/references/product/shape/references/product-acceptance.md")
    assert "Bounded parallel work stays `EXECUTE`" in controller
    assert "current verbatim user request" in technical
    assert "Defining a hard-stop condition does not stop the run" in campaign
    assert "Campaign execution alone does not trigger it" in acceptance


def test_technical_reuse_policy_is_contextual() -> None:
    policy = read("plugins/skiphow/skills/skiphow/references/engineering/cto/references/technical-policy.md")
    assert "maintenance evidence appropriate to the project's maturity" in policy
    assert "universal thresholds" in policy
    assert "release within the last 12 months" not in policy
    assert "Each receipt includes `reuse_check`" not in policy
    router = read("plugins/skiphow/skills/skiphow/SKILL.md")
    assert "report that check as `UNVERIFIED` without weakening independent evidence" in router


def test_documentation_has_zero_config_first_run_and_support_matrix() -> None:
    readme = read("README.md")
    assert "## Install with Codex" in readme
    assert "## Install with Claude Code" in readme
    assert "## Support matrix" in readme
    assert "No tracker, Project, Python, `gh`, setup command, or hook is required" in readme
    first_screen = "\n".join(readme.splitlines()[:80])
    assert "preflight" not in first_screen.lower()
    assert "cto-run" not in first_screen.lower()
