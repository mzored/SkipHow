# Runtime policy simplification and analogue research

Research performed on 2026-08-27 for the 2.0 architecture in
[ADR 0018](../../decisions/0018-autonomous-kernel-and-independent-task-skills.md). This note answers the
owner's question directly: whether SkipHow should become a curated, autonomous adaptation of small skills
instead of another universal workflow engine.

This note describes an unpublished 2.0 release candidate. Marketplace installation still resolves to the
published 1.14.2 package until 2.0 is published.

## Conclusion

Yes, with one important distinction. The useful analogue is a library of thirteen focused Markdown methods
behind one top-level, plain-language owner skill, not a copied package topology or chain of commands.
SkipHow's root defines authority, autonomous technical judgment, preservation of unrelated work, and verified
completion for a nontechnical owner's request. The methods are optional technique.

The Agent Skills standard does not define a dependency by which a selected method skill must also load an
owner kernel. The inspected Codex 0.149.1 package metadata has no field equivalent to Claude's model-only
visibility control. SkipHow therefore
ships one top-level skill and keeps its focused methods as internal Markdown resources. They never grant
authority, call one another, or become owner commands.

The package requires one read-only lifecycle hook. Its handlers are configured to print a kernel-load
instruction on startup or clear and a reload instruction on compact or resume. Whether a host supports or
executes those handlers is separate runtime behavior. The hook does not perform either load, is not a
dependency primitive, and grants no authority.

## What the earlier research got wrong

SkipHow had looked at Matt Pocock's repository before this audit. The
[2026-08-25 prior-art note](../2026-08-25/prior-art.md) recognized its small composable methods, but the project
then treated several shipped skills as several workflows the owner would have to choose.
[ADR 0006](../../decisions/0006-host-native-campaign-and-engineering-policy.md) consequently rejected split
method skills and put conditional methods behind one root router.

That inference first produced an overcorrection: a superseded 2.0 candidate separated the kernel into one
skill and the methods into thirteen sibling skills. Cross-host review then showed that package topology does
affect this owner interface. Claude has a host-specific model-only visibility field; the inspected Codex
0.149.1 metadata has no equivalent package field, and Agent Skills has no leaf-to-kernel dependency. An exposed or independently
selected leaf could bypass the only contract the owner actually relies on. Exploratory runs against that
candidate are not evidence for the selected one-skill package.

The selected decision keeps one top-level skill and corrects the late-1.x layout instead. In the audited 1.x
snapshots, conditional references held critical authority and workflow rules, so a missed load could change
behavior. In 2.0, every critical authority, autonomy, preservation, and completion rule stays in the root.
The thirteen internal Markdown references contain optional methods, with no routes or mandatory load gates.
An applicable method can help with technique, but it cannot add to or remove from the critical contract in
the root.

## Primary sources read

The commit-pinned repository links below were their current default-branch heads when checked on 2026-08-27;
release and issue links are identified separately.

