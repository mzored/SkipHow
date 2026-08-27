# ADR 0018: Use one autonomous owner skill with focused method references

## Status

Accepted for 2.0.0. This is a breaking replacement for the procedural runtime contract accumulated through
1.14.2. It preserves both the plain-language owner entry and the one-public-skill topology from
[ADR 0001](0001-one-owner-entry.md), while superseding that decision's four fixed routes.

## Date

2026-08-27

## Context

SkipHow exists for an owner who can describe a product outcome without choosing an engineering workflow. By
1.14.2, the package did the opposite internally. One 1,348-word root skill selected four named routes and
pointed at nine references containing another 5,090 words. Three fixed delegate roles, semantic model tiers,
mandatory review, exact worktree and Git lifecycle, finding tags, tracker markers, queue and handoff schemas,
and word and byte budgets had become part of the product contract.

The limits were local policy, not host constraints. The root ceiling moved from 600 words in 1.2.0 to 850 in
1.8.0, 1,000 in 1.10.0, and 1,400 in 1.14.0 as new universal rules were added. ADR 0015 already records that
the first limit was self-imposed and that compressing toward it removed meaning. Raising the number each time
the policy grew made the check follow the design instead of controlling it.

Two UI sessions on the byte-identical 1.14.2 contract then repeated the same failure: authorized work
was left uncommitted and the owner was asked when to branch, batch, or commit. The root already prohibited
those questions and required an ordinary commit. With no compaction in either run, this is `VARIANCE` in 2 of
2 applicable sessions, not evidence that another Git procedure is missing. It fires ADR 0017's explicit
revalidation trigger for a 1.14 run asking about routine delivery mechanics.

