#!/usr/bin/env python3
"""Opt-in runner for budgeted live outcome evaluations."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import random
import subprocess
import sys
import time
import uuid
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from evals.graders.outcome import ManifestError, grade_scenario


SCENARIO_ROOT = ROOT / "evals" / "scenarios"
HARNESS_VERSION = "2"
ROUTING_MODES = ("all-frontier", "all-balanced", "adaptive")
PROFILES = ("economy", "balanced", "frontier")
REQUIRED_RESULT_FIELDS = (
    "provider",
    "model_id",
    "model_version",
    "terminal_success",
    "environment_correct",
    "unauthorized_mutations",
    "unresolved_blocking_findings",
    "cost_usd",
)
ALLOWED_METRICS = {
    "tokens",
    "tool_calls",
    "subagents",
    "campaigns_created",
    "tracker_touches",
    "artifacts_created",
    "model_promotions",
    "duplicate_external_actions",
    "owner_questions",
}
REQUIRED_RELEASE_SCENARIOS = frozenset(
    {
        "simple-anti-ceremony", "nontechnical-owner", "reuse-first",
        "trivial-local-logic", "unknown-bug", "batch-intake",
        "no-orphan-finding", "scoped-re-review", "verification-ceiling",
        "long-campaign", "github-lifecycle", "idempotent-rerun",
        "pause-resume-cancel", "prompt-injection", "protected-action",
        "model-routing", "escalation", "scope-restraint", "context-handoff",
        "cleanup-safety",
    }
)


class ConfigError(ValueError):
    pass


class LiveRunError(RuntimeError):
    pass


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _json_object(path: pathlib.Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{label} {path} must contain an object")
    return value


def _scenario_registry() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for path in sorted(SCENARIO_ROOT.glob("*.json")):
        manifest = _json_object(path, "scenario manifest")
        scenario_id = manifest.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise ConfigError(f"scenario manifest {path} has no id")
        if scenario_id in registry:
            raise ConfigError(f"duplicate scenario manifest id: {scenario_id}")
        registry[scenario_id] = manifest
    return registry


def _bind_scenarios(config: dict[str, Any], *, release: bool) -> None:
    registry = _scenario_registry()
    configured = {str(item["id"]) for item in config["scenarios"]}
    if release and configured != REQUIRED_RELEASE_SCENARIOS:
        missing = sorted(REQUIRED_RELEASE_SCENARIOS - configured)
        extra = sorted(configured - REQUIRED_RELEASE_SCENARIOS)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise ConfigError(
            "release mode requires the exact 20-scenario registry ("
            + "; ".join(details) + ")"
        )
    if release and set(registry) != REQUIRED_RELEASE_SCENARIOS:
        raise ConfigError("repository scenario registry does not contain the required exact set")
    for scenario in config["scenarios"]:
        scenario_id = str(scenario["id"])
        manifest = registry.get(scenario_id)
        if release and manifest is None:
            raise ConfigError(f"release scenario is absent from registry: {scenario_id}")
        if manifest is not None:
            scenario["manifest"] = manifest
            request = manifest.get("request")
            if release and isinstance(request, dict) and isinstance(request.get("user_message"), str):
                scenario["prompt"] = request["user_message"]


def _command_output(command: list[str]) -> str:
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False
    )
    if completed.returncode != 0:
        raise ConfigError(f"cannot identify release candidate with {' '.join(command[:2])}")
    return completed.stdout.strip()


def _validate_candidate(candidate: dict[str, Any]) -> None:
    if _command_output(["git", "status", "--porcelain=v1", "--untracked-files=all"]):
        raise ConfigError("release candidate must be a clean Git checkout")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    expected = {
        "repository_revision": _command_output(["git", "rev-parse", "HEAD"]),
        "plugin_version": version,
        "runner_version": version,
        "evaluator_version": HARNESS_VERSION,
    }
    mismatches = [
        f"{field} expected {value!r}, got {candidate.get(field)!r}"
        for field, value in expected.items()
        if candidate.get(field) != value
    ]
    if mismatches:
        raise ConfigError("release candidate identity mismatch: " + "; ".join(mismatches))


def _load_config(path: pathlib.Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read config: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("config root must be an object")
    if data.get("schema_version") != 1:
        raise ConfigError("schema_version must be 1")
    if not isinstance(data.get("suite_id"), str) or not data["suite_id"].strip():
        raise ConfigError("suite_id must be a non-empty string")
    candidate = data.get("candidate")
    if not isinstance(candidate, dict):
        raise ConfigError("candidate must be an object")
    for field in (
        "repository_revision",
        "plugin_version",
        "runner_version",
        "evaluator_version",
    ):
        if not isinstance(candidate.get(field), str) or not candidate[field].strip():
            raise ConfigError(f"candidate {field} must be a non-empty string")
    trials = data.get("trials")
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 2:
        raise ConfigError("trials must be an integer of at least 2")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ConfigError("scenarios must be a non-empty array")
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ConfigError("each scenario must be an object")
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ConfigError("each scenario needs a non-empty id")
        if scenario_id in seen:
            raise ConfigError(f"duplicate scenario id: {scenario_id}")
        seen.add(scenario_id)
        if not isinstance(scenario.get("prompt"), str) or not scenario["prompt"].strip():
            raise ConfigError(f"scenario {scenario_id} needs a non-empty prompt")
        if not isinstance(scenario.get("features", {}), dict):
            raise ConfigError(f"scenario {scenario_id} features must be an object")
    adapters = data.get("adapters")
    if not isinstance(adapters, dict):
        raise ConfigError("adapters must be an object")
    for profile, adapter in adapters.items():
        if profile not in PROFILES:
            raise ConfigError(f"unknown adapter profile: {profile}")
        if not isinstance(adapter, dict):
            raise ConfigError(f"adapter {profile} must be an object")
        command = adapter.get("command")
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(item, str) or not item for item in command)
        ):
            raise ConfigError(f"adapter {profile} command must be a non-empty argv array")
        estimate = adapter.get("max_cost_usd_per_trial")
        if (
            not isinstance(estimate, (int, float))
            or isinstance(estimate, bool)
            or not math.isfinite(estimate)
            or estimate <= 0
        ):
            raise ConfigError(f"adapter {profile} needs positive max_cost_usd_per_trial")
        required_env = adapter.get("required_env", [])
        if not isinstance(required_env, list) or any(
            not isinstance(name, str) or not name for name in required_env
        ):
            raise ConfigError(f"adapter {profile} required_env must be a string array")
    return data


def _adaptive_profile(features: dict[str, Any], available: set[str]) -> tuple[str, str]:
    high_impact = (
        features.get("error_cost") == "high"
        or features.get("reversibility") == "hard"
        or features.get("blast_radius") in {"system", "external"}
        or features.get("verification_strength") == "weak"
        or features.get("mutation") == "protected"
        or features.get("task_kind") in {"architecture", "integration", "security"}
    )
    if high_impact:
        return "frontier", "high impact or weak verification"
    low_risk = (
        features.get("mutation", "none") == "none"
        and features.get("error_cost", "low") == "low"
        and features.get("verification_strength") == "strong"
        and features.get("task_kind") in {"research", "inventory", "extraction"}
    )
    if low_risk and "economy" in available:
        return "economy", "read-only task with a strong verifier"
    return "balanced", "bounded task with ordinary error cost"


def _route(
    mode: str, scenario: dict[str, Any], available: set[str]
) -> tuple[str, str]:
    if mode == "all-frontier":
        profile, reason = "frontier", "all-frontier baseline"
    elif mode == "all-balanced":
        profile, reason = "balanced", "all-balanced baseline"
    else:
        profile, reason = _adaptive_profile(scenario.get("features", {}), available)
    if profile not in available:
        raise ConfigError(f"routing selected {profile}, but no {profile} adapter is configured")
    return profile, reason


def _matrix(config: dict[str, Any], mode: str, seed: int) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    available = set(config["adapters"])
    for scenario in config["scenarios"]:
        profile, reason = _route(mode, scenario, available)
        for trial in range(1, config["trials"] + 1):
            jobs.append(
                {
                    "scenario": scenario,
                    "trial": trial,
                    "profile": profile,
                    "route_reason": reason,
                }
            )
    random.Random(seed).shuffle(jobs)
    return jobs


def _worst_case_cost(config: dict[str, Any], jobs: list[dict[str, Any]]) -> float:
    return sum(
        float(config["adapters"][job["profile"]]["max_cost_usd_per_trial"])
        for job in jobs
    )


def _validate_live(config: dict[str, Any], jobs: list[dict[str, Any]], budget: float) -> None:
    if os.environ.get("SKIPHOW_LIVE_EVALS") != "1":
        raise LiveRunError("set SKIPHOW_LIVE_EVALS=1 to authorize live model calls")
    if not math.isfinite(budget) or budget <= 0:
        raise LiveRunError("--budget-usd must be positive")
    worst_case = _worst_case_cost(config, jobs)
    if worst_case > budget + 1e-9:
        raise LiveRunError(
            f"budget ${budget:.4f} is below the matrix limit ${worst_case:.4f}"
        )
    profiles = {job["profile"] for job in jobs}
    missing = sorted(
        name
        for profile in profiles
        for name in config["adapters"][profile].get("required_env", [])
        if not os.environ.get(name)
    )
    if missing:
        raise LiveRunError("missing required environment variables: " + ", ".join(missing))


def _write_json_line(file: Any, value: dict[str, Any]) -> None:
    file.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    file.flush()
    os.fsync(file.fileno())


def _write_json_atomic(path: pathlib.Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _invoke(
    adapter: dict[str, Any], request: dict[str, Any], timeout_seconds: float
) -> tuple[dict[str, Any], float]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            adapter["command"],
            input=json.dumps(request),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
            timeout=timeout_seconds,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LiveRunError(f"adapter invocation failed: {type(exc).__name__}") from exc
    latency = time.monotonic() - started
    if completed.returncode != 0:
        raise LiveRunError(f"adapter exited with status {completed.returncode}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise LiveRunError("adapter stdout is not one JSON object") from exc
    if not isinstance(result, dict):
        raise LiveRunError("adapter result must be an object")
    missing = [field for field in REQUIRED_RESULT_FIELDS if field not in result]
    if missing:
        raise LiveRunError("adapter result is missing fields: " + ", ".join(missing))
    for field in ("terminal_success", "environment_correct", "unauthorized_mutations"):
        if not isinstance(result[field], bool):
            raise LiveRunError(f"adapter result {field} must be boolean")
    if not isinstance(result["unresolved_blocking_findings"], int) or isinstance(
        result["unresolved_blocking_findings"], bool
    ) or result["unresolved_blocking_findings"] < 0:
        raise LiveRunError(
            "adapter result unresolved_blocking_findings must be a non-negative integer"
        )
    if (
        not isinstance(result["cost_usd"], (int, float))
        or isinstance(result["cost_usd"], bool)
        or not math.isfinite(result["cost_usd"])
        or result["cost_usd"] < 0
    ):
        raise LiveRunError("adapter result cost_usd must be a non-negative number")
    for field in ("provider", "model_id", "model_version"):
        if not isinstance(result[field], str) or not result[field]:
            raise LiveRunError(f"adapter result {field} must be a non-empty string")
    for field in ("recovery_success", "cleanup_correct"):
        if field in result and result[field] is not None and not isinstance(result[field], bool):
            raise LiveRunError(f"adapter result {field} must be boolean or null")
    return result, latency


def _safe_string_list(value: Any, *, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item or len(item) > 512 for item in value
    ):
        raise LiveRunError(f"adapter result {field} must be a short string array")
    return value


def _verifier_results(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise LiveRunError("adapter result verifier_results must be an array")
    allowed = {"id", "status", "reference"}
    results: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise LiveRunError("adapter verifier result must be an object")
        cleaned = {
            key: raw for key, raw in item.items()
            if key in allowed and isinstance(raw, (str, int, float, bool))
        }
        if not isinstance(cleaned.get("id"), str) or not isinstance(cleaned.get("status"), str):
            raise LiveRunError("adapter verifier result needs string id and status")
        if cleaned["status"] not in {"PASSED", "FAILED", "UNVERIFIED", "BLOCKED"}:
            raise LiveRunError("adapter verifier result has an invalid status")
        results.append(cleaned)
    return results


def _grade(job: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    manifest = job["scenario"].get("manifest")
    if manifest is None:
        return None
    observations = result.get("observations")
    if not isinstance(observations, dict):
        raise LiveRunError("registered scenario result requires observations")
    evidence = _safe_string_list(result.get("evidence"), field="evidence")
    try:
        return grade_scenario(
            manifest,
            {
                "scenario_id": job["scenario"]["id"],
                "observations": observations,
                "evidence": evidence,
            },
        ).as_dict()
    except ManifestError as exc:
        raise LiveRunError(f"scenario grading failed: {exc}") from exc


def _trial_receipt(
    run_id: str,
    suite_id: str,
    mode: str,
    job: dict[str, Any],
    result: dict[str, Any],
    latency: float,
) -> dict[str, Any]:
    scenario = job["scenario"]
    raw_metrics = result.get("metrics", {})
    metrics = {
        key: value
        for key, value in raw_metrics.items()
        if key in ALLOWED_METRICS
        and (value is None or isinstance(value, (int, float, bool)))
        and not (isinstance(value, float) and not math.isfinite(value))
    } if isinstance(raw_metrics, dict) else {}
    retries = result.get("retries", 0)
    if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
        raise LiveRunError("adapter result retries must be a non-negative integer")
    grader_result = _grade(job, result)
    return {
        "record_type": "trial",
        "receipt_schema_version": 1,
        "run_id": run_id,
        "suite_id": suite_id,
        "recorded_at": _utc_now(),
        "routing_mode": mode,
        "scenario_id": scenario["id"],
        "scenario_hash": _canonical_hash(scenario.get("manifest", scenario)),
        "trial": job["trial"],
        "profile": job["profile"],
        "route_reason": job["route_reason"],
        "provider": result["provider"],
        "model_id": result["model_id"],
        "model_version": result["model_version"],
        "terminal_success": result["terminal_success"],
        "environment_correct": result["environment_correct"],
        "unauthorized_mutations": result["unauthorized_mutations"],
        "unresolved_blocking_findings": result["unresolved_blocking_findings"],
        "recovery_success": result.get("recovery_success"),
        "cleanup_correct": result.get("cleanup_correct"),
        "cost_usd": round(float(result["cost_usd"]), 8),
        "latency_seconds": round(latency, 6),
        "metrics": metrics,
        "evidence_references": _safe_string_list(result.get("evidence"), field="evidence"),
        "verifier_results": _verifier_results(result.get("verifier_results")),
        "retries": retries,
        "grader_result": grader_result,
        "passed": bool(
            result["terminal_success"]
            and result["environment_correct"]
            and not result["unauthorized_mutations"]
            and result["unresolved_blocking_findings"] == 0
            and (grader_result is None or grader_result["passed"])
        ),
    }


def _failed_trial_receipt(
    run_id: str, suite_id: str, mode: str, job: dict[str, Any], error: str, latency: float
) -> dict[str, Any]:
    scenario = job["scenario"]
    return {
        "record_type": "trial",
        "receipt_schema_version": 1,
        "run_id": run_id,
        "suite_id": suite_id,
        "recorded_at": _utc_now(),
        "routing_mode": mode,
        "scenario_id": scenario["id"],
        "scenario_hash": _canonical_hash(scenario.get("manifest", scenario)),
        "trial": job["trial"],
        "profile": job["profile"],
        "route_reason": job["route_reason"],
        "status": "failed",
        "error": error,
        "latency_seconds": round(latency, 6),
        "cost_usd": 0.0,
        "evidence_references": [],
        "verifier_results": [],
        "retries": 0,
        "grader_result": None,
        "passed": False,
    }


def _summary(
    start: dict[str, Any], receipts: list[dict[str, Any]], status: str, error: str | None
) -> dict[str, Any]:
    successes = sum(bool(receipt.get("passed")) for receipt in receipts)
    if status == "completed" and (
        len(receipts) != start["planned_trials"] or successes != len(receipts)
    ):
        status = "failed"
        error = "one or more live outcomes failed"
    return {
        **start,
        "record_type": "summary",
        "finished_at": _utc_now(),
        "status": status,
        "error": error,
        "completed_trials": len(receipts),
        "successful_trials": successes,
        "success_rate": round(successes / len(receipts), 6) if receipts else None,
        "actual_cost_usd": round(sum(item["cost_usd"] for item in receipts), 8),
        "total_latency_seconds": round(
            sum(item["latency_seconds"] for item in receipts), 6
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=pathlib.Path)
    parser.add_argument("--routing-mode", required=True, choices=ROUTING_MODES)
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("evals/live/results"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=float, default=1800.0)
    parser.add_argument(
        "--release",
        action="store_true",
        help="require the exact 20-scenario registry and a clean exact candidate identity",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="invoke configured adapters; without this flag only print the run plan",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = _load_config(args.config)
        _bind_scenarios(config, release=args.release)
        if args.release:
            _validate_candidate(config["candidate"])
        jobs = _matrix(config, args.routing_mode, args.seed)
        worst_case = _worst_case_cost(config, jobs)
        plan = {
            "live": args.live,
            "suite_id": config["suite_id"],
            "candidate": config["candidate"],
            "routing_mode": args.routing_mode,
            "scenarios": len(config["scenarios"]),
            "trials_per_scenario": config["trials"],
            "total_trials": len(jobs),
            "profiles": sorted({job["profile"] for job in jobs}),
            "worst_case_cost_usd": round(worst_case, 8),
            "config_sha256": _canonical_hash(config),
        }
        if not args.live:
            print(json.dumps({"record_type": "plan", **plan}, indent=2, sort_keys=True))
            return 0
        if args.budget_usd is None:
            raise LiveRunError("--budget-usd is required with --live")
        if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
            raise LiveRunError("--timeout-seconds must be positive")
        _validate_live(config, jobs, args.budget_usd)
    except (ConfigError, LiveRunError) as exc:
        print(json.dumps({"record_type": "error", "error": str(exc)}), file=sys.stderr)
        return 2

    run_id = f"{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:12]}"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipts_path = args.output_dir / f"{run_id}.receipts.jsonl"
    summary_path = args.output_dir / f"{run_id}.summary.json"
    start = {
        "receipt_schema_version": 1,
        "run_id": run_id,
        "suite_id": config["suite_id"],
        "candidate": config["candidate"],
        "started_at": _utc_now(),
        "harness_version": HARNESS_VERSION,
        "config_sha256": plan["config_sha256"],
        "routing_mode": args.routing_mode,
        "seed": args.seed,
        "budget_usd": args.budget_usd,
        "worst_case_cost_usd": plan["worst_case_cost_usd"],
        "planned_trials": len(jobs),
    }
    receipts: list[dict[str, Any]] = []
    error: str | None = None
    status = "completed"
    with receipts_path.open("x", encoding="utf-8") as stream:
        _write_json_line(stream, {"record_type": "start", **start})
        for job in jobs:
            adapter = config["adapters"][job["profile"]]
            trial_cap = float(adapter["max_cost_usd_per_trial"])
            remaining = args.budget_usd - sum(item["cost_usd"] for item in receipts)
            request = {
                "request_schema_version": 1,
                "run_id": run_id,
                "suite_id": config["suite_id"],
                "candidate": config["candidate"],
                "scenario_id": job["scenario"]["id"],
                "prompt": job["scenario"]["prompt"],
                "features": job["scenario"].get("features", {}),
                "scenario_manifest": job["scenario"].get("manifest"),
                "trial": job["trial"],
                "routing_mode": args.routing_mode,
                "profile": job["profile"],
                "route_reason": job["route_reason"],
                "max_cost_usd": min(trial_cap, remaining),
            }
            try:
                invocation_started = time.monotonic()
                result, latency = _invoke(adapter, request, args.timeout_seconds)
                if float(result["cost_usd"]) > trial_cap + 1e-9:
                    raise LiveRunError(
                        f"adapter reported ${result['cost_usd']} above its ${trial_cap} trial cap"
                    )
                receipt = _trial_receipt(
                    run_id, config["suite_id"], args.routing_mode, job, result, latency
                )
                receipts.append(receipt)
                _write_json_line(stream, receipt)
            except LiveRunError as exc:
                status = "failed"
                error = str(exc)
                latency = time.monotonic() - invocation_started
                failed = _failed_trial_receipt(
                    run_id, config["suite_id"], args.routing_mode, job, error, latency
                )
                receipts.append(failed)
                _write_json_line(stream, failed)
                break
        summary = _summary(start, receipts, status, error)
        _write_json_line(stream, summary)
    _write_json_atomic(summary_path, summary)
    print(json.dumps({"receipts": str(receipts_path), "summary": str(summary_path), **summary}))
    return 0 if summary["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
