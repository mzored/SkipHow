---
name: dogfood
description: Audit real SkipHow sessions from other projects against the contract they actually ran, then propose package changes the evidence supports. Use when asked to check how SkipHow behaved in a real project, review dogfooding sessions, work out why a run misbehaved, or turn an observed field failure into a change to the shipped skill. For developing SkipHow in this repository only.
---

# Dogfood audit

SkipHow changes from failures observed in real projects, not from redesign. This skill turns the owner's real
sessions in other repositories into that evidence: what the package told a run to do, what the run did, and
which of the two is at fault.

This is a contributor tool. It is not part of the shipped plugin and it does not ship. Do not invoke the
`skiphow` skill to do this work — `AGENTS.md` forbids using the installed plugin to govern this repository,
and the package here is the thing under test, not the authority. Reusing SkipHow's report headings below is a
format choice, nothing more.

## Scope and authority

Read only the sessions the owner named, or a dated range the owner approved. Transcripts hold other projects'
business data; treat every line as private.

The owner's words grant the work, exactly as they do in the product:

- "audit", "check", "why did it do that" — inspect and report. Change nothing.
- "audit and record" — also write the receipt described under Report.
- "audit and fix" — also change the package, but only when the change is covered by an existing ADR's
  revalidation trigger or is purely editorial, such as removing a contradiction an ADR already settled.
  Any other wording change to the contract stops at the proposal: it is a material product decision and it
  belongs to the owner. Bump `VERSION` and add the changelog section when `plugins/skiphow/` changes; never
  push a tag. The release stays the owner's three steps.

Approval is not the same as a new ADR. The changelog section and the receipt are the record a policy edit
gets; record proportionately, and amend the ADR that already owns the question rather than opening a
competing one. Write a new ADR only for a decision that is expensive to reverse, or that rejects an
alternative a future contributor would otherwise propose again.

## Find the sessions

`sessions.py` locates and slices; it never judges.

```sh
python .claude/skills/dogfood/sessions.py list           # external sessions, newest last
python .claude/skills/dogfood/sessions.py coverage       # which ones the receipts already cover
python .claude/skills/dogfood/sessions.py digest <id>    # one session as reviewable evidence
python .claude/skills/dogfood/sessions.py grep <id> <re> # back into the raw bytes, bounded
```

Read digests, never raw transcripts: the largest is megabytes and the digest is kilobytes. `list --all` also
shows excluded sessions with a reason. A session excluded as `self-development` is not noise — it is an
`AGENTS.md` violation worth reporting.

## Judge against the contract the run actually had

A session records the package version it ran. Judge it against those bytes, not against HEAD:
`git show v<version>:plugins/skiphow/skills/skiphow/SKILL.md` and the same for any reference. Read
[the checklist](references/checklist.md) for what to check and what each signal does and does not prove.

Four things must be settled before any check can fail:

- **Is the session still running?** The digest flags a transcript that was written to minutes ago. A live
  session owes nothing yet, and its missing report is not a deviation.
- **Was the run interrupted?** A session that ends mid-tool never owed a report. The digest says so.
- **Did the context compact?** Then "it forgot" is a live innocent explanation.
- **Did the rule that failed ever enter context?** The digest separates a reference that was read from one
  that was only searched or named. A rule that never loaded cannot be blamed on the reference body.

## Verdicts

Give each deviation its evidence, the session, the version, the model, and one cause.

- `DEFECT` — the package text is the proximate cause. Name the file and the sentence. Provable from a single
  session, because it is a readable property of the artifact; omission counts, and 1.7.0's defect was a
  sentence that ordered "give each record a type" without saying what a type is or where it lands.
- `VARIANCE` — the governing sentence was plain and in context, and the run deviated anyway. Never provable
  from one session.
- `NOT-A-DEFECT` — the expectation was wrong. The contract leaves this to judgment, or a repository file
  narrowed scope, which is conformance.
- `UNVERIFIED` — the cause is not yet attributable. This is the default, and it is where a weak text argument
  with one observation belongs.

Count honestly: "2 of 3 sessions", never a percentage, and pool only sessions where the check applied and the
governing sentence was byte-identical. Two deviations in one session are one observation.

## From a defect to a proposal

Root-cause the deviation to one sentence and say plainly what is wrong with it: missing, ambiguous,
contradictory, miscued by the only worked example, or never loaded. Then pass three gates before the proposal
exists.

- Grep `## Rejected alternatives` across `docs/decisions/`. If the project already rejected this, either drop
  it or carry new evidence that the rejection reason no longer holds.
- Grep `## Revalidation triggers`. A match means the project already asked for this receipt, and the ADR must
  be amended alongside the skill.
- Check the budgets in `scripts/check.py`, and read them as a drift guard rather than a target ([ADR
  0015](../../../docs/decisions/0015-unconditional-invariants-live-in-the-root.md)). If a rule must hold on
  every request it belongs in the root, and a binding budget is a reason to review the budget, not to shave
  meaning out of a sentence. Trading words for a number is how ADR 0004 lost its step 4 for six releases.

Prefer deleting a contradiction, then tightening a sentence, then moving it so it loads earlier. Adding is
last: the 1.1 shrink quietly dropped a rule that then governed nothing for six releases, so say what a deleted
sentence was doing.

A defect already fixed at HEAD is not a change. It is a receipt request against HEAD's verification status.

## Report

Report under `Result`, `Evidence`, `Rulings and findings`, `Saved follow-ups`, `Limits`. Limits always names
the blind spot: a finding a run noticed and silently dropped leaves no trace, so tag conformance is an upper
bound.

With a record granted, write `docs/research/<date>/field-audit-<date>.md` in the style of
`real-task-application-audit.md` — no project names, no issue titles, no customer data, no absolute paths —
and add its row to that directory's `README.md`. Include one line per session read, so the next audit can see
its own coverage without a second ledger:

```text
Audited `<8-char session>` · <records> records · plugin <version> · <one-line verdict>
```

Then run `python scripts/check.py`. Its personal-path scan is what stops a transcript path reaching `docs/`.
