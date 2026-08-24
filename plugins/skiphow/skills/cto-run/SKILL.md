---
name: cto-run
description: Run durable CTO delivery campaigns when the user explicitly names cto-run or the internal CTO controller selects durable execution.
---

# cto-run

Use this durable runtime in the current session. Resolve `<runbook> <run-directory> [target]`. Reuse the run directory for a resumed campaign. The internal CTO controller decides whether work needs this runtime. Ask only if the project cannot be identified from the request and runbook.

Read these references before acting:

- `references/operating-policy.md`
- `references/state-contract.md`
- `references/capability-routing.md`
- `references/host-notes.md`

Then read the runbook and every repository instruction that applies. Establish the durable state in the run directory, record the policy and runbook hashes, and reconstruct current state from repository, tracker, CI, and other primary evidence. Treat prior summaries, seeds, branch names, and worker reports as claims to verify.

When the runbook identifies tracked GitHub items, read `../github-task/SKILL.md` and use it only for lifecycle operations. The CTO remains the owner of architecture, implementation, verification, review, and integration decisions. This runtime owns only the durable mechanics: state, recovery, lane coordination, and final reconciliation.

Run the control loop: observe, reconcile, assess, decide, execute or delegate, verify, review, integrate, and learn. Keep the whole ready frontier moving while preserving one writer per mutable scope. Persist state before an external wait, handoff, long operation, integration, or context loss.

After a restart or context loss, reread the contracts, rebuild the projection from `state.json`, `journal.jsonl`, receipts, and `briefing.md`, verify it against primary systems, and resume idempotently. Stop only when the runbook reaches its terminal condition or an authorized blocker stops the affected lane.
