"""Local contracts for the opt-in suite. These tests never start a host."""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


schema = load("skiphow_live_schema", "evals/live/schema.py")
sys.modules["schema"] = schema
collectors = load("skiphow_live_collectors", "evals/live/collectors.py")
sys.modules["collectors"] = collectors
hosts = load("skiphow_live_hosts", "evals/live/hosts.py")
sys.modules["hosts"] = hosts
run = load("skiphow_live_run", "evals/live/run.py")


def test_manifest_is_complete_and_references_only_versioned_files() -> None:
    suite = schema.load_suite(ROOT / "evals/live/suite.json")
    assert {item["id"] for item in suite["scenarios"]} == schema.APPROVED_SCENARIOS
    for scenario in suite["scenarios"]:
        assert set(scenario["collectors"]) <= schema.SUPPORTED_COLLECTORS
        assert scenario["execution"] in {"single", "restart", "paired", "github"}
        assert isinstance(scenario["explicit_skill"], bool)
        for field in ("prompt", "fixture", "oracle"):
            assert (ROOT / "evals/live" / scenario[field]).exists()


def test_run_is_opt_in_and_keeps_roots_outside_candidate(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    scenarios = [{"id": "small-fix"}]
    blocked = SimpleNamespace(confirm_live=False, total_budget_usd="1", per_invocation_budget_usd="1", model="model", effort="high", host="claude", accept_advisory_codex_budget=False, credential_env=None, candidate=str(candidate), work_root=str(tmp_path / "work"), receipt_root=str(tmp_path / "receipts"))
    with pytest.raises(run.GateError, match="confirm-live"):
        run.gate(blocked, scenarios)
    assert run._outside(candidate, tmp_path / "work", "work root") == (tmp_path / "work").resolve()
    with pytest.raises(run.GateError, match="outside"):
        run._outside(candidate, candidate / "receipts", "receipt root")
    with pytest.raises(run.GateError, match="outside"):
        run._outside(candidate, tmp_path, "receipt root")
    with pytest.raises(run.GateError, match="canonical"):
        run.run_live(SimpleNamespace(suite=str(tmp_path / "custom-suite.json")))
    with pytest.raises(run.GateError, match="candidate checkout"):
        run.run_live(SimpleNamespace(suite=str(run.DEFAULT_SUITE), candidate=str(candidate)))


def test_budget_and_credential_gates_are_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    base = dict(confirm_live=True, total_budget_usd="1.00", per_invocation_budget_usd="1.01", model="model", effort="high", host="codex", accept_advisory_codex_budget=False, credential_env=None, candidate=str(candidate), work_root=str(tmp_path / "work"), receipt_root=str(tmp_path / "receipts"))
    with pytest.raises(run.GateError, match="total budget"):
        run.gate(SimpleNamespace(**base), [{"id": "small-fix"}])
    base.update(total_budget_usd="2", per_invocation_budget_usd="1", accept_advisory_codex_budget=True)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(run.GateError, match="unset or empty"):
        run.gate(SimpleNamespace(**base), [{"id": "small-fix"}])
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    (tmp_path / "work").mkdir()
    (tmp_path / "receipts").mkdir()
    (tmp_path / "work").chmod(0o755)
    assert run.gate(SimpleNamespace(**base), [{"id": "small-fix"}])[1:3] == (run.Decimal("2"), run.Decimal("1"))
    assert (tmp_path / "work").stat().st_mode & 0o777 == 0o755


def test_codex_oauth_gate_uses_call_count_without_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (tmp_path / "work").mkdir()
    (tmp_path / "receipts").mkdir()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    args = SimpleNamespace(
        confirm_live=True,
        total_budget_usd=None,
        per_invocation_budget_usd=None,
        model="model",
        effort="low",
        host="codex",
        codex_oauth=True,
        max_calls=1,
        accept_advisory_codex_budget=False,
        credential_env=None,
        candidate=str(candidate),
        work_root=str(tmp_path / "work"),
        receipt_root=str(tmp_path / "receipts"),
    )
    assert run.gate(args, [{"id": "small-fix"}])[1:] == (None, None, [])
    args.max_calls = 0
    with pytest.raises(run.GateError, match="max-calls"):
        run.gate(args, [{"id": "small-fix"}])


def test_candidate_proof_hash_is_sorted_and_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = tmp_path / "candidate"
    plugin = candidate / "plugins/skiphow"
    (plugin / ".codex-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin").mkdir()
    (plugin / "skills").mkdir()
    evaluation = candidate / "evals/live"
    evaluation.mkdir(parents=True)
    (evaluation / "suite.json").write_text('{"schema_version":1}', encoding="utf-8")
    (candidate / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    for path in (plugin / ".codex-plugin/plugin.json", plugin / ".claude-plugin/plugin.json"):
        path.write_text('{"version":"1.2.3"}', encoding="utf-8")
    (plugin / "skills/z.txt").write_text("z", encoding="utf-8")
    (plugin / "skills/a.txt").write_text("a", encoding="utf-8")
    tracked = "\n".join(path.relative_to(candidate).as_posix() for path in sorted(plugin.rglob("*")) if path.is_file())
    evaluation_tracked = "evals/live/suite.json"
    def command(arguments, cwd):
        if arguments[0] == "status":
            return ""
        if arguments[0] == "ls-files":
            if "--error-unmatch" in arguments:
                return "VERSION"
            if "--others" in arguments:
                return ""
            return evaluation_tracked if arguments[-1] == "evals/live" else tracked
        if arguments[0] == "hash-object":
            return "blob"
        if arguments[0] == "rev-parse" and str(arguments[1]).startswith("HEAD:"):
            return "blob"
        return "tree" if arguments[1] == "HEAD^{tree}" else "head"

    monkeypatch.setattr(run, "_command", command)
    first, second = run.candidate_proof(candidate), run.candidate_proof(candidate)
    assert first == second
    assert [item["path"] for item in first["plugin_files"]] == sorted(item["path"] for item in first["plugin_files"])
    (plugin / "ignored.tmp").write_text("ignored", encoding="utf-8")
    with pytest.raises(run.GateError, match="tracked files only"):
        run.candidate_proof(candidate)


def test_candidate_proof_rejects_a_worktree_blob_that_differs_from_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = tmp_path / "candidate"
    plugin = candidate / "plugins/skiphow"
    (plugin / ".codex-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin").mkdir()
    evaluation = candidate / "evals/live"
    evaluation.mkdir(parents=True)
    (evaluation / "suite.json").write_text('{"schema_version":1}', encoding="utf-8")
    (candidate / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    for path in (plugin / ".codex-plugin/plugin.json", plugin / ".claude-plugin/plugin.json"):
        path.write_text('{"version":"1.2.3"}', encoding="utf-8")
    tracked = "\n".join(path.relative_to(candidate).as_posix() for path in sorted(plugin.rglob("*")) if path.is_file())

    def command(arguments, cwd):
        if arguments[0] == "status":
            return ""
        if arguments[0] == "ls-files":
            if "--error-unmatch" in arguments:
                return "VERSION"
            if "--others" in arguments:
                return ""
            return "evals/live/suite.json" if arguments[-1] == "evals/live" else tracked
        if arguments[0] == "hash-object":
            return "changed"
        if arguments[0] == "rev-parse" and str(arguments[1]).startswith("HEAD:"):
            return "committed"
        return "tree" if arguments[1] == "HEAD^{tree}" else "head"

    monkeypatch.setattr(run, "_command", command)
    with pytest.raises(run.GateError, match="does not match HEAD"):
        run.candidate_proof(candidate)


def test_collectors_read_plain_data_and_mark_model_text_unverified(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "old.txt").write_text("before", encoding="utf-8")
    before = collectors.file_inventory(workspace)
    (workspace / "old.txt").write_text("after", encoding="utf-8")
    (workspace / "new.txt").write_text("new", encoding="utf-8")
    delta = collectors.tree_delta(before, workspace)
    assert delta["added"] == ["new.txt"]
    assert delta["modified"] == ["old.txt"]
    inbox = workspace / "inbox.md"
    original = "## seed-1\n- Recorded: 2026-08-25T12:00:00Z\n- Source: owner\n- Original: old request\n- Normalized: old request\n- Disposition: NEW\n- Links: None\n- Evidence: note\n- Open questions: none\n"
    inbox.write_text(original + "## finding-2\n- Recorded: 2026-08-25T12:01:00Z\n- Source: test\n- Original JSON: \"new finding\\nwith context\"\n- Normalized: save it\n- Disposition: NEEDS_RESEARCH\n- Links: None\n- Evidence: log\n- Assumptions: None\n- Open questions: owner\n", encoding="utf-8")
    assert collectors.structured_file(inbox, kind="append_only_inbox", before=original, expected_count=2)["status"] == "PASSED"
    evidence = collectors.structured_file(inbox, kind="append_only_inbox", before=original, expected_count=2)
    assert "added_records" not in evidence
    linked = collectors.structured_file(
        inbox,
        kind="append_only_inbox",
        before=original,
        expected_count=2,
        relationships=[{"source": {"Disposition": "NEEDS_RESEARCH"}, "target": {"id": "seed-1"}}],
    )
    assert linked["status"] == "FAILED"
    assert collectors.host_event([{"type": "final", "text": "trust me"}], event_type="final")["status"] == "UNVERIFIED"
    assert collectors.host_event([], event_type="host_process")["status"] == "UNVERIFIED"
    snapshot = tmp_path / "github.json"
    snapshot.write_text('{"name":"sandbox"}', encoding="utf-8")
    assert collectors.github_state(snapshot)["status"] == "UNVERIFIED"
    assert collectors.github_state(snapshot, expected={"name": "sandbox"})["status"] == "PASSED"
    value_file = workspace / "value.json"
    value_file.write_text('{"credential":"fixture-secret"}', encoding="utf-8")
    assert "value" not in collectors.structured_file(value_file, kind="json", expected={"credential": "fixture-secret"})


def test_file_inventory_observes_modes_directories_and_rejects_special_entries(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "target.txt"
    target.write_text("protected", encoding="utf-8")
    before = collectors.file_inventory(workspace)
    target.chmod(0o700)
    (workspace / "unexpected-empty").mkdir()
    delta = collectors.tree_delta(before, workspace)
    assert delta["modified"] == ["target.txt"]
    assert delta["added"] == ["unexpected-empty"]
    fifo = workspace / "unexpected-fifo"
    if hasattr(os, "mkfifo"):
        os.mkfifo(fifo)
        with pytest.raises(ValueError, match="special entries"):
            collectors.file_inventory(workspace)


def test_status_precedence_and_secrets_never_reach_receipts(tmp_path: Path) -> None:
    assert schema.aggregate_status(["PASSED", "UNVERIFIED", "BLOCKED", "FAILED"]) is schema.Status.FAILED
    target = tmp_path / "receipt.json"
    secret = "do-not-persist"
    run._write_receipt(target, {"assertions": [{"nested": secret}]}, [secret])
    assert secret not in target.read_text(encoding="utf-8")


def test_host_call_detail_stays_redacted_in_trial_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    credential = "provider-secret"
    monkeypatch.setenv("ANTHROPIC_API_KEY", credential)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    call_root = tmp_path / "private-host-1"
    candidate = call_root / "private-candidate"
    receipt_root = tmp_path / "receipts"

    def reject_candidate(*args: object, **kwargs: object) -> dict[str, object]:
        raise run.hosts.HostError(f"rejected {candidate} with {credential}")

    monkeypatch.setattr(run.hosts, "install_candidate", reject_candidate)
    call = run._host_call(
        SimpleNamespace(
            host="claude",
            credential_env=None,
            codex_marketplace_source=None,
            model="model",
            effort="high",
        ),
        candidate=candidate,
        proof={"version": "0.9.0"},
        workspace=workspace,
        prompt="test",
        call_root=call_root,
        receipt_root=receipt_root / "calls/1",
        explicit_skill=True,
        network=False,
        per_call_budget=run.Decimal("1"),
        budget={"total": run.Decimal("1"), "observed_spend": run.Decimal("0")},
        secrets=[credential],
    )
    assert call["status"] == "BLOCKED"
    assert str(candidate) not in call["detail"]
    run._finish_trial(
        scenario={"id": "redaction-regression"},
        trial_index=1,
        arm="test",
        workspace=workspace,
        receipt_root=receipt_root,
        oracle={"assertions": [{"id": "blocked", "collector": "tree_delta"}]},
        before={},
        structured_before={},
        calls=[call],
        started=run.time.time(),
        secrets=[credential],
    )
    persisted = (receipt_root / "receipt.json").read_text(encoding="utf-8")
    assert str(call_root) not in persisted
    assert str(candidate) not in persisted
    assert credential not in persisted
    assert "[REDACTED]" in persisted


def test_tree_constraints_and_fixture_inbox_baseline_are_exact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    before = collectors.file_inventory(workspace)
    (workspace / "unexpected.txt").write_text("x", encoding="utf-8")
    evidence = run._run_assertions({"assertions": [{"collector": "tree_delta", "allowed_added": ["result.txt"]}]}, workspace, before, {}, [], tmp_path)
    assert evidence[0]["status"] == "FAILED"
    (workspace / "unexpected.txt").unlink()
    (workspace / "result.txt").write_text("wrong", encoding="utf-8")
    evidence = run._run_assertions(
        {"assertions": [{"collector": "tree_delta", "required_added": ["result.txt"], "allowed_added": ["result.txt"], "allowed_removed": [], "allowed_modified": [], "expected_text": {"result.txt": "right"}}]},
        workspace,
        before,
        {},
        [],
        tmp_path,
    )
    assert evidence[0]["status"] == "FAILED"
    fixture = ROOT / "evals/live/fixtures/mixed-intake/.skiphow/inbox.md"
    baseline = fixture.read_text(encoding="utf-8")
    inbox = tmp_path / "inbox.md"
    inbox.write_text(baseline, encoding="utf-8")
    assert collectors.structured_file(inbox, kind="append_only_inbox", before=baseline, expected_count=1)["status"] == "PASSED"


def test_collectors_and_runner_have_no_command_escape_or_repository_lifecycle() -> None:
    collector_source = inspect.getsource(collectors)
    runner_source = inspect.getsource(run) + inspect.getsource(hosts)
    assert "shell=True" not in collector_source
    assert "os.system" not in collector_source
    assert "git init" not in runner_source
    assert "git clone" not in runner_source
    assert "repo create" not in runner_source
    assert "repo delete" not in runner_source
    assert "CODEX_API_KEY" not in runner_source + collector_source + inspect.getsource(hosts)
    assert "--skip-git-repo-check" in inspect.getsource(hosts.invoke)
    assert '"--sandbox", "workspace-write"' in inspect.getsource(hosts.invoke)
    assert '"--max-budget-usd"' in inspect.getsource(hosts.invoke)
    assert '"--bare"' in inspect.getsource(hosts.invoke)
    assert '"allowUnsandboxedCommands": False' in inspect.getsource(hosts.invoke)
    assert '"failIfUnavailable": True' in inspect.getsource(hosts.invoke)


def test_claude_live_settings_require_the_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config"
    workspace = tmp_path / "workspace"
    config.mkdir()
    workspace.mkdir()
    monkeypatch.setattr(hosts, "executable", lambda host: "claude")
    monkeypatch.setattr(hosts, "_run", lambda command, **kwargs: (0, "", ""))
    hosts.invoke(
        "claude",
        workspace,
        "test",
        "model",
        "high",
        "1",
        {"CLAUDE_CONFIG_DIR": str(config)},
        candidate=tmp_path / "candidate",
        explicit_skill=True,
        network=False,
    )
    settings = json.loads((config / "live-settings.json").read_text(encoding="utf-8"))
    assert settings["sandbox"] == {
        "allowUnsandboxedCommands": False,
        "enabled": True,
        "failIfUnavailable": True,
        "network": {"allowedDomains": []},
    }


def test_host_environment_is_minimal_and_inventory_is_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("OPENAI_API_KEY", "ambient-provider")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "must-not-pass")
    _, environment = hosts.fresh_config("codex", tmp_path / "host", credential="selected-provider", github_token="selected-github")
    assert environment["OPENAI_API_KEY"] == "selected-provider"
    assert environment["GH_TOKEN"] == "selected-github"
    assert "AWS_SECRET_ACCESS_KEY" not in environment
    codex = {"installed": [{"pluginId": "skiphow@skiphow", "version": "0.9.0", "enabled": True, "installed": True, "source": {"path": "/plain/plugin"}}]}
    claude = [{"id": "skiphow@skiphow", "version": "0.9.0", "enabled": True, "installPath": "/plain/plugin"}]
    assert hosts._installed_skiphow("codex", json.dumps(codex))["version"] == "0.9.0"
    assert hosts._installed_skiphow("claude", json.dumps(claude))["enabled"] is True
    with pytest.raises(ValueError, match="expected one"):
        hosts._installed_skiphow("claude", json.dumps(claude * 2))


def test_codex_oauth_environment_reuses_auth_without_api_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-pass")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "must-not-pass")
    config, environment = hosts.fresh_config("codex", tmp_path / "host", credential=None, codex_oauth=True)
    assert config == codex_home
    assert environment["CODEX_HOME"] == str(codex_home)
    assert "OPENAI_API_KEY" not in environment
    assert "AWS_SECRET_ACCESS_KEY" not in environment


def test_codex_oauth_install_requires_exact_enabled_cached_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = tmp_path / "candidate"
    installed = tmp_path / "installed"
    shutil.copytree(ROOT / "plugins/skiphow", candidate / "plugins/skiphow")
    shutil.copytree(ROOT / "plugins/skiphow", installed)
    inventory = {
        "installed": [
            {
                "pluginId": "skiphow@skiphow",
                "version": "0.9.0",
                "enabled": True,
                "installed": True,
                "source": {"path": str(installed)},
            }
        ]
    }
    monkeypatch.setattr(hosts, "executable", lambda host: "codex")
    monkeypatch.setattr(hosts, "require_codex_chatgpt_oauth", lambda environment: None)
    monkeypatch.setattr(hosts, "_run", lambda command, **kwargs: (0, json.dumps(inventory), ""))
    result = hosts.install_candidate(
        "codex",
        candidate,
        {"CODEX_HOME": str(tmp_path / "codex-home")},
        version="0.9.0",
        codex_oauth=True,
    )
    assert result["auth_mode"] == "chatgpt-oauth"
    assert result["load_mode"] == "existing-codex-profile"
    (installed / "LICENSE").write_text("changed", encoding="utf-8")
    with pytest.raises(hosts.HostError, match="payload does not match"):
        hosts.install_candidate(
            "codex",
            candidate,
            {"CODEX_HOME": str(tmp_path / "codex-home")},
            version="0.9.0",
            codex_oauth=True,
        )


def test_codex_live_source_is_plain_external_and_byte_exact(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    source = tmp_path / "source"
    (candidate / ".agents/plugins").mkdir(parents=True)
    (source / ".agents/plugins").mkdir(parents=True)
    shutil.copytree(ROOT / "plugins/skiphow", candidate / "plugins/skiphow")
    shutil.copytree(ROOT / "plugins/skiphow", source / "plugins/skiphow")
    manifest = (ROOT / ".agents/plugins/marketplace.json").read_bytes()
    (candidate / ".agents/plugins/marketplace.json").write_bytes(manifest)
    (source / ".agents/plugins/marketplace.json").write_bytes(manifest)
    assert hosts.verify_codex_plain_source(candidate, str(source))[0] == source.resolve()
    (source / "plugins/skiphow/LICENSE").write_text("changed", encoding="utf-8")
    with pytest.raises(hosts.HostError, match="does not match"):
        hosts.verify_codex_plain_source(candidate, str(source))
    with pytest.raises(hosts.HostError, match="plain local snapshot"):
        hosts.verify_codex_plain_source(candidate, "https://example.invalid/repository.git")


def test_traversal_symlinks_and_invalid_usage_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(run.GateError, match="escapes"):
        run._contained(root, "../secret", "test path")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "link"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="symlinks"):
        collectors.plain_directory(root)
    invalid = collectors.provider_usage([{"type": "turn.completed", "usage": {"total_tokens": -1, "cost_usd": "NaN"}}])
    assert invalid["status"] == "UNVERIFIED"
    assert invalid["cost_status"] == "UNVERIFIED"
    assert collectors.git_state(ROOT / "evals/live/fixtures/small-fix")["status"] == "UNVERIFIED"


def test_github_installation_is_single_repository_and_write_limited() -> None:
    installation = {
        "repository_selection": "selected",
        "permissions": {"contents": "write", "issues": "write", "pull_requests": "write", "metadata": "read"},
    }
    repository = {"id": 42, "full_name": "owner/sandbox"}
    assert run._validate_github_installation(installation, {"total_count": 1, "repositories": [repository]}, repository="owner/sandbox", repository_id=42)["contents"] == "write"
    with pytest.raises(run.GateError, match="exactly one"):
        run._validate_github_installation(installation, {"total_count": 2, "repositories": [repository, {"id": 43, "full_name": "owner/other"}]}, repository="owner/sandbox", repository_id=42)
    excessive = {**installation, "permissions": {**installation["permissions"], "workflows": "write"}}
    with pytest.raises(run.GateError, match="exactly contents"):
        run._validate_github_installation(excessive, {"total_count": 1, "repositories": [repository]}, repository="owner/sandbox", repository_id=42)


def test_github_snapshot_grades_exact_head_merge_checks_and_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = {"operation": "skiphow-eval:one", "issues": [1, 2], "required_checks": ["test"], "branch_prefix": "skiphow-eval-"}

    def fake_read(endpoint, **kwargs):
        if endpoint == "/repos/owner/sandbox":
            return {"id": 42}
        if "/issues/" in endpoint:
            number = int(endpoint.rsplit("/", 1)[1])
            return {"number": number, "state": "closed", "body": "skiphow-eval:one"}
        if "pulls?" in endpoint:
            return [{"number": 9, "body": "skiphow-eval:one", "head": {"ref": "skiphow-eval-work"}}]
        if endpoint.endswith("/pulls/9"):
            return {"number": 9, "body": "skiphow-eval:one\nCloses #1\nCloses #2", "merged_at": "2026-08-25T12:00:00Z", "head": {"ref": "skiphow-eval-work", "sha": "abc", "repo": {"full_name": "owner/sandbox"}}}
        if endpoint.endswith("/commits/abc/check-runs?per_page=100"):
            return {"total_count": 1, "check_runs": [{"name": "test", "conclusion": "success", "head_sha": "abc"}]}
        if endpoint.endswith("/branches?per_page=100"):
            return [{"name": "main"}]
        if "/branches/" in endpoint:
            return None
        raise AssertionError(endpoint)

    monkeypatch.setattr(run, "_gh_json", fake_read)
    destination = tmp_path / "snapshot.json"
    run._fetch_github_snapshot(tmp_path, "owner/sandbox", "token", marker, destination)
    expected = {
        "repository_id": 42,
        "issue_count": 2,
        "all_selected_are_issues": True,
        "all_issues_closed": True,
        "pull_request_count_at_least": 1,
        "all_pull_requests_merged": True,
        "all_closing_links_present": True,
        "all_required_checks_passed": True,
        "all_head_repositories_match": True,
        "all_owned_branches_deleted": True,
        "operation_marker_present": True,
    }
    assert collectors.github_state(destination, expected=expected)["status"] == "PASSED"

    def orphaned_branch(endpoint, **kwargs):
        value = fake_read(endpoint, **kwargs)
        if endpoint.endswith("/branches?per_page=100"):
            return [{"name": "main"}, {"name": "skiphow-eval-orphan"}]
        return value

    monkeypatch.setattr(run, "_gh_json", orphaned_branch)
    run._fetch_github_snapshot(tmp_path, "owner/sandbox", "token", marker, destination)
    assert collectors.github_state(destination, expected=expected)["status"] == "FAILED"

    def duplicate_failed_check(endpoint, **kwargs):
        value = fake_read(endpoint, **kwargs)
        if endpoint.endswith("/commits/abc/check-runs?per_page=100"):
            return {"total_count": 2, "check_runs": [
                {"name": "test", "conclusion": "success", "head_sha": "abc"},
                {"name": "test", "conclusion": "failure", "head_sha": "abc"},
            ]}
        return value

    monkeypatch.setattr(run, "_gh_json", duplicate_failed_check)
    run._fetch_github_snapshot(tmp_path, "owner/sandbox", "token", marker, destination)
    assert collectors.github_state(destination, expected=expected)["status"] == "FAILED"


def test_protected_action_preserves_the_reachable_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "request.txt").write_text("protected", encoding="utf-8")
    (workspace / "protected-release.json").write_text('{"deployed":false}', encoding="utf-8")
    before = collectors.file_inventory(workspace)
    (workspace / "protected-release.json").write_text('{"deployed":true}', encoding="utf-8")
    (workspace / "decision.json").write_text('{"disposition":"BLOCKED","reason":"production approval required","target":"protected-release.json"}', encoding="utf-8")
    oracle = json.loads((ROOT / "evals/live/oracles/protected-action.json").read_text(encoding="utf-8"))
    evidence = run._run_assertions(oracle, workspace, before, {}, [], tmp_path)
    assert evidence[0]["status"] == "FAILED"


def test_restart_uses_two_fresh_calls_and_external_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scenario = next(item for item in schema.load_suite(ROOT / "evals/live/suite.json")["scenarios"] if item["execution"] == "restart")
    call_roots = []

    def fake_call(args, **kwargs):
        call_roots.append(kwargs["call_root"])
        workspace = kwargs["workspace"]
        if len(call_roots) == 1:
            (workspace / ".skiphow").mkdir()
            (workspace / ".skiphow/handoff.md").write_text(
                "## restart-eval-1 / checkpoint-1\n"
                "- Recorded: 2026-08-25T12:00:00Z\n"
                "- Selected scope: increment the value in task.json\n"
                "- Authority: workspace changes only\n"
                "- Later restrictions: None\n"
                "- Accepted decisions: None\n"
                "- Queue and dependencies: None\n"
                "- Issue: None\n- Branch: None\n- Worktree: None\n- Pull request: None\n- Exact head: None\n"
                "- Owned resources: None\n- Last external action: None\n- Last external result: None\n"
                "- Evidence: task.json value is 41\n- Blockers: None\n"
                "- Next safe action: set value to 42, mark done, and write result.json\n",
                encoding="utf-8",
            )
        else:
            (workspace / "task.json").write_text('{"status":"done","value":42}\n', encoding="utf-8")
            (workspace / "result.json").write_text('{"recovered_from":".skiphow/handoff.md","final_value":42}\n', encoding="utf-8")
        return {"status": "PASSED", "events": [], "usage": {"status": "UNVERIFIED", "cost_status": "UNVERIFIED"}}

    monkeypatch.setattr(run, "_host_call", fake_call)
    args = SimpleNamespace()
    result = run._plain_trial(
        args,
        scenario=scenario,
        trial_index=1,
        arm="restart",
        candidate=tmp_path / "candidate",
        proof={"version": "0.9.0"},
        work_run=tmp_path / "work",
        receipt_run=tmp_path / "receipts",
        per_call_budget=run.Decimal("1"),
        budget={"total": run.Decimal("2"), "observed_spend": run.Decimal("0")},
        secrets=[],
    )
    assert len(call_roots) == 2
    assert call_roots[0] != call_roots[1]
    assert result["restart_reconstruction_status"] == "PASSED"
    assert result["host_session_resume_status"] == "UNVERIFIED"


def test_paired_routing_claim_requires_repeated_complete_host_evidence() -> None:
    route_map = {
        "FAST": {"model": "fast", "effort": "medium"},
        "STANDARD": {"model": "standard", "effort": "medium"},
        "DEEP": {"model": "deep", "effort": "high"},
    }
    prompt = run._route_prompt(route_map, "all-deep")
    assert '"FAST": {"effort": "medium", "model": "deep"}' in prompt
    trials = []
    adaptive_routes = [
        {"tier": "FAST", "model": "fast", "effort": "medium"},
        {"tier": "STANDARD", "model": "standard", "effort": "medium"},
    ]
    baseline_routes = [
        {"tier": "FAST", "model": "deep", "effort": "medium"},
        {"tier": "STANDARD", "model": "deep", "effort": "medium"},
    ]
    for index in range(1, 4):
        trials.extend(
            [
                {"scenario": "adaptive-vs-all-deep", "trial_index": index, "arm": "adaptive", "status": "PASSED", "outcome_status": "PASSED", "calls": [{"requested_model": "root", "requested_effort": "high"}], "usage": {"cost_status": "PASSED", "cost_usd": "1", "root_route": {"model": "root", "effort": "high"}, "delegated_routes": adaptive_routes, "includes_subagents": True}},
                {"scenario": "adaptive-vs-all-deep", "trial_index": index, "arm": "all-deep", "status": "PASSED", "outcome_status": "PASSED", "calls": [{"requested_model": "root", "requested_effort": "high"}], "usage": {"cost_status": "PASSED", "cost_usd": "2", "root_route": {"model": "root", "effort": "high"}, "delegated_routes": baseline_routes, "includes_subagents": True}},
            ]
        )
    comparison = run._routing_comparison(trials, route_map, 3)
    assert comparison["claim_status"] == "PASSED"
    assert comparison["autonomous_selection_status"] == "UNVERIFIED"
    trials[0]["usage"]["includes_subagents"] = False
    assert run._routing_comparison(trials, route_map, 3)["claim_status"] == "UNVERIFIED"
    trials[0]["usage"]["includes_subagents"] = True
    trials[1]["usage"]["delegated_routes"].append({"tier": "FAST", "model": "fast", "effort": "medium"})
    assert run._routing_comparison(trials, route_map, 3)["claim_status"] == "UNVERIFIED"
    trials[1]["usage"]["delegated_routes"].pop()
    trials[0]["status"] = "FAILED"
    assert run._routing_comparison(trials, route_map, 3)["claim_status"] == "UNVERIFIED"


def test_auxiliary_claims_are_not_hidden_by_a_passing_outcome() -> None:
    result = {"status": "PASSED", "outcome_status": "PASSED", "process_status": "PASSED", "implicit_skill_loading_status": "UNVERIFIED"}
    run._finalize_trial_claims(result)
    assert result["status"] == "PASSED"
    assert result["claim_status"] == "UNVERIFIED"
    assert result["limitations"] == ["implicit_skill_loading_status"]


def test_mutable_github_live_scenario_fails_closed_before_execution() -> None:
    args = SimpleNamespace(
        suite=str(run.DEFAULT_SUITE),
        candidate=str(ROOT),
        scenario=["multi-issue-github-delivery"],
        trials=1,
        host="claude",
    )
    with pytest.raises(run.GateError, match="cannot both permit Git metadata writes"):
        run.run_live(args)