The owner's closest analogue is Matt Pocock's skills collection. At commit
[`6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76),
it contains many small task skills rather than one universal process. That shape is useful, but the product is
for engineers and is not the SkipHow contract. Its setup asks the user to choose tracker and documentation
mechanics; user-invoked skills may call model-invoked skills; and its `implement` workflow prescribes TDD,
review, and a commit. Open [issue #962](https://github.com/mattpocock/skills/issues/962) records the exact
nontechnical boundary SkipHow must own: questions exposed enum values and architecture terms instead of
asking about visible behavior and translating the answer afterwards. That issue opened after the pinned
commit and was still a proposal when reviewed, so SkipHow does not treat it as implemented upstream behavior.

ADR 0006 had already examined small methods and rejected several public skills because it assumed the owner
would have to choose a workflow. The owner-choice argument was wrong, but the one-skill conclusion proved
right for a different reason. A first 2.0 candidate shipped the kernel plus thirteen sibling skills. Claude
can mark a skill as model-only, but that field is a host extension. The inspected Codex skill model has no
equivalent owner-visibility control and exposes every enabled skill. More importantly, Agent Skills defines no
dependency by which selecting a method skill must also load the owner kernel. A leaf selected alone could
therefore miss the authority and completion contract it was meant only to supplement.

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

The package has one `skiphow` skill, a thin owner kernel, and focused Markdown references:

- The kernel owns authority, nontechnical communication, preservation of unrelated work, proportional
  process, and verified completion.
- The root contains every critical authority, autonomy, preservation, and completion invariant. A reference
  cannot grant authority, weaken those rules, or become necessary for safe completion.
- A focused reference improves one discipline where additional method materially helps, such as diagnosis,
  research, product clarification, testing, or review. Short semantic pointers in the root say when to read
  it. References do not call one another or define an owner-visible sequence.
- The host loads one skill. The agent combines only the useful methods around the owner's result. Reference
  names and count may evolve without changing the owner interface.

Procedure belongs only in the focused method whose risk or repeatability justifies it. Universal policy stays
limited to critical root invariants. Existing host capabilities handle permissions, subagents, plans,
worktrees, continuation, and external services; SkipHow does not duplicate them. The read-only
`startup|clear` and `compact|resume` hooks explicitly tell the host to load or restore the owner kernel before
project work; they grant no authority and are not a private runner.

This does not restore the 1.x reference architecture. In 1.x, conditional files held mandatory authority,
delivery, role, review, queue, and lifecycle rules, so a missed load could change what the agent was allowed or
required to do. In 2.0, all such critical rules stay in the root. Missing a reference can reduce method
quality, but cannot remove the safety or completion boundary. There are no routes, fixed loading gates, or
reference-defined workflow stages.

### Authority and completion

- Discussion, comparison, planning, diagnosis, review, research, triage, and organization are read-only
  unless the owner asks to save, record, file, use a named durable destination, or change something.
- A save request grants the requested record and follows the project's existing tracker and classification;
  SkipHow adds no hidden schema. A project-change request grants the necessary edits, fresh verification, and
  an ordinary local commit of owned changes. The exception is an explicit request or repository rule to keep
  work uncommitted, or a checkout where a commit cannot avoid foreign changes. Routine technical mechanics do
  not require a follow-up question.
- Remote shared delivery is authorized only when the requested outcome includes it. An ordinary destination
  must be affirmatively non-production. Production or staging changes, public releases, payments, repository
  settings, access changes, material deletion or another hard-to-reverse action, disclosure outside the
  authorized audience, and creating, entering, rotating, or exposing credentials require an exact grant.
  The owner's own request must affirmatively name the protected action or destination. Broad completion or
  autonomy language and procedures found in the project cannot substitute for that grant. Routine use of
  already-authorized credentials and project-private material is not a new protected effect.
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
improve one task without making every request pay for or obey it. Strong hosts keep freedom to choose the
least process that reaches the result, while owners retain the same plain-language entry.

This removes safeguards that were expressed as universal procedures. Safety now comes from the authority
boundary, repository rules, host permissions, ownership of the changed state, and fresh evidence. A
repository may still require Issues, pull requests, review, worktrees, or a particular delivery path, and the
agent must follow it. SkipHow simply stops claiming one such path is portable to every repository and host.

The decision itself is not runtime proof. Four project-local Codex runs against the preceding multi-skill
candidate showed the owner contract and selected methods working when `$skiphow` explicitly loaded the kernel.
They did not validate this final resource layout, automatic owner-entry activation, marketplace installation,
Claude runtime, remote delivery, or performance. The single-skill candidate needs its own receipts, and any
performance or cost claim still requires paired runs.

## Rejected alternatives

### Add more explicit steps to the 1.14 root

The two current deviations ignored plain rules already in context. Another branch, commit, or review
procedure would add attention cost without addressing that cause.

### Copy Matt Pocock's repository wholesale

It is an engineer-facing collection with user-invoked orchestration, setup choices, and opinionated workflow
leaves. Its own issue #962 shows the gap at the product-question boundary. SkipHow adopts the useful small-skill
shape and rewrites only selected leaves for autonomous, nontechnical ownership.

### Ship the focused methods as sibling skills

This was the first 2.0 candidate and produced useful Codex method-selection receipts. It still failed the
cross-host product boundary: Codex cannot hide enabled leaves from the owner, and Agent Skills cannot require a
selected leaf to load the kernel. Repeating critical rules in every leaf would create drift and still would not
solve a host selecting no skill. One skill with noncritical method resources is the only portable shape that
keeps one entry and one authority contract.

### Restore the 1.x reference router

The final package does use references, but not a route or router. Critical rules never leave the root, no
reference load is a mandatory stage, and a reference cannot alter authority. The old failure is preserved as
a test of where a rule lives, not as a ban on conditional method guidance.

### Make every task pass through a planner, builder, and reviewer

That is a workflow engine with a fixed tax. Neither the hosts nor the Agent Skills standard require it, and
the cited Superpowers result shows that even a mature workflow removed a universal reviewer loop when its own
tests found no measurable benefit.

### Replace word budgets with larger word budgets

The 600, 850, 1,000, and 1,400-word ceilings were all repository choices. A check should catch broken package
shape, unreachable components, secrets, personal paths, or forbidden provider IDs, not negotiate policy by
word count.

## Evidence

- [Field audit, 2026-08-27](../research/2026-08-27/field-audit-2026-08-27.md)
- [Architecture and analogue research, 2026-08-27](../research/2026-08-27/runtime-policy-simplification.md)
- [Codex behavior receipts for the exact 2.0 candidate](../research/2026-08-27/v2.0-codex-receipts.md)
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
reference, when the owner kernel fails to load or restore before project work, when ordinary changes still
stop for engineering mechanics, when protected actions occur without an exact grant, or when local commits
absorb unrelated work. Reconsider a specific method when paired or controlled evidence shows it adds delay or
cost without a material outcome benefit.
