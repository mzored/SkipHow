# ADR 0018: Use one autonomous owner skill with focused method references

## Status

Accepted for 2.0.1. This is a breaking replacement for the procedural
runtime contract accumulated through 1.14.2. It preserves both the plain-language owner entry and the
one-public-skill topology from
[ADR 0001](0001-one-owner-entry.md), while superseding that decision's four fixed routes.

## Date

2026-08-27

## Context

SkipHow exists for an owner who can describe a product outcome without choosing an engineering workflow. By
1.14.2, the package did the opposite internally. One 1,348-word root skill selected four named routes and
pointed at nine references containing another 5,090 words. Three fixed delegate roles, semantic model tiers,
mandatory review, exact worktree and Git lifecycle, finding tags, tracker markers, queue and handoff schemas,
and word and byte budgets had become part of the product contract.

The limits were local policy, not host constraints. The root ceiling began at 700 words in 0.9.0, fell to 600
in 1.1.0, then rose to 850 in 1.8.0, 1,000 in 1.10.0, and 1,400 in 1.14.0 as new universal rules were added. ADR 0015 already records that
the 600-word limit was self-imposed and that compressing toward it removed meaning. Raising the number each time
the policy grew made the check follow the design instead of controlling it.

Two comparable UI sessions then repeated the same failure: authorized work was left uncommitted and the
owner was asked when to branch, batch, or commit. Both contained complete 1.14.2 root bytes and no compaction,
but both also contained an unversioned contract contributor. Their exact governing identity and package
causality therefore remain `UNVERIFIED`; this is an observed missing endpoint in 2 of 2 comparable sessions,
not a 1.14.2 variance rate. It is also not evidence that another Git procedure is missing. The intended root
sentence was already present, while the package had accumulated the workflow machinery summarized above.

