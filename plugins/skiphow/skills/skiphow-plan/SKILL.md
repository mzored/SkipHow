---
name: skiphow-plan
description: Prepare an idea or substantial change for implementation with research, a reviewed specification, vertical slices, and an execution prompt. Explicit invocation requests durable planning records; ordinary read-only planning stays read-only. Stop before implementation.
---

# SkipHow plan

Prepare work that another agent can execute without rediscovering settled decisions. Before consequential work, have the [SkipHow CTO kernel](../skiphow/SKILL.md) in context. Read it if absent. It remains responsible for technical judgment and owner questions.

Explicit invocation of this skill requests a specification and planning records in the project's authorized tracker. Selecting it automatically for a read-only planning request grants no writes. An explicit read-only constraint takes precedence over the durable default. Keep implementation, commits, and delivery outside this workflow.

Use [product](../skiphow/references/product.md) to recover the intended outcome, current behavior, constraints, exclusions, and acceptance conditions. Investigate questions before taking genuinely unresolved product choices to the owner. Keep dependent behavior undecided until its answer arrives, and prepare independent work meanwhile.

Use [technical design](../skiphow/references/technical-design.md) for consequential choices and build-versus-reuse analysis. Establish what the repository already provides before proposing new logic or dependencies. Research current primary sources where they settle a material uncertainty. Choose engineering mechanisms yourself and record enough rationale for another agent to preserve the decision.

Apply [delegation](../skiphow/references/delegation.md) to substantial independent research and to slicing. Each slice should deliver an observable outcome within a bounded agent assignment. Include acceptance criteria, relevant evidence, exclusions, and real dependencies. Keep open product decisions explicit. Cover integration, migration, rollback, and operation where the proposed behavior needs them. Split further when evidence shows an assignment is too large; one pass is a sizing goal, not a promise.

Have an independent agent review the proposed work against the request and source evidence using [verification](../skiphow/references/verification.md). Check missing outcomes, conflicting decisions, unworkable slices, and unverifiable acceptance conditions. Resolve supported findings before finalizing the records. If independent review is unavailable, finish the preparation and report review as unverified.

Use [tracked work](../skiphow/references/tracked-work.md) to reconcile existing records and save the plan when authorized. Use GitHub Issues within the established audience unless the project uses another authorized tracker. Write engineering artifacts in English. If tracking is unavailable or unsafe, return complete issue drafts in the authorized private channel and the specific blocker.

Return the specification and issue links or drafts, material decisions, review evidence and unresolved limits, and a short execution prompt naming the accepted records, intended destination, scope, and existing authorization boundaries. The prompt should start execution without repeating the CTO policy or granting new protected actions. Stop before implementation.
