# Owner report: commit messages in the conversation's language, 2026-08-27

An owner report, not a transcript audit. It is recorded here because [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md)
makes field evidence the thing a policy edit answers to, and because the 1.11.0 edit has no other receipt.
No project name, path, or Issue title appears here.

## What the owner observed

Working in a repository whose Git history is entirely English, with SkipHow installed, talking to the run in
Russian: the agent wrote its commit messages in Russian. The owner judged this bad practice, asked whether
the package said anything about commits at all, and asked for a systemic fix rather than a correction to
that one run.

No transcript was captured, so the plugin version, host, and route are unrecorded. The report is evidence
that the behavior occurred; it is not evidence of how often, or on which versions.

## What the package said

Verified against `6aa91c0`, the tip at the time of the report. Which version the reporting run had actually loaded is unrecorded, and the [field audit](field-audit-2026-08-27.md) in this directory records an owner watching a version their session had never loaded:

- The word `commit` appeared three times in `plugins/skiphow/`, all incidental: a review candidate's
  identity (`references/engineering.md`), a checkpoint field (`references/long-work.md`), and a deletion
  guard (`references/github.md`). No rule named the act of committing.
- `references/github.md` ran Issue → branch → implement → pull request, with no commit named between
  implement and pull request. The root now closes every change, so 1.11.0 points that step at the root
  rather than restating it.
- Nothing anywhere named the language of what a run writes. The only language clause in the repository is
  `CONTRIBUTING.md`, which governs SkipHow's own package text and never loads at runtime.

So the run had no convention to follow and one signal in front of it: the conversation.

## Why this is not a commit-message problem

The same gap reaches branch names, pull request bodies, and Issue titles — every durable artifact a run
writes. It is also the failure [ADR 0014](../../decisions/0014-conform-to-the-tracker-classification.md)
already named for tracker labels, on a surface that ADR did not cover: the project's own record answered the
question and the run did not read it. 1.11.0 amends that ADR rather than opening a competing one.

## Related evidence already in this directory

The [field audit](field-audit-2026-08-27.md) records, from a real eight-delegate session, that
"independent review earned its spawn: two of three reviewer delegations returned blocking defects on
branches that were otherwise ready." That is the in-repo evidence behind 1.11.0's second change, which makes
a `reviewer` pass close every project change instead of leaving it to a conditional trigger.

## Open

Whether the 1.11.0 invariant changes runtime behavior is `UNVERIFIED`. The next audit should look for a run
committing in a repository whose history language differs from the conversation's, and for a bounded change
that closes with a reviewer pass.
