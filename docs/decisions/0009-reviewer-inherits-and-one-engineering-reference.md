# ADR 0009: The reviewer inherits the session model; engineering methods are one reference

## Status

Accepted in 1.2.0, amended in 1.12.0 (see below). Amended by [ADR 0015](0015-unconditional-invariants-live-in-the-root.md) on the root budget. Amends [ADR 0007](0007-host-adapters-for-routing-and-continuity.md) (reviewer tier) and [ADR 0006](0006-host-native-campaign-and-engineering-policy.md) (method layout). [ADR 0008](0008-receipts-over-a-live-harness.md) stands.

## Date

2026-08-26

## Context

ADR 0007 pinned the `reviewer` adapter to the `opus` family alias so the `DEEP` tier would be "the strongest" model. The 1.1 routing receipt showed the opposite in practice: the root ran on `fable` and the reviewer it delegated to ran on `opus`, a weaker model. Any alias pinned for the top tier falls behind the owner's own choice as soon as a stronger family appears, which is the one failure the tier was meant to avoid.

The current subagent documentation lists `fable` as an accepted alias, but Fable access is enabled per organization, may bill usage credits with a consent prompt, and its mapping on non-Anthropic providers is undocumented. `best` is documented only for the session picker, not for agent definitions. `effort` in an agent definition defaults to the session's level.

Separately, ADR 0006 placed five engineering methods (testing, review, design, prototype, conflicts) under a router reference. Together they were about 950 words across six files, most of it advice a strong model already applies; the parts that matter are a handful of invariants (review the exact head, a bug test fails before the fix, a prototype never ships unchanged, never resolve a conflict by picking a side).

`claude plugin eval` now exists in the host with a no-plugin baseline arm. On 2026-08-26 it reported "currently in early access" for this account and could not run.

## Decision

The `reviewer` adapter sets `model: inherit` and no `effort`; it runs on the owner's session model at the session's effort. The `DEEP` tier is therefore "the model the owner chose to pay for", and role escalation ends there. `scout` (`haiku`, low effort) and `builder` (`sonnet`, isolated worktree) are unchanged. The deterministic check requires exactly this.

The five method files and their router collapse into one `references/engineering.md` of about 450 words holding only the invariants. The reference set is eight files.

Evaluation stays receipt-based under ADR 0008. When `plugin eval` becomes available, its baseline arm is the intended way to back comparative claims; until then such claims are labelled hypotheses.

## Consequences

Review quality follows the owner's session model instead of a vendor alias, on every provider and model generation, with no package change. An owner who runs a cheap session model gets a cheap reviewer; the guide says so.

The references total about 3,450 words (from about 4,300). `scripts/check.py` folds the former budget script into one function with fixed limits (root under 600 words, references under 4,000 in total and 600 per file).

## Amendment, 1.12.0

### Context

Since 1.11.0 every project change closes with an independent pass by a `reviewer` delegate. On both
hosts that delegate runs on the session model: `inherit` in the Claude Code adapter, a same-session
spawn at `high` effort on Codex. A fresh context is not an independent one: the priors that
wrote the change are the priors that judge it, so the closing pass is the same model family reviewing
its own work.

The decision above closed the ladder on purpose, and that reasoning still holds: a pinned family
alias ages behind the owner's own session model, which is the failure the `DEEP` tier existed to
avoid. What it left is a ceiling. The root tells a run to raise the role one tier after a second
failure with the same cause, and for work already at `reviewer` there is no tier above.

`open-gsd/gsd-core` answers the same question in `/gsd-review`: it detects installed AI CLIs, skips
its own host for independence, and feeds each remaining one the same prompt. Its effort handling is a
universal ladder rendered per host — `claude --effort <level>`, `codex -c model_reasoning_effort=<level>`,
`opencode --variant <level>` — clamped to what each CLI documents, with no flag ever guessed for a CLI
that documents none. The idea transfers. Its thirteen reviewer lanes, capability-manifest registry and
`review.models.<slug>` config keys do not: SkipHow has two hosts, so "the other one" needs no registry
to resolve, and it has no configuration surface to put one in.

Codex ships a first-party non-interactive `codex review` that takes custom instructions on stdin and
reviews the pending change in a read-only sandbox, so this rung needs no prompt harness of SkipHow's
own — which is what [ADR 0002](0002-host-native-execution.md) asks for.

### Decision

- Independence is a second axis, not a higher tier. When the review widens — security, a public
  contract, a large integration, weak evidence, a repeated failure — the one independent pass goes to
  the **other installed host** rather than to a same-model delegate. Escalation ends there. This does
  not age, because the rule names the other host and never a model.
- The ordinary closing pass is unchanged and stays in-host. The cross-host rung is escalation only, so
  a bounded change acquires no second CLI and no extra wait.
- It covers **a candidate change only**. The `reviewer` role's planning and diagnosis work stays
  in-host: there is no candidate to name, and the external review command is diff-scoped.
