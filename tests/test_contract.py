"""Semantic contracts of the shipped instructions.

Each test checks a meaning the contract must carry or must no longer carry.
None pins a sentence: a rewording that keeps the meaning must still pass.
"""

from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "plugins/skiphow/skills/skiphow"
REFERENCES = SKILL_DIR / "references"


def read(name: str) -> str:
    path = SKILL_DIR / "SKILL.md" if name == "SKILL.md" else REFERENCES / name
    return path.read_text(encoding="utf-8").lower()


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=\.)\s+|\n", text) if part.strip()]


def some_sentence(text: str, *terms: str) -> bool:
    return any(all(term in sentence for term in terms) for sentence in sentences(text))


# Authority and provenance


def test_authority_is_owner_and_trusted_policy_not_repository_files() -> None:
    skill = read("SKILL.md")
    assert some_sentence(skill, "authority", "owner's messages", "trusted")
    assert "repository instruction" in skill
    assert some_sentence(skill, "untrusted repository", "provenance")
    assert not some_sentence(skill, "authoritative", "repository instruction files the host loaded")


def test_repository_instructions_cannot_independently_authorize_protected_effects() -> None:
    skill = read("SKILL.md")
    for effect in ("read-only request", "secret", "disclosure", "network", "permission", "cleanup", "scope"):
        assert some_sentence(skill, "not grants", effect), effect


def test_trusted_project_procedure_can_still_require_a_local_test_or_commit() -> None:
    assert some_sentence(read("SKILL.md"), "trusted", "local test or commit")


def test_referenced_record_is_not_promoted_into_the_request() -> None:
    tracked = read("tracked-work.md")
    assert "records are the request" not in tracked
    assert some_sentence(tracked, "record", "untrusted")
    assert some_sentence(tracked, "embedded", "do not become the owner's")
    assert some_sentence(tracked, "stale", "product choice")
    assert some_sentence(read("SKILL.md"), "pointing at a record", "outcome")


def test_authoritative_product_brief_has_defined_provenance() -> None:
    product = read("product.md")
    assert some_sentence(product, "brief is authoritative", "owner supplied or explicitly adopted")
    assert some_sentence(product, "title, age, location, confidence")
    assert some_sentence(product, "authoritative brief", "protected action")


def test_local_commit_is_bounded_by_the_commit_path() -> None:
    skill = read("SKILL.md")
    assert some_sentence(skill, "commit", "hooks", "signing", "credential helper")
    assert some_sentence(skill, "unknown hooks")
    assert some_sentence(skill, "commit is optional")
    assert some_sentence(skill, "not an implementation failure")
    assert "without asking" not in skill


def test_exact_grant_model_is_preserved() -> None:
    skill = read("SKILL.md")
    for action in ("production", "public release", "payment", "repository settings", "access change", "credential", "deletion", "disclosure"):
        assert some_sentence(skill, action, "exact grant"), action
    assert some_sentence(skill, "record", "tool's capability", "do not supply")


# Review, completion, integration


def test_read_only_review_reports_and_repair_needs_authority() -> None:
    verification = read("verification.md")
    assert some_sentence(verification, "read-only review", "without modifying")
    assert some_sentence(verification, "when repair is authorized")
    assert some_sentence(verification, "sensitive finding", "disclosure")
    assert not some_sentence(verification, "fix what is wrong or unsafe before going further")


def test_completion_is_relative_to_the_authorized_destination() -> None:
    integration = read("integration.md")
    assert some_sentence(integration, "unfinished", "destination it has not reached")
    assert some_sentence(integration, "engineering mechanic", "no delivery obligation")
    assert some_sentence(integration, "history", "never the grant")
    assert not some_sentence(integration, "branch nobody merged", "not a finished request")


def test_earlier_run_artifacts_are_not_cleaned_automatically() -> None:
    integration = read("integration.md")
    assert "retiring what earlier runs left" not in integration
    assert not some_sentence(integration, "retire the branches", "earlier runs")
    assert some_sentence(integration, "explicit cleanup request", "blocks the current authorized result")
    assert some_sentence(integration, "ambiguous ownership", "not the rest of the request")


