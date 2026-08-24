# Durable operating policy

The shared technical policy at `../../cto/references/technical-policy.md` applies first. This file adds only the mechanics needed for a durable campaign.

## Recovery and control loop

Before mutation, reconstruct actual state from primary evidence. Inspect instructions, mutable paths, workspaces, state identities, integration history, tracker state, CI, and authoritative external systems. For Git work, include dirty paths, worktrees, refs, ancestry, and exact commits. Keep `briefing.md` as a concise map of authorities, hashes, decisions, locations, and unresolved questions. Verify an entry before it supports an architecture, security, or integration decision.

Persist state before handoff, an external wait, a long operation, integration, or context loss. On recovery, re-hash the policy and runbook, rebuild from durable records, compare that result with canonical systems, retain conflicting observations, and resume without duplicating work.

At each boundary run observe, reconcile, assess, decide, execute or delegate, verify, review, integrate, and learn. Reassess the whole executable frontier. Do not stop after planning, a report, one task, a recoverable failure, or a temporary outage.

## Frontier and decomposition

Prefer independently verifiable vertical slices: each lane should deliver a narrow complete behavior across the layers it needs rather than one horizontal layer of a future feature. Express real blockers in the durable task graph and keep every unblocked lane on the executable frontier visible.

For an inherently cross-cutting mechanical migration that cannot land as vertical slices, use expand, migrate in bounded batches that preserve compatibility, then contract after every caller has moved. Preserve green integration boundaries whenever possible and make any shared integration branch and final verification explicit.

Do not pre-decompose uncertainty. Create durable work items only for work or questions concrete enough to execute or investigate now. Keep suspected future work that cannot yet be stated precisely as `not yet specified` at campaign level. Revisit it when frontier work clears enough uncertainty to make it actionable, dismisses it, or places it outside the campaign goal.

## Durable execution health

Only the root changes shared run state. Workers write scoped receipts and evidence. Record command budgets, attempts, baselines, failure signatures, leases, and exact state identities in the durable state defined by `state-contract.md`.

After three consecutive failures with the same signature, set the lane to `CIRCUIT_BROKEN`. Reopen it only through a recorded review decision that names what changed. Pause the affected lane, capture diagnostics, classify the cause, apply the smallest systemic correction, rerun the smallest reproducer, update durable state, and continue independent lanes.

## Durable handoff

The campaign ends only when every included item satisfies the shared technical policy and the runbook's terminal condition. Reconcile workspaces, delivered-state identities, tracker state, and mutable paths from fresh evidence; for Git work include branches, worktrees, and dirty paths. Write `FINAL.md` with completed outcomes, pending external reconciliation, blocked items, evidence, residual risks, decisions, recurring failures, recommended improvements, and confirmation that no unauthorized protected action occurred.
