"""Structural contracts for the plugin-only package.

These tests check package shape and the few semantic invariants whose absence
caused a field failure. Other prose remains free to change.
"""

from __future__ import annotations

import importlib.util
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
        "model-routing.md",
        "worktrees.md",
    }
)
CHECK = importlib.util.spec_from_file_location("skiphow_check_shape", ROOT / "scripts/check.py")
_MODULE = importlib.util.module_from_spec(CHECK)
CHECK.loader.exec_module(_MODULE)
VERSIONED_MODEL = _MODULE.CONCRETE_MODEL_ID
PERSONAL_PATH = _MODULE.PERSONAL_PATH


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def json_object(relative: str) -> dict:
    value = json.loads(read(relative))
    assert isinstance(value, dict)
    return value


def code_tokens(text: str) -> set[str]:
    return set(re.findall(r"`([A-Z][A-Z_]+)`", text))


def frontmatter(path: Path) -> dict:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    assert match, path
    value = yaml.safe_load(match.group(1))
    assert isinstance(value, dict)
    return value


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


def headings(relative: str) -> list[str]:
    return re.findall(r"^#{1,6} (.+)$", read(relative), re.MULTILINE)


def fenced_blocks(relative: str) -> list[str]:
    return re.findall(r"```(?:text)?\n(.*?)```", read(relative), re.DOTALL)


# Package shape


def test_both_hosts_package_the_same_canonical_skill() -> None:
    codex = json_object("plugins/skiphow/.codex-plugin/plugin.json")
    claude = json_object("plugins/skiphow/.claude-plugin/plugin.json")
    assert codex["name"] == claude["name"] == "skiphow"
    assert codex["skills"] == claude["skills"] == "./skills/"
    assert "hooks" not in codex and "agents" not in codex
    assert "hooks" not in claude and "agents" not in claude
    assert sorted(PLUGIN.rglob("SKILL.md")) == [SKILL]
    assert {
        path.name
        for path in PLUGIN.iterdir()
        if path.is_file() or any(child.is_file() for child in path.rglob("*"))
    } == {".claude-plugin", ".codex-plugin", "agents", "hooks", "LICENSE", "skills"}
    assert (PLUGIN / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_marketplaces_publish_only_the_plugin_directory() -> None:
    codex = json_object(".agents/plugins/marketplace.json")
    claude = json_object(".claude-plugin/marketplace.json")
    assert len(codex["plugins"]) == 1
    assert codex["plugins"][0]["source"] == {"source": "local", "path": "./plugins/skiphow"}
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
    assert release not in read("README.md")
    assert f"| {release.rsplit('.', 1)[0]}.x | Yes |" in read("SECURITY.md")


def every_uses(node: object) -> list[str]:
    """Collect every `uses` value, including job-level reusable workflows."""
    if isinstance(node, dict):
        found = [node["uses"]] if isinstance(node.get("uses"), str) else []
        return found + [item for value in node.values() for item in every_uses(value)]
    if isinstance(node, list):
        return [item for value in node for item in every_uses(value)]
    return []


def test_workflows_are_sha_pinned_with_least_privilege() -> None:
    """A job-level `uses` is a dependency too, and permissions is a whole mapping.

    The step-level regex this replaced ignored reusable workflows, and the
    permissions regex matched a prefix, so an added `id-token: write` stayed green.
    """
    for name, granted in (("ci.yml", "read"), ("release.yml", "write")):
        workflow = yaml.safe_load(read(f".github/workflows/{name}"))
        uses = every_uses(workflow)
        assert uses, name
        assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in uses), (name, uses)
        assert workflow["permissions"] == {"contents": granted}, name
        assert all("permissions" not in job for job in workflow["jobs"].values()), name


def test_release_refuses_a_tag_outside_main() -> None:
    workflow = yaml.safe_load(read(".github/workflows/release.yml"))
    steps = workflow["jobs"]["release"]["steps"]
    guard = next(step for step in steps if step.get("name") == "Require the tag commit to be on main")
    commands = [line.strip() for line in guard["run"].splitlines() if line.strip()]
    assert commands == [
        "git fetch --no-tags origin main",
        'git merge-base --is-ancestor "${GITHUB_SHA}" origin/main',
    ]



# Skill wiring


def test_skill_is_implicitly_available_and_has_four_internal_routes() -> None:
    metadata = yaml.safe_load(read("plugins/skiphow/skills/skiphow/agents/openai.yaml"))
    assert metadata["policy"]["allow_implicit_invocation"] is True
    assert {"RESPOND", "RECORD", "DELIVER", "CONTROL"} <= code_tokens(SKILL.read_text(encoding="utf-8"))


def test_progressive_references_are_complete_and_reachable() -> None:
    reference_root = SKILL.parent / "references"
    actual = {path.relative_to(reference_root).as_posix() for path in reference_root.rglob("*.md")}
    assert actual == REFERENCES
    assert skill_links() == {(reference_root / name).resolve() for name in REFERENCES}


