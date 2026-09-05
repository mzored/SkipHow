#!/usr/bin/env python3
"""Prepare and retain manual evaluation evidence without launching a model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import shutil

from check_hosts import _payload, package_identity
from receipt_privacy import sanitize as sanitize_receipt, sanitize_text

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals/fixtures"


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def files(root: Path) -> list[Path]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("fixture must be an ordinary directory")
    result = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.relative_to(root).parts:
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError("fixture contains a symlink or special file")
        if stat.S_ISREG(mode):
            result.append(path)
    if not result:
        raise ValueError("fixture contains no regular files")
    return result


def manifest(root: Path) -> dict:
    return {
        "schema": 1,
        "scope": "pre-session worktree regular files excluding .git",
        "files": [
            {"path": path.relative_to(root).as_posix(),
             "mode": "100755" if path.stat().st_mode & 0o111 else "100644",
             "sha256": digest(path.read_bytes())}
            for path in files(root)
        ],
    }


def source(name: str, seen: tuple[str, ...] = ()) -> tuple[dict, str]:
    """Use the corpus's source-layer hash format, including fixture metadata."""
    payload = {}

    def add(layer: str, ancestors: tuple[str, ...]) -> dict:
        if not layer or Path(layer).name != layer or layer in ancestors:
            raise ValueError("invalid or cyclic fixture source")
        directory = FIXTURES / layer
        hashes = _payload(directory)
        record = json.loads((directory / "fixture.json").read_text())
        if record.get("synthetic") is not True:
            raise ValueError("only declared synthetic fixtures may be captured")
        if record.get("derives_from"):
            add(record["derives_from"], (*ancestors, layer))
        for relative, sha in hashes.items():
            payload[f"{layer}/{relative}"] = {
                "sha256": sha,
                "executable": bool((directory / relative).stat().st_mode & 0o111),
            }
        return record

    record = add(name, seen)
    return record, digest(canonical(payload).encode())


def materialize(name: str, destination: Path) -> None:
    """Copy retained layers; leave declared Git and scenario setup to the operator."""
    source(name)  # Validate every layer before creating an owned directory.
    if destination.exists():
        raise ValueError("materialize requires a new destination")
    destination.mkdir()
    try:
        def copy(layer: str) -> None:
            directory = FIXTURES / layer
            record = json.loads((directory / "fixture.json").read_text())
            if record.get("derives_from"):
                copy(record["derives_from"])
            shutil.copytree(directory, destination, dirs_exist_ok=True)
        copy(name)
    except BaseException:
        shutil.rmtree(destination)
        raise


def write_new(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def validate_config(config: dict) -> None:
    for field in ("run_id", "case_id", "arm", "host", "host_version", "model",
                  "effort", "permission", "sandbox", "activation", "instructions",
                  "isolation", "control_run", "prompt", "observable", "host_command",
                  "permitted_command_evidence", "setup_performed"):
        if not config.get(field):
            raise ValueError(f"missing configuration: {field}")
    limits = config.get("limits", {})
    for field in ("session_usd", "receipt_usd", "sessions_in_flight", "wall_seconds"):
        value = limits.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"missing positive limit: {field}")
    baseline = config.get("baseline", {})
    if (not isinstance(baseline.get("argv"), list) or not baseline["argv"]
            or not all(isinstance(arg, str) and arg for arg in baseline["argv"])
            or not isinstance(baseline.get("returncode"), int)
            or not isinstance(baseline.get("contains"), str) or not baseline["contains"]):
        raise ValueError("baseline needs argv, expected returncode and nonempty output substring")


def prepare(fixture: Path, name: str, config: dict, output: Path) -> dict:
    validate_config(config)
    if output.exists() or output.resolve().is_relative_to(fixture.resolve()):
        raise ValueError("receipt must be new and outside the fixture")
    record, revision = source(name)
    if config["setup_performed"] != record["setup"]:
        raise ValueError("record the exact fixture setup before preparing")
    for marker in config.get("absent_markers", []):
        if Path(marker).exists():
            raise ValueError("a forbidden pre-session marker already exists")
    before = manifest(fixture)
    baseline = config["baseline"]
    result = subprocess.run(baseline["argv"], cwd=fixture, capture_output=True,
                            text=True, timeout=config["limits"]["wall_seconds"], check=False)
    combined = result.stdout + result.stderr
    if result.returncode != baseline["returncode"] or baseline["contains"] not in combined:
        raise ValueError("baseline differs from the declared result; no model run is ready")
    after = manifest(fixture)
    if before != after:
        raise ValueError("baseline changed fixture files; disable caches or restore and retry")
    value = {
        "schema": 1, "kind": "manual-evaluation-preparation", "configuration": config,
        "fixture_directory": str(fixture.resolve()),
        "package": package_identity(),
        "fixture_snapshot": {
            "id": name, "setup": record["setup"], "fixture_revision_sha256": revision,
            "built_content": {"verification": "manifest", "sha256": digest(canonical(before).encode()),
                              "manifest": before},
        },
        "baseline": {"argv": baseline["argv"], "returncode": result.returncode, "output": combined},
        "evidence_label": "UNVERIFIED",
    }
    write_new(output, value)
    return value


