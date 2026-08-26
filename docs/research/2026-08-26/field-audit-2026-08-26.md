# Field audit, 2026-08-26

The first audit of real SkipHow sessions in other repositories, produced with the contributor `dogfood` skill
and recorded per [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md). Sessions are named by id
and date only; no project names, Issue titles, or paths appear here.

## What was read

Four external sessions on Claude Code 2.1.246, all on 2026-08-26, two repositories.

| Session | Plugin | Route | State |
| --- | --- | --- | --- |
| `4d32702f` | 1.6.1 | `DELIVER` | complete |
| `0df7f9b0` | 1.6.1 | `DELIVER` | complete |
| `63ef1e3e` | 1.7.0 | `DELIVER` | in flight while read; report and cleanup still ahead of it |
| `7e4cabd8` | 1.7.0 | `RESPOND` | complete |

Each was judged against the bytes it ran (`git show v<version>:…`), not against HEAD. Excluded from the
sample: 39 temporary harness runs and 2 sessions inside this repository.

## The finding that explains the others

**A reference that does not load does not govern.** Across the four sessions, references loaded three times
against roughly twelve applicable triggers.

- `model-routing.md`: unloaded in 3 of 3 sessions that delegated. Consequence: delegates were spawned without
  a role, against "Every delegation names its role; nothing inherits by omission."
- `github.md`: unloaded in 2 of 3 sessions that wrote to GitHub. Consequence, measured: **0 of 7 Issue-create
  commands carried a `skiphow:<id>` marker** in those two sessions; the one session that loaded the reference
  carried the marker on 1 of 1. The rule and its observance correlate exactly with the load.
- `diagnosis.md`: unloaded in 2 of 2 sessions whose cause was unknown. `decision.md`: unloaded in the one
  session that made a material product choice.
- `delivery.md`: unloaded in 2 of 3, which the contract permits for a bounded change. Not scored.

The `Read` tool is not the signal: one session made 266 `Bash` calls and no `Read` calls. Loading was
detected by matching fragments of each reference against the transcript, which also separates a `grep` over a
reference from a read of it. One session grepped two references for a single word; that is not a load, and
treating it as one would have inverted the conclusion below.

## Deviations

**Merge and push without an end-to-end grant — 2 of 2 completed delivery sessions.** Both requests were bug
reports asking for a systematic fix. Neither said "end to end", "finish these Issues", or an equivalent. Both
runs merged a task branch into the shared integration branch, pushed it, and deleted the branch. The
prohibition existed only in `github.md`, which neither run loaded; the root skill stated the grant positively
("end-to-end work also grants merge and cleanup") and never stated what does not grant it, while both target
repositories describe merging into that branch as their normal flow. `DEFECT`: the root named the grant and
not the boundary.

**A heading was dropped from the report — 2 of 3 sessions that owed one.** `Saved follow-ups` was missing in
both, once while the run had four saved follow-ups and listed them under another heading; `Evidence` was
missing in one. The contract named the five headings in a fenced block and never said whether a heading with
no answer is kept. `DEFECT` by omission.

**`TRACKED` used for records the run created itself — 1 of 2 sessions that created Issues.** One run created
four Issues and tagged all four `TRACKED`. The contract attached "(link it)" to `TRACKED` and defined `SAVED`
by its procedure, never by who created the record, so a run that creates an Issue and links it can read
`TRACKED` as satisfied. `DEFECT`, ambiguity.

**Saved follow-ups carried no links — 1 session.** The owner had to ask twice, first whether the items were
done or pending, then for the links. `SAVED` is the tag the contract does not ask to link.

**Absolute local paths in delegate briefs — 3 of 3 delegating sessions.** The rule said "never copy … private
paths … into prompts or public records". A brief to a local delegate is a prompt, and it needs the working
directory. No Issue body leaked a path. `NOT-A-DEFECT` in the runs and a defect in the rule's scope: it named
a surface it cannot govern.

**Two findings vocabularies shipped at once.** `engineering.md` defined review dispositions `RESOLVED`,
`PERSISTED`, `DUPLICATE`, `DISMISSED` while the root defined `TRACKED`, `SAVED`, `UNSAVED`, `DISMISSED`. The
two overlap, `DISMISSED` meant different things in each, and [ADR 0013](../../decisions/0013-read-only-requests-save-nothing.md)
recorded `PERSISTED` as "a tag the skill does not define" when a shipped reference did define it. No run in
this sample used it; the 1.6 receipts record two that did.

## What 1.7.0 got right

The tracker-classification defect that produced [ADR 0014](../../decisions/0014-conform-to-the-tracker-classification.md)
is visible in `4d32702f` at 1.6.1: five Issues created, two carrying a classification label the tracker does
not use for classification, caught by the owner rather than the run. At 1.7.0, `63ef1e3e` loaded `github.md`,
read the tracker's own labels and Issues before writing, and created its Issue with the tracker's native type
and no classification label.

That is the first field receipt for the 1.7.0 rule, and it moves the changelog's `UNVERIFIED` line one step:
the rule works when the reference loads. It is one session, on a tracker that uses native types; the
labels-only half of the changelog's request is still `UNVERIFIED`. The residual risk is the finding above —
the rule lives in two references that most sessions never load.

## Not deviations

The read-only session wrote nothing at all: no file, no record, two findings tagged `UNSAVED` and one
`DISMISSED` with its reason, and its second-hand claims marked `UNVERIFIED` under Limits. That is a clean
receipt for [ADR 0013](../../decisions/0013-read-only-requests-save-nothing.md). One session stopped to ask
the owner a product question the owner had invited; the contract reserves direction and scope to the owner,
so that is conformance. Duplicate search preceded the first create in all three creating sessions. No run
called a stale check passed.

## Limits

- **Findings a run noticed and did not mention leave no trace.** Every tag count here is an upper bound.
- `63ef1e3e` was still being written while it was read, and it had compacted. Everything said about it is
  provisional, and its missing report is not a deviation.
- Two of the four sessions are the same repository, same day, same model. They share a version and pool
  legitimately, but they are not independent evidence about behavior across repositories.
- No network calls were made. "The report links Issue N" is a claim about the transcript, never about the
  tracker.
- Codex sessions are not covered by the audit tooling at all.

```text
Audited `4d32702f` · 846 records · plugin 1.6.1 · classification DEFECT (fixed in 1.7.0); merge and push without grant; three references unloaded
Audited `0df7f9b0` · 1147 records · plugin 1.6.1 · merge and push without grant; no markers; heading dropped; no reference loaded
Audited `63ef1e3e` · 1168 records · plugin 1.7.0 · in flight, owes no report; native type and marker present, first 1.7.0 field receipt
Audited `7e4cabd8` · 50 records · plugin 1.7.0 · read-only, wrote nothing; two headings dropped
```
