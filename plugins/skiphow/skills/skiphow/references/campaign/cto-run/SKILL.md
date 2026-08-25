---
name: cto-run
description: Internal durable runtime used when the technical controller determines that coordination needs persistent recovery state.
---

# cto-run

Use this specialized durable runtime after the technical controller selects a campaign. Resolve the runbook, run directory, and target from its handoff. Reuse the run directory for a resumed campaign. This is not the stricter form of ordinary engineering and is not a user-facing workflow.

Read these references before acting:

- `../../engineering/cto/references/technical-policy.md`
- `references/operating-policy.md`
- `references/state-contract.md`
- `references/capability-routing.md`
- `references/host-notes.md`
- `../../host-capabilities.md`

Then read the runbook and every repository instruction that applies. Establish the durable state in the run directory, record the policy and runbook hashes, and reconstruct current state from repository, tracker, CI, and other primary evidence. Treat prior summaries, seeds, branch names, and worker reports as claims to verify.

When the runbook identifies tracked GitHub items, read `../../trackers/github-task/SKILL.md` and use it only for lifecycle operations. The CTO remains the owner of architecture, implementation, verification, review, and integration decisions. This runtime owns only durable state, recovery, lane coordination, and final reconciliation.

Before dispatch, preserve the original outcome unchanged, relate every lane to its parent goal and reason, set a budget envelope from reliable host signals or bounded attempts, commands, or wall-clock, and define the hard stop. Run the control loop: observe, reconcile, assess, decide, execute or delegate, verify, review, integrate, and learn. Keep the whole ready frontier moving while preserving one writer per mutable scope. Persist a compact checkpoint before an external wait, handoff, long operation, integration, or context loss.

After a restart or context loss, reread the contracts, rebuild the projection from `state.json`, `journal.jsonl`, receipts, and `briefing.md`, verify it against primary systems, recover orphaned work, and resume idempotently. Stop when the terminal or hard-stop condition occurs, the budget is exhausted, or an authorized blocker stops the affected lane. Defining a hard-stop condition does not stop the run. Always reconcile final campaign and external state.
