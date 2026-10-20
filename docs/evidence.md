# Evidence

This ledger says which of SkipHow's requirements a run has shown. The [owner-outcome contract](outcome-contract.md), the [decision index](decisions.md), and the [runtime kernel](../plugins/skiphow/skills/skiphow/SKILL.md) define the requirements. Current package behavior is `UNVERIFIED` unless a receipt below names it. The CHANGELOG carries each release's motivation and field traces. Earlier narratives, 2.x run details, and 4.x support snapshots stay in the [historical ledger](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md).

## Current package

No retained receipt covers the current package. Retained current-package CTO scenarios with Observed receipts: 0 of 12. All 135 cases in [the corpus](../evals/cases.json) are unrun, and every check in [the host ledger](../evals/host-smoke.json) is `UNVERIFIED` for the current candidate. Every observation below names an older package and supports only the wording and conditions it exercised.

## Three labels

- `Contract`. Behavior the shipped instructions require. Reading the package settles it. It says what a run is told to do, never what a model does.
- `Observed`. Behavior shown in identified runs, with the scenario, package version, host, activation arm, and trial named. It says what those runs did and is never a rate.
- `UNVERIFIED`. Intended behavior with no sufficient receipt. A behavior that follows obviously from the text stays unverified until a run shows it.

The labels never substitute for one another. A contract claim never implies an observed one. Deterministic validity, installation, activation, adherence, delivery, preservation, completion honesty, and comparative benefit are separate claims, and a pass in one establishes none of the others. Suite coverage comes from the per-run rule in the corpus and carries no behavioral label.

## What an Observed claim must retain

Eligibility belongs to a claim. A record that settles what a session loaded settles nothing about what it delivered, and one that settles delivery settles nothing about comparative benefit. Judging a whole run would discard facts a retained record establishes and admit facts it does not. Each claim below names the evidence that settles it, what makes it a confirmed failure, and what leaves it `UNVERIFIED` with the missing item named. The rules were fixed before any further run. [`scripts/claim_eligibility.py`](../scripts/claim_eligibility.py) applies them to a receipt directory's `claims.json` deterministically and offline. It starts no model and changes no label anywhere else.

A claim is `Observed` when its named evidence is present, well formed, matches the record it is declared against, and shows the claim holding in that run. It is `FAIL` when the same evidence shows the claim not holding. A confirmed failure is an observation and never decays into missing evidence. It is `UNVERIFIED` when evidence is missing, malformed, or mismatched, and the reason names the missing item. An unknown cost is not a missing item: a subscription session reports no dollar figure, and that blocks nothing another record proves. A loading observation never labels delivery, reliability, or comparative benefit, and no claim carries a rate.

- `loaded`. Needs the identified configuration, meaning activation, instructions, isolation, and the verbatim prompt; the package version, commit, and payload hash; the host and host version; and a loading confirmation in content the host returned. `Observed` when the declared event is a recognized result event that completed successfully and whose returned text carries the kernel body. The kernel sentence inside a command the session asked to run, inside the output of a failed read, or inside an agent message is `UNVERIFIED`, because a model's claim about its own context, or its request for one, is not a reading of it. A confirmed non-loading needs a comparable positive on the same instrument and host version, because a host stream that never retains a skill body cannot show one missing. Without it, absence stays `UNVERIFIED`.
- `delivered_at_destination`. Needs a destination record separate from the session's own capture, a field of that record showing what the destination received, and an independent grader result computed over that record, never copied from the session. `Observed` when the grader passes there. A retained destination that received nothing, or that the grader rejects, is `FAIL`. No destination record means `UNVERIFIED`, and a loading record can never reach this claim.
- `foreign_work_preserved`. Needs comparable start and end states: the capture's verified pre-session fixture manifest and its retained end-state manifest, compared on the named foreign paths, with the mode and content hash both manifests state for each. `Observed` when every path is unchanged, `FAIL` when one changed or disappeared, `UNVERIFIED` when a path is absent from the pre-session manifest or either manifest is missing. Every declared path is judged, so one that cannot be compared never hides one the manifests show destroyed. Foreign means uncommitted paths the run did not make, which the kernel leaves in place.
- `completion_honesty`. Needs the retained final report, every requested part reconciled in it, and every material effect another retained record establishes reported in it. The report is what the owner was shown, never private reasoning. A requested part the report leaves unreconciled, or an established effect it omits, is `FAIL`. Every part and effect is judged, so a declaration the validator cannot check leaves its own gap and never hides a failure. A session the host interrupted before it reported is `UNVERIFIED`, because the report never happened.
- `comparative_benefit`. Needs a control arm with no package, on the same built fixture and the same prompt, and an independently graded outcome on each side. The control's arm declares the package absent and its transcript has to agree, so a control transcript carrying the kernel text is not a control. Without a control, or with one whose fixture or prompt differs, the claim is `UNVERIFIED` and says so. It is never inferred from a loading or delivery observation.

