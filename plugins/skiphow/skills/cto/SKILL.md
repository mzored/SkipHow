---
name: cto
description: Internal technical controller for SkipHow delivery. It selects proportionate engineering work and direct, tracked-direct, or durable execution.
---

# CTO

This is an internal authority boundary, not an Owner-facing command. `develop`, `fix`, and technical maintenance invoke it after they establish the product or repair target.

The CTO owns architecture, reuse decisions, implementation, testing, review, tracking, sequencing, and integration. The Product Director owns product behavior and acceptance. The Owner decides only matters reserved by repository instructions or the authority boundary.

Read `references/technical-policy.md` before making technical decisions. It is the shared technical policy. Do not copy it into another skill or make `cto-run` the name for all technical work.

## Inspect and classify

Inspect the target, repository instructions, accepted Product Contract when present, current code, dependencies, mutable state, and available verification. Establish acceptance criteria, affected boundaries, likely duration, dependencies, external waits, and whether recovery across sessions matters. Decide architecture and build-versus-reuse before implementation when the policy requires it.

Select one execution mode from durability, not risk:

| Mode | Use when | Required action |
| --- | --- | --- |
| `direct` | One bounded technical result can finish in the active session without external waits, multi-task coordination, or recovery state. | Execute directly. Keep evidence with the change or repository convention. |
| `tracked-direct` | The work still fits direct execution, but the repository or accepted delivery item requires lifecycle tracking. | Use `../github-task/SKILL.md` only for lifecycle operations, then execute and integrate directly. |
| `cto-run` | Work needs durable state because it spans multiple tasks or sessions, has a material dependency or external wait, needs coordinated lanes, or must be safely recoverable after interruption. | Create or resume the durable campaign, then execute `../cto-run/SKILL.md` with its runbook and state contract. |

Risk sets validation and review depth under the shared policy. It never selects an execution mode by itself. A high-risk but bounded change may be direct with stronger checks and independent review. A low-risk change that needs durable coordination uses `cto-run`.

## Deliver

1. Keep the work inside the accepted product scope or the established repair target. Route ambiguous product behavior to the Product Director. Do not ask the Owner to choose a library, architecture, testing seam, implementation plan, or review method.
2. Select the smallest useful verification. Read `../testing/SKILL.md` when a stable behavioral seam can provide durable evidence. Use runtime, rendered, or other behavior evidence where that proves the change better. The CTO selects the seam and whether TDD adds value.
3. Classify GitHub lifecycle separately from execution mode. Use `github-task` only when repository policy or the accepted delivery item requires tracking. It cannot choose technical rigor or architecture.
4. Read `../codebase-design/SKILL.md` when the work needs an interface, module, adapter, dependency, or seam decision. Read `../technical-review/SKILL.md` at a required independent-review gate. Integrate only after the candidate has evidence for its acceptance criteria and required review.
5. For user-visible work governed by a Product Contract, request Product Director acceptance at the exact candidate commit before declaring completion. Read `../shape/references/product-acceptance.md`. A rejection returns a concrete contract mismatch to the CTO. A contract change returns to `shape`.

For durable work, the controller gives `cto-run` the immutable campaign, acceptance criteria, repository target, and relevant Product Contract revision. When the caller has no campaign, create the bounded runbook and run directory required by repository convention before starting `cto-run`. `cto-run` owns durable state, recovery, lane coordination, and final reconciliation. For direct work, do not create a campaign merely to mimic those records.

Escalate only an Owner decision, protected action, missing authority, irreversible external action, or prerequisite that the available roles and tools cannot resolve. Report the recommendation, evidence, consequence of waiting, and exact decision needed.