def test_report_and_record_formats_are_fenced() -> None:
    report = fenced_blocks("plugins/skiphow/skills/skiphow/SKILL.md")
    assert any(
        block.split() == ["Result", "Evidence", "Rulings", "and", "findings", "Saved", "follow-ups", "Limits"]
        for block in report
    )
    handoff = fenced_blocks("plugins/skiphow/skills/skiphow/references/long-work.md")
    labels = {line.split(":")[0].strip("- ") for block in handoff for line in block.splitlines() if line.startswith("- ")}
    assert labels == {
        "Recorded", "Outcome", "Selected scope", "Queue", "Authority", "Accepted decisions",
        "Done", "In progress", "Owned resources", "Last external result", "Evidence",
        "Blockers", "Next safe action",
    }
    inbox = fenced_blocks("plugins/skiphow/skills/skiphow/references/intake.md")
    inbox_labels = {
        line.split(":")[0].strip("- ")
        for block in inbox
        for line in block.splitlines()
        if line.startswith("- ")
    }
    assert inbox_labels == {
        "Recorded", "Source", "Original", "Normalized", "Type",
        "Disposition", "Priority", "Links", "Evidence", "Assumptions", "Open questions",
    }


def test_named_contracts_stay_in_lazy_references() -> None:
    intake = code_tokens(read("plugins/skiphow/skills/skiphow/references/intake.md"))
    routing = read("plugins/skiphow/skills/skiphow/references/model-routing.md")
    review = code_tokens(read("plugins/skiphow/skills/skiphow/references/engineering.md"))
    assert {"NEW", "UPDATE", "DUPLICATE", "RELATED", "NEEDS_RESEARCH", "DISMISSED"} <= intake
    # `BLOCKED` left this reference in 1.10.0 with the escalation ladder it belonged to.
    # The ladder binds wherever a delegate exists, so it lives in the root now (ADR 0016).
    assert {"FAST", "STANDARD", "DEEP", "UNVERIFIED"} <= code_tokens(routing)
    assert "BLOCKED" not in code_tokens(routing)
    assert {"scout", "builder", "reviewer"} <= set(re.findall(r"`(\w+)`", routing))
    # Review findings carry the skill's four tags. A second findings vocabulary in a
    # reference contradicts the root contract, which is how `PERSISTED` reached a report.
    tags = code_tokens(read("plugins/skiphow/skills/skiphow/SKILL.md"))
    assert {"TRACKED", "SAVED", "UNSAVED", "DISMISSED", "BLOCKED"} <= tags
    assert not review & {"RESOLVED", "PERSISTED"}
    for relative in ("long-work.md", "github.md", "delivery.md"):
        assert {"BLOCKED", "UNVERIFIED"} & code_tokens(read(f"plugins/skiphow/skills/skiphow/references/{relative}"))


def test_autonomy_and_isolation_invariants_are_shipped() -> None:
    root = read("plugins/skiphow/skills/skiphow/SKILL.md")
    worktrees = read("plugins/skiphow/skills/skiphow/references/worktrees.md")
    builder = read("plugins/skiphow/agents/builder.md")
    assert "At every owner turn" in root
    assert "not from a required phrase" in root
    assert "non-production integration branch" in root
    assert "staging or production branch" in root
    assert "other installed host" in root
    assert "ordinary integration or commit commands and hooks" in root
    assert "normal path" in root
    assert "ordinary fast-forward push" in root
    assert "reject force or non-fast-forward updates" in root
    github = read("plugins/skiphow/skills/skiphow/references/github.md")
    assert "Do not create an Issue solely because a pull request is required" in github
    assert "Delete the remote head only when this operation created it" in github
    for forbidden_escape in ("alternate index", "plumbing commands", "force-checking out", "bypassing hooks"):
        assert forbidden_escape in worktrees
    assert "before the first write and before the commit" in builder
    assert "ordinary commit command and hooks" in builder
    routing = read("plugins/skiphow/skills/skiphow/references/model-routing.md")
    assert "owned worktree and branch" in routing
    assert "each call's working directory" in routing
    package_text = "\n".join(path.read_text(encoding="utf-8") for path in PLUGIN.rglob("*") if path.is_file())
    assert not re.search(r"end[- ]to[- ]end", package_text, re.IGNORECASE)


# Host adapters


def test_agent_adapters_route_roles_to_family_aliases() -> None:
    agents = {path.stem: frontmatter(path) for path in (PLUGIN / "agents").glob("*.md")}
    assert set(agents) == {"scout", "builder", "reviewer"}
    assert agents["scout"]["model"] == "haiku"
    assert agents["builder"]["model"] == "sonnet"
    assert agents["reviewer"]["model"] == "inherit"
    assert agents["scout"]["effort"] == "low"
    assert "effort" not in agents["reviewer"]
    assert agents["builder"]["isolation"] == "worktree"
    for role, meta in agents.items():
        assert meta["name"] == role
        assert meta["description"].strip()
        assert not ({"hooks", "mcpServers", "permissionMode"} & set(meta))
        tools = {item.strip() for item in str(meta.get("tools", "")).split(",") if item.strip()}
        assert tools
        if role == "builder":
            assert {"Edit", "Write"} <= tools
        else:
            assert not ({"Edit", "Write", "NotebookEdit"} & tools)