def capture(fixture: Path, prepared: Path, trace: Path, output: Path,
            redactions: dict[str, str], terminal: str) -> dict:
    if output.exists() or output.resolve().is_relative_to(fixture.resolve()):
        raise ValueError("capture must be new and outside the fixture")
    raw = prepared.read_bytes()
    value = json.loads(raw)
    if value.get("kind") != "manual-evaluation-preparation":
        raise ValueError("capture requires a preparation record")
    if value.get("fixture_directory") != str(fixture.resolve()):
        raise ValueError("capture fixture differs from the prepared directory")
    validate_config(value["configuration"])
    built = value["fixture_snapshot"]["built_content"]
    if digest(canonical(built["manifest"]).encode()) != built["sha256"]:
        raise ValueError("pre-session manifest was altered")
    if not trace.is_file() or not trace.read_text().strip():
        raise ValueError("capture requires a retained nonempty trace")
    if terminal not in {"task_completed", "stopped_at_observable", "failed_to_reach_observable", "interrupted"}:
        raise ValueError("unknown terminal state")
    if any(not key or not replacement for key, replacement in redactions.items()):
        raise ValueError("redactions require nonempty literals and replacements")
    replacements = {str(fixture.resolve()): "<fixture>", **redactions}

    def redact(text: str) -> str:
        return sanitize_text(text, replacements)

    artifacts = []
    for path in files(fixture):
        data = path.read_bytes()
        try:
            content = redact(data.decode("utf-8"))
        except UnicodeDecodeError:
            raise ValueError("binary artifact needs a deliberate privacy-safe export before capture") from None
        retained = canonical({"encoding": "utf-8", "content": content,
                              "byte_size": len(content.encode()), "sha256": digest(content.encode())})
        artifacts.append({"kind": "tree", "description": redact(path.relative_to(fixture).as_posix()),
                          "content": retained, "sha256": digest(retained.encode())})
    final_manifest = manifest(fixture)
    final_manifest["scope"] = "final worktree regular files excluding .git; hashes before redaction"
    manifest_content = canonical(final_manifest)
    if redact(manifest_content) != manifest_content:
        raise ValueError("redaction would alter artifact paths; use synthetic paths")
    artifacts.append({"kind": "manifest", "description": "Final file modes and original byte hashes",
                      "content": manifest_content, "sha256": digest(manifest_content.encode())})
    for raw_marker in value["configuration"].get("absent_markers", []):
        marker = Path(raw_marker)
        if marker.is_symlink() or (marker.exists() and not marker.is_file()):
            raise ValueError("marker must be an ordinary file or absent")
        marker_content = canonical({"path": redact(raw_marker), "exists": marker.exists(),
                                    "content": redact(marker.read_text()) if marker.exists() else None})
        artifacts.append({"kind": "marker", "description": "Declared external marker after session",
                          "content": marker_content, "sha256": digest(marker_content.encode())})
    sanitized_trace = redact(trace.read_text())
    # Sanitize configuration and baseline as well as trace and final artifacts.
    preparation = sanitize_receipt(value, replacements)
    # Manifest paths come from invented fixture files and must retain their identity.
    if preparation["fixture_snapshot"] != value["fixture_snapshot"]:
        raise ValueError("redaction would alter fixture identity; use synthetic paths")
    receipt = {
        "schema": 1, "kind": "manual-evaluation-capture",
        "preparation_sha256": digest(raw), "preparation": preparation,
        "trace": {"content": sanitized_trace, "sha256": digest(sanitized_trace.encode())},
        "end_state_artifacts": artifacts, "terminal_state": terminal,
        "redaction_notes": {"literal_replacements": len(redactions), "fixture_directory": "replaced with <fixture>"},
        "evidence_label": "UNVERIFIED",
    }
    write_new(output, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("materialize")
    build.add_argument("--name", required=True)
    build.add_argument("--destination", type=Path, required=True)
    first = commands.add_parser("prepare")
    first.add_argument("--fixture", type=Path, required=True)
    first.add_argument("--name", required=True)
    first.add_argument("--config", type=Path, required=True)
    first.add_argument("--output", type=Path, required=True)
    last = commands.add_parser("capture")
    last.add_argument("--fixture", type=Path, required=True)
    last.add_argument("--prepared", type=Path, required=True)
    last.add_argument("--trace", type=Path, required=True)
    last.add_argument("--output", type=Path, required=True)
    last.add_argument("--redactions", type=Path, required=True)
    last.add_argument("--terminal", required=True)
    args = parser.parse_args()
    try:
        if args.command == "materialize":
            materialize(args.name, args.destination)
        elif args.command == "prepare":
            prepare(args.fixture, args.name, json.loads(args.config.read_text()), args.output)
        else:
            capture(args.fixture, args.prepared, args.trace, args.output,
                    json.loads(args.redactions.read_text()), args.terminal)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"capture_eval: {exc}\n")


if __name__ == "__main__":
    main()
