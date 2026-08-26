# ADR 0009: The reviewer inherits the session model; engineering methods are one reference

## Status

Accepted in 1.2.0. Amended by [ADR 0015](0015-unconditional-invariants-live-in-the-root.md) on the root budget. Amends [ADR 0007](0007-host-adapters-for-routing-and-continuity.md) (reviewer tier) and [ADR 0006](0006-host-native-campaign-and-engineering-policy.md) (method layout). [ADR 0008](0008-receipts-over-a-live-harness.md) stands.

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

## Rejected alternatives

- `model: fable` for the reviewer: gated per organization, may bill credits, undocumented on other providers, and would age the same way `opus` did.
- `model: best`: not documented for agent definitions.
- Keep `opus`: proven weaker than the root in the 1.1 receipt.
- Keep the method files: the invariants fit in one reference; the rest was ceremony for the model, which ADR 0006 itself warned against.

## Evidence

- [1.1 receipts](../research/2026-08-26/v1.1-receipts.md) (effective models per delegate)
- [1.2 receipts](../research/2026-08-26/v1.2-receipts.md)
- [Claude Code subagent documentation](https://code.claude.com/docs/en/sub-agents.md) and [model configuration](https://code.claude.com/docs/en/model-config.md), read on 2026-08-26

## Revalidation triggers

Revisit when a host lets an agent definition ask for "the strongest available model" by a documented stable name, when receipts show the inherited reviewer missing defects a stronger tier would catch, or when `plugin eval` becomes available to this project.
