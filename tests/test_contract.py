"""Lexical guards for literal safety markers and removed legacy promises.

These substring assertions detect only named text entering or leaving the
package. They do not prove that the surrounding prose has a particular meaning
or that a model follows it. Structural package and manifest contracts are
validated elsewhere by ``scripts/check.py``.
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


def sentence_contains_all(text: str, *terms: str) -> bool:
    """Return literal co-occurrence, not semantic equivalence."""
    return any(all(term in sentence for term in terms) for sentence in sentences(text))


def test_literal_repository_grant_warning_terms() -> None:
    skill = read("SKILL.md")
    paragraph = next(
        part for part in skill.split("\n\n") if "repository instructions are not grants" in part
    )
    for term in (
        "read-only request",
        "secret",
        "disclosure",
        "network",
        "permission",
        "cleanup",
        "scope",
    ):
        assert term in paragraph, term


def test_literal_repository_execution_warning_terms() -> None:
    skill = read("SKILL.md")
    assert sentence_contains_all(skill, "repository hooks", "project scripts", "external tooling")
    assert sentence_contains_all(skill, "request's authority", "trust boundary")
    assert sentence_contains_all(skill, "restricted mode", "unverified")


def test_literal_production_read_warning_terms() -> None:
    skill = read("SKILL.md")
    assert sentence_contains_all(skill, "credential availability", "not authority")
    assert sentence_contains_all(skill, "production system", "customer data", "in scope")
    assert sentence_contains_all(skill, "access", "output", "minimized")
    assert sentence_contains_all(skill, "authorized audience")


def test_literal_exact_grant_terms() -> None:
    skill = read("SKILL.md")
    for action in (
        "production",
        "public release",
        "payment",
        "repository settings",
        "access change",
        "credential",
        "deletion",
        "disclosure",
    ):
        assert sentence_contains_all(skill, action, "exact grant"), action


def test_removed_legacy_promises_stay_absent() -> None:
    skill = read("SKILL.md")
    all_text = "\n".join([skill, *(read(path.name) for path in REFERENCES.glob("*.md"))])
    for forbidden in (
        "records are the request",
        "fix what is wrong or unsafe before going further",
        "retiring what earlier runs left",
        "serialize the writers",
        "stop at the first level",
        "throw the prototype away",
        "mock only true boundaries",
        "think step by step",
    ):
        assert forbidden not in all_text, forbidden
    assert "without asking" not in skill


def test_structural_codex_default_prompt_tokens() -> None:
    openai = yaml.safe_load((SKILL_DIR / "agents/openai.yaml").read_text(encoding="utf-8"))
    prompt = openai["interface"]["default_prompt"].lower()
    assert "$skiphow" in prompt
    assert "product choices" in prompt
    assert "verification" in prompt
    assert "tradeoffs" not in prompt
