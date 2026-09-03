"""Release and site workflow invariants: privilege separation, pinning, same-ref flow.

These are security/release invariants (spec 11.3 class 2), not shape preferences:
untrusted dependency or validator code never runs in a job holding `contents: write`,
every action is pinned to a full commit SHA, the release and the site come from the
same exact tag commit, and the manual repair workflow refuses a moving ref.
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


def test_release_validate_job_holds_only_read_and_runs_all_repository_code() -> None:
    release = workflow("release.yml")
    assert triggers(release) == {"push": {"tags": ["v*"]}}
    jobs = release["jobs"]
    assert set(jobs) == {"validate", "publish-release", "deploy-site"}
    validate = jobs["validate"]
    assert validate["permissions"] == {"contents": "read"}
    assert validate["timeout-minutes"] <= 10
    lines = run_lines(validate)
    assert any("pip install -r requirements-dev.txt" in line for line in lines)
    assert any("scripts/check_hosts.py" in line for line in lines)
    assert "--package-gate" in lines
    assert "--require-codex-validator" in lines
    assert 'test "v$(cat VERSION)" = "${GITHUB_REF_NAME}"' in lines
    assert "git fetch --no-tags origin main" in lines
    assert 'git merge-base --is-ancestor "${GITHUB_SHA}" origin/main' in lines
    checkouts = [step for step in validate["steps"] if step.get("uses", "").startswith("actions/checkout@")]
    own = next(step for step in checkouts if "repository" not in step.get("with", {}))
    assert own["with"]["ref"] == "${{ github.sha }}"
    assert own["with"]["persist-credentials"] is False
    validator = next(step for step in checkouts if step.get("with", {}).get("repository") == "openai/codex")
    assert re.fullmatch(r"[0-9a-f]{40}", validator["with"]["ref"])
    assert validator["with"]["persist-credentials"] is False


def test_release_validate_uploads_notes_and_the_site_of_the_same_commit() -> None:
    validate = workflow("release.yml")["jobs"]["validate"]
    uploads = [step for step in validate["steps"] if step.get("uses", "").startswith("actions/upload-artifact@")]
    names = {step["with"]["name"]: step["with"] for step in uploads}
    assert names["release-notes"]["path"] == "release-notes.md"
    assert names["release-notes"]["if-no-files-found"] == "error"
    assert "release-validation-matrix" in names
    pages = next(step for step in validate["steps"] if step.get("uses", "").startswith("actions/upload-pages-artifact@"))
    assert pages["with"] == {"path": "site"}
    assert any("release-notes.md" in line for line in run_lines(validate))


def test_release_publish_job_runs_no_repository_code_and_only_consumes_the_notes() -> None:
    publish = workflow("release.yml")["jobs"]["publish-release"]
    assert publish["needs"] == "validate"
    assert publish["permissions"] == {"contents": "write"}
    assert publish["timeout-minutes"] <= 10
    assert action_names(publish) == ["actions/download-artifact"]
    download = next(step for step in publish["steps"] if "uses" in step)
    assert download["with"]["name"] == "release-notes"
    lines = run_lines(publish)
    assert not any(token in line for line in lines for token in ("pip ", "python", "scripts/", "npm", "git "))
    assert "test -s release-notes.md" in lines
    assert any(line.startswith("gh release create") for line in lines)
    assert "--verify-tag" in lines
    assert "--notes-file release-notes.md" in lines
    assert publish["steps"][-1]["env"] == {"GH_TOKEN": "${{ github.token }}"}


def test_release_site_deploys_the_validated_artifact_without_building() -> None:
    deploy = workflow("release.yml")["jobs"]["deploy-site"]
    assert "validate" in deploy["needs"] and "publish-release" in deploy["needs"]
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
    assert deploy["timeout-minutes"] <= 10
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["concurrency"] == {"group": "pages", "cancel-in-progress": False}
    assert action_names(deploy) == ["actions/deploy-pages"]
    assert not any("run" in step for step in deploy["steps"])


def test_write_capable_release_jobs_never_check_out_or_install() -> None:
    jobs = workflow("release.yml")["jobs"]
    for name in ("publish-release", "deploy-site"):
        actions = action_names(jobs[name])
        assert "actions/checkout" not in actions, name
        assert "actions/setup-python" not in actions, name
        assert not any("install" in line for line in run_lines(jobs[name])), name


def test_pages_repair_is_manual_and_requires_an_exact_ref() -> None:
    pages = workflow("pages.yml")
    on = triggers(pages)
    assert set(on) == {"workflow_dispatch"}, "no push trigger: a repair never deploys moving content"
    ref = on["workflow_dispatch"]["inputs"]["ref"]
    assert ref["required"] is True
    assert ref["type"] == "string"
    build = pages["jobs"]["build"]
    assert build["permissions"] == {"contents": "read"}
    guard, checkout = build["steps"][0], build["steps"][1]
    assert guard["env"] == {"REQUESTED_REF": "${{ inputs.ref }}"}
    assert "exit 1" in guard["run"]
    assert "[0-9a-f]{40}" in guard["run"]
    assert checkout["uses"].startswith("actions/checkout@")
    assert checkout["with"]["ref"] == "${{ inputs.ref }}"
    assert checkout["with"]["persist-credentials"] is False
    assert not any("pip" in line or "scripts/" in line for line in run_lines(build))
    upload = next(step for step in build["steps"] if step.get("uses", "").startswith("actions/upload-pages-artifact@"))
    assert upload["with"] == {"path": "site"}
    deploy = pages["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
    assert action_names(deploy) == ["actions/deploy-pages"]


def test_ci_keeps_read_only_permissions_and_no_write_capable_job() -> None:
    ci = workflow("ci.yml")
    assert ci["permissions"] == {"contents": "read"}
    for job in ci["jobs"].values():
        assert job.get("permissions", {"contents": "read"}) == {"contents": "read"}


def test_pages_actions_are_shared_between_release_and_repair() -> None:
    """The same pinned upload/deploy pair serves both paths, so one review covers both."""
    release_uses = set(every_uses(workflow("release.yml")))
    pages_uses = set(every_uses(workflow("pages.yml")))
    shared = {item for item in pages_uses if item.split("@")[0] in ("actions/upload-pages-artifact", "actions/deploy-pages", "actions/checkout")}
    assert shared <= release_uses
