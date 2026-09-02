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
    assert "UNVERIFIED" in capsys.readouterr().out


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


def test_codex_validator_can_use_the_managed_python(tmp_path: Path) -> None:
    managed = tmp_path / "python"
    managed.write_text("", encoding="utf-8")
    with patch.object(
        hosts,
        "checked",
        side_effect=[(False, "missing yaml"), (True, str(managed))],
    ):
        assert hosts.validator_python() == (str(managed), "repository-managed Python")


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
    assert "Codex isolated install: UNVERIFIED" in capsys.readouterr().out


def test_required_install_fails_when_host_is_missing() -> None:
    with (
        patch.object(hosts, "codex_validator", return_value=None),
        patch.object(hosts.shutil, "which", return_value=None),
    ):
        assert hosts.main(["--require-codex-install"]) == 1
        assert hosts.main(["--require-claude-install"]) == 1
