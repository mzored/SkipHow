---
name: dogfood
description: Audit real SkipHow sessions from other projects against the contract they actually ran, then deliver package changes the evidence supports. Use when asked to check how SkipHow behaved in a real project, review dogfooding sessions, work out why a run misbehaved, or turn an observed field failure into a change to the shipped skill. For developing SkipHow in this repository only.
---

# Dogfood audit

SkipHow changes from failures observed in real projects, not from redesign. This skill turns the owner's real
sessions in other repositories into evidence: what the package told a run to do, what the run did, and whether
the available record supports attribution or leaves it unverified. When the owner asks for a fix, it carries
the evidence-supported result through the delivery they authorized.

This is a contributor tool. It is not part of the shipped plugin and it does not ship. Do not invoke the
`skiphow` skill to do this work — `AGENTS.md` forbids using the installed plugin to govern this repository,
and the package here is the thing under test, not the authority.

## Scope and authority

Read only the sessions the owner named, or freeze the session IDs in a dated range the owner approved before
judging them. Transcripts hold other projects' business data; treat every line as private.

The owner's words grant the work, exactly as they do in the product:

- "audit", "check", "why did it do that" — inspect and report. Change nothing.
- "audit and record" — also write the audit report and coverage sidecar described under Report.
- "audit and fix" — also record the audit, implement and verify evidence-supported changes, and make an
  ordinary local commit when repository policy permits. Remote delivery still depends on the requested shared
  outcome. Own technical and architectural choices. Stop at a
  proposal only when evidence leaves a material product or rollout choice unresolved, or when the requested
  outcome does not grant a required protected action.