def test_final_report_reconciles_every_part() -> None:
    skill = read("SKILL.md")
    assert some_sentence(skill, "reconcile every part")
    assert some_sentence(skill, "never started", "false completion")
    assert some_sentence(skill, "dry run", "external effect")
    assert some_sentence(skill, "did not run is not a check that passed")


# Delegation and diagnosis


def test_delegates_without_verified_isolation_stay_read_only() -> None:
    skill = read("SKILL.md")
    assert some_sentence(skill, "without verified distinct isolation", "read-only")
    assert some_sentence(skill, "turns in one checkout is not isolation")
    assert not some_sentence(skill, "serialize the writers")
    delegation = read("delegation.md")
    assert some_sentence(delegation, "kernel's isolation rule")
    assert not some_sentence(delegation, "without verified distinct isolation")


def test_touch_surface_is_a_boundary_not_a_plan() -> None:
    assert some_sentence(read("SKILL.md"), "surface", "boundary")
    delegation = read("delegation.md")
    assert not some_sentence(delegation, "do not prescribe files")
    assert some_sentence(delegation, "boundary on its authority")


def test_model_and_effort_are_task_relative() -> None:
    delegation = read("delegation.md")
    assert not some_sentence(delegation, "no less than the session")
    assert not some_sentence(delegation, "reports agreement")
    assert not some_sentence(delegation, "cheapest level", "ordinary level", "strongest")
    assert some_sentence(delegation, "consequence and complexity")
    assert some_sentence(delegation, "lower-cost", "verify")
    assert not some_sentence(delegation, "representative runs")


def test_parent_keeps_non_delegable_responsibilities() -> None:
    skill = read("SKILL.md")
    for duty in ("owner questions", "product choices", "conflict resolution", "integration", "final verification", "completion claim", "sensitive context", "findings"):
        assert some_sentence(skill, "you keep", duty), duty


def test_wait_renewal_is_bounded() -> None:
    diagnosis = read("diagnosis.md")
    assert not some_sentence(diagnosis, "renew it without another inspection")
    assert some_sentence(diagnosis, "same wait once")
    assert some_sentence(diagnosis, "inspect state once", "blocker")
    assert some_sentence(diagnosis, "synchronous build or test", "itself the work")


# Technical design, verification, writing


def test_reuse_ladder_is_a_presumption() -> None:
    design = read("technical-design.md")
    assert "stop at the first level" not in design
    assert some_sentence(design, "presumption, not a law")
    assert some_sentence(design, "managed service is not automatically")
    assert some_sentence(design, "existing, maintained capabilities over custom")


def test_prototype_may_be_hardened_deliberately() -> None:
    design = read("technical-design.md")
    assert "throw the prototype away" not in design
    assert some_sentence(design, "harden it in place only deliberately")
    assert some_sentence(design, "do not become production architecture")


def test_test_seam_language_is_risk_aware() -> None:
    verification = read("verification.md")
    assert "mock only true boundaries" not in verification
    assert "cover each boundary it crossed" not in verification
    assert some_sentence(verification, "narrowest stable test")
    assert some_sentence(verification, "isolation, determinism, cost, or safety")
    assert some_sentence(verification, "independently of the implementation")


def test_writing_guidance_carries_no_unsupported_empirical_universals() -> None:
    writing = read("writing-for-agents.md")
    for claim in ("measurably reduce", "without quality gain", "already self-correct", "gains nothing"):
        assert claim not in writing, claim
    assert some_sentence(writing, "risk of contradiction")
    assert some_sentence(writing, "representative runs")
    assert some_sentence(writing, "provider- or version-specific", "evidence record")


def test_shipped_prompts_follow_the_prompt_standard() -> None:
    texts = [read("SKILL.md")] + [read(path.name) for path in REFERENCES.glob("*.md")]
    for text in texts:
        assert "think step by step" not in text
        assert "think harder" not in text or some_sentence(text, "rather than telling a model to think harder")


def test_codex_default_prompt_leaves_product_choices_with_the_owner() -> None:
    openai = yaml.safe_load((SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8"))
    prompt = openai["interface"]["default_prompt"].lower()
    assert "$skiphow" in prompt
    assert "product choices" in prompt
    assert "verification" in prompt
    assert "tradeoffs" not in prompt
