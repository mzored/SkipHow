"""Owned activation edits preserve trusted user instructions and land where the host reads them."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/skiphow/skills/skiphow/scripts/activation.py"
spec = importlib.util.spec_from_file_location("skiphow_activation", SCRIPT)
assert spec and spec.loader
activation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = activation
spec.loader.exec_module(activation)


@pytest.mark.parametrize("original", [None, b"", b"Keep this", b"Keep this\n", b"Keep this\r\n", "Правило\n".encode()])
def test_lifecycle_restores_exact_original(original):
    installed = activation.transform(original, "install")
    assert activation.transform(installed, "install") == installed
    assert activation.transform(installed, "remove") == original
    assert activation.transform(original, "remove") == original


def test_later_unrelated_edits_survive_removal():
    installed = activation.transform(b"Original without newline", "install")
    assert activation.transform(b"Before\n" + installed + b"After\n", "remove") == b"Before\nOriginal without newline\nAfter\n"
    assert activation.transform(installed + b"\nAfter\n", "remove") == b"Original without newline\nAfter\n"
    assert activation.transform(installed + b"\r\nAfter\r\n", "remove") == b"Original without newline\r\nAfter\r\n"
    new_file = activation.transform(None, "install")
    assert activation.transform(new_file + b"Owner addition\n", "remove") == b"Owner addition\n"


@pytest.mark.parametrize("edit", [
    lambda value: value.replace(b"adaptive", b"different"),
    lambda value: value + value,
    lambda value: value.replace(b"<!-- /skiphow activation -->\n", b""),
    lambda value: value.replace(b"v1 separator=0", b"v2 separator=0"),
])
def test_edited_or_ambiguous_blocks_fail(edit):
    value = edit(activation.transform(b"", "install"))
    for action in ("install", "remove"):
        with pytest.raises(ValueError):
            activation.transform(value, action)


def test_cli_previews_and_applies_then_restores_missing_file(tmp_path, capsys):
    target = tmp_path / "AGENTS.md"
    args = ["install", "--target", str(target)]
    assert activation.main(args) == 0
    assert not target.exists()
    assert "Preview only" in capsys.readouterr().out
    assert activation.main(args + ["--apply"]) == 0
    assert activation.main(["status", "--target", str(target)]) == 0
    assert "runtime loading are UNVERIFIED" in capsys.readouterr().out
    assert activation.main(["remove", "--target", str(target), "--apply"]) == 0
    assert not target.exists()


def test_cli_preserves_modes_and_rejects_symlinks_and_edited_blocks(tmp_path):
    target = tmp_path / "CLAUDE.md"
    target.write_bytes(b"Private rule")
    target.chmod(0o600)
    assert activation.main(["install", "--target", str(target), "--apply"]) == 0
    assert target.stat().st_mode & 0o777 == 0o600
    link = tmp_path / "link"
    link.symlink_to(target)
    assert activation.main(["remove", "--target", str(link), "--apply"]) == 1
    target.write_bytes(target.read_bytes().replace(b"adaptive", b"edited"))
    before = target.read_bytes()
    assert activation.main(["remove", "--target", str(target), "--apply"]) == 1
    assert target.read_bytes() == before


@pytest.mark.parametrize("failure", [OSError("write failed"), KeyboardInterrupt()])
@pytest.mark.parametrize("original", [None, b"Existing private instructions\n"])
def test_failed_or_interrupted_staged_write_preserves_target_and_cleans_up(tmp_path, monkeypatch, failure, original):
    target = tmp_path / "AGENTS.md"
    if original is not None:
        target.write_bytes(original)
        target.chmod(0o640)

    def fail_flush(_descriptor):
        # The staged file already holds bytes; no partial write may reach the target.
        raise failure

    monkeypatch.setattr(activation.os, "fsync", fail_flush)
    with pytest.raises(type(failure)):
        activation.atomic_write(target, original, b"Replacement content\n")
    assert (target.read_bytes() if target.exists() else None) == original
    if original is not None:
        assert target.stat().st_mode & 0o777 == 0o640
    assert list(tmp_path.iterdir()) == ([target] if original is not None else [])


def test_failed_atomic_replacement_preserves_original_and_cleans_up(tmp_path, monkeypatch):
    target = tmp_path / "AGENTS.md"
    target.write_bytes(b"Owner instructions\n")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(activation.os, "replace", fail_replace)
    assert activation.main(["install", "--target", str(target), "--apply"]) == 1
    assert target.read_bytes() == b"Owner instructions\n"
    assert list(tmp_path.iterdir()) == [target]


# --- Host-aware resolution -------------------------------------------------


@pytest.fixture
def codex_home(tmp_path, monkeypatch):
    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    monkeypatch.setattr(activation, "MANAGED_POLICY", {"codex": (), "claude-code": ()})
    return home


@pytest.fixture
def claude_home(tmp_path, monkeypatch):
    home = tmp_path / "claude-config"
    home.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    monkeypatch.setattr(activation, "MANAGED_POLICY", {"codex": (), "claude-code": ()})
    return home


def status(host):
    return activation.status_report(activation.resolve(host))


def test_ordinary_codex_home_installs_into_agents_md_only(codex_home):
    agents = codex_home / "AGENTS.md"
    agents.write_bytes(b"Use short answers.\n")
    assert activation.main(["install", "--host", "codex", "--apply"]) == 0
    assert agents.read_bytes() == activation.transform(b"Use short answers.\n", "install")
    assert not (codex_home / "AGENTS.override.md").exists()
    report = status("codex")
    assert report["configured"] is True and report["effective_file"] == str(agents)
    assert report["shadowed_blocks"] == []
    assert activation.main(["remove", "--host", "codex", "--apply"]) == 0
    assert agents.read_bytes() == b"Use short answers.\n"


def test_nonempty_override_is_the_effective_codex_file(codex_home, capsys):
    override = codex_home / "AGENTS.override.md"
    agents = codex_home / "AGENTS.md"
    override.write_bytes(b"Prefer British spelling.\n")
    agents.write_bytes(b"Use short answers.\n")
    report = status("codex")
    assert report["effective_file"] == str(override)
    assert any("does not read AGENTS.md" in note for note in report["notes"])
    assert activation.main(["install", "--host", "codex", "--apply"]) == 0
    assert override.read_bytes() == activation.transform(b"Prefer British spelling.\n", "install")
    assert agents.read_bytes() == b"Use short answers.\n"
    assert status("codex")["configured"] is True
    assert activation.main(["remove", "--host", "codex", "--apply"]) == 0
    assert override.read_bytes() == b"Prefer British spelling.\n"
    assert agents.read_bytes() == b"Use short answers.\n"


def test_a_block_left_in_the_shadowed_file_is_reported_and_moved(codex_home):
    override = codex_home / "AGENTS.override.md"
    agents = codex_home / "AGENTS.md"
    override.write_bytes(b"Prefer British spelling.\n")
    agents.write_bytes(activation.transform(b"Use short answers.\n", "install"))
    report = status("codex")
    assert report["configured"] is False
    assert report["shadowed_blocks"] == [str(agents)]
    assert activation.main(["install", "--host", "codex", "--apply"]) == 0
    assert override.read_bytes() == activation.transform(b"Prefer British spelling.\n", "install")
    assert agents.read_bytes() == b"Use short answers.\n"
    assert status("codex")["configured"] is True


def test_custom_codex_home_that_does_not_exist_is_reported_without_writing(tmp_path, monkeypatch, capsys):
    missing = tmp_path / "absent-home"
    monkeypatch.setenv("CODEX_HOME", str(missing))
    monkeypatch.setattr(activation, "MANAGED_POLICY", {"codex": (), "claude-code": ()})
    report = status("codex")
    assert report["availability"].startswith("not installed")
    assert activation.main(["install", "--host", "codex", "--apply"]) == 1
    assert "must already exist" in capsys.readouterr().err
    assert not missing.exists()


def test_edited_block_in_the_effective_file_stops_every_change(codex_home, capsys):
    override = codex_home / "AGENTS.override.md"
    override.write_bytes(activation.transform(b"", "install").replace(b"adaptive", b"edited"))
    before = override.read_bytes()
    assert status("codex")["edited_blocks"] == [str(override)]
    assert activation.main(["install", "--host", "codex", "--apply"]) == 1
    assert activation.main(["remove", "--host", "codex", "--apply"]) == 1
    assert override.read_bytes() == before


def test_codex_availability_reads_the_plugin_cache_and_config(codex_home):
    assert status("codex")["availability"].startswith("not installed")
    cache = codex_home / "plugins/cache/skiphow/skiphow/4.2.0"
    cache.mkdir(parents=True)
    assert status("codex")["availability"] == "installed: cached versions 4.2.0"
    (codex_home / "config.toml").write_text('[plugins."skiphow@skiphow"]\nenabled = false\n')
    assert status("codex")["availability"].startswith("installed but disabled")


def test_claude_config_dir_installs_into_claude_md_and_removes_rule_copies(claude_home):
    primary = claude_home / "CLAUDE.md"
    rules = claude_home / "rules"
    rules.mkdir()
    primary.write_bytes(b"# Preferences\n")
    (rules / "skiphow.md").write_bytes(activation.transform(None, "install"))
    report = status("claude-code")
    assert report["effective_file"] == str(primary)
    assert report["shadowed_blocks"] == [str(rules / "skiphow.md")]
    assert activation.main(["install", "--host", "claude-code", "--apply"]) == 0
    assert primary.read_bytes() == activation.transform(b"# Preferences\n", "install")
    assert not (rules / "skiphow.md").exists()
    assert status("claude-code")["configured"] is True
    assert activation.main(["remove", "--host", "claude-code", "--apply"]) == 0
    assert primary.read_bytes() == b"# Preferences\n"


def test_claude_availability_reads_the_inventory_and_settings(claude_home):
    assert status("claude-code")["availability"].startswith("not installed")
    plugins = claude_home / "plugins"
    plugins.mkdir()
    inventory = plugins / "installed_plugins.json"
    inventory.write_text(json.dumps({"plugins": {"skiphow@skiphow": [
        {"scope": "project", "projectPath": "/somewhere/app", "version": "4.1.1"}]}}))
    assert status("claude-code")["availability"].startswith("installed for specific projects only")
    inventory.write_text(json.dumps({"plugins": {"skiphow@skiphow": [{"scope": "user", "version": "4.2.0"}]}}))
    assert status("claude-code")["availability"] == "installed: user 4.2.0"
    (claude_home / "settings.json").write_text(json.dumps({"enabledPlugins": {"skiphow@skiphow": False}}))
    assert status("claude-code")["availability"].startswith("installed but disabled")


def test_managed_policy_files_are_reported_not_evaluated(codex_home, tmp_path, monkeypatch, capsys):
    policy = tmp_path / "requirements.toml"
    policy.write_text('[marketplaces]\nrestrict_to_allowed_sources = true\n')
    monkeypatch.setattr(activation, "MANAGED_POLICY", {"codex": (policy,), "claude-code": ()})
    assert status("codex")["managed_policy"] == [str(policy)]
    assert activation.main(["status", "--host", "codex"]) == 0
    assert "managed policy present" in capsys.readouterr().out
    assert policy.read_text().startswith("[marketplaces]")


def test_json_status_carries_every_fact_separately(codex_home, capsys):
    assert activation.main(["status", "--host", "codex", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert set(report) >= {"host", "effective_file", "block", "configured", "shadowed_blocks",
                           "edited_blocks", "availability", "managed_policy", "loading"}
    assert report["configured"] is False
    assert "observed only in a fresh session" in report["loading"]


def test_packaged_helper_is_a_plain_non_executable_resource():
    assert not SCRIPT.stat().st_mode & 0o111
    assert "scripts/activation.py" in (ROOT / "plugins/skiphow/skills/skiphow/references/setup.md").read_text()