A public release needs an explicit owner grant. When granted, follow the repository's
[release instructions](../../../CONTRIBUTING.md#release) through merge, tag, and verification instead of
handing the steps back to the owner. Without that grant, a changed plugin is left as a reviewed release
candidate. A contributor-only change does not by itself justify moving the plugin version.

Use the audit report, coverage sidecar, and changelog as the ordinary record of a policy edit. Treat existing
ADRs as dated evidence. Amend one when the current decision still belongs there, or supersede it when current
evidence changes the decision. Write a new ADR when repository policy calls for durable rationale.

## Find the sessions

`sessions.py` locates Claude Code project transcripts, slices an explicitly supplied Claude or flat
`codex exec --json` transcript, and mechanically classifies observable evidence. It does not discover Codex
desktop rollout storage and it does not make a causal or conformance ruling.

```sh
python .claude/skills/dogfood/sessions.py list --on 2026-08-27 # exact-day plus date-uncertain candidates
python .claude/skills/dogfood/sessions.py coverage       # Claude sessions covered by strict sidecars
python .claude/skills/dogfood/sessions.py digest <id>    # one session as reviewable evidence
python .claude/skills/dogfood/sessions.py grep <id> <re> # back into the raw bytes, bounded
```

Read digests, not whole transcripts: the largest is megabytes and the digest is reviewable. Use bounded
`grep` when the digest visibly reports truncated final text or an event remains disputed. `list` returns one
candidate per root Claude owner chat. It scans nested subagent JSONLs, aggregates their marker, date, and
unreadable evidence into the parent, and explicitly scopes sidechain-only evidence instead of presenting each
subagent log as another owner chat. Only logs below the host's `<session>/subagents/` directory are nested
subagent evidence; unrelated descendant JSONLs are not folded into the owner chat. A missing, unopenable, or
unscannable parent remains visible as an unverified candidate when nested or unreadable evidence prevents
exclusion. Its displayed ID resolves to an aggregated digest whose claims remain `UNVERIFIED`, not to a
subagent transcript presented as owner evidence.
`--on` selects candidates with a marker on that exact local calendar day and retains date-uncertain candidates
whose undated, unreadable, or unscannable evidence prevents safe exclusion; `--since` is a lower bound with the
same fail-closed treatment. Neither filter uses chat creation time. A path mention or quoted example is not
proof of activation.
`list` keeps every marker-bearing candidate. Its observed CWD fields are context, not classifications,
exclusions, or proof of activation; correlate them with the marker and activation evidence before making a
ruling.

A complete `list --json` row carries an `evidence_fingerprint`. It is a privacy-safe freshness key over the
root transcript and every root or nested fact that contributes to that candidate's scope, date, and plugin
identity. Any unreadable, unscannable, or otherwise incomplete candidate reports `unverified` instead. The
fingerprint proves only that a later sidecar entry describes the same mechanically observed evidence; it does
not prove activation, conformance, causality, or audit quality. Keep the frozen row used for the audit and copy
its record count, plugin identity, and fingerprint together into the sidecar. Do not reconstruct those fields
from a later `list` run.

Every `sessions.py` output is private root evidence, including text or JSON from `list`, `coverage`, `digest`,
and `grep`. Some of these expose project names or paths even when they do not show
transcript text. Never paste command output into a delegate brief. Restate only the facts manually sanitized
for that lane, without session IDs, project names, paths, owner text, commands, report text, customer data,
or credentials.

## Judge against the contract the run actually had

Use an exact package version or source tree only when the transcript or preserved setup identifies it. For a
released version, compare with `git show v<version>:plugins/skiphow/skills/skiphow/SKILL.md` and the same
reference path. An unversioned project copy or missing tag/cache leaves contract-body scoring `UNVERIFIED`;
never substitute HEAD. When the observed activation proves an exact cache root, reference bytes and their
roster come from that same agreed root or roots; missing or differing roots leave reference scoring
`UNVERIFIED` rather than falling back to a tag. Read [the checklist](references/checklist.md) for what each
observation proves.

Four observations constrain any ruling:

- **What terminal state is present?** The digest reports a static host sequence. It can identify a completed,
  failed, open, or unobserved sequence, and marks ambiguous lifecycle evidence or an incomplete readable
  transcript as unverified instead of forcing a state. An open sequence does not prove the session is currently
  running and does not by itself excuse a missing result.
- **What is the last observable activity?** A trailing unresolved tool call proves only that no matching
  terminal event appears later in the readable transcript; it does not prove why the run stopped.
- **Did the context compact?** Then "it forgot" is a live innocent explanation.
- **Did the failed rule enter context?** Complete exact-version reference text in model-visible output proves
  the whole body was observed. An exact Read excerpt proves only the rules it contains when at least one typed
  input path exists, every input and result path agrees, and any present structured result has a recognized
  file/content shape whose partial-frame metadata is complete and internally consistent. A result-only path or
  contradictory structured result remains action evidence, not exact text provenance. A structured host
  Read/Search/Write event proves the action, not what the model received, and shell command semantics are not
  inferred. Generic line matches, path evidence, missing output, and transcript absence prove neither presence
  nor absence.

## Verdicts

Give each deviation its evidence, session, version, model, and the cause or causes the record supports. If the
evidence cannot distinguish among plausible causes, use `UNVERIFIED` and name the uncertainty.

- `DEFECT` — the package guidance is the proximate cause. Identify the affected artifact and the exact gap or
  interacting text. Provable from a single session, because it is a readable property of the artifact;
  omission counts, and 1.7.0's defect was a
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

Locate the defect as narrowly as the evidence allows and say plainly whether the guidance is missing,
ambiguous, contradictory, miscued by the only worked example, unreachable, or not shown to have entered
context.

- Check relevant rejected alternatives and revalidation triggers in `docs/decisions/`. Compare their rationale
  with the current evidence. If the evidence changes an accepted decision, amend or supersede its ADR as
  appropriate.
- Check the package boundary in [ADR 0015](../../../docs/decisions/0015-unconditional-invariants-live-in-the-root.md)
  and [ADR 0018](../../../docs/decisions/0018-autonomous-kernel-and-independent-task-skills.md). If a rule must
  hold on every request, it belongs in the root. A focused method may improve technique, but it must not carry
  authority or completion policy that disappears when the method is not read.

Prefer deleting a contradiction, then tightening a sentence, then moving it so it loads earlier. Adding is
last: the 1.1 shrink quietly dropped a rule that then governed nothing for six releases, so say what a deleted
sentence was doing.

A defect already fixed at HEAD is not a change. It is an audit-record request against HEAD's verification
status.

## Report

Report the result and evidence. Include rulings, material findings, saved follow-ups, and limits when they
exist. Name the blind spot: a finding the run noticed and silently dropped leaves no trace, so finding
conformance is an upper bound.

The digest selects the observable terminal response, reports whether that selection is verified, and states
when its displayed prefix was omitted. It infers no report template, heading set, tag vocabulary, or
version-based applicability. Compare the selected text manually with the exact governing body established for
that session; use bounded `grep` before judging text omitted from the digest.

With a record granted, write `docs/research/<date>/field-audit-<date>.md` in the style of
`real-task-application-audit.md` — no project names, no issue titles, no customer data, no absolute paths —
and add its row to that directory's `README.md`. Beside it, write
`field-audit-<date>.receipts.json`. That strict sidecar is the sole coverage source; Markdown text is never
parsed as a receipt. It has exact top-level keys `schema`, `source`, and `receipts`, with schema
`skiphow.dogfood.coverage/v1` and source `claude-code-project-transcripts`. Each receipt has exact keys
`session`, `records`, `plugin_versions`, and `evidence_fingerprint`. Set `session` to `receipt_session` copied
exactly from the same frozen `list --json` row; never reconstruct or shorten it manually. Copy the count,
version list, and fingerprint from that row too. A migrated historical entry may use JSON `null`; incomplete current evidence uses
`"unverified"`. Neither can establish coverage.

`coverage` fails closed if any sidecar is malformed and marks an entry covered only when session identity,
root record count, order-insensitive plugin identity, and a full `sha256-v1` fingerprint all match the current
candidate. A stale or incomplete entry remains `STALE`. An explicitly supplied flat Codex transcript is not
rediscovered by `coverage`; document it in the report without claiming automatic census coverage.

Review the note manually for private identifiers, then run `python scripts/check.py`. Its personal-path scan is
a backstop for common home-directory forms, not a complete privacy guarantee.
