# Prior art

SkipHow exists because I used the popular agent frameworks on my own work first and kept hitting the same wall. This page records what I took from each of them, what I left out, and why. It is not a benchmark. None of these projects has been run side by side with SkipHow on the same task, and nothing here claims any of them is worse at what it set out to do.

## What I tried

| Project | Mechanism kept or studied | Boundary SkipHow chose instead |
| --- | --- | --- |
| [Superpowers](https://github.com/obra/superpowers) | Scoped re-review, worktree practice, naming the break a test would catch, checking a finding before acting on it, compact delegate returns | Adaptive method selection instead of mandatory brainstorming, design approval, planning, TDD, and review stages |
| [Matt Pocock's skills](https://github.com/mattpocock/skills) | Small methods, the question frontier, diagnosis from a feedback loop, tests through the caller's interface, the deletion test, vertical slices | No setup interview, no owner-operated spec and ticket chain, no candidate menus |
| [Paperclip](https://github.com/paperclipai/paperclip) | External task state, idempotent reconciliation, dependency semantics | No server, task database, company model, or dashboard |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | Stating intent clearly for a material contract change; thin host packaging | No proposal, specification, design, and task artifacts for every change |
| [BMAD](https://github.com/bmad-code-org/bmad-method) | One governing entry; planning depth chosen from the work | No personas, menus, repeated handoffs, or standing ledgers |
| [GSD](https://github.com/open-gsd/gsd-core) | Fresh context per unit, dependency-aware parallelism, proportional depth | No large command tree, mandatory phases, or parallel state files |
| [Mesa](https://github.com/msoedov/mesa) | Atomic ownership, event-driven wake-up | No fixed roles, embedded tracker, or company simulation |
| [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin) | Keeping the owner's statements, proposals, and assumptions apart | No standing personas or mandatory scoring |
| [Ponytail](https://github.com/dietrichgebert/ponytail) | Sufficient reuse, concrete complexity findings, fixes checked beyond the reported path, replacements that finish their callers | Accepted behavior and total cost govern simplification; no line-count objective, mode, hook, or debt ledger |
| [Addy Osmani's agent skills](https://github.com/addyosmani/agent-skills) | Delete an abstraction before polishing it; a removal takes its tests and docs; stop when doubt stops producing information | No slash-command lifecycle |
| [claude-flow](https://github.com/ruvnet/ruflo), now Ruflo | Parallel reads are safe and parallel writes are not, so one writer per checkout | No coordination runtime |
| [Anthropic's skill authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Leave out what a capable model already knows; keep the skill short | A character limit per file, because a shell read cuts long files |

## What went wrong for me

Every one of these got something right. The problem was consistent, and it was not quality.

They ask the person who owns the product to operate the software process. I was choosing between `/plan`, `/spec` and `/implement` before I had finished saying what I wanted. I was approving ticket granularity, spec wording and test seams for changes I could describe in one sentence. On a small fix the ceremony cost more than the fix.

Users of the closest project reported the same thing. These are user reports, not a project position: on 2026-09-04 the GitHub API gave `author_association: NONE` for all three authors, and all three issues were open.

- [Issue #962](https://github.com/mattpocock/skills/issues/962) reports enum values and architecture terms put to nontechnical users. SkipHow adopted its fix: ask about the visible outcome, then map the answer to the technical term.
- [Issue #883](https://github.com/mattpocock/skills/issues/883) reports blocking questions from setup, TDD, review and implementation that deadlock when no human is attached.
- [Issue #885](https://github.com/mattpocock/skills/issues/885) reports missing completion and escalation seams when the skills run under an external orchestrator.

So the methods were fine. The owner was the one expected to drive them.

## What SkipHow does instead

One CTO kernel stays in context on every request. It holds authority, owner decisions, an engineering standard that keeps the owner's system small, custody of engineering state, and honest completion. The agent opens a focused playbook when the act in front of it calls for one: a test to write, a change to review, work to split, a branch to integrate. Playbooks are not routes, stages, commands or personas. The owner can pick an optional workflow such as plan, bug, or simplify, and the CTO still owns the engineering inside it.

That is orchestration policy. Claude Code or Codex runs the model, tools, sessions and subagents.

That leaves a different division of labour. You decide what people will see, scope, priority, cost, risk, privacy and rollout. SkipHow decides libraries, schemas, tests, branches, decomposition and review. It comes back to you only for an open product choice, an action that needs your grant, work only a person can do, or a blocker outside the project.

## The primary influence, and the licence

[Matt Pocock's skills](https://github.com/mattpocock/skills) is the main influence. It showed that engineering guidance splits into small disciplines, and SkipHow keeps that modularity inside one portable owner skill without copying the package layout. The repository is MIT licensed. The adapted paths and the inspected revision are in [`SOURCES.json`](../plugins/skiphow/SOURCES.json), and the package carries the licence and copyright in [`THIRD_PARTY_NOTICES.md`](../plugins/skiphow/THIRD_PARTY_NOTICES.md). Every idea taken from the other projects is written in SkipHow's own words, with no source text or code. Outside agent tooling, the plan workflow's thin first slice comes from Hunt and Thomas's [tracer bullets](https://www.artima.com/articles/tracer-bullets-and-prototypes), and refactoring in small reviewable units from [Martin Fowler](https://martinfowler.com/bliki/OpportunisticRefactoring.html) and [Google's review practice](https://google.github.io/eng-practices/review/developer/small-cls.html).

Two adopted ideas were later removed. The `wayfinder` claim, where a session marks an item as its own before investigating it, and Paperclip's split between a sub-item and a real dependency both shipped for a while and are gone. Tracker assignment now proves nothing about who holds a lane.

## Ideas read and rejected

I write the rejections down so the same argument does not get reopened.

**Design approval before every task.** Superpowers' `brainstorming` gates work behind a human approving the design, including tasks it calls too simple to need one, and its `writing-plans` asks the owner to confirm the plan and pick the execution machinery. Settled small work gets no confirmation turn here.

**The exhaustive interview.** `grilling` gave SkipHow its question frontier: ask what is answerable now, recommend an answer, recompute after the replies. Its walk through every branch of a design tree, its compulsory fact-finding delegates and its final confirmation did not come along. SkipHow stops at the first point where nothing material is open and never asks what the project or a source can settle.

**The owner approving engineering shape.** `to-spec`, `to-tickets`, the setup interview, and a spec-to-tickets chain each make the owner supervise a specification, ticket granularity or a sequence of engineering steps. SkipHow owns all of that.

**Technical menus.** `finishing-a-development-branch` halts on a three-way choice between merging, opening a pull request and doing nothing. `improve-codebase-architecture` and `retro` end by handing the user candidates to pick from. Here the CTO decides and carries the change through. The typed-confirmation ritual for discarding work went too, because the grant rule for material deletion already covers it.

**New record formats in someone else's project.** `triage`'s `.out-of-scope/` directory, the architecture skill's HTML report, `idea-refine`'s "not doing" list, `wayfinder`'s map and one-ticket-per-session rule, a dated handoff file per branch, and Ponytail's debt ledger each add a record the owner keeps paying to read. SkipHow uses the project's own tracker, and Git holds what Git can hold. The purpose of `.out-of-scope/` survives: tracked work searches closed records, so a refused idea is reported as refused instead of built.

**Coordination runtimes.** GSD's state locks, Paperclip's leases and budgets, `claude-presence`'s resource claims, `mcp_agent_mail`'s file reservations, and the port arbitration in Paperclip and humanlayer are code. Leases outlive their operation and claims outlive a dead session, and SkipHow ships no runtime to manage them. Prose cannot establish who owns a port.

**Fixed counts and tiers.** Superpowers' three-tier model table, fix-round escalation, round caps, fifteen-line return cap and report file per assignment, and GSD's numeric guards, per-task commits, checkpoint records and blanket stash ban stop or pad work at a number, and a cap can hide findings. SkipHow routes each delegate by consequence and cost.

**Stopping on every blocker.** Superpowers' `executing-plans` stops to ask whenever something blocks. The kernel keeps independent work moving while one part waits.

**Standing roles and scores.** Autonomous PM's assumption mapper, BMAD's personas and Mesa's fixed roles keep a role alive between tasks, and score tables make guesses look like measurements. SkipHow argues order in sentences.

**A command surface.** Slash commands in the shape Addy Osmani's repository uses were built for SkipHow and removed before release. Half of them restated policy the methods already carried, and Codex plugins have no command surface.

**Test policies that only add.** Defense in depth at every layer, coverage floors, a regression test for every bug, blanket DRY, and "build the check before writing the rule" each add code that stays. So does a separate coding-standards file for reviewers. A test here has to name the break it would catch, and code shape goes to the linter the project already runs.

**Shortest code as the goal.** Ponytail's line-count objective, unconditional native reuse and intensity modes optimize something other than the owner's result. SkipHow keeps the accepted behavior and minimizes total cost.

**A switch saying humans write code here.** It would make the kernel's account of every branch depend on configuration nobody maintains. A project where a human writes code is a reason to reopen the decision.

## The adoption rule

An idea from another project becomes a playbook method or a kernel rule only when it answers an observed task need or protects a high-risk boundary. Good practice somewhere else is not enough. The default stays the least process that reaches a fresh, verified result while keeping the owner's authority and unrelated work intact.

The reasoning behind each surviving rule is in [decision history](decisions.md), and what real runs have shown is in [current evidence](evidence.md). The per-release reading notes, with source revisions and dates, are in the [pre-cleanup snapshot](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/prior-art.md) and, for the newest releases, in [this file's history](https://github.com/mzored/SkipHow/blob/2f72c7f/docs/prior-art.md).
