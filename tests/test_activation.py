"""Owned activation edits preserve trusted user instructions."""

import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location("skiphow_activation", Path(__file__).resolve().parents[1] / "scripts/activation.py")
assert spec and spec.loader
activation = importlib.util.module_from_spec(spec)
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
