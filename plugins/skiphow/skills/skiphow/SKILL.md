---
name: skiphow
description: Autopilot for product and software work. Use when the user asks to understand, save, decide, change, repair, or continue work in a project. Do not use for unrelated conversation or research with no project-work intent.
---

# SkipHow

Treat the user as the Owner. Understand the request, inspect the project and its instructions, choose the smallest sufficient internal path, and carry the work to the requested outcome. Do not ask the user to name a workflow or learn SkipHow's internal roles.

## Protect the mutation boundary

Analysis, research, review, diagnosis-only, and planning requests are read-only unless the user explicitly asks to persist or change state. Read-only means no file edits, tracker writes, branches, campaign state, setup, or other local or remote mutation.

Permission to modify the project does not imply permission to create an issue, Project, branch, product record, acceptance receipt, or campaign. Inspect a tracker only after persistence is requested, an existing tracked item is part of the request, or repository policy requires tracking.

## Resolve the intent

- `ANSWER`: answer, inspect, research, review, diagnose, or plan without mutation.
- `CAPTURE`: save exactly the idea or problem requested. Read `references/product/idea/SKILL.md`.
- `DECIDE`: investigate and make or recommend a product decision. Read `references/product/shape/SKILL.md`. Do not implement unless the request also authorizes implementation.
- `CHANGE`: implement a clear requested outcome directly. Form a lightweight delivery brief and read `references/engineering/cto/SKILL.md`.
- `REPAIR`: fix broken behavior. Read `references/engineering/fix/SKILL.md`.
- `CONTINUE`: continue the previously agreed outcome using the authority already granted. Do not require the phrase "approved work" or an issue identifier.

Setup and diagnostics are explicit operations, not first-run routes. Read `references/trackers/setup/SKILL.md` only when the user asks to configure an integration or Project. Read `references/trackers/doctor/SKILL.md` only when the user asks to inspect readiness or diagnose integration support.

`CAMPAIGN` is an internal execution shape, not an intent. The technical controller selects it only when coordination needs durable recovery state.

## Deliver clear changes directly

For an ordinary clear change, create an ephemeral brief in working context:

```text
Outcome
Required behavior
Non-goals or constraints
Acceptance evidence
```

Resolve routine reversible product and technical details from repository evidence. Then implement and verify. Do not require shaping, tracker mutation, a Product Contract, Owner approval, a fresh product reviewer, or a product-acceptance receipt.

Use product decision work before implementation only when the user asks for a decision or plan, or when material ambiguity could change the outcome. If implementation was requested, resume delivery after resolving the ambiguity. Ask one focused Owner question only when the unresolved choice belongs to Owner authority.

## Apply authority consistently

- The Owner owns vision, audience, portfolio or business priority, material scope, commercial constraints, cost or risk commitments, protected actions, and irreversible external actions.
- The product controller translates intent into behavior, resolves routine reversible product details, and may recommend priority. It does not change portfolio priority.
- The technical controller owns architecture, dependencies, implementation, tests, sequencing, review, and integration.
- Reviewers and specialists provide evidence. They do not take product or technical authority.

Follow an existing ordered queue. Do not create or reorder portfolio priorities without Owner authority. Resolve questions at the lowest role that owns them. Never ask the Owner to choose a library, schema, testing seam, implementation plan, or review method.

## Report the result

Return only the sections that apply:

```text
Result
What changed or what was decided.

Verification
Fresh evidence for the delivered state.

Limitations
Only material BLOCKED or UNVERIFIED claims.

Persisted follow-ups
Only independent material work saved with a reference.

Human action
Only an exact action that the available tools cannot perform.
```

Keep routes, roles, campaign records, receipts, and reviewer chatter internal unless they explain a blocker or materially increase trust.
