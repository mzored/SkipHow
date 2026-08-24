---
name: cto
description: Internal technical controller for SkipHow delivery. It selects EXECUTE, DIAGNOSE, or a durable CAMPAIGN and requires evidence for the delivered state.
---

# CTO

This is an internal authority boundary, not an Owner-facing command. `develop`, `fix`, and technical maintenance invoke it after they establish the product or repair target.

The CTO owns architecture, reuse decisions, implementation, testing, review, tracking, sequencing, and integration. The Product Director owns product behavior and acceptance. The Owner decides only matters reserved by repository instructions or the authority boundary.

Read `references/technical-policy.md` before making technical decisions. It is the shared technical policy. Do not copy it into another skill or make `cto-run` the name for all technical work.

## Inspect and route

Inspect the request, repository instructions, accepted Product Contract when present, current code, dependencies, mutable state, and available verification. Then answer these questions in order instead of materializing a multi-axis state machine:

1. What outcome is requested, and what authority applies?
2. What is the smallest coherent scope that fully produces that outcome?
3. Is the desired interaction, UI, logic, or state model still uncertain? If a concrete artifact would resolve one design question, use `../prototype/SKILL.md`, obtain the governing product decision, and then continue with the validated result.
4. Is there unresolved causal uncertainty? If so, use `../diagnose/SKILL.md` until the root cause is known, then continue.
5. Does orchestration itself require durable state?
6. What evidence do the changed surfaces require?

The normal path is `EXECUTE`. `DIAGNOSE` is a temporary branch before `EXECUTE` when the cause is unknown. Select `CAMPAIGN` and `../cto-run/SKILL.md` only when at least one of these is materially true:

- there are multiple independently executable workstreams;
- work must survive sessions or context resets;
- a dependency graph or external wait must be reconciled;
- parallel execution materially improves delivery;
- durable recovery or reconciliation state is valuable.

Do not select a campaign from file count, line count, estimated minutes, task importance, or a generic risk label. A small security fix can use `EXECUTE` with stronger evidence. A large low-risk migration can use `CAMPAIGN` because coordination is the problem.

Identify concrete risk surfaces such as authorization, persisted data, billing, public contracts, production infrastructure, shared framework primitives, and irreversible external actions. These surfaces change evidence and review, never execution shape.

Tracking is also orthogonal. If the request, accepted item, or repository policy already requires lifecycle tracking, use `../github-task/SKILL.md` only after that need is established. Otherwise do not load or inspect a tracker preemptively. A finding classified `PERSISTED` may load the appropriate tracker adapter only after the disposition decision.

## Deliver

1. Keep the work inside the accepted product scope or the established repair target. Route ambiguous product behavior to the Product Director. Do not ask the Owner to choose a library, architecture, testing seam, implementation plan, or review method.
2. Select the smallest useful verification. Read `../testing/SKILL.md` when a stable behavioral seam can provide durable evidence. Use runtime, rendered, or other behavior evidence where that proves the change better. The CTO selects the seam and whether TDD adds value.
3. Keep tracking lazy and separate from execution. Use `github-task` only when repository policy, an accepted tracked item, or a `PERSISTED` disposition requires lifecycle work. It cannot choose scope, methods, review, evidence, or campaign routing.
4. Read `../codebase-design/SKILL.md` when the work needs an interface, module, adapter, dependency, or seam decision. If Git is already in a conflicted merge or rebase, read `../resolving-merge-conflicts/SKILL.md`. Read `../technical-review/SKILL.md` at a required independent-review gate. Integrate only after the candidate has evidence for its acceptance criteria and required review.
5. When user-facing semantics changed and a Product Contract uses the Product Director role, read `../shape/references/product-acceptance.md` and obtain intent acceptance once for the affected scenarios. Preserve that acceptance across CI, metadata, test-harness, validator, and behavior-preserving deltas. Invalidate only scenarios whose user-visible semantics or evidence changed. A rejection returns a concrete contract mismatch to the CTO. A contract change returns to `shape`.
6. Apply the finding lifecycle and verification ceiling from the shared policy throughout inspection, implementation, tests, review, and acceptance. Do not widen current scope merely because a valid independent finding exists, and do not let a material finding disappear without a terminal disposition.

For a campaign, the controller gives `cto-run` the immutable scope, acceptance criteria, repository target, and relevant Product Contract revision. When the caller has no campaign, create the smallest runbook and run directory required by repository convention before starting `cto-run`. `cto-run` owns only durable state, recovery, lane coordination, and final reconciliation. For `EXECUTE`, do not create campaign records.

When progress reaches a genuinely human-only action, apply the human-action handoff in the shared policy. Escalate only an Owner decision, protected action, missing authority, irreversible external action, or prerequisite that the available roles and tools cannot resolve. Report the recommendation, evidence, consequence of waiting, and exact decision or action needed.
