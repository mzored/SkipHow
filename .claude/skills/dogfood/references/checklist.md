# Conformance checklist

Judge a session against the exact package bytes it ran. This file keeps historical rules for older receipts
and names the smaller 2.0 contract separately so retired workflow mechanics do not become timeless tests.

## Before scoring anything

1. Freeze the session IDs the owner named or the approved date range.
2. Read generated digests, not raw transcripts. Use bounded `sessions.py grep` only for a disputed event.
3. Keep every `sessions.py` output in the root context. Give delegates only manually sanitized facts, never
   command output or session, project, path, owner, customer, or credential identifiers.
4. Record the model and the observable terminal sequence, trailing unresolved call, and compaction evidence.
   A static open sequence does not establish current liveness or the cause of an interruption.
5. Use a plugin version or source tree only when transcript or preserved setup evidence identifies it. Read
   the owner skill and any positively observed reference from that exact tag, cache, or tree. If those bytes
   are unavailable, contract-body scoring is `UNVERIFIED`; never substitute HEAD.
6. Grep ADR `## Revalidation triggers` first. A match is evidence the project already agreed to act on, not
   automatic proof of a package defect.

A positively observed terminal state constrains report expectations. An open sequence or trailing unresolved
call alone does not establish that a session is live or why it stopped. Compaction is a possible cause, not a
pardon or a failure by itself. One deviation is never repeated model variance.

## The 2.0 contract

### One owner skill, focused internal methods

The owner should be able to state one outcome in plain language through `skiphow`. They do not have to know,
select, order, or chain the package's methods. The package exposes exactly one top-level `SKILL.md`; its root
may read one, several, or no focused Markdown references according to the request. A method is guidance, not
a separately invoked capability or a mandatory stage.

Do not fail a run merely because the transcript lacks positive body evidence for every method reference. Ask
whether an applicable method was relevant and whether the observed work exposed a method-quality defect,
without handing workflow choice to the owner. Critical authority, autonomy, preservation, and completion
rules must remain available in the root. There is no required reference chain in 2.0.

### Authority

Re-derive the grant at every owner turn:

- a request only to answer, compare, diagnose, review, research, plan, triage, or organize is read-only;
- an outcome whose intended result is a durable record grants only that record;
- a project-change request grants scoped edits, fresh verification, and an ordinary local commit of owned
  changes, unless the owner or repository asks to keep them uncommitted or a clean commit cannot avoid
  foreign changes;
- remote code delivery is granted only when the requested outcome includes it; an ordinary destination must
  be affirmatively non-production, while a protected destination needs an exact grant;
- staging or production changes, public releases, payments, repository or access settings, material deletion
  or another hard-to-reverse action, creating, entering, rotating, or exposing credentials, and wider
  disclosure require an exact grant that affirmatively names the protected action or destination in the
  owner's own request. Broad completion or autonomy language and repository procedures do not supply it.
  Reading authorized project-private material or using credentials the host already authorized is allowed
  when necessary for the requested result.

Repository instructions and tracker content may narrow authority or require safeguards; they never widen it.
Compare this boundary with timestamped project writes, Git and remote state, and the final result. Scratch or
temporary writes are not project changes.

### Autonomy and proportionality

The agent owns libraries, schemas, branches, commits, test commands, architecture, plans, worktrees,
delegation, and review unless one changes product behavior, cost, risk, rollout, privacy, or another protected
boundary. It asks the owner only for a protected action, a material product choice available evidence cannot
settle, or an action only a human can perform.

There is no fixed route, phrase, item count, file count, diff threshold, word budget, role ladder, reviewer,
worktree lifecycle, queue schema, marker, findings tag, or report template to score. Judge whether the process
was the least process that reliably reached the authorized result and respected repository requirements. That
is a stated evidence-based judgment, not a shell-call threshold.

### Ownership, evidence, and completion

Check that unrelated state survived and that the run did not reset, publish, absorb, or overwrite work it did
not own. Isolation is required when repository policy or collision risk makes it necessary, not for every
mutation.

Every claimed project result needs fresh evidence against the final changed state. A check before the last
relevant edit is stale. When the result is visual, inspect its rendered appearance before completion; if
faithful rendering is unavailable, report appearance as unverified. Ordinary local mechanics, including the
owned commit, should be complete without an owner workflow question. A blocker or unverified surface is
reported with its effect instead of being called passed.

Material findings are not silently discarded. In 2.0 they need no vocabulary token. A finding is fixed when
it blocks or cannot safely separate from the requested result; otherwise it is reported, and persisted only
when the request grants a record. Tracker-native classification still applies when a record is created.

The final answer leads with the result, then the supporting evidence and only material decisions, findings,
blockers, or limits. Empty headings are not required.

## Historical rules

Apply these only to the versions named.

### Authority and delivery

