# Prior art

SkipHow exists because I used the popular agent frameworks on my own work first and kept hitting the same wall. This page records what I took from each of them, what I left out, and why. It is not a benchmark. None of these projects has been run side by side with SkipHow on the same task, and nothing here claims any of them is worse at what it set out to do.

## What I tried

Star counts are a rough measure of how many people are solving this problem, not of fitness. They were read on 2026-08-29 and will be stale soon after.

| Project | Stars | What I kept or studied | What I left out |
| --- | --- | --- | --- |
| [Superpowers](https://github.com/obra/superpowers) | 279,011 | Isolated review, bounded repair, safe worktree and conflict practice | Mandatory brainstorming, approval gates, test-first as a universal stage |
| [Matt Pocock's skills](https://github.com/mattpocock/skills) | 240,118 | Small methods, one discipline each; semantic discovery; diagnosis driven by an observable loop | The setup interview, the named-invocation orchestration skills, the owner-visible spec and ticket chain |
| [Paperclip](https://github.com/paperclipai/paperclip) | 79,564 | External task state, idempotent reconciliation, dependency semantics | A server, a task database, a company model, a dashboard |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | 66,569 | Stating intent clearly for a material contract change; thin host packaging | Proposal, specification, design and task artifacts for every change |
| [BMAD](https://github.com/bmad-code-org/bmad-method) | 52,420 | One entry point; planning depth chosen from the work | Personas, menus, repeated handoffs, standing ledgers |
| [GSD](https://github.com/open-gsd/gsd-core) | 8,845 | Fresh context per unit, dependency-aware parallelism, proportional depth | A large command tree, mandatory phases, several state files |
| [Mesa](https://github.com/msoedov/mesa) | 69 | Atomic ownership, event-driven wake-up | Fixed roles, an embedded tracker, company simulation |
| [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin) | 1 | Provenance, and keeping facts separate from assumptions | Standing personas, mandatory scoring |

## What went wrong for me

Every one of these got something right. The problem was consistent and it was not quality.

They ask the person who owns the product to operate the software process. I was choosing between `/plan`, `/spec` and `/implement` before I had finished saying what I wanted. I was approving ticket granularity, spec wording and test seams for changes I could describe in one sentence. On a small fix the ceremony cost more than the fix.

The maintainers of the closest project say the same thing in their own tracker. All three of these were open on 2026-08-29:

- [issue #962](https://github.com/mattpocock/skills/issues/962) reports enum values and architecture terms shown to nontechnical users, and proposes asking about visible outcomes before recording the technical mapping.
- [issue #883](https://github.com/mattpocock/skills/issues/883) reports blocking questions from setup, TDD, review and implementation that deadlock when no human is attached.
- [issue #885](https://github.com/mattpocock/skills/issues/885) reports missing completion and escalation seams when the skills run under an external orchestrator.

So the gap is not that the methods are bad. It is that the owner is expected to drive them.

## What SkipHow does instead

The owner kernel keeps authority, autonomy, preservation of unrelated work and honest completion in context at all times. The same agent reads whichever focused methods help the current request. Methods are not routes, stages, commands or personas, and the owner never picks one.

That leaves a different division of labour. You decide visible behavior, priority, cost, risk, privacy and rollout. SkipHow decides libraries, schemas, tests, branches, decomposition and review, and comes back only when your answer would change one of your six, when an action needs a grant only you can give, or when only a person can do it.

## The primary influence, and the licence

[Matt Pocock's skills](https://github.com/mattpocock/skills) is the main modular-method influence on SkipHow 2.x. It showed that engineering guidance splits into small, adaptable disciplines rather than one framework that owns the whole process. SkipHow adapts that modularity inside one portable owner skill rather than copying the package layout.

Adapted ideas include small single-discipline methods, semantic discovery with progressive disclosure, research from high-trust primary sources, diagnosis driven by an observable feedback loop, vertical slices with proportionate tests, intent-aware conflict resolution, code review as independent judgment, and concise handoffs when work must survive an interruption.

The upstream repository is MIT licensed. The exact adapted paths and the inspected revision are recorded in [`SOURCES.json`](../plugins/skiphow/SOURCES.json), and the distributed package carries the source licence and copyright in [`THIRD_PARTY_NOTICES.md`](../plugins/skiphow/THIRD_PARTY_NOTICES.md). An idea taken without source text is credited here and written in SkipHow's own words.

## Ideas read and rejected

Rejection is part of the record, so the same argument does not get reopened.

`grilling` is where SkipHow's question frontier comes from: ask the decisions whose prerequisites are settled, then recompute after the answers. The interview around it is not adapted. `grilling` runs until every branch of a design tree has been visited; SkipHow stops at the first point where nothing material is open, and never opens a round for a choice the project or a source can settle on its own.

Superpowers' `brainstorming` was read and rejected whole. It gates every task behind a human approving the design, including the tasks it calls too simple to need one, which is the opposite of this project's boundary.

`to-spec` and `to-tickets` were read twice and rejected twice. Both require the owner to approve engineering shape, one a specification and the other ticket granularity. SkipHow owns both.

A spec-to-tickets chain and an implement-spec fork were considered as orchestration and rejected for the same reason: they turn a product request into a sequence the owner has to supervise.

## The adoption rule

An idea from another project becomes a focused method or a kernel invariant only when it answers an observed task need or protects a high-risk boundary. Good practice somewhere else is not enough. The default stays the least process that reaches a fresh, verified result while preserving the owner's authority and unrelated work.

The reasoning behind each rule that survived is in [decision history](decisions.md), and what real runs have and have not shown is in [current evidence](evidence.md).
