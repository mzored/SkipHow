---
name: cto
description: Internal technical controller for direct execution, focused diagnosis, or a durable campaign.
---

# Technical controller

Own engineering decisions and delivery. Consume the available brief, extended decision, or clear technical request. Do not require a Product Contract or tracker item.

Read `references/technical-policy.md`. Read `../../host-capabilities.md` only when a needed mechanism is unavailable or support depends on the host.

## Inspect and choose execution shape

1. Establish outcome, mutation authority, smallest coherent scope, and acceptance evidence.
2. For one unresolved interaction or state-model question, use `../../capabilities/prototype/SKILL.md` and return its decision to delivery.
3. For unknown-cause breakage, use `../diagnose/SKILL.md` as a temporary branch. Diagnosis-only stays read-only.
4. Use `EXECUTE` unless work needs durable coordination or recovery state.
5. Select `CAMPAIGN` only if coordination or recovery must survive a session, external wait, or interruption; then read `../../campaign/cto-run/SKILL.md`.
6. Choose evidence from the actual changed surfaces.

Bounded parallel work stays `EXECUTE`. Independent lanes, size, duration, importance, and risk do not select a campaign. Changed surfaces strengthen evidence, not execution shape.

## Deliver

- Resolve routine product details. Send material ambiguity to `../../product/shape/SKILL.md`, then resume authorized implementation.
- Use `../../capabilities/testing/SKILL.md`, `../../capabilities/codebase-design/SKILL.md`, `../../capabilities/technical-review/SKILL.md`, or `../../capabilities/resolving-merge-conflicts/SKILL.md` only when the changed work needs that guidance.
- Read `../../trackers/github-task/SKILL.md` only for tracked work, requested persistence, or repository policy.
- Use selective product acceptance only when an extended decision, regulated or high-impact flow, or repository policy requires it. Read `../../product/shape/references/product-acceptance.md`. Ordinary delivery ends with scenario evidence and no receipt.
- Apply the policy's finding and verification rules. Revalidate only evidence invalidated by the final delta.

For a campaign, provide its immutable outcome, scope, exclusions, evidence, target, and governing decision. Normal execution creates no campaign state.

Escalate only an Owner decision, missing authority, protected or irreversible action, or unavailable prerequisite. Give evidence, recommendation, consequence, and exact needed action.