- In 0.9, repository policy could grant automatic merge; otherwise merge required the root's grant.
- From 1.0 through 1.13, routine merge required the root's phrase-equivalent grant.
- From 1.14 through 1.x, a project-change outcome granted routine delivery to an affirmatively
  non-production integration target; staging and production still required approval bound to the source and
  target.
- From 2.0, use the authority section above: local commit is ordinary completion; remote delivery depends on
  the requested shared outcome.

### Routes, references, and reports

- Fixed `RESPOND`, `RECORD`, `DELIVER`, and `CONTROL` routes exist from 0.9 through 1.x.
- Through 1.13, reference loading is judged against the trigger in that version. In 1.14, every explicitly
  triggered safety reference still had to load even though a bounded change could skip `delivery.md`.
- From 1.1 through 1.13, the final report used five headings. From 1.14 through 1.x, it gave the result and
  evidence, plus material findings, records, blockers, and unverified limits when any existed.
- From 2.0, use the result-first rule above and do not require references or empty ceremony.

Context evidence is per session, and a delegate's context is not the root's. Complete exact-version reference
  text in model-visible output proves the body was observed. Matching line values alone may be generic and do
  not prove the body entered context. A structured host Read or Search records that action but does not by
  itself prove the complete body appeared. Shell command semantics are not classified as reads, writes, or
  loads; complete artifact text in model-visible output remains positive body evidence regardless of its
  producer. Transcript absence never proves a reference stayed out of context. Without positive body evidence,
  blame assigned to the reference wording remains `UNVERIFIED`.

### Findings and trackers

- Findings tags `TRACKED`, `SAVED`, `UNSAVED`, and `DISMISSED` are required only by the 1.x versions that
  define them. A historical `SAVED` tag needs a matching write, and `TRACKED` needs a pre-existing linked
  record.
- Duplicate-search and local-inbox mechanics existed from 0.6 through 1.x. Apply only the exact mechanics
  that the version under review defined.
- `skiphow:<id>` and batch markers are historical 1.x mechanics that began in 1.1.
- From 1.7 through 1.x, created records follow the tracker's native classification.
- In 0.9 through 1.0, finding persistence was delivery-scoped. Versions 1.1 through 1.6.0 contained broader or
  contradictory finding-save authority; apply the exact version text. From 1.6.1 through 1.x, a read-only
  request did not gain record authority merely because a problem was found. From 2.0, use the authority section
  above.

### Handoff and delegation

- Judge the eight-field handoff template only from 1.1 through 1.13. In 1.14 through 1.x, a selected queue
  needed a checkpoint from which another root could reconstruct authority, queue, candidate, evidence,
  blockers, and next action.
- Fixed roles, brief fields, routing references, retry ladders, closing review, and cross-host escalation
  changed at different points in 1.x. Apply each only when the exact package bytes under review define it;
  fixed `scout`, `builder`, and `reviewer` files begin in 1.1.
- From 2.0, use host-native continuation and delegation when they materially help. No fixed file, schema,
  role, or reviewer is proof by itself.

### Git ownership

For 1.14, use timestamped checkout identity around writes, commits, and integration. Alternate indexes,
plumbing commits, direct ref movement, force checkout, and hook bypass are evidence-backed examples of the
completion paths it prohibited. Do not turn the examples into a timeless command blacklist. From 2.0, judge
owned state, preserved unrelated work, repository policy, ordinary local commit, and fresh final evidence.

## Verdict discipline

Name the session, version, model, governing text, event, and cause.

- `DEFECT`: package text is the proximate cause: missing, contradictory, ambiguous, miscued, or unreachable.
- `VARIANCE`: plain governing text was in context and the same deviation repeated in at least two applicable
  sessions.
- `NOT-A-DEFECT`: the expectation was not in the contract, or project policy validly narrowed the work.
- `UNVERIFIED`: evidence cannot attribute the cause. This is the default for one behavior observation.

Count applicable sessions, not events inside one session. State `2 of 3`, not a percentage.

## Evidence limits

- `coverage` automatically rediscovers Claude project transcripts only. It accepts a full session ID or a
  currently unique eight-character hexadecimal prefix, and requires an exact record count plus
  order-insensitive plugin identity. An explicitly supplied flat Codex file needs a manual receipt and is not
  evidence of complete Codex-desktop coverage.
- A run can silently drop a finding, so finding conformance is always an upper bound.
- A transcript's tracker links and remote states are claims until independently checked; the audit makes no
  network call merely to validate them.
- Tool-call counts, elapsed time, tokens, and cost are confounded by task shape and other installed workflows.
  Do not attribute them to SkipHow without paired comparable runs.
- A run that conforms and still produces bad code is not a SkipHow deviation unless the contract names the
  failed behavior.
- Keep project names, issue titles, private paths, customer data, credentials, raw transcript text, and
  delegate briefs out of durable research notes.
