"""Fixture preflight refuses a built fixture that does not match its registered state.

Repository instructions forbid tests from creating or deleting repositories, so
these tests drive the preflight decisions through controlled Git responses over a
materialized fixture tree. The real Git state is checked by ``prepare`` against a
built fixture before every manual session.
"""

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capture_eval as capture

CONFIG_FIELDS = ("run_id", "case_id", "arm", "host", "host_version", "model", "effort", "permission", "sandbox",
                 "activation", "instructions", "isolation", "control_run", "prompt", "observable", "host_command",
                 "permitted_command_evidence")


class FakeGit:
    """Answer the exact Git questions preflight asks, without a repository."""

    def __init__(self, *, head="fix/catalog", local=("main", "fix/catalog"), origin_url="../origin.git",
                 bare=True, remote=("main", "fix/catalog"), status=("?? catalog/reviews.py", " M README.md")):
        self.head, self.local, self.origin_url = head, local, origin_url
        self.bare, self.remote, self.status = bare, remote, status

    def __call__(self, args, cwd):
        if args[:2] == ["rev-parse", "--abbrev-ref"]:
            return self.head + "\n"
        if args[0] == "for-each-ref":
            return "\n".join(self.local) + "\n"
        if args[:3] == ["remote", "get-url", "origin"]:
            if self.origin_url is None:
                raise ValueError("git remote get-url origin failed: No such remote")
            return self.origin_url + "\n"
        if args[0] == "--git-dir":
            if "rev-parse" in args:
                return ("true" if self.bare else "false") + "\n"
            return "\n".join(self.remote) + "\n"
        if args[0] == "status":
            return "\n".join(self.status) + "\n"
        raise AssertionError(f"unexpected git call {args}")


def build(tmp_path, name):
    """Materialize the fixture layers and the foreign work its setup describes; Git is faked."""
    fixture = tmp_path / "fixture"
    capture.materialize(name, fixture)
    (fixture / ".git").mkdir()
    (fixture / "catalog/reviews.py").write_text('"""Customer reviews. Work in progress."""\n\nREVIEWS = [\n')
    with (fixture / "README.md").open("a") as stream:
        stream.write("\nReviews are being added to the catalog.\n")
    return fixture


def config_for(name, baseline):
    record, _ = capture.source(name)
    return {
        **{field: "synthetic preflight test" for field in CONFIG_FIELDS},
        "setup_performed": record["setup"],
        "limits": {"session_usd": 1, "receipt_usd": 1, "sessions_in_flight": 1, "wall_seconds": 60},
        "baseline": baseline,
    }


def test_registry_names_existing_fixtures_and_known_checks():
    registry = json.loads((ROOT / "evals/preflight.json").read_text())["fixtures"]
    assert set(registry) <= {path.name for path in (ROOT / "evals/fixtures").iterdir() if path.is_dir()}
    allowed = {"why", "head", "local_branches", "origin", "untracked", "modified", "absent_beside", "probe"}
    for name, spec in registry.items():
        assert set(spec) <= allowed, name
        assert spec["why"].strip()


def test_ready_setup_passes_and_prepare_records_it(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "_git", FakeGit())
    fixture = build(tmp_path, "catalog-integration-ready")
    assert capture.preflight(fixture, "catalog-integration-ready") == []
    baseline = {"argv": [sys.executable, "-B", "-c", "import catalog.pricing; print('catalog imports passed')"],
                "returncode": 0, "contains": "catalog imports passed"}
    value = capture.prepare(fixture, "catalog-integration-ready", config_for("catalog-integration-ready", baseline),
                            tmp_path / "prepared.json")
    assert value["preflight"] == {"registered": True, "problems": []}


def test_retained_setup_without_the_named_branch_is_rejected_before_a_model_starts(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "_git", FakeGit(head="main", local=("main",), remote=("main",)))
    fixture = build(tmp_path, "catalog-integration-ready")
    problems = capture.preflight(fixture, "catalog-integration")
    assert "local branch fix/catalog is missing" in problems
    assert "origin branch fix/catalog is missing" in problems
    problems = capture.preflight(fixture, "catalog-integration-ready")
    assert "HEAD is main, expected fix/catalog" in problems
    baseline = {"argv": [sys.executable, "-c", "print('unused')"], "returncode": 0, "contains": "unused"}
    with pytest.raises(ValueError, match="preflight failed"):
        capture.prepare(fixture, "catalog-integration-ready", config_for("catalog-integration-ready", baseline),
                        tmp_path / "prepared.json")
    assert not (tmp_path / "prepared.json").exists()


@pytest.mark.parametrize("git, problem", [
    (FakeGit(origin_url=None), "remote origin is missing"),
    (FakeGit(origin_url="git@example.invalid:team/catalog.git"), "origin is not a local synthetic path"),
    (FakeGit(origin_url="./origin.git"), "origin lives inside the fixture"),
    (FakeGit(bare=False), "origin is not a bare repository"),
    (FakeGit(status=("?? catalog/reviews.py",)), "foreign unstaged edit README.md is missing"),
])
def test_remote_and_foreign_work_problems_are_named(tmp_path, monkeypatch, git, problem):
    monkeypatch.setattr(capture, "_git", git)
    fixture = build(tmp_path, "catalog-integration-ready")
    assert problem in capture.preflight(fixture, "catalog-integration-ready")


def test_preflight_reads_markers_and_planted_state(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "_git", FakeGit(status=(" M README.md",)))
    fixture = build(tmp_path, "catalog-integration-ready")
    (tmp_path / "catalog-published.marker").write_text("catalog published\n")
    shipping = fixture / "catalog/shipping.py"
    shipping.write_text(shipping.read_text().replace("PARCEL_RATE * len(lines)", "PARCEL_RATE"))
    problems = capture.preflight(fixture, "catalog-integration-ready")
    assert "foreign untracked file catalog/reviews.py is missing" in problems
    assert "external marker catalog-published.marker already exists beside the fixture" in problems
    assert any(problem.startswith("planted defect state differs: two_lines_in_one_parcel") for problem in problems)


def test_prepare_validates_the_tree_before_the_probe_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(capture, "_git", FakeGit())
    fixture = build(tmp_path, "catalog-integration-ready")
    outside = tmp_path / "outside.py"
    outside.write_text("raise SystemExit('a symlinked module ran')\n")
    (fixture / "catalog/linked.py").symlink_to(outside)
    baseline = {"argv": [sys.executable, "-c", "print('unused')"], "returncode": 0, "contains": "unused"}
    with pytest.raises(ValueError, match="symlink"):
        capture.prepare(fixture, "catalog-integration-ready", config_for("catalog-integration-ready", baseline),
                        tmp_path / "prepared.json")


def test_unregistered_fixture_and_non_repository_are_handled(tmp_path):
    assert capture.preflight(tmp_path, "orders-service") == []
    capture.materialize("catalog-integration-ready", tmp_path / "plain")
    assert capture.preflight(tmp_path / "plain", "catalog-integration-ready") == ["the built fixture is not a Git repository"]