- Effort is fixed at `high`, from the role's `DEEP` tier, rendered per host (`--effort high`;
  `-c model_reasoning_effort="high"`). No model is passed — the tool's own default answers, and its
  identity is recorded when the tool discloses it. There is no knob and no config key.
- No prompt precedes the pass, and nothing here grants it: it runs a tool the owner installed, on this
  machine, under the authority the change already carries. A reference cannot widen the root's authority
  contract and this one does not try. The report names which host produced the verdict.
- The two hosts do not bound the pass equally, and the reference says so rather than claiming a sandbox
  it does not have. Codex runs the review in an OS-level read-only sandbox and a planted project hook did
  not fire; `claude -p --permission-mode plan` bounds the model's tools, and a planted project `PreToolUse`
  hook wrote a file during a plan-mode run. Measured, not assumed ([1.12 receipts](../research/2026-08-27/v1.12-receipts.md)).
- Availability is the switch. When the other host is absent, unauthorized, or fails, the in-host
  `reviewer` takes the pass and Limits says the independent pass shared the session's model.

### Consequences

An owner with one CLI keeps exactly today's behavior and is told so. An owner with both is told to use a
different model family on the changes where a missed defect costs most, at the price of one external
call that runs in minutes, not seconds. Nothing is installed, written, or configured to get it.

Amended again in 1.13.0: effort is requested only from the host that validates the request. `claude --effort` warns and falls back on an unknown value; on codex-cli 0.149.1 with the model disclosed as `gpt-5.6-sol`, `codex -c model_reasoning_effort` accepts any value, including a bogus one, and the run stays at the host default across eight measured passes, three of them through `codex review` itself. Naming a level there was a claim the tool does not honour. The reference states the rule and the receipt carries the measurement, so no version-bound host claim ships in the package. The model is still never named on either side.

The mechanics are two commands in `model-routing.md` and one sentence in `engineering.md`; the root is
untouched, because the rule is conditional on the other host existing and [ADR 0015](0015-unconditional-invariants-live-in-the-root.md)
puts conditional detail in a reference. Both loading triggers the root already lists reach it.

### Rejected alternatives

- **A reviewer-lane registry and `review.*` config keys in gsd-core's shape.** [ADR 0014](0014-conform-to-the-tracker-classification.md)
  and [ADR 0015](0015-unconditional-invariants-live-in-the-root.md) each rejected a configuration
  surface. Two hosts do not need a registry to name "the other one", and availability already answers
  the question a `default_reviewers` list exists to answer.
- **Both passes on every change.** Doubles the wait and the spend for a second opinion the escalation
  triggers already scope, on the population of changes least likely to need it.
- **Pinning a stronger model alias for the reviewer.** The original rejection above, unchanged.
- **A `PreToolUse` hook that blocks a report without a cross-host verdict.** Rejected for the third
  time on the grounds ADR 0014 and ADR 0015 already give: per-project, on a protected settings surface,
  and it hardcodes one workflow's commands.
- **Disabling the external Claude reviewer's `CLAUDE.md` and auto-memory,** the way gsd's `claude` lane
  does. gsd needs that for fairness across thirteen lanes starting from one assembled prompt. SkipHow's
  reviewer is told to judge against repository standards second, and those standards live in exactly
  those files.
- **Reviewing plans and decompositions across hosts,** which is what `/gsd-review` actually reviews.
  There is no candidate to name and the external review command cannot take one. Revisit with a receipt.

### Revalidation triggers

Revisit when a receipt shows the cross-host reviewer returning nothing the in-host pass did not, when a
host removes its non-interactive review or its effort surface, or when a third host is supported — at
which point "the other host" stops resolving and the selection question gsd answers with a registry
becomes real.

## Rejected alternatives

- `model: fable` for the reviewer: gated per organization, may bill credits, undocumented on other providers, and would age the same way `opus` did.
- `model: best`: not documented for agent definitions.
- Keep `opus`: proven weaker than the root in the 1.1 receipt.
- Keep the method files: the invariants fit in one reference; the rest was ceremony for the model, which ADR 0006 itself warned against.

## Evidence

- [1.1 receipts](../research/2026-08-26/v1.1-receipts.md) (effective models per delegate)
- [1.2 receipts](../research/2026-08-26/v1.2-receipts.md)
- [1.12 receipts](../research/2026-08-27/v1.12-receipts.md) (the cross-host rung: what each host accepts, the read-only boundary, and this release's own review)
- [Claude Code subagent documentation](https://code.claude.com/docs/en/sub-agents.md) and [model configuration](https://code.claude.com/docs/en/model-config.md), read on 2026-08-26

## Revalidation triggers

Revisit when a host lets an agent definition ask for "the strongest available model" by a documented stable name, when receipts show the inherited reviewer missing defects a stronger tier would catch, or when `plugin eval` becomes available to this project.
