# Durable operating policy

The shared technical policy at `../../cto/references/technical-policy.md` applies first. This file adds only the mechanics needed for a durable campaign.

## Recovery and control loop

Before mutation, reconstruct actual state from primary evidence. Inspect instructions, dirty paths, worktrees, refs, ancestry, exact commits, integration history, tracker state, CI, and authoritative external systems. Keep `briefing.md` as a concise map of authorities, hashes, decisions, locations, and unresolved questions. Verify an entry before it supports an architecture, security, or integration decision.

Persist state before handoff, an external wait, a long operation, integration, or context loss. On recovery, re-hash the policy and runbook, rebuild from durable records, compare that result with canonical systems, retain conflicting observations, and resume without duplicating work.

At each boundary run observe, reconcile, assess, decide, execute or delegate, verify, review, integrate, and learn. Reassess the whole executable frontier. Do not stop after planning, a report, one task, a recoverable failure, or a temporary outage.

## Durable execution health

Only the root changes shared run state. Workers write scoped receipts and evidence. Record command budgets, attempts, baselines, failure signatures, leases, and exact commits in the durable state defined by `state-contract.md`.

After three consecutive failures with the same signature, set the lane to `CIRCUIT_BROKEN`. Reopen it only through a recorded review decision that names what changed. Pause the affected lane, capture diagnostics, classify the cause, apply the smallest systemic correction, rerun the smallest reproducer, update durable state, and continue independent lanes.

## Durable handoff

The campaign ends only when every included item satisfies the shared technical policy and the runbook's terminal condition. Reconcile branches, worktrees, tracker state, and dirty paths from fresh evidence. Write `FINAL.md` with completed outcomes, pending external reconciliation, blocked items, evidence, residual risks, decisions, recurring failures, recommended improvements, and confirmation that no unauthorized protected action occurred.
