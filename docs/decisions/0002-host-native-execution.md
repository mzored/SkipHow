# ADR 0002: Use host-native execution

## Status

Accepted as amended by [ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md). Host-native
execution, permissions, continuation, and the rejection of a private runtime stand. Fixed routes, required
worktrees, and the three role adapters do not.

## Date

2026-08-25

## Current interpretation, 2026-08-28

Host-native execution and the rejection of a private SkipHow runtime remain current. The workflow triggers,
state hierarchy, and fallback records below describe the historical 1.x contract;
[ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md) governs the 2.0.1 candidate when they
conflict.

No item count, external wait, or unattended phrase selects a long-work procedure. The agent uses host tasks,
delegates, worktrees, continuation, or a handoff only when they materially help the authorized result or the
repository requires them. GitHub is not a universal task record, and SkipHow defines no automatic handoff or
fixed local inbox. A requested durable record follows the project's existing tracker and classification; a
project change does not gain remote-write authority from that tracker or from repository procedure.

## Context

SkipHow built a Python runner with a CLI, SQLite state, provider adapters, scheduling, model routing, verification, recovery, and a separate GitHub delivery command. Its deterministic tests cover many internal contracts. They do not prove the owner outcome that matters: take several tracked issues, finish them through pull requests and CI, merge them, and clean up owned branches without manual handoffs.

The runner also duplicates mechanisms available in the supported hosts. Codex and Claude expose different combinations of sessions, subagents, isolated worktrees, context compaction, resume, and long-running work. SkipHow uses a capability only after the installed host confirms it. Keeping a second implementation adds code and trust boundaries while still depending on each host for model execution and permissions.

The audit found concrete gaps. The runner works in the foreground, does not create durable subagent or worktree lifecycles, and keeps GitHub delivery outside its supervisor loop. Its worker can write inside the project that contains controller authority state. Its verifier runs repository-controlled commands without a separate operating-system sandbox. The live harness does not install the candidate plugin it claims to evaluate.

## Decision

SkipHow delegates execution mechanics to the host.

The host owns:

- model sessions and turns;
- goals, background tasks, pause, resume, and cancellation;
- subagent creation and context isolation;
- worktree creation for independent mutable work;
- compaction and session recovery;
- sandboxing, permissions, approvals, and interruption;
- the concrete model and reasoning controls available in that host.

SkipHow owns:

- the owner's requested outcome and granted authority;
- the `RESPOND`, `RECORD`, `DELIVER`, and `CONTROL` routes;
- the choice between bounded work in the current session and host-managed long work;
- product intake, finding disposition, delivery policy, and completion criteria;
- reconciliation against Git, GitHub, CI, and the final project state;
- an honest report when a host cannot provide a required capability.

Bounded work runs in the current session. Work with several issues, external waits, or an explicit request to continue unattended uses the host's goal or background-task mechanism. SkipHow parallelizes read-only work when useful. It permits parallel writes only in separate host-managed worktrees, with one root agent responsible for integration.

Git, GitHub, and the host task remain the sources of truth. After compaction or resume, the root agent reconstructs state from those systems and a short handoff when one exists. SkipHow does not replay a private event database.

The custom Python runner, its CLI, SQLite controller, provider transports, scheduler, model catalog, recovery engine, and compatibility shims will be removed. SkipHow will not replace them with a daemon or another local workflow engine.

Capability loss degrades behavior plainly:

- without subagents, SkipHow runs independent work in sequence;
- without managed worktrees, SkipHow does not run mutable lanes in parallel;
- without background execution or resume, SkipHow completes the safe session-bound work and records a handoff;
- without GitHub, `RECORD` uses the documented local inbox and tracked delivery stays local;
- when a capability cannot be tested, support for that capability is `UNVERIFIED`.

SkipHow must not claim unattended continuity, crash recovery, or cross-session resume on a host that does not provide and pass those checks.

## Consequences

- The product becomes a portable skill and policy package instead of a second agent runtime.
- Installation no longer requires the Python runner, runtime schemas, or a project-local task database.
- Host security is the real execution boundary. SkipHow documents the boundary instead of claiming an independent sandbox.
- Long-work behavior can differ between hosts. Package and live checks must report those differences.
- GitHub Issues and pull requests hold tracked delivery state. A local inbox or handoff is a fallback, not a parallel tracker.
- Pause, resume, subagent routing, and worktree cleanup use host APIs and tools. SkipHow cannot promise features a host does not expose.
- Removing the runner is a breaking change. The changelog and release notes must say so.

## Rejected alternatives

### Repair and extend the current runner

Closing the known gaps would require a persistent supervisor, a multi-issue state machine, isolated workers, sandboxed verification, GitHub reconciliation, provider-specific resume, and real product-bound evaluations. That would keep SkipHow in competition with its hosts and expand the code owners must trust.

### Keep a thin persistent coordinator

A smaller SQLite coordinator still creates a second source of task state and needs recovery, migrations, locking, security, and provider adapters. Current requirements do not justify that cost. GitHub and host tasks already hold the state needed for supported workflows.

### Adopt an external workflow platform

Temporal, Restate, or a hosted queue can provide durable retries and waits. They also add services, workers, deployment, and operations to a tool that should install as a skill. No measured SkipHow workload currently requires that infrastructure.

### Promise identical behavior on every host

The hosts expose different controls and durability. Hiding those differences would turn missing capabilities into false support claims.

## Evidence

- [Repository audit](../research/2026-08-25/repository-audit.md)
- [Host capability research](../research/2026-08-25/host-capabilities.md)
- [Security and evaluation research](../research/2026-08-25/security-and-evals.md)
- [Live evaluation host contract](../research/2026-08-25/live-evaluation-hosts.md)
- [Prior-art research](../research/2026-08-25/prior-art.md)
- [Host-native campaign policy](0006-host-native-campaign-and-engineering-policy.md)

## Revalidation triggers

Revisit this decision if any of the following occurs:

- supported hosts remove the session, worktree, resume, or long-work capabilities SkipHow depends on;
- product-bound evaluations show that host state cannot recover a tracked run after compaction or process loss;
- a required compliance boundary needs controller-owned authority and audit records outside the worker host;
- users require provider-neutral unattended execution on hosts without native durability, and measured demand justifies operating a runtime;
- an external workflow platform becomes a host-provided capability with no separate service or operator burden.
