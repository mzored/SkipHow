# Architecture

SkipHow has two planes. The plugin kernel handles ordinary work inside the current host. The optional runner exists only for work that must survive a session or process interruption, coordinate independent tracked items, or wait for external state.

```text
owner request
    |
semantic kernel ---- direct path in the current host
    |
durable runner, when required
    |
provider adapters ---- Git, GitHub, CI, local tracker
```

The kernel owns intent, authority, scope, evidence, finding disposition, and final alignment with the original request. The runner owns transactions, task scheduling, leases, checkpoints, retries, control state, provider sessions, recovery, and terminal reconciliation. A foreground supervisor dispatches provider work and enforces invocation limits. Provider and integration adapters execute mechanical protocols. They do not decide product scope or engineering method.

## Direct path

`ANSWER`, bounded `CHANGE`, `REPAIR`, and simple `INTAKE` requests run directly. They do not need runner state, a tracker, a branch, a review, or a persistent artifact unless the outcome itself needs one. Risk changes evidence and authority checks, not the execution shape.

## Durable runner

The runner is an optional Python package and CLI. It uses SQLite transactions as controller authority, an append-only material event journal, snapshots for inspection, revision checks, attempt IDs, idempotency keys, and expiring leases. Provider transcripts are supporting records, never the only state.

`skiphow execute` starts one foreground supervisor and runs until the campaign settles, pauses, or reaches a configured duration or reported-cost ceiling. `skiphow worker` processes one ready frontier. The supervisor renews leases while waiting for provider events, polls persisted external waits, and checkpoints process exit. Pause and duration stops return unfinished claimed work to the frontier. A cost stop blocks the task for inspection. The runner has no mandatory server, dashboard, or daemon. A machine reboot does not restart it automatically.

The provider contract supports capability discovery, configured model catalogs, session start and resume, forking, turns, event streams, interruption, compaction, usage, and cleanup. Model IDs and provider flags come from adapters or personal configuration. Core routing sees only `ECONOMY`, `BALANCED`, and `FRONTIER` profiles plus required capabilities.

## Policy ownership

| Concern | Canonical owner |
| --- | --- |
| Intent, authority, and direct or durable selection | `skills/skiphow/SKILL.md` |
| Technical delivery and evidence | `references/engineering/cto/` |
| Product decisions | `references/product/shape/` |
| Product signal intake | `references/product/intake/` |
| Durable mechanics | `src/skiphow/` and `schemas/` |
| Tracker and delivery protocols | `references/trackers/` and adapters |
| Host capability vocabulary | `references/host-capabilities.md` |

The legacy `references/campaign/cto-run/` files retain the short semantic handoff contract. They do not claim that prose provides process durability.

## Host capability contract

The controller selects mechanisms by capability. The canonical vocabulary is:

- `inspect_project`
- `mutate_project`
- `run_local_commands`
- `optional_external_verifier`
- `research_external_sources`
- `delegate_read_only`
- `delegate_mutable_lane`
- `fresh_independent_review`
- `persist_external_work`
- `perform_protected_action`
- `durable_execution`

Missing delegation does not block bounded sequential work. Missing `durable_execution` means background, crash recovery, and resume claims stay `UNVERIFIED`. Protected actions still need explicit authority.

## Campaign state

Run and task transitions are monotonic and revision-checked. A stale worker cannot move a terminal task back into execution. Each mutable attempt records its worker, lease, idempotency key, optional owned resources and state identities, last progress, failure signature, provider session, and next action. The current code checkpoints provider dispatch, external waits, control requests, provider errors, verification, cost-limit stops, and process exit. Integration adapters must add their own checkpoint and reconciliation evidence.

Recovery first tries to resume the last recorded provider session. If resume is unavailable, it starts a new session with a capsule containing the immutable outcome, current task, constraints, saved decisions, Git state supplied by prior checkpoints, completed evidence, open findings, session identifiers, and one next action. Open-finding text is labelled untrusted. The capsule does not replay the full transcript.

Git, GitHub, and CI remain authoritative for their own records. The standalone GitHub lifecycle adapter and E2E gate reconcile exact remote identities before mutation. They are not yet dispatched by the generic campaign supervisor. Cleanup requires verified ownership and preserves unmerged branches, unique commits, dirty worktrees, and unrelated user state.

## Persistence boundary

The SQLite store redacts recognized tokens, credential assignments, authorization fields, and private-key blocks before serializing controller records. This applies to run and task payloads, journal events, attempts, findings, checkpoints, snapshots, and exports. Redaction is defense in depth, not proof that every possible secret format is covered.

## Configuration and persistence

Project-safe configuration uses `.skiphow/config.json` schema v2. Personal execution preferences and provider catalogs use the user's platform configuration directory. Credentials stay in provider or host credential stores and never enter either file.

The runner reads v1 project configuration. Explicit setup can migrate it after writing an adjacent backup. A missing configuration file keeps zero-config direct use working.

## Verification

`scripts/check.py` runs deterministic local checks and never starts a model. The GitHub E2E gate and live model harness are separate opt-in commands. Harness v2 binds release runs to a clean exact candidate and the twenty registered scenarios, but it does not provision their fixtures or independently observe final state. Package checks, adapter conformance, GitHub receipts, live behavior receipts, and release claims remain separate evidence.
