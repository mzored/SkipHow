# Prior art review

Reviewed on 2026-08-25 against SkipHow commit [`a6d34a25614bc0723517032af617b0782158df4d`](https://github.com/mzored/SkipHow/commit/a6d34a25614bc0723517032af617b0782158df4d).

This review answers a narrow question. Which ideas help an owner turn product intent into finished work without making every request follow a software development ceremony? It does not rank the projects or claim that SkipHow contains all of them.

## Review method and limits

The audit inspected checked-out source at the exact commits below. Commit identity, manifests, workflow files, tests, and licenses were inspected directly. Those source findings are `VERIFIED`.

| Project | Audited source | Reported version | License at the audited commit |
| --- | --- | --- | --- |
| GSD | [`f7df920681f233ae0fe064ee659550bdf41ff708`](https://github.com/open-gsd/gsd-core/tree/f7df920681f233ae0fe064ee659550bdf41ff708) | Package version 1.11.0 | [MIT](https://github.com/open-gsd/gsd-core/blob/f7df920681f233ae0fe064ee659550bdf41ff708/LICENSE) |
| OpenSpec | [`6926ccb18afa4ff621112813e9968334576ee11a`](https://github.com/Fission-AI/OpenSpec/tree/6926ccb18afa4ff621112813e9968334576ee11a) | Package version 1.10.0 | [MIT](https://github.com/Fission-AI/OpenSpec/blob/6926ccb18afa4ff621112813e9968334576ee11a/LICENSE) |
| Superpowers | [`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797) | Tag 6.3.0 | [MIT](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/LICENSE) |
| Matt Pocock skills | [`6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76) | Package version 1.2.3, 39 commits after its tag | [MIT](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/LICENSE) |
| BMAD | [`1479a58b2d604382541a184cd59105a580f4e48a`](https://github.com/bmad-code-org/BMAD-METHOD/tree/1479a58b2d604382541a184cd59105a580f4e48a) | Package version 6.11.0 | [MIT](https://github.com/bmad-code-org/BMAD-METHOD/blob/1479a58b2d604382541a184cd59105a580f4e48a/LICENSE) |
| Paperclip | [`2862e1848452d578a27054b66c433e0abc2315aa`](https://github.com/paperclipai/paperclip/tree/2862e1848452d578a27054b66c433e0abc2315aa) | No release version used for this review | [MIT](https://github.com/paperclipai/paperclip/blob/2862e1848452d578a27054b66c433e0abc2315aa/LICENSE) |
| Mesa | [`1bd047c3d8727ad685b374f0947850a123db2a5b`](https://github.com/msoedov/mesa/tree/1bd047c3d8727ad685b374f0947850a123db2a5b) | No release version used for this review | [MIT](https://github.com/msoedov/mesa/blob/1bd047c3d8727ad685b374f0947850a123db2a5b/LICENSE) |
| Autonomous PM | [`6eac45cbd79182fa0920b24a33c988d4380b4fe3`](https://github.com/mlobo2012/autonomous-pm-plugin/tree/6eac45cbd79182fa0920b24a33c988d4380b4fe3) | Plugin version 0.1.0 | [Apache 2.0](https://github.com/mlobo2012/autonomous-pm-plugin/blob/6eac45cbd79182fa0920b24a33c988d4380b4fe3/LICENSE) |

The following test limits matter:

- GSD, OpenSpec, Superpowers, Matt Pocock skills, BMAD, and Paperclip had source inspection only. Their upstream test suites were not run. Runtime behavior is `UNVERIFIED`.
- Autonomous PM passed 25 Python tests, its structural validator, and both shell hook tests. Those checks exercise helper code, package structure, and two hooks. They do not run the advertised 17-agent cycle or its external connectors. End-to-end behavior is `UNVERIFIED`.
- Mesa could not be built or tested because Go was unavailable in the audit environment. Its runtime behavior is `UNVERIFIED`.
- No project was run through the same live product task corpus. Relative quality, token use, latency, and recovery rates are `UNVERIFIED`.

The retained research report did not preserve every test command. This document records the results that were preserved and does not reconstruct missing commands.

## GSD

The audited tree is large by design. Static inventory found 71 Markdown command files, 35 Markdown agent definitions, and 88 top-level Markdown workflows. GSD gives long work fresh contexts, dependency-aware execution, worktrees, review steps, and configurable model profiles. Its quick and autonomous paths show that the project has moved beyond one rigid phase sequence.

Keep these ideas:

- give independent work a fresh context;
- run dependency-free tasks in parallel and serialize tasks that share files or contracts;
- make planning depth proportional to uncertainty and consequence;
- keep one advancement rule for pause, resume, retry, and completion;
- require current evidence before calling work done.

Do not copy these defaults:

- a large command vocabulary as the user interface;
- mandatory discuss, plan, execute, verify, and ship phases for a small change;
- multiple Markdown files that compete as the current state;
- fixed agent roles, review counts, or vendor model names in portable policy.

SkipHow should get fresh contexts and dependency-aware execution from the host. It should not reproduce GSD's workflow tree. Revisit this decision if host-native goals cannot recover a multi-issue run from GitHub and Git after a process restart.

Sources: [README](https://github.com/open-gsd/gsd-core/blob/f7df920681f233ae0fe064ee659550bdf41ff708/README.md), [commands](https://github.com/open-gsd/gsd-core/tree/f7df920681f233ae0fe064ee659550bdf41ff708/commands), [agents](https://github.com/open-gsd/gsd-core/tree/f7df920681f233ae0fe064ee659550bdf41ff708/agents), [workflows](https://github.com/open-gsd/gsd-core/tree/f7df920681f233ae0fe064ee659550bdf41ff708/gsd-core/workflows).

## OpenSpec

OpenSpec separates an intent change from the current specification. It generates a canonical workflow for several hosts, uses machine-readable contracts, and can express artifact dependencies. That is useful when a change alters a public API, a migration, security rules, or a complicated business rule.

Keep these ideas:

- one canonical workflow with thin host-specific packaging;
- delta intent for changes where later reviewers need to know what contract changed;
- explicit verification criteria;
- finalize related artifacts as one operation instead of leaving half-applied state.

Do not require a proposal, specification, design, and task list for every request. File existence is not proof that the product works. A keyword-driven verify step is weaker than a check against the final repository and service state.

SkipHow should load a small decision or delivery reference only when the work needs it. Revisit this choice if repeated failures come from missing durable intent on material changes, and only add the artifact that prevents the measured failure.

Sources: [README](https://github.com/Fission-AI/OpenSpec/blob/6926ccb18afa4ff621112813e9968334576ee11a/README.md), [schemas](https://github.com/Fission-AI/OpenSpec/tree/6926ccb18afa4ff621112813e9968334576ee11a/schemas), [skills](https://github.com/Fission-AI/OpenSpec/tree/6926ccb18afa4ff621112813e9968334576ee11a/skills), [source](https://github.com/Fission-AI/OpenSpec/tree/6926ccb18afa4ff621112813e9968334576ee11a/src).

## Superpowers

Superpowers 6.3 has more useful restraint than older summaries suggest. It has isolated implementer and reviewer roles, file-based handoffs, bounded repair, worktree guidance, compaction records, and model tiers. Its own release work also tests whether shorter instructions preserve behavior.

Keep these ideas:

- isolate independent changes and reviews;
- hand a reviewer the work product and acceptance criteria, not the author's reasoning transcript;
- bound repair loops and return unresolved failures to the coordinator;
- preserve a short durable record when work will cross context boundaries;
- treat model choice as a capability and cost decision.

Do not make brainstorming, design approval, strict test-first development, or separate reviews mandatory for every task. Superpowers still assumes a developer who can select and chain engineering workflows. SkipHow's user should state the outcome instead.

SkipHow should use risk-based review and host-managed worktrees. Revisit stronger ceremony only when a behavioral eval shows a specific failure that the extra step prevents.

Sources: [README](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/README.md), [skills](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills), [tests](https://github.com/obra/superpowers/tree/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/tests), [release notes](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/RELEASE-NOTES.md).

## Matt Pocock skills

This collection is strongest as a library of focused engineering methods. The useful parts include progressive disclosure, research before building a new subsystem, repro-first diagnosis, issue triage, plan review, disposable prototypes, merge-conflict guidance, and compact maps for navigating an unfamiliar codebase.

Keep these ideas:

- load detailed instructions only when the task needs them;
- research existing code and maintained solutions before adding a lasting abstraction;
- reproduce an unknown bug before choosing a fix;
- turn raw signals into separate, traceable work items;
- preserve valid findings that do not belong in the current change.

Do not load the whole engineering library into ordinary requests. Do not ask an owner to choose a skill sequence. The collection does not provide the full GitHub lifecycle or unattended multi-issue execution that SkipHow needs.

The audited collection contains model-specific examples but no portable end-to-end routing policy. SkipHow should keep `FAST`, `STANDARD`, and `DEEP` as semantic tiers and let each host resolve current models. Revisit the mapping only after paired outcome tests show that a different tier changes cost without lowering completion quality.

Sources: [README](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/README.md), [skills](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills), [package manifest](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/package.json).

## BMAD

BMAD 6.11 should not be dismissed as a fixed persona chain. Its current Build workflow offers a single entry point, optional planning, a smaller one-shot path, a plan and code review path, one bounded unattended iteration, and deterministic bookkeeping.

Keep these ideas:

- choose depth from the work instead of requiring a full method;
- keep one build entry point;
- classify review failures as an intent gap, a specification problem, a repair, or a deferred finding;
- make unattended repair bounded;
- keep repository instructions short enough to remain useful.

Do not copy the broader persona catalog, menus, repeated handoffs, or several status records. Those structures may help teams that want an explicit method. They are a poor default for an owner who wants to describe a product outcome and leave technical choices to the agent.

Revisit BMAD's artifact depth if SkipHow repeatedly implements the wrong product intent on large changes even when the owner outcome and acceptance criteria are present.

Sources: [README](https://github.com/bmad-code-org/BMAD-METHOD/blob/1479a58b2d604382541a184cd59105a580f4e48a/README.md), [source](https://github.com/bmad-code-org/BMAD-METHOD/tree/1479a58b2d604382541a184cd59105a580f4e48a/src), [tests](https://github.com/bmad-code-org/BMAD-METHOD/tree/1479a58b2d604382541a184cd59105a580f4e48a/test), [package manifest](https://github.com/bmad-code-org/BMAD-METHOD/blob/1479a58b2d604382541a184cd59105a580f4e48a/package.json).

## Paperclip

Paperclip has the clearest durable coordination model in this group. It separates tasks from runs, distinguishes parent relationships from dependencies, claims work atomically, uses leases, wakes work from events, resumes sessions, bounds recovery, isolates worktrees, records cost, and represents human decisions as structured state.

Keep these semantics where the host and GitHub expose them:

- one owner for each mutable task;
- a run may fail or retry without changing the task identity;
- dependency state differs from hierarchy;
- recovery must be idempotent;
- work that writes in parallel needs separate worktrees;
- cost includes retries, context transfer, and review.

Do not build Paperclip's server, database, organization model, dashboard, role system, or periodic model heartbeat into SkipHow. GitHub and the host already hold most of the state SkipHow needs. A second tracker would create reconciliation work before it creates value.

Paperclip does not solve portable task-level model routing. Its cheaper recovery path is useful but too narrow to become SkipHow's routing policy. Revisit an external coordinator only if host-native goals fail a measured restart test and GitHub state cannot reconstruct the next safe action.

Sources: [README](https://github.com/paperclipai/paperclip/blob/2862e1848452d578a27054b66c433e0abc2315aa/README.md), [source](https://github.com/paperclipai/paperclip/tree/2862e1848452d578a27054b66c433e0abc2315aa/server), [tests](https://github.com/paperclipai/paperclip/tree/2862e1848452d578a27054b66c433e0abc2315aa/tests), [package manifest](https://github.com/paperclipai/paperclip/blob/2862e1848452d578a27054b66c433e0abc2315aa/package.json).

## Mesa

Mesa combines intake, triage, agent runs, comments, cost records, and recovery in one local program. The code has atomic issue claiming and event-driven wake-up. Its role prompts are smaller than the process descriptions in several other projects.

Keep these ideas:

- one place for intake and delivery state;
- claim work before mutation;
- wake from state changes instead of spending model calls on status polling;
- retain a concise run and cost receipt.

Do not copy the company simulation, fixed roles, embedded task database, or static model assignment. The audited code assigns the same `opus` model family to its roles rather than selecting a model from task shape. Static inspection also found agents sharing the repository working directory and found no implementation for the README's worktree claim.

Those last findings are source observations, not runtime results. Mesa could not be built during this audit. Revisit it after a release adds tested worktree isolation or task-level routing with published outcome and cost measurements.

Sources: [README](https://github.com/msoedov/mesa/blob/1bd047c3d8727ad685b374f0947850a123db2a5b/README.md), [architecture](https://github.com/msoedov/mesa/blob/1bd047c3d8727ad685b374f0947850a123db2a5b/docs/architecture.md), [source](https://github.com/msoedov/mesa/tree/1bd047c3d8727ad685b374f0947850a123db2a5b/internal), [entry point](https://github.com/msoedov/mesa/blob/1bd047c3d8727ad685b374f0947850a123db2a5b/cmd/mesa/main.go).

## Autonomous PM

Autonomous PM 0.1 models product work with evidence IDs, typed handoffs, a named outcome and review date, explicit risk escalation, disconfirming evidence, and connector categories that do not depend on one tracker vendor. These are useful intake concepts.

Keep these ideas:

- preserve raw signal provenance;
- separate facts, assumptions, and product decisions;
- assign stable evidence IDs before synthesis;
- record an outcome and review date for a product bet;
- ask the owner only when a real product or risk choice remains.

Do not run 17 standing roles, formal scoring, or a full PM cycle for each idea. At the audited commit, `/pm-cycle` is an instruction document rather than an executable orchestration engine. The passing tests exercise Python helpers, package structure, and hooks. They do not prove agent handoffs or connectors.

SkipHow should apply these methods only when a product decision is expensive or hard to reverse. Revisit a larger role set after live tests show that a named dissent or evidence role catches errors that one strong product agent misses often enough to pay for the extra context.

Sources: [README](https://github.com/mlobo2012/autonomous-pm-plugin/blob/6eac45cbd79182fa0920b24a33c988d4380b4fe3/README.md), [PM cycle](https://github.com/mlobo2012/autonomous-pm-plugin/blob/6eac45cbd79182fa0920b24a33c988d4380b4fe3/commands/pm-cycle.md), [agents](https://github.com/mlobo2012/autonomous-pm-plugin/tree/6eac45cbd79182fa0920b24a33c988d4380b4fe3/agents), [tests](https://github.com/mlobo2012/autonomous-pm-plugin/tree/6eac45cbd79182fa0920b24a33c988d4380b4fe3/tests), [connectors](https://github.com/mlobo2012/autonomous-pm-plugin/blob/6eac45cbd79182fa0920b24a33c988d4380b4fe3/CONNECTORS.md).

## Attribution and copying

The projects are research sources, not SkipHow dependencies. A repository link supports an idea. It does not grant permission to copy a file without following that file's license and notices.

At the start of this refactor, SkipHow vendors selected files from Matt Pocock skills at commit [`6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76). Those copies carry the upstream MIT license and copyright notice. Keep their license, source path, commit pin, and integrity record while any copy remains. Removing the copies from a later release removes the distribution obligation for that release, but it does not rewrite the history of earlier releases.

For future work:

- describe an idea in SkipHow's own words when no source text or code is needed;
- retain the exact license and attribution for copied or adapted files;
- record the upstream path and full commit, not only the repository URL;
- review the license at the copied commit because a repository's current license may change;
- do not assume that one file inherits a repository-level license when that file carries a different notice.

## Decision for SkipHow

No reviewed project should become SkipHow's internal runtime. The useful intersection is smaller:

- one owner-facing skill with progressive disclosure;
- direct execution for bounded work;
- host-native goals, subagents, resume, and worktrees for long work;
- GitHub and Git as durable delivery state;
- research before a new lasting subsystem;
- evidence and review proportional to the cost of being wrong;
- semantic model tiers resolved by the current host;
- bounded repair and explicit disposition for valid findings outside the task.

This decision is intentionally reversible. Reopen it when a representative eval shows a recurring failure, a host removes a relied-on capability, or one of the pinned projects publishes measured behavior that fixes a SkipHow failure with less policy or code. A new feature list alone is not enough.