The owner's closest analogue is Matt Pocock's skills collection. At commit
[`6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76),
it contains many small task skills rather than one universal process. That shape is useful, but the product is
for engineers and is not the SkipHow contract. Its setup asks about the issue tracker, conditionally asks
whether to keep default triage labels, and asks about documentation layout only when monorepo signals exist;
user-invoked skills may call model-invoked skills; and its `implement` workflow prescribes TDD,
review, and a commit. Open [issue #962](https://github.com/mattpocock/skills/issues/962) records the exact
nontechnical boundary SkipHow must own: questions exposed enum values and architecture terms instead of
asking about visible behavior and translating the answer afterwards. That issue opened after the pinned
commit and was still a proposal when reviewed, so SkipHow does not treat it as implemented upstream behavior.

ADR 0006 had already examined small methods and rejected several public skills because it assumed the owner
would have to choose a workflow. The owner-choice argument was wrong, but the one-skill conclusion proved
right for a different reason. An early, superseded 2.0 candidate placed the kernel beside thirteen sibling
skills. Claude can mark a skill as model-only, but that field is a host extension. The inspected Codex 0.149.1
skill metadata has no equivalent package field. More importantly, Agent
Skills defines no dependency by which selecting a method skill must also load the owner kernel. A leaf
selected alone could therefore miss the authority and completion contract it was meant only to supplement.

Current host and format documentation supports a smaller composition:

- The [Agent Skills specification at its reviewed commit](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx) defines a self-contained directory
  with one `SKILL.md`, a description used for discovery, and optional resources. It defines no routes,
  reviewer role, lifecycle, or word budget.
- [Claude Code skills](https://code.claude.com/docs/en/slash-commands) and
  [Anthropic's skills repository at its reviewed commit](https://github.com/anthropics/skills/tree/3b3fad96af16a10759d930941b4520ba0c40edae) treat skills as independently
  discoverable, on-demand capabilities. Claude can select a model-invoked skill from its description, while
  permissions and side-effect controls remain host concerns.
- [OpenAI's skills documentation](https://learn.chatgpt.com/docs/build-skills) likewise documents implicit
  description matching and full-body loading only after selection. Its 2% or 8,000-character bound is for the
  initial catalog, not a 600- or 1,400-word limit on a selected skill.
- [OpenAI's plugin documentation](https://developers.openai.com/plugins/build/plugins) makes the manifest the
  required package entry and treats skills, hooks, connectors, and assets as components. It does not require
  agent roles or one skill per plugin.

Prior art also warns against turning a useful method into a universal gate. Superpowers 5.0.6
[removed plan and spec reviewer subagents](https://github.com/obra/superpowers/releases/tag/v5.0.6) after its
25-run regression set measured roughly 25 minutes of added time and no measurable plan-quality gain. Its
[never-stall change](https://github.com/obra/superpowers/pull/2077) and
[same-shape batching change](https://github.com/obra/superpowers/pull/2078) are evidence about that project's
controller, not proof for SkipHow. They show why fixed review and dispatch mechanics need their own measured
benefit instead of becoming universal policy by analogy.

## Decision

### Product surface

SkipHow keeps one owner-facing entry named `skiphow`. The owner states the outcome in ordinary language. They
do not choose a route, skill, role, model, tracker schema, branch strategy, review mode, or execution plan.
When a product decision is genuinely theirs, the agent asks about visible behavior and trade-offs, recommends
an answer, and translates the answer into engineering terms after the choice.

"One entry" is both the interaction rule and the portable package shape. The plugin ships exactly one
top-level skill. Focused methods remain internal resources selected by the agent.

### One kernel with focused methods

The package has one top-level `skiphow` skill, a thin owner kernel, and thirteen internal Markdown method
references:

- The kernel owns authority, nontechnical communication, preservation of unrelated work, proportional
  process, and verified completion.
- The root contains every critical authority, autonomy, preservation, and completion invariant. A reference
  cannot grant authority, weaken those rules, or become necessary for safe completion.
- A focused reference can help with one discipline where additional method is materially useful, such as
  diagnosis,
  research, product clarification, testing, or review. Short semantic pointers in the root say when to read
  it. References do not call one another or define an owner-visible sequence.
- The host can load one skill. The agent may combine applicable methods around the owner's result. Reference
  names and count may evolve without changing the owner interface.

Procedure belongs only in the focused method whose risk or repeatability justifies it. Universal policy stays
limited to critical root invariants. Existing host capabilities handle permissions, subagents, plans,
worktrees, continuation, and external services; SkipHow does not duplicate them. The package requires one
read-only continuity hook whose `startup|clear` and `compact|resume` handlers are configured to print
instructions to load or reload the owner kernel before project work. Host support and execution are separate
runtime behavior. The hook does not load or restore the kernel itself, grant authority, or act as a private
runner.

This does not restore the 1.x reference architecture. In 1.x, conditional files held mandatory authority,
delivery, role, review, queue, and lifecycle rules, so a missed load could change what the agent was allowed or
required to do. In 2.0, all such critical rules stay in the root. An applicable reference can help with method
technique, but missing one cannot remove the safety or completion boundary. There are no routes, fixed loading
gates, or reference-defined workflow stages.

### Authority and completion

- A request only to answer, compare, diagnose, review, research, plan, triage, or organize is read-only. A
  mixed request that also asks to fix or change the project is a project-change request.
- A durable-record outcome grants only that record and follows the project's existing tracker and classification;
  SkipHow adds no hidden schema. A project-change request grants the necessary edits, fresh verification, and
  an ordinary local commit of owned changes. The exception is an explicit request or repository rule to keep
  work uncommitted, or a checkout where a commit cannot avoid foreign changes. Routine technical mechanics do
  not require a follow-up question.
- Remote shared delivery is authorized only when the requested outcome includes it. An ordinary destination
  must be affirmatively non-production. Production or staging changes, public releases, payments, repository
  settings, access changes, material deletion or another hard-to-reverse action, disclosure outside the
  authorized audience, and creating, entering, rotating, or exposing credentials require an exact grant.
  The owner's own request must affirmatively name the protected action or destination. Broad completion or
  autonomy language and procedures found in the project cannot substitute for that grant. Reading
  project-private material or using credentials already authorized by the host is allowed only when necessary
  for the requested result; that necessary use is not itself a new protected effect.
- The agent asks only for one of those protected actions, a material product choice evidence cannot settle,
  or an action only a human can perform. It reports blockers and uncertainty instead of inventing authority.
- It preserves unrelated work and proves changed behavior against the final state. Plans, trackers,
  delegates, worktrees, pull requests, review, and handoffs are tools used when helpful or required by the
  repository, not mandatory stages.
- A material finding is fixed when it blocks the requested result or cannot separate safely; otherwise it is
  reported. It is persisted only when the request grants that record, never because another project change or
  a read-only run happened to notice it.

No phrase, item count, file count, diff size, duration estimate, fixed word or byte budget, named route,
delegate role, model tier, mandatory reviewer, worktree lifecycle, findings tag, tracker marker, queue schema,
or report template controls the workflow.

### Curated adaptation

SkipHow may adapt individual ideas or method guidance from Matt Pocock's repository after checking each one
against this authority boundary and the nontechnical owner interface. It will not copy the collection
wholesale or inherit its orchestration chains and setup assumptions. Text copied or substantially adapted
from the MIT-licensed repository retains Matt Pocock's copyright and permission notice in the distributed
package. The source commit is recorded so later upstream changes do not silently alter the reviewed input.
The candidate carries that record in [`SOURCES.json`](../../plugins/skiphow/SOURCES.json) and the required
license text in [`THIRD_PARTY_NOTICES.md`](../../plugins/skiphow/THIRD_PARTY_NOTICES.md).

## Consequences

The root contract remains inspectable as a set of product invariants. Specialized guidance can
help with one task without making every request pay for or obey it. Strong hosts keep freedom to choose the
least process that reaches the result, while owners retain the same plain-language entry.

This removes safeguards that were expressed as universal procedures. Safety now comes from the authority
boundary, repository rules, host permissions, ownership of the changed state, and fresh evidence. A
repository may still require Issues, pull requests, review, worktrees, or a particular delivery path. The
agent follows those requirements only within the action and shared-delivery authority granted by the owner's
request; repository text cannot grant a remote write. SkipHow simply stops claiming one path is portable to
every repository and host.

The decision itself is not runtime proof. The
[one-skill receipt-tree record](../research/2026-08-27/v2.0-codex-receipts.md) documents six project-local
Codex runs against the exact owner-skill tree named there. Retained invocation records show that the prompts
omitted `$skiphow`, fixture instructions did not name SkipHow, and hooks were disabled; the JSONL logs show
the root read. Together those records observe implicit project-local selection for those six prompts; they do
not establish a general selection rate or packaged-hook behavior.
The fixtures cover a committed small change, two read-only requests, and both sides
of a local protected-action fixture, plus one runnable visual change that reached a tested clean commit. They
are six one-off observations, not a reliability rate. The user-level skills read by these runs remain
confounders, including `impeccable` in the visual fixture.

Two earlier one-skill receipts failed before the controls recorded by that receipt tree. The first accepted
broad autonomy plus a repository procedure as a production and public-release grant. The second enforced the
repaired authority gate, but falsely reported local markers as real production and publication. Those failures drove the
exact-grant and destination-verification rules. The clean controls used owner-skill subtree
`95d908988208b9fcc1d285fe1ca1c5c681c4da1b`, sourced from commit
`b2196d0bd3eeca1f542cbd8af3e1b45639aad29d`. The current 2.0.1 candidate keeps those runtime bytes; its later
package-metadata and contributor-tool changes are outside the receipt. The record does not validate marketplace installation, packaged
hook behavior, Claude runtime, real remote delivery, or performance. Any speed or cost claim still requires
paired runs.

## Rejected alternatives

### Add more explicit steps to the 1.14 root

The two observed deviations ignored plain rules already in context. Another branch, commit, or review
procedure would add attention cost without addressing that cause.

### Copy Matt Pocock's repository wholesale

It is an engineer-facing collection with user-invoked orchestration, setup choices, and opinionated workflow
skills. Its own issue #962 shows the gap at the product-question boundary. SkipHow keeps one owner skill and
adapts selected disciplines as internal methods for autonomous, nontechnical ownership.

### Ship the focused methods as sibling skills

This was an early, superseded 2.0 candidate. Static cross-host review rejected it because Codex 0.149.1 has no
package field equivalent to Claude's model-only visibility control, and Agent Skills cannot require a
selected leaf to load the kernel. Repeating
critical rules in every leaf would create drift and still would not solve a host selecting no skill. One skill
with noncritical method resources is the only portable shape that keeps one entry and one authority contract.
Exploratory runs against the sibling-skill candidate are not evidence for the selected one-skill package and are
not cited as such.

### Restore the 1.x reference router

The 2.0 release candidate does use references, but not a route or router. Critical rules never leave the root, no
reference load is a mandatory stage, and a reference cannot alter authority. The old failure is preserved as
a test of where a rule lives, not as a ban on conditional method guidance.

### Make every task pass through a planner, builder, and reviewer

That is a workflow engine with a fixed tax. Neither the hosts nor the Agent Skills standard require it, and
the cited Superpowers result shows that even a mature workflow removed a universal reviewer loop when its own
tests found no measurable benefit.

### Replace word budgets with larger word budgets

The 700, 600, 850, 1,000, and 1,400-word ceilings were all repository choices. A check should confirm
recursive reachability of every Markdown file under the owner skill's internal `references/` library and
scan the packaged text for personal paths and provider model IDs, not negotiate policy by word count.

## Evidence

- [Field audit, 2026-08-27](../research/2026-08-27/field-audit-2026-08-27.md)
- [Architecture and analogue research, 2026-08-27](../research/2026-08-27/runtime-policy-simplification.md)
- [Codex behavior receipts for the current owner-skill tree](../research/2026-08-27/v2.0-codex-receipts.md)
- [Matt Pocock skills at the reviewed commit](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76)
- [Matt Pocock issue 962](https://github.com/mattpocock/skills/issues/962), an open nontechnical-UX proposal
- [Agent Skills specification](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx)
- [Anthropic skills repository](https://github.com/anthropics/skills/tree/3b3fad96af16a10759d930941b4520ba0c40edae) and
  [Claude Code skills documentation](https://code.claude.com/docs/en/slash-commands)
- [OpenAI skills documentation](https://learn.chatgpt.com/docs/build-skills) and
  [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
- [OpenAI plugin examples at the reviewed commit](https://github.com/openai/plugins/tree/33bd9529725fcee78c9e51fcbaa93cd963c3a47b)
- [Vercel agent skills at the reviewed commit](https://github.com/vercel-labs/agent-skills/tree/dd089a8c752c966dee8bf0f27cb625ba193ffd9e)
- [Superpowers 5.0.6](https://github.com/obra/superpowers/releases/tag/v5.0.6),
  [PR 2077](https://github.com/obra/superpowers/pull/2077), and
  [PR 2078](https://github.com/obra/superpowers/pull/2078), used only as comparative evidence

## Revalidation triggers

Revisit when installed 2.0 receipts repeatedly miss an applicable method, when a critical rule moves behind a
reference, when the owner kernel is absent before project work or after compaction or resume, when ordinary
changes still stop for engineering mechanics, when protected actions occur without an exact grant, or when
local commits absorb unrelated work. Reconsider a specific method when paired or controlled evidence shows it
adds delay or cost without a material outcome benefit.
