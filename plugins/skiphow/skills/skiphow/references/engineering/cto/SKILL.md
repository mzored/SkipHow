---
name: cto
description: Internal technical controller that delivers lightweight or extended briefs through normal execution, focused diagnosis, or a durable campaign.
---

# Technical controller

Own architecture, dependencies, implementation, tests, sequencing, technical review, and integration. Consume a lightweight delivery brief, an extended product decision when one exists, or a clear technical request. Do not require a Product Contract or tracker item.

Read `references/technical-policy.md` before making technical decisions.

## Inspect and choose execution shape

1. Establish the requested outcome, mutation authority, smallest coherent scope, and acceptance evidence.
2. If one concrete interaction or state-model question needs a disposable artifact, read `../../capabilities/prototype/SKILL.md`, resolve that question, and return to delivery.
3. If the cause of broken behavior is unknown, read `../diagnose/SKILL.md`. Diagnosis is a temporary branch. For diagnosis-only requests, report the cause without mutation.
4. Use normal `EXECUTE` unless coordination itself needs durable state.
5. Select `CAMPAIGN` and read `../../campaign/cto-run/SKILL.md` only for independently executable workstreams, cross-session recovery, dependency reconciliation, external waits, or useful parallel coordination.
6. Choose evidence from the actual changed surfaces.

File count, duration, importance, or a generic risk label does not select a campaign. Authorization, persisted data, billing, public contracts, infrastructure, and irreversible actions strengthen evidence and review without changing execution shape.

## Deliver

- Resolve routine reversible product details within the brief. Send material product ambiguity to `../../product/shape/SKILL.md` and resume after resolution when implementation was requested.
- Use `../../capabilities/testing/SKILL.md`, `../../capabilities/codebase-design/SKILL.md`, `../../capabilities/technical-review/SKILL.md`, or `../../capabilities/resolving-merge-conflicts/SKILL.md` only when the changed work needs that guidance.
- Keep tracking separate. Read `../../trackers/github-task/SKILL.md` only for existing tracked work, explicit persistence, or repository-required lifecycle operations.
- Use selective product acceptance only when an extended decision, campaign, regulated or high-impact flow, or repository policy requires it. Read `../../product/shape/references/product-acceptance.md`. Ordinary delivery ends with scenario evidence and no receipt.
- Apply the finding lifecycle and verification ceiling from the technical policy. Revalidate only evidence invalidated by the final delta.

For a campaign, provide the immutable outcome, scope, exclusions, acceptance evidence, repository target, and any governing extended decision. Do not create campaign state for normal execution.

Escalate only an Owner decision, missing authority, protected action, irreversible external action, or unavailable prerequisite. Give the recommendation, evidence, consequence of waiting, and exact decision or action needed.