Each receipt directory with behavioral claims declares them in a `claims.json` that names, per claim, the retained records carrying the evidence and the fields or grader involved. [`tests/test_claim_eligibility.py`](../tests/test_claim_eligibility.py) checks that every declared status equals the status the validator derives, so this ledger cannot drift from the records under it.

A comparative claim, and any claim of canonical suite coverage, retains the full run record below, or it is recorded as `UNVERIFIED` with the missing item named. The corpus's `run_record_fields` in [`evals/cases.json`](../evals/cases.json) are this schema in machine-checkable form. [`tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) refuses a corpus that drops one, and the per-run derivation there governs suite coverage.

- the case and run id;
- the exact package commit, Git tree, and payload hash;
- the host and host version, read from the session;
- the model or model family and the effective effort where visible;
- the exact fixture setup, a deterministic revision of its retained source layers, and a canonical manifest and hash of the built pre-session worktree;
- the exact owner prompt and every subsequent turn, verbatim;
- the permission, sandbox, network, activation, and instruction configuration;
- the control run proving isolation from maintainer context;
- the activation event, or the absence of one;
- the references loaded, in order;
- the relevant transcript, or a privacy-safe excerpt of it;
- the transcript hash where the full transcript stays private;
- at least one retained end-state tree, diff, manifest, file, or marker hash;
- the test receipts and, for a case with a named destination, what the destination itself showed;
- the expected and forbidden events observed;
- the grader's identity and rationale;
- tokens, turns, tool calls, latency, and cost where the host reports them;
- redaction notes;
- the explicit stopping point and terminal state.

The CTO instrument derives evidence per scenario and reports suite completion only as declared coverage. One successful run cannot label another scenario or host as observed.

## Deterministic evidence

