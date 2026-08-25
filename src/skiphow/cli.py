"""Command-line control for durable SkipHow runs."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Sequence

from . import __version__
from .adapters import (
    ClaudeAdapter,
    ClaudeAgentSdkTransport,
    ClaudeCliTransport,
    CodexAdapter,
    CodexAppServerTransport,
    ModelInfo,
    PermissionMode,
    ProviderError,
    create_claude_transport,
)
from .config import (
    ConfigError,
    ProjectConfig,
    load_personal_config,
    load_project_config,
)
from .intake import (
    Candidate,
    DuplicateDisposition,
    LocalIntakeStore,
    Recommendation,
    WorkItem,
    actionable_work_items,
    atomize,
    decide_candidate,
    find_candidates,
    group_signals,
    map_epic,
)
from .github_delivery import (
    DeliveryError,
    DeliveryPlan,
    GhDeliveryBackend,
    GitHubDeliveryCoordinator,
)
from .model_routing import SemanticProfile
from .runner import DurableRunner
from .schemas import RUN_TERMINAL
from .supervisor import CampaignSupervisor, SupervisionLimits, route_provider_catalog
from .verification import EnvironmentVerifier


def _database(project: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = Path(explicit).resolve()
        try:
            candidate.relative_to(project.resolve())
        except ValueError as exc:
            raise ConfigError("database must remain inside the project") from exc
        return candidate
    return load_project_config(project).run_root(project) / "runner.sqlite3"


def _runner(args: argparse.Namespace) -> DurableRunner:
    return DurableRunner(
        _database(args.project_root, args.database),
        parallelism=getattr(args, "parallelism", 1),
    )


def _emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str, ensure_ascii=False))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _intake_candidates(
    item: WorkItem,
    signals_by_id: dict[str, Any],
    existing: Sequence[WorkItem],
) -> list[Candidate]:
    candidates: dict[str, Candidate] = {}
    for signal_id in item.signal_ids:
        for candidate in find_candidates(signals_by_id[signal_id], existing):
            current = candidates.get(candidate.item_id)
            if current is None or candidate.score > current.score:
                candidates[candidate.item_id] = candidate
    return sorted(candidates.values(), key=lambda value: (-value.score, value.item_id))[:20]


def _intake_epic(value: Any, children: Sequence[WorkItem]) -> tuple[WorkItem, tuple[WorkItem, ...]]:
    if not isinstance(value, dict):
        raise ValueError("intake epic must be an object")
    child_ids_value = value.get("children", [item.item_id for item in children])
    if isinstance(child_ids_value, (str, bytes)) or not isinstance(child_ids_value, list):
        raise ValueError("intake epic children must be a list of work item IDs")
    by_id = {item.item_id: item for item in children}
    if not all(isinstance(item_id, str) and item_id in by_id for item_id in child_ids_value):
        raise ValueError("intake epic refers to an unavailable child")
    selected = [by_id[item_id] for item_id in child_ids_value]
    acceptance = value.get("acceptance", [])
    if isinstance(acceptance, (str, bytes)) or not isinstance(acceptance, list):
        raise ValueError("intake epic acceptance must be a list of strings")
    if not all(isinstance(entry, str) and entry.strip() for entry in acceptance):
        raise ValueError("intake epic acceptance must contain non-empty strings")
    non_goals = value.get("non_goals", [])
    if isinstance(non_goals, (str, bytes)) or not isinstance(non_goals, list):
        raise ValueError("intake epic non_goals must be a list of strings")
    if not all(isinstance(entry, str) for entry in non_goals):
        raise ValueError("intake epic non_goals must contain strings")
    epic = WorkItem(
        item_id=value.get("item_id", ""),
        title=value.get("title", ""),
        signal_ids=tuple(
            dict.fromkeys(signal_id for item in selected for signal_id in item.signal_ids)
        ),
        outcome=value.get("outcome", ""),
        why=value.get("why", ""),
        acceptance=tuple(acceptance),
        non_goals=tuple(non_goals),
        recommendation=Recommendation(value.get("recommendation", "INVESTIGATE")),
    )
    dependencies = value.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise ValueError("intake epic dependencies must be an object")
    return map_epic(epic, selected, dependencies=dependencies)


def _run_intake(args: argparse.Namespace) -> dict[str, Any]:
    project_config = load_project_config(args.project_root)
    if project_config.tracker == "github":
        raise ConfigError(
            "the configured GitHub tracker requires the SkipHow plugin Intake workflow; "
            "the local CLI will not substitute .skiphow/intake"
        )
    if project_config.tracker == "none" and args.persist:
        raise ConfigError("intake persistence is disabled by tracker=none")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        records: Any = payload
        decisions_value: Any = []
        epic_value: Any = None
    elif isinstance(payload, dict):
        if "signals" not in payload:
            raise ValueError("intake object must contain signals")
        records = payload["signals"]
        decisions_value = payload.get("decisions", [])
        epic_value = payload.get("epic")
    else:
        raise ValueError("intake input must be a JSON array or object")
    if not isinstance(decisions_value, list):
        raise ValueError("intake decisions must be a list")

    signals = atomize(records, default_source=args.source)
    signals_by_id = {signal.signal_id: signal for signal in signals}
    groups = group_signals(signals)
    proposals = actionable_work_items(signals, groups)
    store = (
        LocalIntakeStore(args.project_root)
        if project_config.tracker != "none"
        else None
    )
    existing = store.work_items() if store is not None else []
    existing_by_id = {item.item_id: item for item in existing}

    decisions: dict[str, dict[str, Any]] = {}
    for raw in decisions_value:
        if not isinstance(raw, dict) or not isinstance(raw.get("item_id"), str):
            raise ValueError("every intake decision needs a work item ID")
        item_id = raw["item_id"]
        if item_id in decisions:
            raise ValueError(f"duplicate intake decision: {item_id}")
        decisions[item_id] = raw

    statuses: dict[str, str] = {}
    candidate_output: dict[str, list[dict[str, Any]]] = {}
    selected: list[WorkItem] = []
    provenance_updates: list[WorkItem] = []
    for item in proposals:
        candidates = _intake_candidates(item, signals_by_id, existing)
        candidate_output[item.item_id] = [
            {"item_id": candidate.item_id, "title": candidate.title, "score": candidate.score}
            for candidate in candidates
        ]
        current = existing_by_id.get(item.item_id)
        if current is not None:
            comparable = (
                replace(current, parent_id=None, dependencies=(), is_epic=False)
                if epic_value is not None
                else current
            )
            if comparable.to_dict() != item.to_dict():
                raise ValueError(f"work item identity collision: {item.item_id}")
            statuses[item.item_id] = "UNCHANGED"
            selected.append(item)
            continue
        raw_decision = decisions.pop(item.item_id, None)
        if raw_decision is None:
            if candidates:
                statuses[item.item_id] = "UNRESOLVED"
                continue
            statuses[item.item_id] = "CREATE"
            selected.append(item)
            continue
        disposition = DuplicateDisposition(raw_decision.get("disposition"))
        candidate_item_id = raw_decision.get("candidate_item_id")
        if candidate_item_id is not None and not isinstance(candidate_item_id, str):
            raise ValueError("candidate_item_id must be a string")
        reason = raw_decision.get("reason")
        if not isinstance(reason, str):
            raise ValueError("intake decision needs a reason")
        decide_candidate(
            signals_by_id[item.signal_ids[0]],
            candidates,
            candidate_item_id,
            disposition,
            reason,
        )
        if disposition in {DuplicateDisposition.DUPLICATE, DuplicateDisposition.UPDATE}:
            target = existing_by_id[candidate_item_id]
            provenance_updates.append(
                replace(
                    target,
                    signal_ids=tuple(dict.fromkeys((*target.signal_ids, *item.signal_ids))),
                    evidence=tuple(dict.fromkeys((*target.evidence, *item.evidence))),
                    relationships=tuple(
                        dict.fromkeys((*target.relationships, f"{disposition.value.lower()}:{item.item_id}"))
                    ),
                )
            )
            statuses[item.item_id] = disposition.value
        elif disposition is DuplicateDisposition.NEEDS_RESEARCH:
            statuses[item.item_id] = "UNRESOLVED"
        else:
            if disposition is DuplicateDisposition.RELATED and candidate_item_id is not None:
                item = replace(
                    item,
                    relationships=tuple(
                        dict.fromkeys((*item.relationships, f"related:{candidate_item_id}"))
                    ),
                )
            statuses[item.item_id] = disposition.value
            selected.append(item)
    if decisions:
        raise ValueError(f"intake decision refers to an unknown proposal: {sorted(decisions)[0]}")

    epic_summary: dict[str, Any] | None = None
    if epic_value is not None:
        epic, mapped = _intake_epic(epic_value, selected)
        selected_by_id = {item.item_id: item for item in selected}
        for child in mapped:
            selected_by_id[child.item_id] = child
        selected = list(selected_by_id.values())
        selected.append(epic)
        statuses[epic.item_id] = (
            "UNCHANGED" if epic.item_id in existing_by_id else "CREATE"
        )
        epic_summary = {
            "item_id": epic.item_id,
            "children": [item.item_id for item in mapped],
            "dependencies": {item.item_id: list(item.dependencies) for item in mapped},
        }

    result: dict[str, Any] = {
        "persisted": False,
        "count": len(signals),
        "signals": [signal.to_dict() for signal in signals],
        "work_items": [item.to_dict() for item in proposals],
        "candidates": candidate_output,
        "dispositions": dict(sorted(statuses.items())),
        "epic": epic_summary,
        "summary": {
            "signals": len(signals),
            "signal_types": dict(sorted(Counter(signal.kind.value for signal in signals).items())),
            "observed": sum(bool(signal.observed_evidence) for signal in signals),
            "speculative": sum(not signal.observed_evidence for signal in signals),
            "groups": len(groups),
            "actionable": len(proposals),
            "dispositions": dict(sorted(Counter(statuses.values()).items())),
            "recommendations": dict(
                sorted(Counter(item.recommendation.value for item in proposals).items())
            ),
        },
    }
    if args.persist:
        if store is None:
            raise ConfigError("intake persistence is disabled")
        result["store"] = store.persist(
            signals,
            selected,
            provenance_updates=provenance_updates,
        )
        result["persisted"] = True
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skiphow")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--database", help="runner database path inside the project")
    commands = parser.add_subparsers(dest="command", required=True)

    setup = commands.add_parser("setup", help="write product-level project preferences")
    setup.add_argument("--tracker", choices=("auto", "none", "github", "local"), default="auto")
    setup.add_argument("--project")
    setup.add_argument("--merge-policy", choices=("never", "when_green", "when_green_and_approved", "auto_merge_or_queue"), default="never")
    setup.add_argument("--cleanup", choices=("merged_only", "never"), default="merged_only")
    setup.add_argument("--findings", choices=("local", "tracker", "ask", "off"), default="local")
    setup.add_argument("--campaign-root", default=".skiphow/runs")
    setup.add_argument("--cost-preference", choices=("auto", "economy", "balanced", "quality"))
    setup.add_argument("--max-cost", type=float)
    setup.add_argument("--max-duration", type=int)
    setup.add_argument("--max-parallelism", type=int)

    start = commands.add_parser("start", help="create a durable run")
    start.add_argument("request", help="original user request, preserved verbatim")
    start.add_argument("--task", action="append", default=[], help="initial task outcome")
    start.add_argument("--authority", default="{}", help="JSON authority record")
    start.add_argument("--budget", default="{}", help="JSON budget record")
    start.add_argument("--run-id")
    start.add_argument("--parallelism", type=int, default=1)

    intake = commands.add_parser("intake", help="atomize and optionally persist product signals")
    intake.add_argument(
        "input",
        type=Path,
        help="JSON signal array or intake object with signals, decisions, and optional Epic",
    )
    intake.add_argument("--source", default="owner-request")
    intake.add_argument("--persist", action="store_true", help="write the project-local intake ledger")

    add = commands.add_parser("add-task", help="append a task to a run")
    add.add_argument("run_id")
    add.add_argument("outcome")
    add.add_argument("--task-id")
    add.add_argument("--depends-on", action="append", default=[])
    add.add_argument("--constraint", action="append", default=[])
    add.add_argument("--priority", type=int, default=0)

    delivery = commands.add_parser(
        "github-deliver",
        help="reconcile one authorized campaign delivery through GitHub",
    )
    delivery.add_argument("run_id")
    delivery.add_argument("--operation-id", required=True)
    delivery.add_argument("--task-id", required=True)
    delivery.add_argument("--repo", required=True)
    delivery.add_argument("--issue", required=True, type=int)
    delivery.add_argument("--branch", required=True)
    delivery.add_argument("--base", default="main")
    delivery.add_argument("--expected-head", required=True)
    delivery.add_argument("--owner", required=True)
    delivery.add_argument("--title", required=True)
    delivery.add_argument("--body", required=True)
    delivery.add_argument("--required-check", action="append", default=[])
    delivery.add_argument(
        "--merge-policy",
        required=True,
        choices=("when_green", "when_green_and_approved"),
    )

    for name in ("execute", "worker"):
        execute = commands.add_parser(
            name,
            help=(
                "supervise a run to a settled state"
                if name == "execute"
                else "process one ready frontier"
            ),
        )
        execute.add_argument("run_id")
        execute.add_argument("--provider", choices=("auto", "codex", "claude"), default="auto")
        execute.add_argument("--model")
        execute.add_argument(
            "--profile",
            choices=tuple(profile.value for profile in SemanticProfile),
            default=SemanticProfile.BALANCED.value,
        )
        execute.add_argument("--worker-id")
        execute.add_argument("--parallelism", type=int, default=1)
        execute.add_argument("--max-duration", type=float)
        execute.add_argument("--max-cost", type=float)
        execute.add_argument("--lease-seconds", type=float, default=900)
        execute.add_argument("--poll-interval", type=float, default=1)
        execute.add_argument(
            "--permissions",
            choices=tuple(mode.value for mode in PermissionMode),
            default=PermissionMode.WORKSPACE_WRITE.value,
        )
        execute.add_argument(
            "--verification-plan",
            type=Path,
            help="trusted JSON environment checks, required for write-capable execution",
        )

    for name in ("status", "pause", "resume", "cancel", "reconcile", "export"):
        command = commands.add_parser(name)
        command.add_argument("run_id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "setup":
            if args.project is not None and not re.fullmatch(
                r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[1-9][0-9]*",
                args.project,
            ):
                raise ValueError("project must be an owner/number value")
            ProjectConfig(
                tracker=args.tracker,
                project=args.project,
                merge_policy=args.merge_policy,
                cleanup=args.cleanup,
                findings_persist=args.findings,
                campaign_root=args.campaign_root,
            ).run_root(args.project_root)
            if args.max_cost is not None and args.max_cost < 0:
                raise ValueError("max cost cannot be negative")
            if args.max_duration is not None and args.max_duration <= 0:
                raise ValueError("max duration must be positive")
            if args.max_parallelism is not None and args.max_parallelism <= 0:
                raise ValueError("max parallelism must be positive")
            project_value = {
                "schema_version": 2,
                "tracker": {"type": args.tracker, "project": args.project},
                "delivery": {"merge_policy": args.merge_policy, "cleanup": args.cleanup},
                "findings": {"persist": args.findings},
                "campaign_root": args.campaign_root,
            }
            project_path = args.project_root / ".skiphow" / "config.json"
            backup: str | None = None
            if project_path.is_file():
                current_text = project_path.read_text(encoding="utf-8")
                current = json.loads(current_text)
                if not isinstance(current, dict):
                    raise ValueError("existing project configuration must be an object")
                if current.get("schema_version") != 2:
                    backup_path = project_path.with_suffix(".json.v1.bak")
                    if not backup_path.exists():
                        backup_path.write_text(current_text, encoding="utf-8")
                    backup = str(backup_path)
            _write_json(project_path, project_value)
            personal_written = False
            if any(value is not None for value in (args.cost_preference, args.max_cost, args.max_duration, args.max_parallelism)):
                config_home = Path(os.environ.get("SKIPHOW_CONFIG_HOME", Path.home() / ".config" / "skiphow"))
                personal_path = config_home / "config.json"
                personal = {
                    "execution_preference": "auto",
                    "cost_preference": args.cost_preference or "balanced",
                    "max_cost_per_run": args.max_cost,
                    "max_duration": args.max_duration,
                    "max_parallelism": args.max_parallelism or "auto",
                    "providers": {},
                }
                _write_json(personal_path, personal)
                personal_written = True
            _emit({"project_config": str(project_path), "backup": backup, "personal_config_written": personal_written})
            return 0
        if args.command == "intake":
            _emit(_run_intake(args))
            return 0
        runner = _runner(args)
        if args.command == "start":
            authority = json.loads(args.authority)
            budget = json.loads(args.budget)
            if not isinstance(authority, dict) or not isinstance(budget, dict):
                raise ValueError("authority and budget must be JSON objects")
            run = runner.start(
                args.request, authority, budget=budget, run_id=args.run_id
            )
            for outcome in args.task:
                runner.add_task(run.run_id, outcome)
            _emit(runner.status(run.run_id))
        elif args.command == "add-task":
            task = runner.add_task(
                args.run_id,
                args.outcome,
                task_id=args.task_id,
                dependencies=tuple(args.depends_on),
                constraints=tuple(args.constraint),
                priority=args.priority,
            )
            _emit(task.to_dict())
        elif args.command == "github-deliver":
            plan = DeliveryPlan(
                operation_id=args.operation_id,
                task_id=args.task_id,
                repo=args.repo,
                issue=args.issue,
                branch=args.branch,
                base=args.base,
                expected_head=args.expected_head,
                owner=args.owner,
                title=args.title,
                body=args.body,
                required_checks=tuple(args.required_check),
                merge_policy=args.merge_policy,
            )
            coordinator = GitHubDeliveryCoordinator(
                runner.store,
                GhDeliveryBackend(args.project_root),
            )
            _emit(coordinator.advance(args.run_id, plan))
        elif args.command == "status":
            _emit(runner.status(args.run_id))
        elif args.command == "pause":
            _control_checkpoint(runner, args.run_id, "pause")
            _emit(runner.pause(args.run_id).to_dict())
        elif args.command == "resume":
            _control_checkpoint(runner, args.run_id, "resume")
            _emit(runner.resume(args.run_id).to_dict())
        elif args.command == "cancel":
            _control_checkpoint(runner, args.run_id, "cancel")
            _emit(runner.cancel(args.run_id).to_dict())
        elif args.command in {"execute", "worker"}:
            _emit(asyncio.run(_supervise(args, runner, once=args.command == "worker")))
        elif args.command == "reconcile":
            _emit(runner.reconcile(args.run_id))
        elif args.command == "export":
            _emit(runner.store.export_run(args.run_id))
        return 0
    except (
        ConfigError,
        DeliveryError,
        ProviderError,
        ValueError,
        KeyError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"skiphow: {exc}", file=sys.stderr)
        return 2


def _control_checkpoint(runner: DurableRunner, run_id: str, action: str) -> None:
    """Persist operator intent before a control transition changes scheduling."""
    run = runner.store.get_run(run_id)
    if run.status not in RUN_TERMINAL:
        runner.store.checkpoint(
            run_id,
            "control_requested",
            {"action": action, "status_before": run.status.value},
        )


async def _supervise(
    args: argparse.Namespace, runner: DurableRunner, *, once: bool
) -> dict[str, Any]:
    personal = load_personal_config()
    run = runner.store.get_run(args.run_id)
    max_duration = _first_number(
        args.max_duration,
        run.budget.get("max_duration"),
        run.budget.get("max_duration_seconds"),
        personal.max_duration,
    )
    max_cost = _first_number(
        args.max_cost,
        run.budget.get("max_cost_usd"),
        run.budget.get("max_cost"),
        personal.max_cost_per_run,
    )
    provider_name = _provider_name(args.provider)
    permission_mode = PermissionMode(args.permissions)
    verifier = None
    if args.verification_plan is not None:
        plan_path = args.verification_plan.resolve()
        try:
            plan_path.relative_to(args.project_root.resolve())
        except ValueError as exc:
            raise ConfigError("verification plan must remain inside the project") from exc
        verifier = EnvironmentVerifier.from_file(args.project_root, plan_path)
    elif permission_mode is not PermissionMode.READ_ONLY:
        raise ConfigError(
            "write-capable execution requires --verification-plan; "
            "provider terminal events are not proof"
        )
    adapter: CodexAdapter | ClaudeAdapter
    transport: CodexAppServerTransport | ClaudeAgentSdkTransport | ClaudeCliTransport
    if provider_name == "codex":
        transport = await CodexAppServerTransport.launch(
            client_version=__version__
        )
        adapter = CodexAdapter(
            transport,
            configured_models=_configured_models(personal.providers, provider_name),
        )
    else:
        transport = create_claude_transport()
        adapter = ClaudeAdapter(
            transport,
            configured_models=_configured_models(personal.providers, provider_name),
        )
    try:
        route, promotion_routes = route_provider_catalog(
            await adapter.list_models(),
            provider=provider_name,
            model_id=args.model,
            profile=SemanticProfile(args.profile),
            outcomes=runner.store.list_route_outcomes(),
        )
        supervisor = CampaignSupervisor(
            runner,
            adapter,
            cwd=args.project_root,
            permissions=permission_mode,
            limits=SupervisionLimits(
                max_duration=max_duration,
                max_cost_usd=max_cost,
                lease_seconds=args.lease_seconds,
                poll_interval=args.poll_interval,
            ),
            promotion_routes=promotion_routes,
        )
        worker_id = args.worker_id or f"{provider_name}-{os.getpid()}"
        return await supervisor.run(
            args.run_id, worker_id, route, verifier=verifier, once=once
        )
    finally:
        if isinstance(transport, CodexAppServerTransport):
            await transport.aclose()


def _provider_name(value: str) -> str:
    if value != "auto":
        if shutil.which(value) is None:
            raise ConfigError(f"provider CLI is not available: {value}")
        return value
    for candidate in ("codex", "claude"):
        if shutil.which(candidate) is not None:
            return candidate
    raise ConfigError("no provider CLI is available; install codex or claude")


def _first_number(*values: Any) -> float | None:
    for value in values:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _configured_models(
    providers: dict[str, dict[str, Any]], provider: str
) -> tuple[ModelInfo, ...]:
    settings = providers.get(provider, {})
    if not isinstance(settings, dict):
        raise ConfigError(f"providers.{provider} must be an object")
    value = settings.get("models", ())
    if not isinstance(value, list):
        raise ConfigError(f"providers.{provider}.models must be an array")
    models: list[ModelInfo] = []
    for item in value:
        if isinstance(item, str) and item:
            models.append(ModelInfo(provider, item, availability="configured"))
            continue
        if not isinstance(item, dict):
            raise ConfigError(f"providers.{provider}.models entries must be strings or objects")
        model_id = item.get("id", item.get("model"))
        if not isinstance(model_id, str) or not model_id:
            raise ConfigError(f"providers.{provider}.models object needs an id")
        context = item.get("context_limit", item.get("context_window"))
        models.append(
            ModelInfo(
                provider,
                model_id,
                model_version=item.get("version") if isinstance(item.get("version"), str) else None,
                context_limit=context if isinstance(context, int) and not isinstance(context, bool) else None,
                pricing=item.get("pricing") if isinstance(item.get("pricing"), dict) else None,
                availability=str(item.get("availability", "configured")),
                deprecated=bool(item.get("deprecated", False)),
                metadata=item,
            )
        )
    return tuple(models)


if __name__ == "__main__":
    raise SystemExit(main())