def test_cross_host_review_names_both_directions() -> None:
    """The escalated review lands on the other host, and both directions ship.

    One direction silently dropped would leave half the owners on a same-model
    reviewer with no signal that the rung is missing. The two effort renderings
    are the one `DEEP` level spelled in each host's own syntax; the reviewer
    adapter itself stays on `inherit`, so this is the only place they appear.
    """
    routing = read("plugins/skiphow/skills/skiphow/references/model-routing.md")
    bullets = {
        line.split(":", 1)[0].removeprefix("- From ").strip(): line
        for line in routing.splitlines()
        if line.startswith("- From ")
    }
    assert set(bullets) == {"Claude Code", "Codex"}
    # Each host names the *other* host's command. Asserting the two commands are
    # present somewhere let a swap -- Claude asking Claude -- stay green.
    assert "codex review" in bullets["Claude Code"]
    assert "claude -p" in bullets["Codex"]
    assert "claude -p" not in bullets["Claude Code"]
    assert "codex review" not in bullets["Codex"]
    # Each direction declares its own boundary flag. They are not equally strong
    # -- Codex sandboxes the pass, plan mode only bounds the model's tools -- so
    # dropping either one leaves that direction's boundary unstated.
    assert 'sandbox_mode="read-only"' in bullets["Claude Code"]
    assert "--effort high" in bullets["Codex"]
    assert "--permission-mode plan" in bullets["Codex"]
    # Measured 2026-08-27: `claude --effort` warns and falls back on an unknown value,
    # so the request is real. `codex -c model_reasoning_effort` is accepted for any
    # value, including a bogus one, and the run stays at the host default -- so naming
    # a level there would be a claim the tool does not honour.
    assert "model_reasoning_effort" not in routing
    # `--allowedTools` pre-approves rather than restricts, so it is never the boundary.
    assert "--allowedTools" not in routing
    # The trigger stays where the review widens; the mechanics stay here.
    engineering = read("plugins/skiphow/skills/skiphow/references/engineering.md")
    assert "model-routing.md" in engineering
    mechanics = ("codex review", "claude -p", "--effort", "model_reasoning_effort", "--permission-mode")
    assert [token for token in mechanics if token in engineering] == []


def test_every_adr_status_agrees_with_the_index() -> None:
    """An ADR whose own Status omits its amendment reads as still in force.

    Five ADRs disagreed with the index at once, in both directions, leaving
    superseded Decisions -- Codex `[agents]` config, shipped role files -- looking
    current to anyone who opened the file rather than the table.
    """
    index = read("docs/decisions/README.md")
    rows = dict(re.findall(r"\| \[(\d{4})\]\([^)]+\) \| [^|]+ \| ([^|]+) \|", index))
    decisions = sorted((ROOT / "docs/decisions").glob("0*.md"))
    assert {path.name[:4] for path in decisions} == set(rows)
    for path in decisions:
        status = re.search(r"## Status\n\n(.+)", path.read_text(encoding="utf-8")).group(1)
        amended = set()
        for clause in re.split(r"(?<=[.])\s+", status):
            if "Amended by" in clause or "Superseded by" in clause:
                amended |= set(re.findall(r"ADR (\d{4})", clause))
        assert amended == set(re.findall(r"\b(\d{4})\b", rows[path.name[:4]])), path.name


def test_continuity_hook_is_the_only_hook() -> None:
    hooks_dir = PLUGIN / "hooks"
    assert [path.name for path in hooks_dir.iterdir()] == ["hooks.json"]
    payload = json_object("plugins/skiphow/hooks/hooks.json")
    assert set(payload["hooks"]) == {"SessionStart"}
    groups = payload["hooks"]["SessionStart"]
    sources = [source for group in groups for source in group["matcher"].split("|")]
    assert sorted(sources) == ["clear", "compact", "resume", "startup"]
    for group in groups:
        (handler,) = group["hooks"]
        assert handler["type"] == "command"
        assert handler["command"].startswith("sh -c ")
        assert ".skiphow/handoff.md" in handler["command"]
        assert handler.get("timeout", 600) <= 30


def test_package_has_no_versioned_model_ids_or_personal_paths() -> None:
    """Both scans are the release checker's own, over every shipped file.

    A second, narrower regex here meant the suite could stay green on an ID the
    release gate rejects, or on one neither pattern happened to name.
    """
    scanned = 0
    for path in PLUGIN.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        scanned += 1
        assert PERSONAL_PATH.search(text) is None, path
        assert VERSIONED_MODEL.search(text) is None, path
    assert scanned == len(_MODULE.PACKAGE_FILES)
    for identifier in ("claude-fable-5", "fable-5", "gpt-oss-120b", "claude-opus-5", "o3"):
        assert VERSIONED_MODEL.search(identifier), identifier
    for personal in ("/Users/person", "C:\\users\\person\\x", "~/.claude"):
        assert PERSONAL_PATH.search(personal), personal
