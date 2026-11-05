"""Release and site workflow invariants: privilege separation, pinning, exact refs.

These are security and release invariants, not shape preferences: no job holding a
write permission checks out or runs repository or dependency code, every action is
pinned to a full commit SHA, CI stays read-only, and the manual site repair deploys
only an exact ref it was given.
"""

from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
SHA_PIN = re.compile(r"[^@\s]+@[0-9a-f]{40}$")


def workflow(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def triggers(document: dict) -> dict:
    return document.get("on", document.get(True))


def every_uses(node: object) -> list[str]:
    if isinstance(node, dict):
        found = [node["uses"]] if isinstance(node.get("uses"), str) else []
        return found + [item for value in node.values() for item in every_uses(value)]
    if isinstance(node, list):
        return [item for value in node for item in every_uses(value)]
    return []


def run_lines(job: dict) -> list[str]:
    return [
        line.strip().rstrip("\\").strip()
        for step in job["steps"]
        if isinstance(step.get("run"), str)
        for line in step["run"].splitlines()
        if line.strip()
    ]


def action_names(job: dict) -> list[str]:
    return [item.split("@", 1)[0] for item in every_uses(job)]


def test_every_action_in_every_workflow_is_pinned_to_a_full_sha_with_a_version_comment() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        uses = every_uses(document)
        assert uses, path.name
        for item in uses:
            assert SHA_PIN.fullmatch(item), (path.name, item)
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "uses:" in line:
                assert re.search(r"@[0-9a-f]{40} # v\d+", line), (path.name, line)


def test_every_workflow_grants_permissions_per_job_only() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if path.name == "ci.yml":
            continue
        assert document.get("permissions") == {}, path.name
        for name, job in document["jobs"].items():
            assert isinstance(job.get("permissions"), dict) and job["permissions"], (path.name, name)


def test_ci_keeps_read_only_permissions_and_no_write_capable_job() -> None:
    ci = workflow("ci.yml")
    assert ci["permissions"] == {"contents": "read"}
    for job in ci["jobs"].values():
        assert job.get("permissions", {"contents": "read"}) == {"contents": "read"}


def test_no_write_capable_job_checks_out_or_runs_repository_code() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        inherited = document.get("permissions") or {}
        for name, job in document["jobs"].items():
            permissions = job.get("permissions", inherited)
            if not isinstance(permissions, dict) or "write" not in permissions.values():
                continue
            actions = action_names(job)
            assert "actions/checkout" not in actions, (path.name, name)
            assert "actions/setup-python" not in actions, (path.name, name)
            for line in run_lines(job):
                assert not any(token in line for token in ("install", "python", "scripts/")), (
                    path.name,
                    name,
                    line,
                )


def test_pages_repair_is_manual_and_requires_an_exact_ref() -> None:
    pages = workflow("pages.yml")
    on = triggers(pages)
    assert set(on) == {"workflow_dispatch"}, "no push trigger: a repair never deploys moving content"
    assert on["workflow_dispatch"]["inputs"]["ref"]["required"] is True
    guard, checkout = pages["jobs"]["build"]["steps"][:2]
    assert "[0-9a-f]{40}" in guard["run"] and "exit 1" in guard["run"]
    assert checkout["with"]["ref"] == "${{ inputs.ref }}"


def test_a_release_tag_must_match_version_and_sit_on_main() -> None:
    lines = run_lines(workflow("release.yml")["jobs"]["validate"])
    assert 'test "v$(cat VERSION)" = "${GITHUB_REF_NAME}"' in lines
    assert 'git merge-base --is-ancestor "${GITHUB_SHA}" origin/main' in lines
