"""Contracts for host validation and isolated installation checks."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hosts = load("skiphow_check_hosts_isolated", "scripts/check_hosts.py")


def test_skip_install_cannot_satisfy_a_required_install() -> None:
    for required in ("--require-codex-install", "--require-claude-install"):
        with pytest.raises(SystemExit) as raised:
            hosts.main(["--skip-install", required])
        assert raised.value.code == 2


def test_only_a_source_policy_denial_is_downgraded() -> None:
    observed = (
        "Error: marketplace source `/tmp/skiphow-codex-install-x/marketplace` is not "
        "allowed by requirements from /etc/codex/requirements.toml"
    )
    assert hosts._codex_policy_block(observed)
    assert hosts._codex_policy_block("blocked by allowed source policy")
    assert not hosts._codex_policy_block("failed to parse /etc/codex/requirements.toml")
    assert not hosts._codex_policy_block("network unreachable")
    assert not hosts._codex_policy_block(
        "network setting is not allowed; failed to parse /etc/codex/requirements.toml"
    )


def test_missing_hosts_are_unverified_unless_required(capsys) -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install"]) == 0
        assert hosts.main(["--require-codex-validator", "--skip-install"]) == 1
        assert hosts.main(["--require-claude", "--skip-install"]) == 1
    output = capsys.readouterr().out
    assert "| Codex schema validation | UNVERIFIED |" in output
    assert "| Claude schema validation | UNVERIFIED |" in output
    assert "PASS" not in output


def test_configured_codex_validator_failure_blocks_release(tmp_path: Path) -> None:
    validator = tmp_path / "validate.py"
    validator.write_text("raise SystemExit(1)\n", encoding="utf-8")
    with (
        patch.object(hosts, "codex_validator", return_value=validator),
        patch.object(
            hosts,
            "validator_python",
            return_value=(sys.executable, "current Python"),
        ),
        patch.object(hosts.shutil, "which", return_value=None),
        patch.object(hosts, "checked", return_value=(False, "invalid plugin")),
    ):
        assert hosts.main(["--skip-install"]) == 1


def test_missing_yaml_leaves_codex_validation_unverified_without_preparing(capsys) -> None:
    """A validator interpreter is never provisioned on the caller's behalf.

    The fallback used to run `scripts/check.py --prepare-only`, which reached a
    package index by proxy. An interpreter without PyYAML now leaves that one
    category unrun and says how to install it.
    """
    with patch.object(hosts, "checked", return_value=(False, "missing yaml")) as checked:
        python, detail = hosts.validator_python()
    assert python is None
    assert "python -m pip install -r requirements-dev.txt" in detail
    assert checked.call_count == 1
    assert "--prepare-only" not in " ".join(checked.call_args[0][0])

    validator = Path(__file__)
    with (
        patch.object(hosts, "codex_validator", return_value=validator),
        patch.object(hosts, "validator_python", return_value=(None, detail)),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install"]) == 0
        assert hosts.main(["--skip-install", "--require-codex-validator"]) == 1
    output = capsys.readouterr().out
    assert "| Codex schema validation | UNVERIFIED |" in output
    assert "PASS" not in output


def test_plain_marketplace_matches_exact_candidate_and_rejects_repositories(
    tmp_path: Path,
) -> None:
    source = hosts._plain_marketplace(tmp_path / "plain", "codex")
    assert not (source / ".agents/skills").exists()
    assert hosts.verify_plain_marketplace_source(str(source), "codex")[0]
    (source / ".git").mkdir()
    passed, output = hosts.verify_plain_marketplace_source(str(source), "codex")
    assert not passed
    assert "repository" in output


def fake_host_install(
    host: str,
    calls: list[tuple[list[str], dict[str, str], Path]],
    *,
    installed_path: Path | None = None,
    codex_add_output: str | None = None,
    inventory_output: str | None = None,
):
    """Simulate host commands while materializing the installed payload."""
    state: dict[str, Path] = {}
    home_variable = "CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"

    def checked(command, **kwargs):
        command = list(command)
        environment = kwargs["env"]
        command_cwd = Path(kwargs["cwd"])
        assert command_cwd.is_dir()
        assert command_cwd.parent == Path(environment[home_variable]).parent
        assert not command_cwd.is_relative_to(ROOT)
        assert not (command_cwd / ".git").exists()
        calls.append((command, environment, command_cwd))
        is_install = command[1:3] == (
            ["plugin", "add"] if host == "codex" else ["plugin", "install"]
        )
        if is_install:
            target = installed_path or Path(environment[home_variable]) / "installed/skiphow"
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(hosts.PLUGIN_ROOT, target)
            state["installed"] = target
            if host == "codex":
                return True, codex_add_output or json.dumps(
                    {
                        "pluginId": "skiphow@skiphow",
                        "installedPath": str(target),
                    }
                )
            return True, "installed"
        if command[1:3] == ["plugin", "list"]:
            if inventory_output is not None:
                return True, inventory_output
            target = state["installed"]
            if host == "codex":
                return True, json.dumps(
                    {
                        "installed": [
                            {
                                "pluginId": "skiphow@skiphow",
                                "enabled": True,
                                "installed": True,
                                "source": {"path": str(hosts.PLUGIN_ROOT)},
                            }
                        ]
                    }
                )
            return True, json.dumps(
                [
                    {
                        "id": "skiphow@skiphow",
                        "enabled": True,
                        "installed": True,
                        "installPath": str(target),
                    }
                ]
            )
        return True, "{}"

    return checked


def test_codex_install_uses_plain_source_without_a_git_ref(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []
    source = hosts._plain_marketplace(tmp_path / "plain", "codex")

    with patch.object(hosts, "checked", side_effect=fake_host_install("codex", calls)):
        assert hosts.isolated_install(
            "codex",
            "/bin/codex",
            codex_marketplace_source=str(source),
        )[0]
    assert calls[0][0][-2:] == [str(source), "--json"]
    assert "--ref" not in calls[0][0]


def test_claude_validation_targets_the_plugin_directory() -> None:
    commands: list[list[str]] = []

    def checked(command, **kwargs):
        commands.append(list(command))
        return True, "ok"

    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", side_effect=[None, "/bin/claude"]),
        patch.object(hosts, "checked", side_effect=checked),
    ):
        assert hosts.main(["--skip-install"]) == 0
    assert [
        "/bin/claude",
        "plugin",
        "validate",
        "--strict",
        str(hosts.PLUGIN_ROOT),
    ] in commands


@pytest.mark.parametrize(
    "host,home_variable",
    [("codex", "CODEX_HOME"), ("claude", "CLAUDE_CONFIG_DIR")],
)
def test_isolated_install_uses_local_marketplace_and_empty_host_home(
    host: str, home_variable: str
) -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []

    with patch.object(hosts, "checked", side_effect=fake_host_install(host, calls)):
        assert hosts.isolated_install(host, f"/bin/{host}")[0]
    assert "marketplace" in " ".join(calls[0][0])
    assert calls[0][1][home_variable]
    assert len({call[1][home_variable] for call in calls}) == 1
    assert len({call[2] for call in calls}) == 1
    assert calls[0][2].name == "command-cwd"
    assert calls[0][2].parent == Path(calls[0][1][home_variable]).parent


def test_isolated_install_rejects_repository_created_in_command_cwd() -> None:
    def repository_creating_host(command, **kwargs):
        command_cwd = Path(kwargs["cwd"])
        (command_cwd / ".git").mkdir()
        return True, "{}"

    with patch.object(hosts, "checked", side_effect=repository_creating_host):
        passed, output = hosts.isolated_install("codex", "/bin/codex")
    assert not passed
    assert output == "host package check created a repository"


@pytest.mark.parametrize("host", ["codex", "claude"])
def test_isolated_install_rejects_external_payload_even_when_bytes_match(
    tmp_path: Path, host: str
) -> None:
    external = tmp_path / f"external-{host}"
    calls: list[tuple[list[str], dict[str, str], Path]] = []
    with patch.object(
        hosts,
        "checked",
        side_effect=fake_host_install(host, calls, installed_path=external),
    ):
        passed, output = hosts.isolated_install(host, f"/bin/{host}")
    assert not passed
    assert output == "installed package path is outside the isolated host home"
    assert hosts._payload(external) == hosts._payload(hosts.PLUGIN_ROOT)


def test_codex_install_rejects_inventory_source_as_install_proof() -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []
    with patch.object(
        hosts,
        "checked",
        side_effect=fake_host_install(
            "codex",
            calls,
            codex_add_output=json.dumps({"pluginId": "skiphow@skiphow"}),
        ),
    ):
        passed, output = hosts.isolated_install("codex", "/bin/codex")
    assert not passed
    assert output == "Codex plugin add output omitted installedPath"


def test_codex_add_receipt_requires_the_target_plugin_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="wrong pluginId"):
        hosts._codex_installed_path(
            json.dumps(
                {
                    "pluginId": "other@skiphow",
                    "installedPath": str(tmp_path / "skiphow"),
                }
            )
        )


@pytest.mark.parametrize("host", ["codex", "claude"])
def test_inventory_requires_exactly_one_enabled_installed_entry(host: str) -> None:
    item = {
        ("pluginId" if host == "codex" else "id"): "skiphow@skiphow",
        "enabled": True,
        "installed": True,
    }
    entries = [item, dict(item)]
    duplicate = {"installed": entries} if host == "codex" else entries
    with pytest.raises(ValueError, match="exactly one"):
        hosts._inventory_entry(host, json.dumps(duplicate))
    entries[1]["enabled"] = False
    mixed_duplicate = {"installed": entries} if host == "codex" else entries
    with pytest.raises(ValueError, match="exactly one"):
        hosts._inventory_entry(host, json.dumps(mixed_duplicate))
    item["enabled"] = False
    disabled = {"installed": [item]} if host == "codex" else [item]
    with pytest.raises(ValueError, match="not enabled and installed"):
        hosts._inventory_entry(host, json.dumps(disabled))


def test_codex_inventory_requires_explicit_installed_boolean() -> None:
    codex = {
        "installed": [
            {
                "pluginId": "skiphow@skiphow",
                "enabled": True,
            }
        ]
    }
    with pytest.raises(ValueError, match="not enabled and installed"):
        hosts._inventory_entry("codex", json.dumps(codex))

    claude = [{"id": "skiphow@skiphow", "enabled": True}]
    assert hosts._inventory_entry("claude", json.dumps(claude)) == claude[0]


@pytest.mark.parametrize("host", ["codex", "claude"])
def test_isolated_install_still_requires_exact_payload_bytes(host: str) -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []

    def corrupting_checked(command, **kwargs):
        passed, output = fake_checked(command, **kwargs)
        if list(command)[1:3] == ["plugin", "list"]:
            home_variable = "CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"
            host_home = Path(kwargs["env"][home_variable])
            (host_home / "installed/skiphow/VERSION").write_text(
                "wrong\n", encoding="utf-8"
            )
        return passed, output

    fake_checked = fake_host_install(host, calls)
    with patch.object(hosts, "checked", side_effect=corrupting_checked):
        passed, output = hosts.isolated_install(host, f"/bin/{host}")
    assert not passed
    assert output == "installed plugin payload does not match the candidate"


def test_available_host_install_failure_blocks_release() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", side_effect=["/bin/codex", None]),
        patch.object(hosts, "isolated_install", return_value=(False, "install failed")),
    ):
        assert hosts.main([]) == 1


def test_managed_codex_policy_is_unverified_unless_install_is_required(capsys) -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(
            hosts.shutil,
            "which",
            side_effect=["/bin/codex", None, "/bin/codex", None],
        ),
        patch.object(
            hosts,
            "isolated_install",
            return_value=(
                False,
                "blocked by /etc/codex/requirements.toml allowed source policy",
            ),
        ),
    ):
        assert hosts.main([]) == 0
        assert hosts.main(["--require-codex-install"]) == 1
    assert "| Clean Codex install | UNVERIFIED |" in capsys.readouterr().out


def test_required_install_fails_when_host_is_missing() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--require-codex-install"]) == 1
        assert hosts.main(["--require-claude-install"]) == 1


def test_matrix_reports_every_capability_on_its_own_row(capsys) -> None:
    """A skipped or absent check stays visible as UNVERIFIED; nothing collapses to PASS."""
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install"]) == 0
    output = capsys.readouterr().out
    for capability in hosts.MATRIX_CAPABILITIES:
        assert f"| {capability} | " in output, capability
    assert "| Deterministic package gate | UNVERIFIED |" in output
    assert "| Clean Codex install | UNVERIFIED | skipped |" in output
    assert "| Clean Claude install | UNVERIFIED | skipped |" in output
    assert "| Explicit invocation | UNVERIFIED |" in output
    assert "| Implicit activation | UNVERIFIED |" in output
    assert "| Continuity/bootstrap | UNVERIFIED |" in output
    assert "| Behavioral contract suite | UNVERIFIED |" in output
    assert "PASS" not in output
    assert "Observed" not in output


def test_render_matrix_requires_the_tracked_capabilities_in_order() -> None:
    rows = [(name, "UNVERIFIED", "x") for name in hosts.MATRIX_CAPABILITIES]
    rendered = hosts.render_matrix(rows)
    assert rendered.splitlines()[0] == "Scope: this release runner. External candidate and model-session receipts are recorded separately."
    assert rendered.splitlines()[2] == "| Capability | Status | Detail |"
    with pytest.raises(ValueError):
        hosts.render_matrix(rows[:-1])


def test_package_gate_runs_check_py_and_fails_the_run(capsys) -> None:
    def checked(command, **kwargs):
        if command[1].endswith("check.py"):
            return False, "gate failed"
        return True, ""

    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
        patch.object(hosts, "checked", side_effect=checked),
    ):
        assert hosts.main(["--skip-install", "--package-gate"]) == 1
    assert "| Deterministic package gate | FAIL |" in capsys.readouterr().out


def test_matrix_out_writes_the_printed_matrix(tmp_path: Path, capsys) -> None:
    target = tmp_path / "matrix.md"
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--skip-install", "--matrix-out", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == capsys.readouterr().out


def test_smoke_requires_a_receipt_dir_and_excludes_skip_install() -> None:
    for argv in (["--smoke"], ["--smoke", "--skip-install", "--receipt-dir", "x"]):
        with pytest.raises(SystemExit) as raised:
            hosts.main(argv)
        assert raised.value.code == 2


def fake_smoke_host(host: str, calls: list[list[str]], *, uninstall_ok: bool = True):
    """Extend the fake install with uninstall and an inventory that empties afterwards."""
    base = fake_host_install(host, calls)
    state = {"installed": False}

    def checked(command, **kwargs):
        command = list(command)
        if command[-1:] == ["--version"]:
            return True, f"{host} 9.9.9"
        if command[1:3] == (["plugin", "remove"] if host == "codex" else ["plugin", "uninstall"]):
            calls.append(command)
            state["installed"] = False
            return uninstall_ok, "removed" if uninstall_ok else "refused"
        if command[1:3] == (["plugin", "add"] if host == "codex" else ["plugin", "install"]):
            state["installed"] = True
        if command[1:3] == ["plugin", "list"] and not state["installed"]:
            calls.append(command)
            return True, json.dumps({"installed": []} if host == "codex" else [])
        return base(command, **kwargs)

    return checked


def fake_committed_package() -> dict[str, str]:
    current = hosts.package_identity()
    return {
        "version": current["version"],
        "commit": "a" * 40,
        "git_tree": "b" * 40,
        "payload_sha256": current["payload_sha256"],
    }


@pytest.mark.parametrize("host", ["codex", "claude"])
def test_smoke_installs_inspects_uninstalls_and_writes_a_privacy_safe_receipt(
    host: str, tmp_path: Path
) -> None:
    calls: list = []
    package = fake_committed_package()
    with (
        patch.object(hosts, "checked", side_effect=fake_smoke_host(host, calls)),
        patch.object(hosts, "package_identity", return_value=package),
    ):
        passed, detail, receipt = hosts.smoke_install(host, f"/bin/{host}", tmp_path / "receipts")
    assert passed, detail
    verbs = [call[2] if isinstance(call, list) else call[0][2] for call in calls if (call[1] if isinstance(call, list) else call[0][1]) == "plugin"]
    assert verbs == ["marketplace", "add" if host == "codex" else "install", "list", "remove" if host == "codex" else "uninstall", "list"]
    document = json.loads(receipt.read_text(encoding="utf-8"))
    assert document["host"] == ("claude-code" if host == "claude" else host)
    assert document["host_version"] == f"{host} 9.9.9"
    assert document["result"] == "PASS"
    assert document["schema"] == "skiphow-host-smoke-bundle/1"
    for check in ("clean_install", "uninstall"):
        result = document["results"][check]
        assert result["status"] == "PASS"
        assert set(result["receipt"]) == set(hosts.HOST_RECEIPT_FIELDS)
        assert result["receipt"]["check"] == check
        assert result["receipt"]["package_version"] == (ROOT / "VERSION").read_text().strip()
        assert len(result["receipt"]["package_payload_sha256"]) == 64
        with patch.object(hosts, "validate_committed_package_identity", return_value=None):
            hosts.validate_host_receipt(
                result["receipt"],
                host=document["host"],
                check=check,
                status=result["status"],
            )
    steps = {step["step"]: step["status"] for step in document["steps"]}
    assert steps["clean host home"] == "PASS"
    assert steps["inspect installed files"] == "PASS"
    assert steps["inspect hook trust/state"] == "UNVERIFIED"
    assert steps["uninstall"] == "PASS"
    assert steps["verify uninstall"] == "PASS"
    assert steps["start a clean session"] == "UNVERIFIED"
    assert steps["verify explicit invocation"] == "UNVERIFIED"
    assert set(document["installed_files"]) == set(hosts._payload(hosts.PLUGIN_ROOT))
    text = receipt.read_text(encoding="utf-8")
    assert str(Path.home()) not in text
    assert "skiphow-" + host + "-smoke-" not in text
    assert all(not key.startswith("/") for key in document["installed_files"])


def test_smoke_reports_a_plugin_that_survives_uninstall(tmp_path: Path) -> None:
    calls: list = []
    base = fake_host_install("codex", calls)

    def sticky(command, **kwargs):
        command = list(command)
        if command[-1:] == ["--version"]:
            return True, "codex 0"
        if command[1:3] == ["plugin", "remove"]:
            return True, "removed"
        return base(command, **kwargs)

    with (
        patch.object(hosts, "checked", side_effect=sticky),
        patch.object(hosts, "package_identity", return_value=fake_committed_package()),
    ):
        passed, detail, receipt = hosts.smoke_install("codex", "/bin/codex", tmp_path)
    assert not passed
    assert detail == "plugin remained installed after uninstall"
    assert json.loads(receipt.read_text())["result"] == "FAIL"


def test_smoke_refuses_a_missing_host_version(tmp_path: Path) -> None:
    with (
        patch.object(hosts, "package_identity", return_value=fake_committed_package()),
        patch.object(hosts, "_host_version", return_value="unknown"),
    ):
        with pytest.raises(ValueError, match="host version"):
            hosts.smoke_install("codex", "/bin/codex", tmp_path)


def test_canonical_host_receipt_cannot_move_between_host_rows() -> None:
    package = fake_committed_package()
    receipt = {
        "host": "codex",
        "package_version": package["version"],
        "package_commit": package["commit"],
        "package_tree": package["git_tree"],
        "package_payload_sha256": package["payload_sha256"],
        "host_version": "codex-cli 0.0.0",
        "date": "2026-09-04",
        "check": "clean_install",
        "outcome": "PASS",
        "configuration": "isolated",
        "command_or_session": "synthetic",
        "observable_evidence": "synthetic",
        "cleanup_result": "synthetic",
        "source": "test",
    }
    with patch.object(hosts, "validate_committed_package_identity", return_value=None):
        with pytest.raises(ValueError, match="ledger host"):
            hosts.validate_host_receipt(
                receipt,
                host="claude-code",
                check="clean_install",
                status="PASS",
            )


def test_canonical_host_receipt_outcome_must_match_ledger_status() -> None:
    package = fake_committed_package()
    receipt = {
        "host": "codex",
        "package_version": package["version"],
        "package_commit": package["commit"],
        "package_tree": package["git_tree"],
        "package_payload_sha256": package["payload_sha256"],
        "host_version": "codex-cli 0.0.0",
        "date": "2026-09-04",
        "check": "clean_install",
        "outcome": "FAIL",
        "configuration": "isolated",
        "command_or_session": "synthetic",
        "observable_evidence": "synthetic failure",
        "cleanup_result": "synthetic",
        "source": "test",
    }
    with patch.object(hosts, "validate_committed_package_identity", return_value=None):
        with pytest.raises(ValueError, match="ledger status"):
            hosts.validate_host_receipt(
                receipt,
                host="codex",
                check="clean_install",
                status="PASS",
            )


def test_committed_identity_accepts_an_earlier_commit_with_the_same_package() -> None:
    package = fake_committed_package()
    receipt = {
        "package_version": package["version"],
        "package_commit": "c" * 40,
        "package_tree": package["git_tree"],
        "package_payload_sha256": package["payload_sha256"],
    }
    committed = {
        "version": receipt["package_version"],
        "git_tree": receipt["package_tree"],
        "payload_sha256": receipt["package_payload_sha256"],
    }
    with (
        patch.object(hosts, "package_identity", return_value=package),
        patch.object(hosts, "committed_package_identity", return_value=committed),
    ):
        hosts.validate_committed_package_identity(receipt)


def test_committed_identity_rejects_an_uncommitted_candidate() -> None:
    package = fake_committed_package() | {"commit": "UNCOMMITTED", "git_tree": "UNCOMMITTED"}
    receipt = {
        "package_version": package["version"],
        "package_commit": "c" * 40,
        "package_tree": "b" * 40,
        "package_payload_sha256": package["payload_sha256"],
    }
    with patch.object(hosts, "package_identity", return_value=package):
        with pytest.raises(ValueError, match="not committed"):
            hosts.validate_committed_package_identity(receipt)


def test_inventory_absent_accepts_only_a_missing_or_uninstalled_entry() -> None:
    assert hosts._inventory_absent("codex", json.dumps({"installed": []}))
    assert hosts._inventory_absent("codex", json.dumps({"installed": [{"pluginId": "skiphow@skiphow", "installed": False}]}))
    assert not hosts._inventory_absent("codex", json.dumps({"installed": [{"pluginId": "skiphow@skiphow", "installed": True}]}))
    assert hosts._inventory_absent("claude", json.dumps([]))
    assert not hosts._inventory_absent("claude", json.dumps([{"id": "skiphow@skiphow", "enabled": True}]))
