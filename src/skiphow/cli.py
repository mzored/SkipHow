"""Command-line control for durable SkipHow runs."""

from __future__ import annotations

import argparse
import asyncio
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
    ClaudeCliTransport,
    CodexAdapter,
    CodexAppServerTransport,
    ModelInfo,
    PermissionMode,
    ProviderError,
)
from .config import (
    ConfigError,
    ProjectConfig,
    load_personal_config,
    load_project_config,
)
from .intake import LocalIntakeStore, atomize
from .model_routing import SemanticProfile
from .runner import DurableRunner
from .schemas import RUN_TERMINAL
from .supervisor import CampaignSupervisor, SupervisionLimits, route_provider_models


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
    intake.add_argument("input", type=Path, help="JSON array of strings or signal objects")
    intake.add_argument("--source", default="owner-request")
    intake.add_argument("--persist", action="store_true", help="write the project-local intake ledger")

    add = commands.add_parser("add-task", help="append a task to a run")
    add.add_argument("run_id")
    add.add_argument("outcome")
    add.add_argument("--task-id")
    add.add_argument("--depends-on", action="append", default=[])
    add.add_argument("--constraint", action="append", default=[])
    add.add_argument("--priority", type=int, default=0)

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
            records = json.loads(args.input.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise ValueError("intake input must be a JSON array")
            signals = atomize(records, default_source=args.source)
            result: dict[str, Any] = {
                "signals": [signal.to_dict() for signal in signals],
                "count": len(signals),
                "persisted": False,
            }
            if args.persist:
                result["store"] = LocalIntakeStore(args.project_root).persist(signals)
                result["persisted"] = True
            _emit(result)
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
    adapter: CodexAdapter | ClaudeAdapter
    transport: CodexAppServerTransport | ClaudeCliTransport
    if provider_name == "codex":
        transport = await CodexAppServerTransport.launch(
            client_version=__version__
        )
        adapter = CodexAdapter(
            transport,
            configured_models=_configured_models(personal.providers, provider_name),
        )
    else:
        transport = ClaudeCliTransport()
        adapter = ClaudeAdapter(
            transport,
            configured_models=_configured_models(personal.providers, provider_name),
        )
    try:
        route = route_provider_models(
            await adapter.list_models(),
            provider=provider_name,
            model_id=args.model,
            profile=SemanticProfile(args.profile),
        )
        supervisor = CampaignSupervisor(
            runner,
            adapter,
            cwd=args.project_root,
            permissions=PermissionMode(args.permissions),
            limits=SupervisionLimits(
                max_duration=max_duration,
                max_cost_usd=max_cost,
                lease_seconds=args.lease_seconds,
                poll_interval=args.poll_interval,
            ),
        )
        worker_id = args.worker_id or f"{provider_name}-{os.getpid()}"
        return await supervisor.run(
            args.run_id, worker_id, route, once=once
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
