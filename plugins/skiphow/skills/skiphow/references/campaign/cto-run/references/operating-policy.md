# Durable operating policy

The shared technical policy at `../../../engineering/cto/references/technical-policy.md` applies first. This file adds only the mechanics needed for a durable campaign.

Do not add a default heartbeat, server, dashboard, database, organization chart, or unattended scheduler. The campaign persists only the state needed for coordination and recovery.

## Recovery and control loop

Before mutation, reconstruct actual state from primary evidence. Inspect instructions, mutable paths, workspaces, state identities, integration history, tracker state, CI, and authoritative external systems. For Git work, include dirty paths, worktrees, refs, ancestry, and exact commits. Keep `briefing.md` as a concise map of authorities, hashes, decisions, locations, and unresolved questions. Verify an entry before it supports an architecture, security, or integration decision.

Persist state before handoff, an external wait, a long operation, integration, or context loss. On recovery, re-hash the policy and runbook, rebuild from durable records, compare that result with canonical systems, retain conflicting observations, and resume without duplicating work.

Treat the recorded original outcome as immutable. Every lane records its parent goal and why its result advances that goal. A changed interpretation becomes an explicit authorized decision; it never overwrites the original outcome.

At each boundary run observe, reconcile, assess, decide, execute or delegate, verify, review, integrate, and learn. Reassess the whole executable frontier. Do not stop after planning, a report, one task, a recoverable failure, or a temporary outage.

## Frontier and decomposition

Prefer independently verifiable vertical slices: each lane should deliver a narrow complete behavior across the layers it needs rather than one horizontal layer of a future feature. Express real blockers in the durable task graph and keep every unblocked lane on the executable frontier visible.

For an inherently cross-cutting mechanical migration that cannot land as vertical slices, use expand, migrate in bounded batches that preserve compatibility, then contract after every caller has moved. Preserve green integration boundaries whenever possible and make any shared integration branch and final verification explicit.

Do not pre-decompose uncertainty. Create durable work items only for work or questions concrete enough to execute or investigate now. Keep suspected future work that cannot yet be stated precisely as `not yet specified` at campaign level. Revisit it when frontier work clears enough uncertainty to make it actionable, dismisses it, or places it outside the campaign goal.

## Durable execution health

Only the root changes shared run state. Workers write scoped receipts and evidence. Before dispatch, choose an estimated budget envelope and say what signal it uses. Use tokens or cost only when the host reports them reliably. Otherwise bound tool calls, command attempts, or wall-clock time. An estimate is not an exact budget. Record consumption, attempts, baselines, failure signatures, leases, and exact state identities in the durable state defined by `state-contract.md`.

Check the cancel flag and whether the hard-stop condition has occurred before each dispatch, retry, and integration mutation. Stop launching work only after cancellation or the condition occurs. Let an active operation reach its safe cancellation boundary, record partial state, and reconcile owned mutable state.

Claim a lane with an idempotent claim token tied to its current state identity and lease. A repeated claim with the same token is a no-op. A conflicting live lease cannot take the lane. State transitions are monotonic: a stale worker result cannot move a terminal or newer lane backward. On recovery, inspect expired leases and primary state before returning an orphaned in-progress lane to the ready frontier or accepting its completed work.

When repeated attempts show no meaningful progress with the same failure signature, set the lane to `CIRCUIT_BROKEN`. A repository or runbook may set a numeric attempt limit. Reopen the lane only through a recorded review decision that names what changed. Pause the affected lane, capture diagnostics, classify the cause, apply the smallest systemic correction, rerun the smallest reproducer, update durable state, and continue independent lanes.

## Durable handoff

Write a compact checkpoint before a session or context handoff. Include the immutable outcome, current state identity, ready and active lanes, leases, budget consumption, cancel state, blockers, last evidence, and exact resume action. Do not use a prose summary as the only recovery record.

The campaign ends only when every included item satisfies the shared technical policy and terminal condition, or its hard-stop condition occurs. Reconcile workspaces, delivered-state identities, tracker state, external waits, leases, and mutable paths from fresh evidence; for Git work include branches, worktrees, and dirty paths. Generate `FINAL.md` from reconciled durable state with completed outcomes, pending external reconciliation, blocked or cancelled items, evidence, residual risks, decisions, recurring failures, budget result, and confirmation that no unauthorized protected action occurred.
