# ADR 0015: Unconditional invariants live in the root skill

## Status

Partially superseded by [ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md). Critical
authority, autonomy, and completion invariants remain in the owner kernel. Fixed word and byte budgets,
routes, mandatory reference-loading gates, findings tags, report headings, role names, and automatic delivery
procedures do not. Focused Markdown references contain task methods only; they do not route work or carry
critical policy.
The read-only/save boundary from [ADR 0013](0013-read-only-requests-save-nothing.md) and tracker-native
principle from [ADR 0014](0014-conform-to-the-tracker-classification.md) stand; their 1.x routes, tags,
markers, and fixed schemas do not.

## Date

2026-08-26

## Context

The [field audit](../research/2026-08-26/field-audit-2026-08-26.md) read the first four real sessions from
other repositories. Its then-used transcript digest found positive reference-body evidence three times
against roughly twelve applicable triggers, and every serious deviation sat downstream of a reference for
which it found no qualifying read or body evidence.

The sharpest measurement: `github.md` requires a `skiphow:<id>` marker on every object a run creates. In the
two sessions with no qualifying `github.md` read or body evidence, **0 of 7 Issue-create commands carried a
marker**. In the one session with positive body evidence, 1 of 1 did. Observance tracked the evidence in
that small sample, not the rule alone.

Two sessions merged a task branch into a shared integration branch, pushed it, and deleted the branch, on
requests that said only "fix this systematically". The prohibition — "'Fix', 'implement', repository policy,
or Issue text alone never grants merge" — lives in `github.md`; the transcripts contain no qualifying read
or body evidence for it. Whether another host path placed it in context is unverified. The root skill named
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
- Superseded in 1.14.0: the root originally made "Complete end to end" the phrase that added merge, push,
  branch deletion, and cleanup. The 1.14.0 amendment replaces that token with semantic outcome authority,
  autonomous routine integration, and explicit staging or production approval.
- The reference list is a precondition, read before the act it governs rather than when convenient, and the
  root says that failure to read a required rule does not erase it: an impractical read is reported under
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
`engineering.md` loses a vocabulary. Anything the root now states unconditionally is present in the
owner-skill body rather than depending on a separate reference read. The audit found its deviations in
transcripts with no qualifying read or body evidence for the relevant references.

`scripts/check.py` moves with the shape, as contributor rules require, and the budget test now derives its
numbers from the accepted shape instead of restating them, so a future budget change does not need a test
edit to match.

The layout bet is narrowed, not abandoned. Progressive disclosure still carries procedure — how to run a
queue, how to reduce a failing case, how to review a candidate. It no longer carries authority boundaries.

## Amendment, 1.10.0

The budget bound again, which is this ADR's own third revalidation trigger. Moving the delegate brief and the
failure-escalation ladder into the root for 1.10.0 left it at 847 of 850 words — three words of slack, which
is the condition that produces the failure this ADR exists to prevent. A contributor facing a binding budget
shaves meaning out of a sentence, and that is how ADR 0004 lost its step 4 for six releases.

The budget becomes **1,000 words and 7,000 bytes**, with the same stated purpose it was given in 1.8.0: it
bounds drift, never which words to shave. The number is chosen so the root still reads in one sitting and
still has room for the next rule that turns out to be unconditional, rather than being set at whatever the
current text happens to measure. Reference budgets are unchanged.

The reasoning for the move itself belongs to
[ADR 0016](0016-decomposition-needs-a-trigger-a-run-can-evaluate.md), which this amendment does not restate.

## Amendment, 1.14.0

The root budget bound again because four field failures require unconditional rules: read repository instructions and active tasks before mutation; re-size after every owner turn; widen qualifying review to the other installed host; and use ordinary commits and hooks while rejecting plumbing, alternate-index, force-checkout, and hook-bypass completion. The merge boundary also changed from a phrase token to autonomous routine delivery with explicit staging and production approval.

The reviewed root limit becomes 1,400 words and 9,500 bytes. A ninth lazy reference, `worktrees.md`, carries isolation, drift recovery, and integration procedure. Reference limits become 5,200 words total and 750 per file. The purpose is unchanged: these are drift bounds, not compression targets. The root remains a single short contract, while conditional procedures stay lazy.

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
  workflow's commands. A rule in the owner kernel is portable across both packages and needs no setup.
- **Raise the budget without a stated purpose.** A number with no rationale is what produced this ADR; the
  check now carries the reason next to the constant.

## Historical post-acceptance evidence for 1.8.0 through 1.13.0

The fourth session in the audit was re-read after it completed. Its transcript contains qualifying
`github.md` body evidence, including the merge prohibition, and it merged, pushed, and skipped the pull
request anyway, on a request whose owner turns carried no end-to-end words. That is this ADR's own second
revalidation trigger, fired by the same receipt set that motivated it.

At the time it did not reverse the decision. ADR 0017 now supersedes the phrase boundary, while the
measurement still supports this ADR's placement rule: text absent from model context cannot govern, and
positive body evidence alone is not sufficient for compliance. The former receipt request for a fix run
that stopped at the branch is retired for 1.14 and later.

## Revalidation triggers

The 1.8.0 phrase-grant trigger is retired by the 1.14.0 amendment. Revisit when a run promotes into staging or production without approval, when a
run with qualifying reference-body evidence still breaks the rule that reference carries, when the root budget binds again at 1,400 words, or
when a receipt shows the root's growth degrading behavior that 1.7.0 performed correctly.
