---
name: skiphow-plan
description: Prepare the whole requested scope for implementation with research, a completed product interview, a reviewed specification, bounded tasks, and an execution prompt suited to its size. Explicit invocation requests durable planning records; ordinary read-only planning stays read-only. Stop before implementation. If context was compacted while this workflow governed, reopen this file and the SkipHow CTO skill before the next consequential action.
---

# SkipHow plan

Prepare the whole requested scope so another agent can execute it without rediscovering settled decisions. Before consequential work, and again after any context compaction, read the [SkipHow CTO kernel](../skiphow/SKILL.md) unless its full text is already in context; a summary is not its text. It stays responsible for technical judgment and owner questions.

## What the request grants

Explicit invocation of this skill requests a specification and planning records in the project's authorized tracker. Selecting it automatically for a read-only planning request grants no writes, and an explicit read-only constraint overrides the durable default. Implementation, commits, and delivery stay outside this workflow. Completion means the requested scope is prepared, not that its current questions and drafts are recorded.

Interview answers and grants for planned actions belong in the execution records; they do not switch this session to execution. An explicit request to execute after planning authorizes that switch once preparation is ready, within host restrictions and existing grants, without another confirmation. Otherwise return the plan and launch prompt, then stop.

## The interview

Use [product](../skiphow/references/product.md) to recover the intended outcome, current behavior, constraints, exclusions, and acceptance conditions. Investigate before taking an open product choice to the owner. Carry the interview through the questions the answers reveal until no known product choice in the accepted execution scope stays open. Keep settled answers distinct from recommendations and assumptions.

Leave dependent behavior undecided until its answer arrives, and prepare independent work meanwhile. A pending answer keeps the interview open. When no useful independent preparation remains, wait through available host controls or return a waiting status with the question and what resumes the work. Resume on the answer, including the choices it newly exposes. Elapsed time, a saved draft, or a ready independent task does not complete preparation. Later discoveries can still need a decision during execution.

## The specification

Use [technical design](../skiphow/references/technical-design.md) for consequential choices and build-versus-reuse analysis. Establish what the repository and platform already provide before proposing new logic or dependencies, and settle material uncertainty from current primary sources. Choose engineering mechanisms yourself and record enough of the reason for another agent to keep the decision. Plan the least that delivers the outcome: no tests, tooling, flags, layers, or documents the outcome does not need.

For user-facing work, carry the relevant journeys, design direction, and reuse constraints into the specification and the tasks that depend on them. Separate accepted product decisions from proposals and engineering judgments, and keep enough source context for an implementer to understand what must hold and why. Record decisions and acceptance conditions apart from the specialist capability that helped reach them; the executing agent picks from the capabilities its own host has.

## Tasks

Slice with [delegation](../skiphow/references/delegation.md#the-size-of-a-unit), and use it for substantial independent research. Every execution task is one that a single implementation agent can carry from its record to a verified, reviewable candidate within normal tool calls and review corrections. A grouping record collects tasks and is never dispatched. Size every task in the accepted scope now, and split one that needs several agents or defers its own split. Small cohesive work stays one task. Size is a judgment from evidence, and the executing lead reslices a task that proves larger.

Judge one-agent feasibility from the context needed, how many materially different changes there are, and the checking, review, and integration load together. Where workload is uncertain, use existing measurements, comparable finished work, or a look at representative source; a full inventory is not needed. Split where reliability and total cost improve, counting repeated context, coordination, and integration. File, line, and acceptance counts are no universal limit.

Where the work has no proven path through its components, choose a thin first slice with real behavior. Build only the structure that slice needs, verify the working path, then expand through the remaining slices. In a mature project, reuse the established path. The first working behavior keeps required safety, integrity, and compatibility. Name what its result unblocks and which later assumptions the lead must recheck at dispatch. There is no universal foundation stage.

Write tasks to the [task contract](../skiphow/references/tracked-work.md#writing-one-that-survives-the-wait) in tracked work. Show real blocking results, available parallel work, and shared writes, runtime resources, or integration capacity that limit dispatch. Keep open product decisions explicit.

## Review

Get one independent review of the specification and task set against the request and source evidence, by the bar in [review](../skiphow/references/review.md), unless the plan is small and low risk, where a cold self-review against the same list is enough. Ask it to look for:

- Missing or uncovered outcomes, conflicting decisions, and acceptance that cannot be checked.
- Consequential choices taken without the owner, and changes to existing behavior or dependent state.
- Invented or missing dependencies, overlapping tasks, and prescription the executor does not need.
- Tasks too large for one agent, where the finding names the load and a smaller independently verifiable cut.
- Tests, tooling, or records the outcome does not need.

Technical slicing cannot shrink the execution scope. Fix what qualifies. Re-review only the fixes that change a consequential decision or task boundary, never the whole plan again, and stop when a round returns nothing that qualifies. If independent review was unavailable, report it as `UNVERIFIED` with the plan's readiness.

## Records and handoff

Use [tracked work](../skiphow/references/tracked-work.md) to reconcile existing records and save the plan when authorized. Use GitHub Issues within the established audience unless the project uses another authorized tracker. Write engineering artifacts in English. If tracking is unavailable or unsafe, return complete issue drafts in the authorized private channel with the blocker. Keep the plan in the tracker, not in repository files. Analysis and plan files written while working are deleted when the work lands, unless the owner asked for that file as the durable record.

Return the specification and issue links or drafts, material decisions, the review result, unresolved limits, and whole-scope readiness. Account for any implementation candidate already created; a planning handoff does not erase that work. Return an execution launch when the scope is ready, or for a ready subset the owner explicitly selected. Keep an unresolved interview open rather than offering a partial launch in its place. Choose ordinary SkipHow for small cohesive work and longrun for substantial work that needs coordinated slices. Keep an execution workflow the owner already selected. Use the target host's explicit invocation syntax and this launch shape, replacing the skill with the selected one.

```text
$skiphow-longrun
Deliver the accepted implementation scope in <plan-reference> to <agreed-destination>.
```

Replace placeholders with concrete accepted records and the agreed destination. Add only an otherwise missing project location, owner-selected subset, or necessary run constraint, keeping where its authorization came from. Requirements and dependencies stay in the task records; execution policy stays in SkipHow. Grant no new protected actions. Keep unfinished preparation, inaccessible sources, and known human prerequisites explicit as blockers to the affected scope; a saved plan proves neither readiness nor permission. Stop before implementation.
