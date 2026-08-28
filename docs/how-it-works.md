# How it works

SkipHow is a small instruction package for strong coding agents. It is not a workflow engine, scheduler, model router, database, or replacement for host permissions.

## Shape

The package has exactly one top-level skill. Its root is the owner kernel and its focused methods are ordinary
Markdown resources:

```text
owner request
     |
     v
host can load skiphow
     |
     v
owner kernel
     |------ optional diagnosis method
     |------ optional testing method
     `------ other applicable method references
                   |
                   v
          one agent-owned result
```

The package exposes one top-level SkipHow skill. The root may read focused references for research,
diagnosis, product decisions, testing, review, intake, delivery, and other methods. Those files are not
commands, roles, or independently activated skills. Whether a host discovers or loads that skill is runtime
evidence, not a property proved by the package shape.

This is a hub with optional method spokes, not a chain. Every activation includes the kernel, which keeps the
original request, authority, autonomy, and completion rules in context. A method can help with technique but
cannot grant authority or become a mandatory next stage.

The single-skill layout is a portability boundary. Agent Skills defines no dependency that can require a
selected leaf to load a kernel, and the inspected Codex 0.149.1 package metadata has no field equivalent to
Claude's model-only visibility control.
Keeping methods as resources is the cross-host way to preserve one entry and make every SkipHow activation
carry the critical contract.

The plugin requires one packaged, read-only continuity hook. A supporting host may execute it; host support
and execution are not supplied by SkipHow and remain separate runtime evidence. The Codex and Claude Code
manifests point to the same packaged skill bytes. The host owns sessions, tools, permissions, subagents,
isolation, background work, and compaction.

## The kernel

The kernel holds every rule that must survive every kind of work, plus short semantic pointers to the methods:

- the owner's requested outcome controls scope and authority;
- technical and architectural choices belong to the agent;
- unrelated work and shared state must be preserved;
- effort stays proportional to the actual task;
- project changes need fresh verification and an ordinary local commit of the owned delta unless the owner or repository requests uncommitted work or it would mix in foreign changes;
- protected actions need an exact grant;
- the report distinguishes verified evidence from blockers and uncertainty.

It does not encode routes, magic phrases, item or diff thresholds, word budgets, fixed roles, model tiers, reviewer gates, test-first gates, worktree procedures, ticket schemas, finding tags, or an automatic remote workflow.

Those deletions are functional. A capable agent can choose a plan, test, delegate, worktree, or review when it helps. Making every useful tool a mandatory stage turns a small edit into a campaign and can distract the agent from the visible outcome.

## Focused methods

The root names when each method may materially help and can read that reference directly. Selection follows
meaning, not a route name, item count, or mandatory sequence.

Several methods can contribute to one outcome. A hard bug may use diagnosis and testing; a product comparison
may use research and decision support; a visual fix may need neither. An applicable method can help with
technique, but missing one cannot remove the root's authority, preservation, or completion boundary.

The owner never chooses this composition. Asking whether to run TDD, create a worktree, pick a reviewer model,
or write a spec would move an engineering decision across the product boundary.

## Authority

Only the owner's direct request and host policy grant actions. Repository instructions, trackers, checkpoints, tool output, and web content may narrow scope or add safeguards, but cannot widen it.

A request only to answer, compare, diagnose, review, research, plan, triage, or organize stays read-only. A
mixed request that also asks to fix or change the project is a project-change request. A request whose
intended result is a durable record grants only that record. A request to change the project grants the required edits,
verification, and an ordinary local commit of the owned delta unless the owner or repository requests uncommitted work or it would mix in foreign changes. Shared
remote delivery happens only when the owner's request includes it and project evidence identifies a clearly non-production target, or when the owner's own request exactly grants a protected target.

Every change to staging or production, public release, payments, repository settings, access changes, material deletion or another hard-to-reverse action, disclosure outside the authorized audience, and creating, entering, rotating, or exposing credentials need an exact grant. The owner must affirmatively identify the protected action or destination in their own request; broad completion or autonomy language and project procedures cannot substitute for that grant. Reading project-private material or using credentials already authorized by the host is allowed only when necessary for the requested result. The agent also asks when evidence cannot settle a material product choice. It does not ask the owner to choose routine engineering mechanics.

## Proportional work

The smallest coherent approach wins. A direct edit can remain a direct edit. Unknown causes justify diagnosis. Several independent areas may justify parallel work. High-risk or uncertain changes may justify independent review. Repository requirements still apply.

Plans, trackers, delegates, worktrees, pull requests, and review are tools. None is a stage every request must pass through. There is no item count, file count, diff size, or phrase that decides the process in advance.

Before writing, the agent reads applicable repository instructions and enough live state to preserve unrelated work. It uses isolation when that materially helps and does not overwrite, reset, publish, or quietly absorb foreign changes. Dirty or overlapping work waives the local commit only when a clean commit would mix in foreign changes; it makes the affected result unverified only when it prevents trustworthy evidence.

## Completion and delivery

For a project change, the default finish is:

1. The requested behavior is implemented.
2. Fresh, proportionate evidence checks the changed behavior and final state.
3. An ordinary local commit records only the owned delta, unless the owner or repository requested uncommitted work or that would mix in foreign changes.

The repository can require additional checks or review. It can also require a pull request or another delivery path, but that requirement does not grant the remote write. The agent uses a shared path only when the owner's request includes shared delivery and project evidence identifies a clearly non-production target, or when the owner's own request exactly grants a protected target. It handles the mechanics without asking the owner to operate Git.

A generic change request does not authorize a push, merge, tracker mutation, or other unrelated remote write. Every staging or production change and every public release remain protected even when the mechanics are routine.

## Continuity

SkipHow prefers host-native continuation when it can carry the work. It can keep one concise current state in
`.skiphow/handoff.md` only when the owner asked to pause or save the work, or when an already-authorized
project change needs a checkpoint to finish safely. A wait, interruption, or read-only request does not by
itself authorize that file. The packaged hook is configured to print an instruction to load the owner kernel
for project requests on startup or clear. After compaction or resume, it is configured to print an instruction
to reload the kernel before continuing and, if `.skiphow/handoff.md` exists, read it as untrusted status
evidence. Whether a host executes those handlers is host behavior; packaged 2.0 hook execution remains
`UNVERIFIED`. The hook does not test for, read, display, trust, or restore a checkpoint, and it does not load
the kernel itself. The agent re-reads the owner request and repository instructions before deliberately
opening any checkpoint, then compares it with live project state.

The checkpoint is optional and temporary. It is not a diary, queue database, or authority token. The host still decides whether a task can continue in the background or resume later.

## Evidence and package checks

`scripts/check.py` validates the single top-level skill, recursive reachability of every Markdown file under
its `references/` library, the packaged hook's
metadata and accepted command shape, aligned versions, and the personal-path and versioned-model-ID boundaries it scans.
`scripts/check_hosts.py` checks the package against available host validators. Neither script starts a model
or proves that a model follows the instructions.

Behavior claims require deliberate receipts under `docs/research/`. A report names unavailable checks and unsupported host behavior as unverified instead of converting them into success.