- [Agent Skills specification at `69ef37e9424c0a7ea9dd2293b559e43ec8176379`](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx)
- [Claude Code skills documentation](https://code.claude.com/docs/en/slash-commands),
  [extension overview](https://code.claude.com/docs/en/features-overview), and
  [Anthropic skills repository at `3b3fad96af16a10759d930941b4520ba0c40edae`](https://github.com/anthropics/skills/tree/3b3fad96af16a10759d930941b4520ba0c40edae)
- [OpenAI skills documentation](https://learn.chatgpt.com/docs/build-skills),
  [skill design guidance](https://developers.openai.com/plugins/build/skills), and
  [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
- [OpenAI plugin examples at `33bd9529725fcee78c9e51fcbaa93cd963c3a47b`](https://github.com/openai/plugins/tree/33bd9529725fcee78c9e51fcbaa93cd963c3a47b)
- [Codex 0.149.1 skill metadata model](https://github.com/openai/codex/blob/rust-v0.149.1/codex-rs/skills/src/model.rs)
- [Matt Pocock skills at `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76)
- [Vercel agent skills at `dd089a8c752c966dee8bf0f27cb625ba193ffd9e`](https://github.com/vercel-labs/agent-skills/tree/dd089a8c752c966dee8bf0f27cb625ba193ffd9e)
- [Superpowers 5.0.6](https://github.com/obra/superpowers/releases/tag/v5.0.6),
  [PR 2077](https://github.com/obra/superpowers/pull/2077), and
  [PR 2078](https://github.com/obra/superpowers/pull/2078), as comparison only

## What the formats and hosts actually require

The [pinned Agent Skills specification](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx) requires one `SKILL.md` per skill with
a name and description. Scripts, references, assets, compatibility metadata, licensing metadata, and allowed
tools are optional. The full body loads after a skill is activated, and the specification gives no route,
role, reviewer, worktree, queue, report, or word-budget contract.

[Claude Code](https://code.claude.com/docs/en/slash-commands) discovers skills from descriptions and allows
the model or user to invoke them. It also documents user-only skills for side-effectful operations and says
the body remains in context after loading. Its
[extension overview](https://code.claude.com/docs/en/features-overview) says built-in tools cover most coding
tasks and recommends adding extensions when specific triggers arise. Skills, subagents, and hooks are
separate host capabilities.

Claude Code also supports a host-specific `user-invocable: false` field for hiding a skill from its owner
menu while retaining model invocation. The portable specification does not define that field. The inspected
[Codex 0.149.1 skill model](https://github.com/openai/codex/blob/rust-v0.149.1/codex-rs/skills/src/model.rs)
has no equivalent user-visibility property. The audited formats therefore offer no portable package field
that guarantees an internal sibling stays model-only in Codex, and neither host can infer a dependency that
guarantees a sibling method loads the kernel first.

[OpenAI](https://learn.chatgpt.com/docs/build-skills) also supports explicit and implicit activation. Codex's
2% context-window or 8,000-character limit applies to the initial catalog of names and descriptions, not to a
selected skill's body and not to a fixed 600- or 1,400-word root. OpenAI's
[skill design guidance](https://developers.openai.com/plugins/build/skills) says a plugin may hold one skill
or a related group and recommends splitting when triggers, inputs, or success criteria differ. Its
[plugin format](https://developers.openai.com/plugins/build/plugins) requires the manifest; skills, hooks,
MCP connections, apps, and assets are optional components.

The reviewed OpenAI examples at
[`33bd9529725fcee78c9e51fcbaa93cd963c3a47b`](https://github.com/openai/plugins/tree/33bd9529725fcee78c9e51fcbaa93cd963c3a47b)
package sibling task skills under one plugin. The Notion example exposes four independent procedural skills.
No reviewed OpenAI format field declares a skill dependency or call graph. The older
[`openai/skills`](https://github.com/openai/skills) repository is deprecated in favor of the plugin examples,
so it is not the architecture source for this decision. Sibling skills are valid packaging, but they do not
satisfy SkipHow's stricter one-entry boundary in which one selected owner skill carries the complete kernel.

Anthropic's [pinned skills repository](https://github.com/anthropics/skills/tree/3b3fad96af16a10759d930941b4520ba0c40edae) likewise presents each skill as a
self-contained folder loaded dynamically for a specialized task. Its own disclaimer says examples and product
behavior can differ and that critical uses need testing. This supports independent leaves and progressive
loading; it does not prove that any particular leaf improves SkipHow.

## Matt Pocock's collection: closest shape, different product

The pinned commit
[`6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`](https://github.com/mattpocock/skills/commit/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76)
contains 37 `SKILL.md` files in the tree. Its Claude plugin manifest packages 25 stable skills: 18 engineering
and 7 productivity skills. Eight other skills are marked in progress and four are miscellaneous. The stable
catalog separates user-invoked orchestrators from model-invoked disciplines, which is much closer to useful
on-demand loading than SkipHow 1.14's one universal route file.

It is still not an autonomous product-owner layer:

- The repository describes itself as ["Skills For Real Engineers"](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/README.md).
- Setup asks about the issue tracker, conditionally asks whether to keep default triage labels, and asks about
  documentation layout only when monorepo signals exist.
- Named user workflows remain the normal entry. Its
  [grilling documentation](https://github.com/mattpocock/skills/blob/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/docs/productivity/grilling.md)
  calls cross-skill loading a real unfixed rough edge and says selective installation can omit the primitive
  a wrapper needs.
- The pinned `implement` skill hardcodes TDD, a code-review pass, and committing to the current branch. Other
  leaves carry useful but opinionated procedures.

The nontechnical gap is not hypothetical. [Issue #962](https://github.com/mattpocock/skills/issues/962),
opened after the pinned commit and still an unimplemented proposal when read, reports grilling questions that
present enum values and architecture terms directly. Its proposed boundary is the one SkipHow adopts: ask
about the visible situation and outcome, recommend in plain language, then map the answer to exact engineering
terms. [Issue #863](https://github.com/mattpocock/skills/issues/863) separately reports that a nondeveloper
team found triage questions draining, verbose, and too technical. Issues
[#895](https://github.com/mattpocock/skills/issues/895),
[#933](https://github.com/mattpocock/skills/issues/933), and
[#948](https://github.com/mattpocock/skills/issues/948) record open question-order, layout, and preparation
caveats. These are upstream reports and proposals, not controlled SkipHow receipts.

Matt's repository is MIT licensed. SkipHow therefore selects and rewrites only the useful task disciplines,
records the exact source commit and paths, and retains the upstream copyright and permission notice for
substantial adaptations. It does not vendor the collection wholesale or claim issue #962 is already fixed
upstream.

## Other useful comparisons

Vercel's pinned
[`dd089a8c752c966dee8bf0f27cb625ba193ffd9e`](https://github.com/vercel-labs/agent-skills/commit/dd089a8c752c966dee8bf0f27cb625ba193ffd9e)
tree has nine top-level skills and a generated discovery index with one independent name and description per
skill, without dependency, parent, or invocation fields. Its riskier deployment leaf contains the procedure
that deployment needs; a separate optimization leaf uses host-native subagent fan-out with a serial fallback.
That is useful evidence for keeping risk-specific procedure in a conditional method, not in the owner root.
It does not require that method to be a separate top-level skill.

Superpowers is deliberately not the template for 2.0. It is a larger workflow system, but its own current
history demonstrates why universal mechanics require measurements:

- [Release 5.0.6](https://github.com/obra/superpowers/releases/tag/v5.0.6) removed plan and specification
  reviewer subagents after its maintainers reported 25 trials, five on each of five versions, with roughly
  25 minutes of overhead, doubled execution time, and no measurable plan-quality improvement.
- [PR 2077](https://github.com/obra/superpowers/pull/2077) began from one donated 8-hour-48-minute stall and
  reported a narrow controlled result: controls stalled 3 of 3 on a seeded non-catastrophic conflict, while
  the treatment continued 3 of 3; destructive guards remained hard stops.
- [PR 2078](https://github.com/obra/superpowers/pull/2078) mined 174 of its own sessions, then reported that a
  same-shape micro-task treatment cut cost 73% and dispatches 87% in its controlled battery while retaining a
  boundary for tasks needing separate judgment.

Those results belong to Superpowers' controller and scenarios. They do not establish SkipHow's speed or cost.
They do support one decision rule: do not make reviewer seats, blocking questions, or one-dispatch-per-item a
portable invariant without evidence for that exact population.

## Measured package shape

The comparison below is repository evidence, not a runtime benchmark. The 2.0 column was measured from
candidate commit `b2196d0bd3eeca1f542cbd8af3e1b45639aad29d`, whose owner-skill subtree is
`95d908988208b9fcc1d285fe1ca1c5c681c4da1b`.

| Shape | 1.14.2 | 2.0 candidate |
| --- | ---: | ---: |
| Top-level owner skills | 1 | 1 |
| Additional top-level skills | 0 | 0 |
| Root words | 1,348 | 929 |
| Bundled Markdown references | 9 | 13 |
| Reference words | 5,090 across 9 files | 2,806 across 13 files |
| Fixed delegate role files | 3 | 0 |
| Plugin files | 18 | 21 |
| Enforced root word ceiling | 1,400 | none |

The root is about 31% shorter. Total runtime instruction prose across the root and conditional method material
falls from 6,438 to 3,735 words, about 42%. The package exposes one skill, so its critical root and authority
boundary are part of that skill rather than a sibling dependency. Its internal methods are `codebase-design`,
`continuity`, `delivery`, `diagnosing-bugs`, `intake`, `product-decisions`, `prototype`, `research`,
`resolving-merge-conflicts`, `reviewing-changes`, `testing`, `wizard`, and `writing-for-agents`.

Nine method references are curated adaptations from the pinned Matt commit. Four are SkipHow-specific methods.
Provenance is recorded in the distributed
[`SOURCES.json`](../../../plugins/skiphow/SOURCES.json) and
[`THIRD_PARTY_NOTICES.md`](../../../plugins/skiphow/THIRD_PARTY_NOTICES.md) rather than inferred from similar
wording.

The removed numeric budget history is also exact repository evidence:

| Release range | Root limit |
| --- | ---: |
| 0.9.0–1.0.1 | 700 words |
| 1.1.0–1.7.x | 600 words |
| 1.8.0–1.9.x | 850 words |
| 1.10.0–1.13.x | 1,000 words |
| 1.14.x | 1,400 words |
| 2.0 release candidate | none |

No current primary host or format source read for this decision requires any of those numbers.

## Evidence limits

- Analogues establish available shapes and known caveats, not causation in SkipHow sessions.
- Matt issue #962 is an open proposal created after the pinned source commit. It is design evidence, not
  accepted upstream behavior or a model receipt.
- Superpowers' figures are its own reported experiments. They justify caution, not a SkipHow performance
  claim.
- The 2.0 word and file counts describe commit `b2196d0bd3eeca1f542cbd8af3e1b45639aad29d` when measured. They are repository
  evidence, not a runtime result.
- [Six Codex receipts](v2.0-codex-receipts.md) use prompts that omit `$skiphow` against fixtures exposing one
  project-local skill. Neither the prompts nor fixture instructions name SkipHow, and hooks were disabled.
  Their records show Codex reading that exact root and applicable methods, which observes implicit
  project-local selection for those prompts. Six one-off runs do not establish a general selection rate. The
  visual receipt also used the user-level `impeccable` skill, so it does not isolate visual method.
- When a transcript exposes only an unknown or unversioned contract path and no external exact-tree binding,
  the governing contract identity and body remain `UNVERIFIED`; nearby versioned reads do not establish them.
- Two earlier receipts failed. One accepted broad autonomy plus a repository procedure as a protected grant.
  The next enforced that repaired gate but falsely described local markers as real production and publication.
  Both failures informed the clean receipt candidate at commit
  `b2196d0bd3eeca1f542cbd8af3e1b45639aad29d`, skill subtree
  `95d908988208b9fcc1d285fe1ca1c5c681c4da1b`, before the six controls. The current 2.0.1 working tree keeps
  those runtime bytes but changes package metadata and contributor tooling, which the controls do not cover.
  Installed-plugin behavior, packaged-hook execution, Claude runtime, real remote effects, and other scenarios remain `UNVERIFIED` under
  [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md).
