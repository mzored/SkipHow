# ADR 0014: Conform to the tracker's classification, do not configure it

## Status

Accepted as amended by [ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md). A requested
record still follows the tracker's native classification and project conventions without configuring a
second workflow. The `skiphow-batch` marker and fixed inbox schema are historical 1.x mechanics.

## Date

2026-08-26

## Context

Dogfooding 1.6.1 on a real project, a `RECORD` run created five Issues with `--label bug`. That tracker classifies work with native GitHub issue types, not labels. Measured with `gh issue list --json issueType,labels` over 237 Issues: 175 carry a native type (Bug 69, Feature 48, Task 45, Epic 13) and 62 carry none, while labels are a separate legacy axis (`beta-feedback` 46, `needs-triage` 46, `bug` 45, `ux` 22, `enhancement` 13). The dominant convention was unambiguous and one call away.

The skill named half the rule. `intake.md` ordered "give each record a type" without saying what a type is or where it lands; `type` appeared once in the whole package, and the fenced inbox block had no `Type:` field, so on the no-tracker path the required type had nowhere to go. The only concrete tracker write the package named anywhere was a label, `skiphow-batch:<date>`, and the [1.2 receipts](../research/2026-08-26/v1.2-receipts.md) record a "type label (`bug`, `question`, `enhancement`, `documentation`)" as validated behavior. An agent told to give a record a type, writing to GitHub, with a label as the only worked example, reaches for `--label bug`. The package nudged it there.

The [prior-art research](../research/2026-08-26/prior-art-mechanics.md) had already read Matt Pocock's `setup-matt-pocock-skills`, whose per-repo `docs/agents/issue-tracker.md` and `triage-labels.md` map canonical skill roles onto each repository's own label strings. The principle is right: the skill names a role, the repository supplies the string. The mechanism is a one-time setup interview and committed config files, which the same research classified as ceremony a strong model does not need.

## Decision

- Before writing to a tracker, read how it already classifies work: native item types, labels, templates, and required fields. Match what its recent items use. Where they disagree, follow the newest consistent convention and report the choice as a ruling.
- Never invent a classification the tracker does not already use.
- Resolve the convention from the live tracker at use time. SkipHow does not add a per-repository tracker config, a setup step, or a label vocabulary of its own.
- `skiphow-batch:<date>` is SkipHow's own bookkeeping. It selects a batch later; it does not classify the work, and a label is never a second workflow engine.
- The inbox block carries a `Type:` field so the no-tracker path can record what the contract already demanded.

## Consequences

A `RECORD` run costs one extra read of the tracker before its first write. Classification stays correct as a project's convention drifts, because nothing is cached: the tracker in the receipt above drifted three times in one month, and its newest Issue carries neither a type nor a label. Projects need no SkipHow setup to get this, and Codex and Claude Code get the same behavior from the same shipped reference rather than from per-tool memory.

The rule constrains form, not judgment: choosing Bug over Task for a given record remains the model's call, reported as a ruling when the tracker is inconsistent.

## Amendment, 1.11.0

### Context

An owner report from the field surfaced the same failure on a surface the package never named ([owner report](../research/2026-08-27/owner-report-commit-language.md)). The owner talks to the run in Russian; the run wrote its commit messages in Russian, into a repository whose history is entirely English. The package said nothing about commits at all — `commit` appeared three times in it, all incidental — and nothing anywhere about the language of what a run writes. With no convention named, the run took the one signal in front of it: the conversation. The defect is one level above commits. The same slip reaches branch names, pull request bodies, and Issue titles, and it is the same shape as the label failure above: the project's own record answered the question, and the run did not read it.

### Decision

- The rule generalizes past the tracker. Durable text a run writes into the project — commits, branch names, records, pull requests — follows the conventions the project's own recent history shows, in the language that history uses. Read `git log` on the base branch before the first commit and match its message form and granularity. Where the project has no record to read, write English. The owner's conversation language is never the source.
- The convention clause is unconditional, so it lives in the root skill per [ADR 0015](0015-unconditional-invariants-live-in-the-root.md); `delivery.md` keeps only the `git log` mechanic.
- Still no commit-message vocabulary of SkipHow's own. Mandating Conventional Commits would be this ADR's original failure one surface over: the project's history supplies the form.

### Consequences

A run reads `git log` once before its first commit, the same shape of cost as the one tracker read above. `setup-matt-pocock-skills` was re-read against this surface and again adopts nothing: it names neither commits nor language, and its committed per-repository config stays rejected for the reason below.

## Rejected alternatives

- A per-repository tracker config in the style of `setup-matt-pocock-skills`: `github.md` already derives its tracker (GitHub when present, `.skiphow/inbox.md` otherwise) with no setup step, so a config subsystem contradicts a settled architecture. Written conventions also go stale, while a live read cannot. That skill needs its config because it spans GitHub, GitLab, local markdown, and Jira, where the choice is genuinely underivable; SkipHow does not have that problem.
- Adopting the five-role triage vocabulary (`needs-triage`, `ready-for-agent`, and the rest): SkipHow's dispositions are report-time, not tracker state, and the [system review](../research/2026-08-26/system-review.md) says the existing label vocabularies should shrink, not grow.
- A `PreToolUse` hook rejecting an untyped `gh issue create`: enforceable but per-project, on a protected settings surface, and it hardcodes one tracker's flags into a durable file. A rule in the reference works everywhere with no setup.
- Naming a default type vocabulary in the skill: that is the failure being fixed, one level up.

## Revalidation triggers

Revisit when a receipt shows a run inventing a classification token a tracker does not use, ignoring a tracker's native types, stalling because the tracker's convention could not be read, or writing a durable artifact in a language or message form the project's own history does not use.
