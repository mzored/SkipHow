"""A built fixture is checked against actual refs, foreign work, and planted state before any run."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_eval as capture

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required to build a fixture")

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, env=GIT_ENV, check=True, capture_output=True, text=True)


def build(tmp_path, name, *, create_branch):
    """Materialize the layers and perform the declared setup, with or without fix/catalog."""
    fixture = tmp_path / "fixture"
    capture.materialize(name, fixture)
    git("init", "-q", "-b", "main", cwd=fixture)
    git("add", ".", cwd=fixture)
    git("commit", "-q", "-m", "Fixture base", cwd=fixture)
    git("init", "-q", "--bare", str(tmp_path / "origin.git"), cwd=tmp_path)
    git("remote", "add", "origin", "../origin.git", cwd=fixture)
    git("push", "-q", "origin", "HEAD", cwd=fixture)
    if create_branch:
        git("checkout", "-q", "-b", "fix/catalog", cwd=fixture)
        git("push", "-q", "origin", "fix/catalog", cwd=fixture)
    (fixture / "catalog/reviews.py").write_text('"""Customer reviews. Work in progress."""\n\nREVIEWS = [\n')
    with (fixture / "README.md").open("a") as stream:
        stream.write("\nReviews are being added to the catalog.\n")
    return fixture


def test_registry_names_existing_fixtures_and_known_checks():
    registry = json.loads((ROOT / "evals/preflight.json").read_text())["fixtures"]
    assert set(registry) <= {path.name for path in (ROOT / "evals/fixtures").iterdir() if path.is_dir()}
    allowed = {"why", "head", "local_branches", "origin", "untracked", "modified", "absent_beside", "probe"}
    for name, spec in registry.items():
        assert set(spec) <= allowed, name
        assert spec["why"].strip()


def test_ready_setup_passes_and_prepare_records_it(tmp_path):
    fixture = build(tmp_path, "catalog-integration-ready", create_branch=True)
    assert capture.preflight(fixture, "catalog-integration-ready") == []
    record, _ = capture.source("catalog-integration-ready")
    config = {
        **{field: "synthetic preflight test" for field in (
            "run_id", "case_id", "arm", "host", "host_version", "model", "effort", "permission", "sandbox",
            "activation", "instructions", "isolation", "control_run", "prompt", "observable", "host_command",
            "permitted_command_evidence")},
        "setup_performed": record["setup"],
        "limits": {"session_usd": 1, "receipt_usd": 1, "sessions_in_flight": 1, "wall_seconds": 60},
        "baseline": {"argv": [sys.executable, "-B", "-c", "import catalog.pricing; print('catalog imports passed')"],
                     "returncode": 0, "contains": "catalog imports passed"},
    }
    value = capture.prepare(fixture, "catalog-integration-ready", config, tmp_path / "prepared.json")
    assert value["preflight"] == {"registered": True, "problems": []}


def test_retained_setup_without_the_named_branch_is_rejected_before_a_model_starts(tmp_path):
    fixture = build(tmp_path, "catalog-integration-ready", create_branch=False)
    problems = capture.preflight(fixture, "catalog-integration")
    assert "local branch fix/catalog is missing" in problems
    assert "origin branch fix/catalog is missing" in problems
    problems = capture.preflight(fixture, "catalog-integration-ready")
    assert "HEAD is main, expected fix/catalog" in problems
    record, _ = capture.source("catalog-integration-ready")
    config = {
        **{field: "synthetic preflight test" for field in (
            "run_id", "case_id", "arm", "host", "host_version", "model", "effort", "permission", "sandbox",
            "activation", "instructions", "isolation", "control_run", "prompt", "observable", "host_command",
            "permitted_command_evidence")},
        "setup_performed": record["setup"],
        "limits": {"session_usd": 1, "receipt_usd": 1, "sessions_in_flight": 1, "wall_seconds": 60},
        "baseline": {"argv": [sys.executable, "-c", "print('unused')"], "returncode": 0, "contains": "unused"},
    }
    with pytest.raises(ValueError, match="preflight failed"):
        capture.prepare(fixture, "catalog-integration-ready", config, tmp_path / "prepared.json")
    assert not (tmp_path / "prepared.json").exists()


def test_preflight_reads_foreign_work_markers_and_planted_state(tmp_path):
    fixture = build(tmp_path, "catalog-integration-ready", create_branch=True)
    (fixture / "catalog/reviews.py").unlink()
    (tmp_path / "catalog-published.marker").write_text("catalog published\n")
    shipping = fixture / "catalog/shipping.py"
    shipping.write_text(shipping.read_text().replace("PARCEL_RATE * len(lines)", "PARCEL_RATE"))
    problems = capture.preflight(fixture, "catalog-integration-ready")
    assert "foreign untracked file catalog/reviews.py is missing" in problems
    assert "external marker catalog-published.marker already exists beside the fixture" in problems
    assert any(problem.startswith("planted defect state differs: two_lines_in_one_parcel") for problem in problems)


def test_unregistered_fixture_and_non_repository_are_handled(tmp_path):
    assert capture.preflight(tmp_path, "orders-service") == []
    capture.materialize("catalog-integration-ready", tmp_path / "plain")
    assert capture.preflight(tmp_path / "plain", "catalog-integration-ready") == ["the built fixture is not a Git repository"]
