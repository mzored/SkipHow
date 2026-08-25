---
name: skiphow
description: Autopilot for project work. Use for project answers, inspection, research, review, capture, decisions, changes, repairs, or continuation. Do not use for unrelated conversation.
---

# SkipHow

Treat the user as Owner. Inspect the project and its instructions, choose the smallest sufficient path, and complete the outcome without asking for an internal workflow. Keep the original request verbatim as normative input. Briefs may clarify but never replace, narrow, or extend it.

## Protect the mutation boundary

Analysis, research, review, diagnosis-only, and planning requests are read-only unless the user explicitly asks to persist or change state. Read-only permits no file, tracker, branch, campaign, setup, or remote mutation.

Project mutation does not authorize tracking, branches, records, receipts, or campaigns. Inspect a tracker only for requested persistence, existing tracked work, or repository policy.

## Resolve the intent

- `ANSWER`: answer, inspect, research, review, diagnose, or plan without mutation.
- `CAPTURE`: save exactly the idea or problem requested. Read `references/product/idea/SKILL.md`.
- `DECIDE`: investigate and make or recommend a product decision. Read `references/product/shape/SKILL.md`. Do not implement unless the request also authorizes implementation.
- `CHANGE`: implement a clear requested outcome directly. Dispatch by changed surface as described below.
- `REPAIR`: fix broken behavior. Read `references/engineering/fix/SKILL.md`.
- `CONTINUE`: continue the previously agreed outcome using the authority already granted. Do not require the phrase "approved work" or an issue identifier.

Setup and diagnostics are explicit. Read `references/trackers/setup/SKILL.md` for requested integration setup and `references/trackers/doctor/SKILL.md` for readiness diagnosis. Read `references/project-context.md` only for explicit context setup, refresh, record, or audit. Read `references/extension-contract.md` only when changing a domain or integration capability.

`CAMPAIGN` is an internal execution shape, not an intent. Select it only when execution needs durable coordination or recovery state.

## Deliver clear changes directly

Dispatch inside `CHANGE` without creating a public route:

- Software, system behavior, or repository mechanics: form a lightweight delivery brief and read `references/engineering/cto/SKILL.md`.
- Non-software project artifact: work directly under repository instructions. Do not load engineering policy unless technical behavior or repository mechanics also change. The requested output is the primary contract. Use current authoritative sources for factual claims and an available render or preview for visual output. Match evidence to the artifact.

Load a domain capability only when its trigger applies.

For an ordinary clear change, keep this ephemeral brief in working context:

```text
Outcome
Required behavior
Non-goals or constraints
Acceptance evidence
```

Resolve routine reversible details from project evidence, then implement and verify. Do not require shaping, tracking, a Product Contract, approval, product review, or a receipt.

Use product decision work first only when requested or when material ambiguity could change the outcome. Resume authorized implementation after resolving it. Ask one focused question only for Owner authority.

## Apply authority

Owner controls vision, audience, portfolio priority, material scope, commercial or risk commitments, protected actions, and irreversible external actions. Product resolves routine reversible behavior. Technical owns engineering mechanisms. Reviewers provide evidence. Follow an existing queue and never ask Owner to choose engineering mechanisms.

## Report the result

Report the outcome and fresh evidence. Include only material `BLOCKED` or `UNVERIFIED` limits, referenced persisted follow-ups, and exact human-only actions. Keep internal process out unless it explains a blocker or adds trust.

If the request or host profile names an unavailable optional verifier, report that check as `UNVERIFIED` without weakening independent evidence.

Before completion, compare the result with the verbatim request. Mark each outcome completed, declined with reason, or blocked. Confirm no narrowed intent, unauthorized material behavior, or lost constraint, format, prohibition, or read-only boundary. This is an internal check, not a document or review lane.
