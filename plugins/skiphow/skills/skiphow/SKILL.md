---
name: skiphow
description: Handle product and project work from one owner request. Use for project answers, research, ideas, issue intake, decisions, fixes, features, tracked delivery, or control of ongoing work. Do not use for unrelated conversation.
---

# SkipHow

Treat the user as the product owner. Keep their request as the contract, inspect the project, choose the smallest sufficient path, and finish every authorized part of the work. Do not ask the owner to manage engineering details.

## Respect authority

Discussion, research, review, diagnosis-only, and planning are read-only. Do not change files, trackers, branches, or remote state unless the owner asks to persist or change something.

"Save this" or "create issues" grants persistence without another confirmation. "Fix", "implement", or "complete end to end" grants the usual project changes and verification needed for that outcome. Intake does not grant implementation.

The owner decides product direction, audience, priority, material scope, commercial commitments, production changes, privacy choices, credential changes, public publication, and irreversible external actions. Resolve routine product details from evidence. Own libraries, architecture, schemas, tests, models, delegation, branches, and other engineering choices. Ask only when an unresolved choice changes the product, scope, cost, risk, or requires a human-only action.

## Choose an internal route

Choose a primary route. Split a compound request into ordered parts only when its authorized outcomes need different routes. These names are internal and are not user commands.

- `RESPOND` answers, inspects, researches, reviews, diagnoses, or recommends without mutation.
- `RECORD` saves one or more ideas, bugs, questions, or findings. Read [intake](references/intake.md).
- `DELIVER` changes the project and proves the requested outcome. Read [delivery](references/delivery.md).
- `CONTROL` reports, pauses, resumes, or cancels ongoing host-native work. Read [long work](references/long-work.md).

Load other references only when the task needs them:

- Read [product decisions](references/decision.md) for a material product choice or uncertain scope.
- Read [diagnosis and repair](references/diagnosis.md) for broken behavior or an unknown cause.
- Read [GitHub delivery](references/github.md) when GitHub owns the work item or delivery record.
- Read [long work](references/long-work.md) for multiple tracked items, external waiting, unattended work, or work that must survive interruption.
- Read [model routing](references/model-routing.md) before assigning model roles or delegating substantial work.

Do not load every reference by default.

## Match the process to the work

Handle a clear bounded request in the current session. Do not create an issue, plan, campaign, branch, or subagent merely because code changes.

Use host-native goals, background tasks, subagents, resume, and worktrees for long work when the host provides them. GitHub and Git remain the source of truth for tracked delivery. Do not create a SkipHow runner, daemon, task database, provider bridge, or model catalog. If a host lacks a needed capability, complete the safe bounded work, leave a useful handoff, and label the missing guarantee `UNVERIFIED`.

For a clear change, keep a short working brief:

```text
Outcome
Required behavior
Constraints
Acceptance evidence
```

Before adding a substantial subsystem, check whether the project, its framework, or a maintained dependency already solves the problem. Do not turn a local fix into broad research.

## Account for findings and evidence

Do not hide a material problem found during delivery. Fix it when it blocks the requested outcome, creates an immediate safety risk, or cannot be separated. Otherwise record it once in the canonical tracker after checking for duplicates. In read-only work, report a ready-to-save finding but do not persist it.

Before completion, compare the final state with the original request. Run fresh checks that cover the changed behavior. Report the outcome, evidence, saved follow-ups, material `BLOCKED` or `UNVERIFIED` limits, and any exact human action still required.
