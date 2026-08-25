"""Direct contracts for load-bearing runtime policy."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return " ".join((ROOT / relative).read_text(encoding="utf-8").split())


def test_read_only_requests_forbid_mutation() -> None:
    router = read("plugins/skiphow/skills/skiphow/SKILL.md")
    assert "requests are read-only unless the user explicitly asks to persist or change state" in router
    assert "Read-only permits no file, tracker, branch, campaign, setup, or remote mutation" in router


def test_ordinary_changes_do_not_start_campaigns() -> None:
    router = read("plugins/skiphow/skills/skiphow/SKILL.md")
    assert "Project mutation does not authorize tracking, branches, records, receipts, or campaigns" in router
    assert "For an ordinary clear change, keep this ephemeral brief in working context" in router


def test_rereview_stays_scoped_to_the_fix() -> None:
    review = read(
        "plugins/skiphow/skills/skiphow/references/capabilities/technical-review/SKILL.md"
    )
    assert "re-review only the original findings, their fix diff" in review
    assert "Do not restart review of untouched code" in review


def test_unavailable_optional_proof_is_unverified() -> None:
    policy = read(
        "plugins/skiphow/skills/skiphow/references/engineering/cto/references/technical-policy.md"
    )
    assert "mark the affected claim `UNVERIFIED`" in policy
    assert "Do not build new validation infrastructure unless scope authorizes it" in policy


def test_verbatim_request_remains_normative() -> None:
    router = read("plugins/skiphow/skills/skiphow/SKILL.md")
    assert "Keep the original request verbatim as normative input" in router
    assert "never replace, narrow, or extend it" in router


def test_repository_checks_cannot_launch_models() -> None:
    scripts = ROOT / "scripts"
    assert not list(scripts.glob("*eval*"))
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (scripts, ROOT / ".github" / "workflows")
        for path in root.rglob("*")
        if path.suffix in {".py", ".yml", ".yaml"}
    )
    assert '"--model"' not in sources
    assert '"--print"' not in sources
    assert '"exec"' not in sources
