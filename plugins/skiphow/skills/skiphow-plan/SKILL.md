---
name: skiphow-plan
description: Prepare an idea or substantial change for implementation with research, a reviewed specification, vertical slices, and an execution prompt. Explicit invocation requests durable planning records; ordinary read-only planning stays read-only. Stop before implementation.
---

# SkipHow plan

Prepare work that another agent can execute without rediscovering settled decisions. Before consequential work, have the [SkipHow CTO kernel](../skiphow/SKILL.md) in context. Read it if absent. It remains responsible for technical judgment and owner questions.

Explicit invocation of this skill requests a specification and planning records in the project's authorized tracker. Selecting it automatically for a read-only planning request grants no writes. An explicit read-only constraint takes precedence over the durable default. Keep implementation, commits, and delivery outside this workflow.

Use [product](../skiphow/references/product.md) to recover the intended outcome, current behavior, constraints, exclusions, and acceptance conditions. Investigate questions before taking genuinely unresolved product choices to the owner. Keep dependent behavior undecided until its answer arrives, and prepare independent work meanwhile.

Use [technical design](../skiphow/references/technical-design.md) for consequential choices and build-versus-reuse analysis. Establish what the repository already provides before proposing new logic or dependencies. Research current primary sources where they settle a material uncertainty. Choose engineering mechanisms yourself and record enough rationale for another agent to preserve the decision.

Apply [delegation](../skiphow/references/delegation.md) to substantial independent research and to slicing. Distinguish a tracker grouping, a verifiable end-to-end product slice, and a delegate assignment where they differ. The next ready assignments should be executable from the plan, with boundaries grounded in the inspected workload, necessary context, expected output, verification, and integration. A broad work package alone does not establish a bounded assignment. Include acceptance criteria, relevant evidence, exclusions, and real dependencies. Show which independent preparation or assignments can proceed in parallel and where shared writes or integration constrain them. Keep open product decisions explicit. Keep later boundaries provisional when earlier results determine them, and keep small cohesive work direct. Cover integration, migration, rollback, and operation where the proposed behavior needs them. One pass is a sizing goal, not a promise; adjust boundaries when evidence warrants it.

Have an independent agent review the proposed work against the request and source evidence using [verification](../skiphow/references/verification.md). Check missing outcomes, conflicting decisions, assignment feasibility, real dependencies, and verifiable acceptance conditions, including whether the planned review and integration workload is itself bounded. Resolve supported findings before finalizing the records. If independent review is unavailable, finish the preparation and report review as unverified.

Use [tracked work](../skiphow/references/tracked-work.md) to reconcile existing records and save the plan when authorized. Use GitHub Issues within the established audience unless the project uses another authorized tracker. Write engineering artifacts in English. If tracking is unavailable or unsafe, return complete issue drafts in the authorized private channel and the specific blocker.

Return the specification and issue links or drafts, material decisions, review evidence and unresolved limits, and a short execution prompt naming the accepted records, intended destination, scope, and existing authorization boundaries. The prompt should start execution without repeating the CTO policy or granting new protected actions. Stop before implementation.
