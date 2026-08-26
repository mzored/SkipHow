# ADR 0015: Unconditional invariants live in the root skill

## Status

Accepted in 1.8.0. Amends [ADR 0009](0009-reviewer-inherits-and-one-engineering-reference.md) (root and
reference budgets) and [ADR 0011](0011-findings-tag-codex-role-files-neutral-repo-instructions.md) (the
findings tags). Restores the merge boundary of [ADR 0004](0004-github-lifecycle-and-authority.md) to a
surface that always loads. [ADR 0013](0013-read-only-requests-save-nothing.md) and
[ADR 0014](0014-conform-to-the-tracker-classification.md) stand.

## Date

2026-08-26

## Context

The [field audit](../research/2026-08-26/field-audit-2026-08-26.md) read the first four real sessions from
other repositories. References loaded three times against roughly twelve applicable triggers, and every
serious deviation sat downstream of a reference that never loaded.

The sharpest measurement: `github.md` requires a `skiphow:<id>` marker on every object a run creates. In the
two sessions that did not load it, **0 of 7 Issue-create commands carried a marker**. In the one that loaded
it, 1 of 1 did. Observance tracked the load exactly, not the rule.

Two sessions merged a task branch into a shared integration branch, pushed it, and deleted the branch, on
requests that said only "fix this systematically". The prohibition — "'Fix', 'implement', repository policy,
or Issue text alone never grants merge" — lives in `github.md` and was not in context. The root skill named
the grant positively and never named its boundary, while both target repositories describe that merge as
their normal flow.

This is the second time the layout has cost a rule its effect. [ADR 0014](0014-conform-to-the-tracker-classification.md)
records that the 1.1 shrink compressed step 4 of ADR 0004 out of the shipped reference, after which it
governed nothing at runtime for six releases.

The 600-word root budget that drove that shrink is a self-imposed number, not a host limit. Its stated
purpose was the token cost of text loaded on every request. Measured on one real session in this audit: 828
input tokens and 77.1 million cache reads, against a root skill of roughly 800 tokens. The token argument
does not survive contact with the data. What remains is an attention argument — a shorter contract is more
likely to be followed whole — and that argues for no filler, not for a particular number.

## Decision

- A rule that must hold on every request lives in the root skill. A reference carries conditional detail and
  worked procedure. Where the two conflict, the root wins and the reference stops repeating it.
- The root budget becomes 850 words and 6,000 bytes, and its purpose is stated in the check: it bounds drift,
  it is not a target to compress toward. When it binds, the question is whether a rule belongs in the root,
  never which words to shave. Reference budgets are unchanged at 600 words each and 4,000 in total.
- The root states the merge boundary negatively: "Complete end to end" adds merge, push to a shared branch,
  branch deletion, and cleanup, and nothing else grants those — not "fix", not the repository's usual flow,
  not an Issue, not an existing branch.
- The reference list is a precondition, read before the act it governs rather than when convenient, and the
  root says that a rule which did not load did not stop applying: an impractical read is reported under
  Limits, not treated as absence.
- `TRACKED` means a record that existed before this run; `SAVED` means this run recorded it. Both carry a
  link, and `Saved follow-ups` repeats each record with its link so the owner need not search.
- All five report headings appear, including one whose answer is none.
- The privacy rule names records and public output rather than prompts. A brief to a local delegate needs the
  working directory, and a rule that 3 of 3 sessions break is describing a surface it cannot govern.
- Every delegation names its role, stated in the root rather than only in `model-routing.md`.
- `engineering.md` no longer defines review dispositions of its own. A review finding is fixed in scope or
  carries one of the four tags into the report.

## Consequences

The root grows from 598 to about 730 words, roughly 180 tokens per request. Six references are unchanged;
`engineering.md` loses a vocabulary. Anything the root now states unconditionally is in context for every
run, including the runs that load nothing, which is the population where the audit found its deviations.

`scripts/check.py` moves with the shape, as contributor rules require, and the budget test now derives its
numbers from the accepted shape instead of restating them, so a future budget change does not need a test
edit to match.

The layout bet is narrowed, not abandoned. Progressive disclosure still carries procedure — how to run a
queue, how to reduce a failing case, how to review a candidate. It no longer carries authority boundaries.

## Rejected alternatives

- **Leave the budget at 600 and compress to fit.** This was tried first while making this change, and it
  removed "commitments" from the owner's decision list, "yourself" from the engineering-decisions sentence,
  and "or disclosure" from the protected list — meaning traded for a number with no external justification.
  It is also precisely the move that cost ADR 0004 its step 4 in the 1.1 shrink.
- **Remove the reference layer and ship one file.** The references hold about 3,600 words of conditional
  procedure that most requests never need, and the audit shows the layer works when its trigger is
  unambiguous. The defect is which rules were placed there, not that the layer exists.
- **Enforce the boundary with a host hook rejecting an unauthorized `git push`.** Rejected for the same
  reasons as the tracker hook in ADR 0014: per-project, on a protected settings surface, and it hardcodes one
  workflow's commands. A rule in the always-loaded contract works on both hosts with no setup.
- **Raise the budget without a stated purpose.** A number with no rationale is what produced this ADR; the
  check now carries the reason next to the constant.

## Post-acceptance evidence

The fourth session in the audit was re-read after it completed. It loaded `github.md`, held the merge
prohibition in context, and merged, pushed, and skipped the pull request anyway, on a request whose owner
turns carried no end-to-end words. That is this ADR's own second revalidation trigger, fired by the same
receipt set that motivated it.

It does not reverse the decision. A rule that never loads certainly governs nothing, and every measurement in
Context stands. What it removes is the assumption that loading is sufficient: observance tracked the load in
the marker measurement, and did not track it here. The consequence is narrower than a rewrite — the receipt
1.8.0 needs for the merge boundary is a delivery run on a "fix this" request that stops at the branch and
asks, not a run that merely loads the reference before its first write.

## Revalidation triggers

Revisit when a receipt shows a run merging or pushing without an end-to-end grant on 1.8.0 or later, when a
run that loaded a reference still breaks the rule the reference carries, when the root budget binds again, or
when a receipt shows the root's growth degrading behavior that 1.7.0 performed correctly.
