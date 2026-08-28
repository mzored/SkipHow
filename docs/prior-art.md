# Prior art

SkipHow is one autonomous owner skill whose kernel can consult a curated library of focused method references. It learns from existing projects without treating any of them as a runtime dependency or a workflow to copy wholesale.

The dated research under [`docs/research/`](research/) records exact inspected revisions, source findings, licenses, test limits, and revalidation triggers. When SkipHow copies or adapts source text, the distributed package keeps the applicable license and copyright notice and records the upstream path and inspected commit. Borrowed ideas are described in SkipHow's own words.

## Matt Pocock's skills

[Matt Pocock's skills](https://github.com/mattpocock/skills) are the primary modular-method influence for SkipHow 2.0. The project demonstrates that engineering guidance can be split into small, adaptable disciplines instead of one framework that owns the whole process. SkipHow adapts that modularity inside one portable owner skill rather than copying the upstream package topology.

SkipHow keeps or adapts selected ideas:

- small methods centered on one reusable discipline;
- semantic discovery and progressive disclosure;
- research from high-trust primary sources;
- diagnosis driven by an observable feedback loop;
- vertical slices and proportionate tests where they fit;
- intent-aware conflict resolution;
- code review as an available independent judgment;
- concise handoffs when work must survive interruption.

SkipHow does not copy the upstream main flow wholesale. Its setup asks about the issue tracker, conditionally asks whether to keep default triage labels, and asks about documentation layout when monorepo signals exist. Several orchestration skills must be invoked by name, and the documented engineering path can expose grilling, specs, tickets, TDD seams, implementation, and review as owner-visible steps. That design is useful for engineers who want to control the method. It remains too technical and ceremonial for an owner who knows the desired behavior but should not have to operate the software process.

The caveat is supported by current upstream evidence, not a hypothetical objection:

- [issue #962](https://github.com/mattpocock/skills/issues/962) says nontechnical users can be shown enum values and architecture terms, and proposes asking about visible outcomes before recording the technical mapping;
- [issue #883](https://github.com/mattpocock/skills/issues/883) documents blocking questions from TDD, review, implementation, and setup that can deadlock unattended work;
- [issue #885](https://github.com/mattpocock/skills/issues/885) documents missing completion, escalation, and machine-readable graph seams when the skills run under an external orchestrator.

SkipHow takes these as design inputs. The owner kernel keeps authority, autonomy, continuity, and completion in context. The same agent reads applicable method references and applies their discipline to the result. They do not form a mandatory chain, require setup choices from the owner, or make the owner translate a product request into method names.

Matt Pocock's repository is MIT licensed. Any distributed source adaptation must retain its attribution and notice. An idea alone is credited here and expressed in SkipHow's own contract.

## Other projects

| Project | Keep or study | Leave out by default |
| --- | --- | --- |
| [GSD](https://github.com/open-gsd/gsd-core) | Fresh context, dependency-aware parallelism, proportional depth | A large command tree, mandatory phases, and several state files |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | Clear intent for material contract changes, thin host packaging | Proposal, specification, design, and task artifacts for every change |
| [Superpowers](https://github.com/obra/superpowers) | Isolated review, bounded repair, safe worktree and conflict practices | Mandatory brainstorming, approval gates, and test-first development |
| [BMAD](https://github.com/bmad-code-org/bmad-method) | One entry and planning depth based on the work | Personas, menus, repeated handoffs, and standing ledgers |
| [Paperclip](https://github.com/paperclipai/paperclip) | External task state, idempotent reconciliation, dependency semantics | A server, task database, company model, and dashboard |
| [Mesa](https://github.com/msoedov/mesa) | Atomic ownership and event-driven wake-up | Fixed roles, an embedded tracker, and company simulation |
| [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin) | Provenance and separation of facts from assumptions | Standing personas and mandatory scoring |

These projects have not been run side by side with SkipHow. Their inclusion is architectural research, not evidence that SkipHow is faster, cheaper, or more reliable.

## Adoption rule

A useful idea becomes a focused method reference or root invariant only when it addresses an observed task need or protects a high-risk boundary. Procedures do not enter the owner kernel merely because they are good practice somewhere else. The default is still the least process that reaches a fresh, verified result while preserving the owner's authority and unrelated work.
