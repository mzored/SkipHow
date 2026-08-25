#!/usr/bin/env python3
"""Validate or opt in to repository outcome evaluations."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "plugins/skiphow/evals"
OUTCOMES = EVAL_DIR / "outcome_scenarios.json"
ACTIVATION = EVAL_DIR / "activation_scenarios.json"
HOST_PROFILES = EVAL_DIR / "host_profiles.json"
MUTATIONS = EVAL_DIR / "policy_mutations.json"
SMOKE_IDS = {"clear-feature", "analysis-only", "tiny-auth-fix", "optional-verifier-unavailable", "host-without-subagents", "zero-config-no-persistence"}
SPEC = importlib.util.spec_from_file_location("skiphow_eval_shared", ROOT / "scripts/run_codex_evals.py")
assert SPEC and SPEC.loader
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)


def load(path: Path, *, minimum: int, versions: set[int] = {1}) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    scenarios = document.get("scenarios") if isinstance(document, dict) else None
    if document.get("schema_version") not in versions or not isinstance(scenarios, list):
        raise ValueError(f"invalid eval corpus: {path}")
    if len(scenarios) < minimum:
        raise ValueError(f"{path.name} needs at least {minimum} scenarios")
    identifiers = [row.get("id") for row in scenarios if isinstance(row, dict)]
    if len(identifiers) != len(scenarios) or len(identifiers) != len(set(identifiers)) or any(not value for value in identifiers):
        raise ValueError(f"{path.name} has missing or duplicate ids")
    return document


def load_host_profiles() -> dict[str, Any]:
    document = json.loads(HOST_PROFILES.read_text(encoding="utf-8"))
    capabilities, profiles = document.get("capabilities"), document.get("profiles")
    if document.get("schema_version") != 1 or not isinstance(capabilities, list) or not isinstance(profiles, dict):
        raise ValueError("invalid host_profiles.json")
    known = set(capabilities)
    if len(known) != len(capabilities) or not known:
        raise ValueError("host capabilities must be unique and non-empty")
    for name, profile in profiles.items():
        disabled = profile.get("disabled") if isinstance(profile, dict) else None
        if not isinstance(disabled, list) or not set(disabled) <= known:
            raise ValueError(f"host profile {name} has unknown disabled capabilities")
    return document


def validate_corpora() -> tuple[dict[str, Any], dict[str, Any]]:
    activation = load(ACTIVATION, minimum=10)
    outcomes = load(OUTCOMES, minimum=24, versions={2})
    profiles = load_host_profiles()["profiles"]
    if {row.get("category") for row in activation["scenarios"]} != {"direct", "indirect", "follow-up", "negative", "boundary"}:
        raise ValueError("activation corpus must cover all five categories")
    for scenario in outcomes["scenarios"]:
        graders = scenario.get("graders")
        if not isinstance(scenario.get("fixture"), dict) or not isinstance(scenario.get("prompt"), str):
            raise ValueError(f"outcome {scenario.get('id')} lacks fixture or prompt")
        if scenario.get("host_profile", "full") not in profiles:
            raise ValueError(f"outcome {scenario.get('id')} names an unknown host profile")
        if not isinstance(graders, dict) or not isinstance(graders.get("files", []), list) or "side_effects" not in graders:
            raise ValueError(f"outcome {scenario.get('id')} lacks semantic or side-effect graders")
        if any(not isinstance(row, dict) or not isinstance(row.get("path"), str) for row in graders.get("files", [])):
            raise ValueError(f"outcome {scenario.get('id')} has an invalid file grader")
    mutations = json.loads(MUTATIONS.read_text(encoding="utf-8"))
    if mutations.get("schema_version") != 2 or len(mutations.get("mutations", [])) < 5:
        raise ValueError("policy mutation corpus needs at least five mutations")
    for mutation in mutations["mutations"]:
        source = ROOT / mutation.get("source", "")
        if not source.is_file() or source.read_text(encoding="utf-8").count(mutation.get("target", "")) != 1:
            raise ValueError(f"policy mutation {mutation.get('id')} does not select one runtime passage")
    return activation, outcomes


def runtime_policy_failures(root: Path = ROOT) -> list[str]:
    """Check load-bearing semantics in the actual staged runtime Markdown."""
    def read(relative: str) -> str:
        return " ".join((root / relative).read_text(encoding="utf-8").lower().split())

    router = read("plugins/skiphow/skills/skiphow/SKILL.md")
    technical = read("plugins/skiphow/skills/skiphow/references/engineering/cto/references/technical-policy.md")
    review = read("plugins/skiphow/skills/skiphow/references/capabilities/technical-review/SKILL.md")
    rules = {
        "mutation_boundary": (router, r"requests are read-only.*permits no file.*remote mutation", r"may update files and trackers"),
        "no_automatic_campaign": (technical, r"blast radius.*change evidence and review, not execution shape", r"automatically selects a durable campaign"),
        "proportional_rereview": (review, r"re-review only the original findings, their fix diff.*do not restart review of untouched code", r"restart a full review of all code"),
        "verification_ceiling": (technical, r"mark the affected claim `unverified`.*do not build new validation infrastructure", r"build a replacement validator"),
        "verbatim_intent_alignment": (router, r"original request verbatim as normative input.*never replace, narrow, or extend it", r"agent-generated brief as normative"),
    }
    return [name for name, (text, required, forbidden) in rules.items() if not re.search(required, text) or re.search(forbidden, text)]


def apply_policy_mutation(root: Path, mutation: dict[str, str]) -> None:
    path = root / mutation["source"]
    text = path.read_text(encoding="utf-8")
    if text.count(mutation["target"]) != 1:
        raise ValueError(f"mutation {mutation['id']} target is not unique")
    path.write_text(text.replace(mutation["target"], mutation["replacement"]), encoding="utf-8")


def run(command: Sequence[str], *, cwd: Path, env: dict[str, str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(list(command), cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        def decoded(value: str | bytes | None) -> str:
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""

        return subprocess.CompletedProcess(
            list(command), 124, decoded(exc.stdout), decoded(exc.stderr) or f"timed out after {timeout} seconds"
        )


def write_fixture(repo: Path, fixture: dict[str, str]) -> None:
    for relative, contents in fixture.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "SkipHow eval"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "--allow-empty", "-m", "fixture"],
        cwd=repo,
        check=True,
    )


def _range_failure(label: str, value: int, bound: Any) -> str | None:
    if isinstance(bound, int):
        return None if value == bound else f"expected {label}={bound}, got {value}"
    if isinstance(bound, dict) and (value < bound.get("min", value) or value > bound.get("max", value)):
        return f"expected {label} in [{bound.get('min', '-inf')}, {bound.get('max', 'inf')}], got {value}"
    return None


def _unexpected_changes(repo: Path, file_graders: list[dict[str, Any]]) -> list[str]:
    if not (repo / ".git").exists():
        return []
    completed = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "-z"], cwd=repo, capture_output=True, check=False)
    if completed.returncode:
        return ["could not inspect repository scope"]
    allowed = [row["path"].rstrip("/") for row in file_graders if not row.get("unchanged") and row.get("exists") is not False]
    ephemeral = {".pytest_cache", "__pycache__", ".coverage"}
    unexpected: list[str] = []
    for entry in completed.stdout.decode("utf-8", errors="replace").split("\0"):
        if not entry:
            continue
        relative = entry[3:].split(" -> ")[-1]
        parts = set(Path(relative).parts)
        if parts & ephemeral or any(relative == path or relative.startswith(path + "/") for path in allowed):
            continue
        unexpected.append(relative)
    return unexpected


def grade(repo: Path, fixture: dict[str, str], graders: dict[str, Any], observation: dict[str, Any] | Path | None = None) -> list[str]:
    """Apply correctness as a hard gate; economy is reported, not graded."""
    if isinstance(observation, Path):
        calls = len(observation.read_text(encoding="utf-8").splitlines()) if observation.exists() else 0
        observation = {"commands": [], "metrics": {"tracker_touches": calls}, "final_response": ""}
    observation = observation or {}
    failures: list[str] = []
    for expected in graders.get("files", []):
        relative, path = expected["path"], repo / expected["path"]
        exists = path.exists()
        if expected.get("exists") is True and not exists:
            failures.append(f"missing {relative}")
            continue
        if expected.get("exists") is False and exists:
            failures.append(f"unexpected {relative}")
            continue
        content_keys = ("equals", "contains", "changed", "unchanged")
        if any(key in expected for key in content_keys) and (not exists or not path.is_file()):
            failures.append(f"missing file {relative}")
            continue
        if not path.is_file():
            continue
        text, original = path.read_text(encoding="utf-8"), fixture.get(relative)
        if "equals" in expected and text != expected["equals"]:
            failures.append(f"{relative} content mismatch")
        if expected.get("changed") and original is not None and text == original:
            failures.append(f"{relative} did not change")
        if expected.get("unchanged") and text != original:
            failures.append(f"{relative} changed")
        failures.extend(f"{relative} lacks {needle!r}" for needle in expected.get("contains", []) if needle not in text)
        failures.extend(f"{relative} contains forbidden text {needle!r}" for needle in expected.get("not_contains", []) if needle.lower() in text.lower())
        if "json_equals" in expected:
            try:
                value: Any = json.loads(text)
                for component in expected["json_equals"]["path"].split("."):
                    value = value[int(component)] if isinstance(value, list) else value[component]
                if value != expected["json_equals"]["value"]:
                    failures.append(f"{relative} JSON value mismatch")
            except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
                failures.append(f"{relative} lacks required JSON structure")
    for expected in graders.get("behavior", []):
        command = expected.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(value, str) for value in command):
            failures.append("invalid behavioral grader command")
            continue
        try:
            completed = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            failures.append(f"behavioral grader could not run: {exc}")
            continue
        if completed.returncode != expected.get("returncode", 0):
            failures.append(f"behavioral grader failed: {' '.join(command)}")
        if "stdout" in expected and completed.stdout.strip() != expected["stdout"]:
            failures.append(f"behavioral grader stdout mismatch: {' '.join(command)}")
    commands = observation.get("commands", [])
    command_text = "\n".join(str(row.get("command", row)) if isinstance(row, dict) else str(row) for row in commands)
    for expected in graders.get("commands", []):
        matches = [row for row in commands if re.search(expected["matches"], str(row.get("command", "")), re.I)]
        if not matches:
            failures.append(f"required command did not run: {expected['matches']}")
        elif expected.get("passed") and not any(row.get("returncode") == 0 for row in matches):
            failures.append(f"required command did not pass: {expected['matches']}")
    final = observation.get("final_response", "")
    final_grader = graders.get("final", {})
    failures.extend(f"final response lacks {needle!r}" for needle in final_grader.get("contains", []) if needle.lower() not in final.lower())
    failures.extend(f"final response contains forbidden claim {needle!r}" for needle in final_grader.get("not_contains", []) if needle.lower() in final.lower())
    alternatives = final_grader.get("contains_any", [])
    if alternatives and not any(value.lower() in final.lower() for value in alternatives):
        failures.append("final response lacks required semantic claim")
    if final_grader.get("required_limitation") and not re.search(r"blocked|cannot|can't|unverified|unavailable|need|requires?|pending", final, re.I):
        failures.append("final response lacks the required limitation or blocker")
    effects = graders.get("side_effects", {})
    failures.extend(f"unexpected out-of-scope change {relative}" for relative in _unexpected_changes(repo, graders.get("files", [])))
    failures.extend(f"unexpected artifact {relative}" for relative in effects.get("forbidden_paths", []) if (repo / relative).exists())
    failures.extend(f"forbidden command ran: {value}" for value in effects.get("forbidden_commands", []) if value.lower() in command_text.lower())
    failures.extend(f"required side effect did not occur: {value}" for value in effects.get("required_commands", []) if value.lower() not in command_text.lower())
    metrics = observation.get("metrics", {})
    aliases = {"owner_questions":"max_owner_questions", "tracker_touches":"max_tracker_touches", "campaign_starts":"max_campaign_starts", "durable_documents":"max_durable_documents", "subagents":"max_subagents", "full_reviews":"max_full_reviews", "rereviews":"max_rereviews"}
    for metric, maximum in aliases.items():
        value = metrics.get(metric)
        if value is None:
            if maximum in effects or metric in effects:
                failures.append(f"required metric unavailable: {metric}")
            continue
        if maximum in effects and value > effects[maximum]:
            failures.append(f"expected {metric}<={effects[maximum]}, got {value}")
        if metric in effects:
            failure = _range_failure(metric, value, effects[metric])
            if failure:
                failures.append(failure)
    return failures


def aggregate_trials(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        grouped.setdefault(row["id"], []).append(row)
    result: dict[str, Any] = {}
    for identifier, trials in grouped.items():
        passed = sum(row.get("returncode") == 0 and not row.get("failures") for row in trials)
        elapsed = [row["metrics"]["elapsed_seconds"] for row in trials]
        costs = [row["metrics"]["cost"] for row in trials if isinstance(row.get("metrics", {}).get("cost"), (int, float))]
        result[identifier] = {"trials":len(trials), "passed":passed, "pass_rate":passed / len(trials), "median_elapsed_seconds":statistics.median(elapsed), "median_cost":statistics.median(costs) if costs else None}
    return result


def build_receipt(*, commit: str, tree: str, host: str, cli_version: str, executable: str, installation_source: str, model: str, host_profile: str, eval_profile: str, trials: int, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "candidate": {"commit": commit, "tree": tree},
        "execution": {
            "host": host,
            "cli_version": cli_version,
            "executable": executable,
            "installation_source": installation_source,
            "model": model,
            "host_profile": host_profile,
            "eval_profile": eval_profile,
        },
        "trials": trials,
        "results": records,
        "aggregate": aggregate_trials(records),
    }


def _write_tool_shims(shim_dir: Path, command_log: Path, gh_log: Path, scenario_id: str) -> None:
    shim_dir.mkdir(parents=True)
    command_log.parent.mkdir(parents=True, exist_ok=True)
    gh_source = f'''#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
with open(os.environ["SKIPHOW_GH_LOG"], "a", encoding="utf-8") as stream:
    stream.write(" ".join(args) + "\\n")
scenario = os.environ.get("SKIPHOW_SCENARIO")
joined = " ".join(args)
if scenario == "project-over-100-no-duplicate" and "project view" in joined:
    print(json.dumps({{"id": "PVT_eval"}}))
elif scenario == "project-over-100-no-duplicate" and "project item-list" in joined:
    items = [{{"id": f"item-{{index}}", "content": {{"url": f"https://example.invalid/issues/{{index}}"}}, "Status": "Todo"}} for index in range(149)]
    items.append({{"id": "item-target", "content": {{"url": "https://example.invalid/issues/150"}}, "Status": "Done"}})
    print(json.dumps({{"totalCount": 150, "items": items}}))
elif "issue list" in joined:
    print("[]")
elif "repo view" in joined:
    print('{{"nameWithOwner":"owner/repo"}}')
elif "issue create" in joined or "issue comment" in joined:
    print("https://example.invalid/issues/1")
'''
    gh = shim_dir / "gh"
    gh.write_text(gh_source, encoding="utf-8")
    gh.chmod(0o755)
    for name in ("pytest", "python", "python3", "git"):
        executable = shutil.which(name)
        if not executable:
            continue
        script = shim_dir / name
        script.write_text(
            "#!/bin/sh\n"
            f"{shlex.quote(executable)} \"$@\"\n"
            "status=$?\n"
            f"printf '%s\\t%s %s\\n' \"$status\" {shlex.quote(name)} \"$*\" >> \"$SKIPHOW_COMMAND_LOG\"\n"
            "exit \"$status\"\n",
            encoding="utf-8",
        )
        script.chmod(0o755)


def _observation(host: str, completed: subprocess.CompletedProcess[str], elapsed: float, command_log: Path, gh_log: Path, repo: Path) -> dict[str, Any]:
    commands: list[dict[str, Any]] = []
    final = completed.stdout
    metrics: dict[str, Any] = {
        "elapsed_seconds": elapsed,
        "tracker_touches": 0,
        "campaign_starts": int((repo / ".skiphow/runs").exists()),
        "subagents": 0 if host == "codex" else None,
        "full_reviews": 0 if host == "codex" else None,
        "rereviews": 0 if host == "codex" else None,
        "command_evidence": "AVAILABLE" if host == "codex" else "SHIMMED_COMMANDS_ONLY",
        "tool_evidence": "AVAILABLE" if host == "codex" else "UNAVAILABLE",
    }
    if command_log.exists():
        for line in command_log.read_text(encoding="utf-8").splitlines():
            status, separator, command = line.partition("\t")
            if separator:
                commands.append({"command": command, "returncode": int(status) if status.isdigit() else None})
    if gh_log.exists():
        gh_commands = gh_log.read_text(encoding="utf-8").splitlines()
        commands.extend({"command":f"gh {line}", "returncode":0} for line in gh_commands)
        metrics["tracker_touches"] = len(gh_commands)
    if host == "codex":
        extracted = shared.codex_metrics(completed.stdout)
        metrics["tool_calls"] = extracted["tool_calls"]
        if isinstance(extracted.get("usage"), dict):
            metrics["tokens"] = sum(value for value in extracted["usage"].values() if isinstance(value, int))
        messages: list[str] = []
        for line in completed.stdout.splitlines():
            try:
                item = json.loads(line).get("item", {})
            except json.JSONDecodeError:
                continue
            if item.get("type") == "command_execution":
                commands.append({"command":item.get("command", ""), "returncode":item.get("exit_code")})
            elif item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                messages.append(item["text"])
            elif item.get("type") == "collaboration_tool_call":
                event_text = json.dumps(item, sort_keys=True).lower()
                if "spawn_agent" in event_text:
                    metrics["subagents"] += 1
                    if re.search(r"re-?review|scoped review", event_text):
                        metrics["rereviews"] += 1
                    elif "review" in event_text:
                        metrics["full_reviews"] += 1
        if messages:
            final = messages[-1]
    else:
        try:
            document = json.loads(completed.stdout)
            final = str(document.get("result", document.get("structured_output", "")))
            if isinstance(document.get("total_cost_usd"), (int, float)):
                metrics["cost"] = document["total_cost_usd"]
            if isinstance(document.get("num_turns"), int):
                metrics["turns"] = document["num_turns"]
            if isinstance(document.get("usage"), dict):
                metrics["tokens"] = sum(value for value in document["usage"].values() if isinstance(value, int))
        except json.JSONDecodeError:
            pass
    metrics["owner_questions"] = final.count("?")
    metrics["durable_documents"] = sum(1 for path in (repo / ".skiphow").rglob("*") if path.is_file()) if (repo / ".skiphow").exists() else 0
    return {"commands":commands, "final_response":final, "metrics":metrics}


def run_live(host: str, executable: str, *, profile: str, trials: int, model: str, host_profile_label: str, output: Path | None, scenario_timeout: int = 300, codex_marketplace_source: str | None = None, codex_auth_file: Path | None = None) -> int:
    _, outcomes = validate_corpora()
    executable_path = shutil.which(executable) or executable
    try:
        version_result = subprocess.run([executable_path, "--version"], capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"run_outcome_evals: cannot identify host version: {exc}", file=sys.stderr)
        return 2
    host_version = (version_result.stdout or version_result.stderr).strip()
    if version_result.returncode or not host_version:
        print("run_outcome_evals: host --version did not return a version", file=sys.stderr)
        return 2
    selected = [row for row in outcomes["scenarios"] if profile == "release" or row["id"] in SMOKE_IDS]
    profiles = load_host_profiles()["profiles"]
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="skiphow-outcomes-") as temporary:
        root = Path(temporary)
        try:
            commit, tree, candidate = shared.snapshot_candidate(root)
        except ValueError as exc:
            print(f"run_outcome_evals: {exc}", file=sys.stderr)
            return 2
        runtime, host_home = root / "runtime", root / "host-home"
        shared.stage_runtime(candidate, runtime)
        host_home.mkdir()
        base_env = os.environ.copy()
        installation_source = "isolated staged candidate"
        if host == "codex":
            if codex_auth_file:
                if not codex_auth_file.is_file():
                    print("run_outcome_evals: configured Codex auth file is unavailable", file=sys.stderr)
                    return 2
                shutil.copy2(codex_auth_file, host_home / "auth.json")
            marketplace_source = codex_marketplace_source or str(runtime)
            installation_source = marketplace_source
            if codex_marketplace_source:
                remote = run(
                    ["git", "ls-remote", codex_marketplace_source, "HEAD"],
                    cwd=root,
                    env=base_env,
                )
                parts = remote.stdout.split()
                remote_commit = parts[0] if remote.returncode == 0 and parts else None
                if remote_commit != commit:
                    print(
                        "run_outcome_evals: remote marketplace HEAD does not match the candidate commit",
                        file=sys.stderr,
                    )
                    return 2
            base_env["CODEX_HOME"] = str(host_home)
            for command in ([executable,"plugin","marketplace","add",marketplace_source,"--json"], [executable,"plugin","add","skiphow@skiphow","--json"]):
                completed = run(command, cwd=root, env=base_env)
                if completed.returncode:
                    print(completed.stdout + completed.stderr, file=sys.stderr)
                    return 2
        else:
            base_env["CLAUDE_CONFIG_DIR"] = str(host_home)
        for trial in range(1, trials + 1):
            for scenario in selected:
                repo = root / f"trial-{trial}" / scenario["id"]
                repo.mkdir(parents=True)
                write_fixture(repo, scenario["fixture"])
                shim_dir = root / "shims" / f"trial-{trial}" / scenario["id"]
                command_log = root / "command-logs" / f"trial-{trial}" / scenario["id"]
                gh_log = root / "gh-logs" / f"trial-{trial}" / scenario["id"]
                _write_tool_shims(shim_dir, command_log, gh_log, scenario["id"])
                environment = dict(base_env)
                environment["PATH"] = f"{shim_dir}{os.pathsep}{environment.get('PATH', '')}"
                environment["SKIPHOW_GH_LOG"] = str(gh_log)
                environment["SKIPHOW_COMMAND_LOG"] = str(command_log)
                environment["SKIPHOW_SCENARIO"] = scenario["id"]
                host_profile = profiles[scenario.get("host_profile", "full")]
                prompt = scenario["prompt"] + "\n\nEnvironment note: " + host_profile["notice"]
                command = [executable,"exec","--ephemeral","--sandbox","workspace-write","--model",model,"--json",prompt] if host == "codex" else [executable,"--plugin-dir",str(runtime),"--print","--no-session-persistence","--permission-mode","dontAsk","--model",model,"--output-format","json",prompt]
                started = time.monotonic()
                completed = run(command, cwd=repo, env=environment, timeout=scenario_timeout)
                observation = _observation(host, completed, time.monotonic() - started, command_log, gh_log, repo)
                record = {"id":scenario["id"], "trial":trial, "returncode":completed.returncode, "failures":grade(repo, scenario["fixture"], scenario["graders"], observation), "final_response":observation["final_response"], "metrics":observation["metrics"]}
                if completed.returncode:
                    record["host_error"] = (completed.stderr or completed.stdout)[-4000:]
                records.append(record)
    receipt = build_receipt(commit=commit, tree=tree, host=host, cli_version=host_version, executable=str(Path(executable_path).resolve()), installation_source=installation_source, model=model, host_profile=host_profile_label, eval_profile=profile, trials=trials, records=records)
    payload = json.dumps(receipt, indent=2, sort_keys=True)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if all(row["pass_rate"] == 1.0 for row in receipt["aggregate"].values()) else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="run paid live outcome evaluations")
    parser.add_argument("--host", choices=("codex", "claude"))
    parser.add_argument("--executable")
    parser.add_argument("--profile", choices=("smoke", "release"), default="smoke")
    parser.add_argument("--trials", type=int)
    parser.add_argument("--model", help="exact model identifier passed to the host")
    parser.add_argument("--host-profile-label", help="explicit label for the host configuration under test")
    parser.add_argument("--codex-marketplace-source", help="remote Codex marketplace whose HEAD matches the candidate")
    parser.add_argument("--codex-auth-file", type=Path, help="credential file copied into the isolated Codex home")
    parser.add_argument("--scenario-timeout", type=int, default=300)
    parser.add_argument("--output", type=Path, help="write the JSON receipt to this path")
    args = parser.parse_args(argv)
    try:
        activation, outcomes = validate_corpora()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"run_outcome_evals: {exc}", file=sys.stderr)
        return 2
    if not args.execute:
        print(f"validated {len(activation['scenarios'])} activation and {len(outcomes['scenarios'])} outcome scenarios offline")
        return 0
    if not args.host:
        print("run_outcome_evals: --execute requires --host", file=sys.stderr)
        return 2
    if not args.model or not args.host_profile_label:
        print("run_outcome_evals: live evaluation requires --model and --host-profile-label", file=sys.stderr)
        return 2
    if args.scenario_timeout < 1:
        print("run_outcome_evals: --scenario-timeout must be positive", file=sys.stderr)
        return 2
    trials = args.trials if args.trials is not None else (3 if args.profile == "release" else 1)
    if trials < 1 or (args.profile == "release" and trials < 3) or (args.profile == "smoke" and trials != 1):
        print("run_outcome_evals: smoke requires one trial; release requires at least three", file=sys.stderr)
        return 2
    if args.profile == "release" and args.output is None:
        print("run_outcome_evals: release evaluation requires --output for its receipt", file=sys.stderr)
        return 2
    return run_live(args.host, args.executable or args.host, profile=args.profile, trials=trials, model=args.model, host_profile_label=args.host_profile_label, output=args.output, scenario_timeout=args.scenario_timeout, codex_marketplace_source=args.codex_marketplace_source, codex_auth_file=args.codex_auth_file)


if __name__ == "__main__":
    raise SystemExit(main())