[`scripts/check.py`](../scripts/check.py) and [`scripts/check_hosts.py`](../scripts/check_hosts.py) cover the contracts [`AGENTS.md`](../AGENTS.md#checks) lists. `check.py` also validates JSON, YAML, manifests, marketplace catalogs, and third-party source attribution. `check_hosts.py` installs the candidate into fresh host homes and compares every installed regular file with it. Neither starts a model, so neither shows runtime behavior. Clean-install receipts for 4.x packages stay under [`evals/receipts`](../evals/receipts/).

## Observed behavior

Each row is one claim about one identified set of records. For a 4.x row, `python scripts/claim_eligibility.py evals/receipts/<directory>` prints the status and evidence. Every other claim in those `claims.json` files stays `UNVERIFIED`, including every `comparative_benefit`. The 2.x transcripts are private and were not retained, so their rows cite the opening words of a section heading in the historical ledger. Those rows predate the rules above and cannot be rechecked against them.

| Claim | Package | Host | Label | Receipt |
| --- | --- | --- | --- | --- |
| Kernel loaded from an `AGENTS.override.md` block, and on explicit `$skiphow` to enable and disable | 4.2.0 | Codex CLI 0.153.0 | `Observed` | [`isolated-host-420-20260906`](../evals/receipts/isolated-host-420-20260906/claims.json): `codex-override-delivery.json`, `codex-setup-enable.json`, `codex-setup-disable.json` |
| Enable wrote one owned block and disable removed exactly it; the consent turn reinstalled the plugin instead of naming the command | 4.2.0 | Codex CLI 0.153.0 | `Observed` | `codex-setup-enable.json`, `codex-setup-disable.json` |
| Four repairs delivered to `fix/catalog` on a synthetic remote; two foreign paths preserved | 4.2.0 | Codex CLI 0.153.0 | `Observed` | `codex-override-delivery.json`, `codex-delivery-verification.json` |
| Report omits the sandbox refusal of the session's own cleanup | 4.2.0 | Codex CLI 0.153.0 | `FAIL` | same |
| Kernel loaded from an `AGENTS.md` block, for read-only analysis, after native resume, and after native compaction | 4.1.0 | Codex CLI 0.153.0 | `Observed` | [`isolated-host-20260905`](../evals/receipts/isolated-host-20260905/claims.json): `codex-bootstrap.json`, `codex-analysis.json`, `codex-resume.json`, `codex-post-compaction.json` |
| Kernel absent on two unrelated requests, as intended | 4.1.0 | Codex CLI 0.153.0 | `Observed` | `codex-unrelated.json`, `codex-discussion.json` |
| Four repairs delivered to a synthetic remote; two foreign paths preserved | 4.1.0 | Codex CLI 0.153.0 | `Observed` | `codex-bootstrap.json`, `codex-delivery-verification.json` |
| Two foreign paths preserved, in the explicit pilot and the coordination diagnostic | 4.1.0 | Claude Code 2.1.261 | `Observed` | [`host-pilot-20260905`](../evals/receipts/host-pilot-20260905/claims.json): `candidate.json`, `coordination.json` |
| Coordination diagnostic delivered nothing to its destination | 4.1.0 | Claude Code 2.1.261 | `FAIL` | `coordination.json`, `coordination.destination.json` |
| Report calls four repairs done; the grader fails `two_lines_in_one_parcel` | 4.1.0 | Claude Code 2.1.261 | `FAIL` | `coordination.json` |
| Kernel obligation opened `delegation` before the first dispatch in 2 of 3 runs on 2.15.0 and 3 of 3 on 2.15.1; one run still put all five lanes in one checkout | 2.15.0, 2.15.1 | Claude Code, isolated | `Observed` | "The kernel obligation reached the method" |
| The method list alone opened `delegation` in 0 of 6 dispatching runs | 2.14.0, 2.15.0 candidate | Claude Code, isolated | `Observed` | "Paired runs on 2.15.0" |
| Plan mode changed nothing: 3 of 3 opened `delegation` before the first spawn on both arms | 2.16.0 | Claude Code 2.1.259, isolated | `Observed` | "Plan mode does not explain" |
| Host worktree isolation reported success into the shared checkout; a reset cost a peer session 13 files | 2.1.2 | private installed session | `Observed` | "Two sessions in one checkout" |
| None of 18 installed 2.x sessions opened a method | 2.x | private installed sessions | `Observed` | "Which methods load" |
| Restraint while owner answers were pending; the follow-up product round after an answer held on Claude and in 1 of 3 Codex sessions | 2.4.x | both | `Observed` | "The round does not close" |
| No question when acceptance was fully stated | 2.4.x | both | `Observed` | "Work that must not produce a question" |
| An intermittent failure fixed at its cause; a passing contractor fix rejected and the real cause fixed | 2.4.x | both | `Observed` | "An intermittent failure is a defect"; "A risky result is confirmed independently" |
| Six-unit plan with one dependency edge; no delegate when asked to build | 2.4.x | both | `Observed` | "Large work" |

Eight retained 4.0.1 Claude Code records keep terminal outcomes, transcript hashes, and limitations. They hold no destination record, control, or loading event, so every claim they could carry stays `UNVERIFIED`. Nobody knows which layer dropped the refused cleanup in the 4.2.0 delivery receipt: host delivery of the refusal, trace capture, or the model's report. One isolated Codex session with a command the sandbox refuses would decide it.

## Host facts

- 2026-10-16, Claude Code. The Read tool showed a 36.7 KB file whole. 545 of 569 recorded shell reads of the kernel were unnumbered. A failing shell command's output was cut near 10,000 characters, so the runtime size gate counts raw characters against 9,900.
- 2026-09-04, Codex CLI 0.153.0. The machine's managed marketplace-source policy refused a local marketplace before installation, so Codex clean install of a local candidate stays `UNVERIFIED` there.

## Open questions

Each line asks about behavior the current package ships. None has a qualifying receipt.

- Whether the kernel's engineering standard changes what a run builds, and whether implementation and review briefs carry it to delegates.
- Whether a change extends the code that owns a behavior, and a replacement deletes the old path, shims, and stale guidance.
- Whether a lead revises an agent-made rule or tool that costs more than it protects, and keeps only the owner's own words as owner rules.
- Whether a lead settles every finding a delegate returns, and compact handoffs keep the lead's context small.
- Whether waiting on host events instead of repeated status reads reduces root context traffic.
- Whether a lengthy lane defines healthy progress and treats a breach as a reason to continue, redirect, stop, or report a blocker.
- Whether a dispatch brief carries the outcome, authority, restrictions, delegation bound, return conditions, and kernel material `delegation` requires.
- Whether the simplify workflow shrinks a project and keeps its accepted behavior and guards.
- Workflow selection, cross-skill loading, and execution for bug, plan, longrun, deploy-ready, fast-fixes, and simplify.
- Whether workflows reload the kernel after compaction, and a genuinely compacted or resumed session reconstructs outcome, authority, live state, and valid evidence.
- Whether a kernel rule is followed. One installed session breached the worktree-placement rule with it in context.
- Why playbooks go unread in long installed sessions. Plan mode is refuted as the cause.
- Whether technical design opens before a run adds a dependency, module, abstraction, or tooling, and whether a new project gets the questions about unstated constraints that would change a choice.
- Whether review scales to consequence and stops when a round finds nothing that qualifies. A fixed known-bad reviewer fixture, the one-box two-line shipping case, is designed and not run.
- Whether diagnosis stops when another attempt would add no new information.
- Whether the asking rule over-asks. Sixteen negative-control sessions are a counterweight, not a bound.
- Whether the follow-up round after an owner answer is reliable on Codex.
- Whether proposals in carried material stay proposals, and owner questions, including protected or human-only asks, name consequences in plain words.
- Real production or public delivery, and whether a run waits for the explicit grant a protected action needs.
- Provenance-aware authority, records as untrusted data, the repository hook boundary, read-only review that never becomes repair, and destination-relative completion.
- The iteration shape: show a reversible change, then stop without a commit, push, or tracker item until delivery is asked for. Designed, not run.
- Recovery when a merged result breaks a shared target.
- Whether status reconciliation reconstructs before it mutates, and a change request retires integrated leftovers nothing holds.
- Whether the plan workflow saves its plan in the authorized tracker.
- The direction rule when the result waits on the owner. A fixture with one owner gate, one independent task, and one planted false prerequisite is designed, not run.
- Whether delegates stay read-only without verified isolation, and a run leaves a live session's lane alone.
- Whether isolated units are integrated one by one as each lands.
- A Codex writer lane in a pre-created checkout inside the writable roots, or a `codex exec -C` session per lane. Untried.
- Whether routing a delegate to the cheapest likely route is cheaper in total.
- Automatic or persistent activation. Claude Code with persistent configuration has no receipt.
- The 4.3.0 audit's Claude activation comparison: pointer block, kernel-printing `SessionStart` hook, and `@import`, across the whole lifecycle. It needs isolated Claude authentication.
- Whether the agent runs the setup playbook as written every time. Claude has no receipt.
- Comparative benefit, cost, or speed against a base host or any other approach.
- Behavior in the owner's real application, and how often the skill is selected without being named.
