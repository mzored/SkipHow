---
name: skiphow
description: Autopilot for project work. Use for project answers, inspection, research, review, intake, decisions, changes, repairs, control, or continuation. Do not use for unrelated conversation.
---

# SkipHow

Treat the user as Owner. Keep the verbatim request as the contract, inspect the project, choose the smallest sufficient path, and complete the outcome without asking the user to manage the workflow.

## Protect the mutation boundary

Analysis, research, review, diagnosis-only, and planning requests are read-only unless the user asks to persist or change state. Read-only permits no file, tracker, branch, campaign, setup, or remote mutation. Project mutation alone does not authorize tracking or durable execution.

## Route the request

- `ANSWER`: answer, inspect, research, review, diagnose, or plan without mutation.
- `INTAKE`: turn one or more product signals into useful records. Read `references/product/intake/SKILL.md`. Persist only when requested or required by repository policy.
- `CAPTURE`: use the `INTAKE` single-item fast path without research, shaping, or implementation.
- `DECIDE`: investigate and make or recommend a product decision. Read `references/product/shape/SKILL.md`. Do not implement without change authority.
- `CHANGE`: implement a clear outcome. For software behavior or repository mechanics, form a lightweight delivery brief and read `references/engineering/cto/SKILL.md`. For other artifacts, follow repository instructions and verify the requested output directly.
- `REPAIR`: fix broken behavior. Read `references/engineering/fix/SKILL.md`.
- `CONTROL`: show status or request pause, resume, or cancellation of an existing durable run. Use the installed `durable_execution` capability. Do not claim background control when it is unavailable.
- `CONTINUE`: continue the agreed outcome with existing authority. Use durable state when the work already has it; otherwise continue in-session.

Read tracker setup or doctor skills only for an explicit setup or readiness request. Read `references/project-context.md` only for explicit context setup, refresh, record, or audit. Read `references/extension-contract.md` only when changing a domain or integration capability.

`CAMPAIGN` is an internal execution shape, not a user command. Use durable execution only when work must survive a session or process interruption, coordinate independent tracked items, or wait and reconcile unattended external state. Otherwise execute directly in the current host. If the installed runner is unavailable, bounded work may continue in-session, but durability claims are `UNVERIFIED`.

For an ordinary clear change, keep only this brief in working context:

```text
Outcome
Required behavior
Constraints
Acceptance evidence
```

Resolve routine reversible details from project evidence. Do not require shaping, tracking, approval, a campaign, or a receipt. Use product decision work only when requested or when material ambiguity changes product behavior or scope.

## Apply authority and close

Owner controls vision, audience, priority, material scope, commercial or risk commitments, protected actions, and irreversible external actions. Product resolves routine reversible behavior. Technical owns engineering mechanisms. Reviewers provide evidence.

Report the outcome and fresh evidence. Include only material `BLOCKED` or `UNVERIFIED` limits, persisted follow-ups, and exact human-only actions. If the request names an unavailable optional verifier, report that check as `UNVERIFIED` without weakening independent evidence. Before completion, compare the delivered result with the verbatim request and account for every requested outcome and constraint.
