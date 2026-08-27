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
and the package here is the thing under test, not the authority. Reusing SkipHow's report headings below is a
format choice, nothing more.

## Scope and authority

Read only the sessions the owner named, or freeze the session IDs in a dated range the owner approved before
judging them. Transcripts hold other projects' business data; treat every line as private.

The owner's words grant the work, exactly as they do in the product:

- "audit", "check", "why did it do that" — inspect and report. Change nothing.
- "audit and record" — also write the receipt described under Report.
- "audit and fix" — also record the audit, implement and verify evidence-supported changes, and make an
  ordinary local commit when repository policy permits. Remote delivery still depends on the requested shared
  outcome. Own technical and architectural choices. Stop at a
  proposal only when evidence leaves a material product or rollout choice unresolved, or when the requested
  outcome does not grant a required protected action.

A public release needs an explicit owner grant. When granted, follow the repository's
[release instructions](../../../CONTRIBUTING.md#release) through merge, tag, and verification instead of
handing the steps back to the owner. Without that grant, a changed plugin is left as a reviewed release
candidate. A contributor-only change does not by itself justify moving the plugin version.

Approval is not the same as a new ADR. The changelog section and the receipt are the record a policy edit
gets; record proportionately, and amend the ADR that already owns the question rather than opening a
competing one. Write a new ADR only for a decision that is expensive to reverse, or that rejects an
alternative a future contributor would otherwise propose again.

## Find the sessions

`sessions.py` locates Claude Code project transcripts, slices an explicitly supplied Claude or flat
`codex exec --json` transcript, and mechanically classifies observable evidence. It does not discover Codex
desktop rollout storage and it does not make a causal or conformance ruling.

```sh
python .claude/skills/dogfood/sessions.py list --on 2026-08-27 # exact-day plus date-uncertain candidates
python .claude/skills/dogfood/sessions.py coverage       # discovered Claude sessions covered by receipts
python .claude/skills/dogfood/sessions.py digest <id>    # one session as reviewable evidence
python .claude/skills/dogfood/sessions.py grep <id> <re> # back into the raw bytes, bounded
```

Read digests, not whole transcripts: the largest is megabytes and the digest is reviewable. Use bounded
`grep` when the digest visibly reports truncated final text or an event remains disputed. `list` returns
marker-bearing Claude candidates. `--on` selects candidates with a marker on that exact local calendar day
and retains date-uncertain candidates whose undated or unreadable marker records prevent safe exclusion;
`--since` is a lower bound with the same fail-closed treatment. Neither filter uses chat creation time. A
path mention or quoted example is not proof of activation.
`list --all` also shows neutral exclusions. A `self-development` match can be legitimate source inspection;
check the correlated activation evidence before calling it an `AGENTS.md` violation.

Every `sessions.py` output is private root evidence, including text or JSON from `list`, `list --all`,
`coverage`, `digest`, and `grep`. Some of these expose project names or paths even when they do not show
transcript text. Never paste command output into a delegate brief. Restate only the facts manually sanitized
for that lane, without session IDs, project names, paths, owner text, commands, report text, customer data,
or credentials.

## Judge against the contract the run actually had

Use an exact package version or source tree only when the transcript or preserved setup identifies it. For a
released version, compare with `git show v<version>:plugins/skiphow/skills/skiphow/SKILL.md` and the same
reference path. An unversioned project copy or missing tag/cache leaves contract-body scoring `UNVERIFIED`;
never substitute HEAD. Read [the checklist](references/checklist.md) for what each observation proves.

Four observations constrain any ruling:

- **What terminal state is present?** The digest reports a static host sequence. It can identify a completed,
  failed, open, or unobserved sequence, and marks ambiguous lifecycle evidence or an incomplete readable
  transcript as unverified instead of forcing a state. An open sequence does not prove the session is currently
  running and does not by itself excuse a missing result.
- **What is the last observable activity?** A trailing unresolved tool call proves only that no matching
  terminal event appears later in the readable transcript; it does not prove why the run stopped.
- **Did the context compact?** Then "it forgot" is a live innocent explanation.
- **Did the rule that failed enter context?** `body_observed` means the complete tagged or cached reference
  text appeared in model-visible tool output. Matching decoded line values are weaker and may be generic; they
  do not establish that the body entered context. A structured host Read/Search/Write event says which
  structured action was observed. Shell command semantics are not inferred; complete artifact text in
  model-visible output can still be observed independently. Path evidence, missing output, and transcript
  absence do not prove that a body entered or stayed out of context.

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
contradictory, miscued by the only worked example, or not shown to have entered context. Then pass three
gates before the proposal exists.

- Grep `## Rejected alternatives` across `docs/decisions/`. If the project already rejected this, either drop
  it or carry new evidence that the rejection reason no longer holds.
- Grep `## Revalidation triggers`. A match means the project already asked for this receipt, and the ADR must
  be amended alongside the skill.
- Check the package boundary in [ADR 0015](../../../docs/decisions/0015-unconditional-invariants-live-in-the-root.md)
  and [ADR 0018](../../../docs/decisions/0018-autonomous-kernel-and-independent-task-skills.md). If a rule must
  hold on every request, it belongs in the root. A focused method may improve technique, but it must not carry
  authority or completion policy that disappears when the method is not read.

Prefer deleting a contradiction, then tightening a sentence, then moving it so it loads earlier. Adding is
last: the 1.1 shrink quietly dropped a rule that then governed nothing for six releases, so say what a deleted
sentence was doing.

A defect already fixed at HEAD is not a change. It is a receipt request against HEAD's verification status.

## Report

Report the result and evidence. Include rulings, findings, saved follow-ups, and limits when they exist. The
limits must name the blind spot: a finding a run noticed and silently dropped leaves no trace, so tag
conformance is an upper bound.

With a record granted, write `docs/research/<date>/field-audit-<date>.md` in the style of
`real-task-application-audit.md` — no project names, no issue titles, no customer data, no absolute paths —
and add its row to that directory's `README.md`. Include one line per session read. For a Claude session
discovered by `list`, use its first eight hexadecimal characters only when that prefix is unique in the
current discovery; otherwise use the full session ID. An explicitly supplied flat Codex transcript is not
rediscovered by `coverage`, so name it manually in the receipt and do not claim automatic census coverage:

```text
Audited `<unique 8-char prefix or full session ID>` · <records> records · plugin <version> · <one-line verdict>
```

Review the note manually for private identifiers, then run `python scripts/check.py`. Its personal-path scan is
a backstop for common home-directory forms, not a complete privacy guarantee.
