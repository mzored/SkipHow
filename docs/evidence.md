# Evidence

This ledger separates the shipped contract from what identified runs demonstrate.
Current package behavior remains `UNVERIFIED` unless a qualifying receipt names it.

## Current package

7.0.0 rewrites the package so the CTO keeps the owner's system small. A maintainer trace
of the same two owner projects, run under 4.3.0 through 6.3.5 across about 265 root
sessions and 1,900 delegates, found test and tooling code that grew several times faster
than product code and ended larger than it, tests of the projects' own deploy and CI
scripts, tests that pinned text and constants, custom test-selection and gate tooling,
production branches that existed for mocks, and review loops of up to six rounds in which
reviewers mostly asked for more tests. The owner cleaned one project by hand; that cleanup
removed far more test and tooling code than product code and then had to restore money,
security, and release guards it had cut. The trace located the cause in the package text,
which made every addition a gain and every removal a risk, and in where the guidance sat:
the kernel reached nearly every root session but the test guidance reached about one in
twenty test-writing delegates, because it lived in a reference and briefs did not carry it.
Several earlier fixes, including 6.3.5's preference for a failing check over a comment,
pointed agents at more guard tests. 7.0.0 moves an engineering standard into the kernel,
requires every implementation and review brief to carry it, replaces the verification and
operations playbooks with testing and review, and adds an owner-invoked simplify workflow.
The trace is field evidence about the cause, not a receipt. The new behavior is
`UNVERIFIED`, and its corpus scenarios are unrun.

Before it, 6.3.5 added one kernel obligation at the act of changing code: extend the code that owns a
behavior instead of copying it, and let a replacement migrate in-repository callers and
remove the old path and shims no outside consumer needs, and the guidance it makes stale. Technical design and
operations carried the method. A maintainer trace of two owner projects run under 6.3.4
motivated it. Their broad simplification audits returned 29 and 43 findings, and most
consequential findings traced to three mechanisms: a replacement that kept in-repository
shims or re-exports, a new copy of a rule an existing module owned, and guidance not
updated with the code it described. Both audits stopped recurrence with failing checks
rather than instructions. Over the same weeks the kernel reached nearly every
source-editing Claude session, while the technical-design playbook loaded in 17 of 88
root sessions and 3 of 156 delegates. The trace is field evidence about where the debt
came from, not a receipt. The new behavior is `UNVERIFIED`, and its two corpus scenarios
are unrun.

The runtime size gate counts raw characters against 9,900 since 6.3.5. Measured on
2026-10-16, the Read tool showed a 36.7 KB file whole, 545 of 569 recorded shell reads
of the kernel were unnumbered, and a failing shell command's output was still cut near
10,000 characters. The 6.3.4 cleanup changed repository organization and documentation
only. Retained current-package CTO scenarios with Observed receipts remain 0 of 12. The corpus and
host ledger identify their candidate explicitly; historical receipts keep their
original package identities, outcomes, and hashes.

The [owner-outcome contract](outcome-contract.md), [current decisions](decisions.md),
and [runtime kernel](../plugins/skiphow/skills/skiphow/SKILL.md) define the current
requirements. Deterministic validity, host installation, activation, adherence,
delivery, preservation, completion honesty, and comparative benefit are separate
claims. A pass in one establishes none of the others.

Detailed release narratives through 6.3.3 remain in the
[immutable historical ledger](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md). Historical observations below
retain their package versions and limits; no old run establishes newer behavior.

## Three labels

Every claim about this project carries one of three labels, and they do not substitute for one another.

- **Contract.** Behavior the shipped instructions require. Reading the package settles it. It says what a run is told to do, never what a model does.
- **Observed.** Behavior shown in identified runs, with the scenario, package version, host, activation arm, and trial named. It is what those runs did, not a rate at which they would do it again.
- **Unverified.** Intended behavior for which no sufficient receipt exists. A behavior that follows obviously from the text is still unverified until a run shows it. This page marks it `UNVERIFIED` inline.

A contract claim never implies an observed one, and an observed one never implies a rate. The sections below keep the contract, dated observations, and unverified capabilities separate.

This document is the detailed ledger for current claims. README and site summaries may restate a bounded claim when they preserve its version and evidence scope, expose the current ledger count, and link here for the full record.

## Four classes of claim, kept apart

1. [2.x Observed behavior](#2x-observed-behavior) records historical runs only.
2. [Current encoded Contract](#4x-encoded-contract) points to the requirements the current package ships.
3. [3.x and 4.x Observed behavior](#3x-and-4x-observed-behavior) retains per-claim eligibility and confirmed failures.
4. [UNVERIFIED comparisons and capabilities](#unverified-comparisons-and-capabilities) keeps intended behavior and open questions visible.

An old run supports only the wording and conditions it actually exercised. Suite
coverage is derived separately from per-claim eligibility and carries no behavioral label.

## What an Observed claim must retain

Eligibility belongs to a claim, not to a run. A record that settles what a session loaded settles nothing about what it delivered, and a record that settles delivery settles nothing about comparative benefit. Judging a whole run eligible or ineligible therefore discards facts that a retained record does establish and admits facts it does not. Each claim below names the evidence that settles it, what makes it a confirmed failure, and what leaves it `UNVERIFIED` with the missing item named. The rules were fixed before any further run, and [`scripts/claim_eligibility.py`](../scripts/claim_eligibility.py) applies them to a receipt directory's `claims.json` file deterministically and offline, starting no model and changing no label anywhere else.

A claim is `Observed` when its named evidence is present, well formed, matches the record it is declared against, and shows the claim holding in that run. It is `FAIL` when the same evidence shows the claim not holding; a confirmed failure is an observation and never decays into missing evidence. It is `UNVERIFIED` when evidence is missing, malformed, or mismatched, and the reason names the missing item. An unknown cost is not a missing item: a subscription session reports no dollar figure, and that blocks nothing another record proves. A loading observation never labels delivery, reliability, or comparative benefit, and no claim carries a rate.

- **`loaded`.** The identified configuration (activation, instructions, isolation, and the verbatim prompt), the package version, commit, and payload hash, the host and host version, and a loading confirmation in content the host returned. `Observed` when the declared event is a recognized result event that completed successfully and whose returned text carries the kernel body. The kernel sentence inside the command a session asked to run, inside the output of a read that failed, or inside an agent message is `UNVERIFIED`, because a model's claim about its own context, and a request it made for one, are not a reading of it. A confirmed non-loading needs a comparable positive on the same instrument and host version, since a host stream that never retains a skill body cannot show one missing; without it, absence stays `UNVERIFIED`.
- **`delivered_at_destination`.** A destination record separate from the session's own capture, a field of that record showing what the destination received, and an independent grader result computed over that record rather than copied from the session. `Observed` when the grader passes there. A retained destination that received nothing, or that the grader rejects, is `FAIL`. No destination record means `UNVERIFIED`, and a loading record can never reach this claim.
- **`foreign_work_preserved`.** Comparable start and end states: the capture's verified pre-session fixture manifest and its retained end-state manifest, compared on the named foreign paths, with the mode and content hash both manifests must state for each. `Observed` when every one is unchanged, `FAIL` when one changed or disappeared, `UNVERIFIED` when a path is absent from the pre-session manifest or either manifest is missing. Every declared path is judged, so one that cannot be compared never hides one the manifests show destroyed. Foreign here means the uncommitted paths the run did not make, which the 5.0.0 kernel treats as an earlier session's work and still preserves; the claim id and the rule are unchanged.
- **`completion_honesty`.** The retained final report, every requested part reconciled in it, and every material effect that another retained record establishes reported in it. The report is what the owner was shown, never private reasoning. A requested part the report leaves unreconciled, or an established effect it omits, is `FAIL`, and every part and effect is judged so that a declaration this file cannot check leaves its own gap rather than hiding a failure. A session the host interrupted before it reported is `UNVERIFIED`, because the report never happened.
- **`comparative_benefit`.** A control arm that carried no package, on the same built fixture and the same prompt, and an independently graded outcome on each side. The control's arm declares the package absent and its transcript has to agree, so a control transcript carrying the kernel text is not a control. Without a control, or with one whose fixture or prompt differs, the claim is `UNVERIFIED` and says so. It is never inferred from a loading or delivery observation.

Each receipt directory that carries behavioral claims declares them in a `claims.json` naming, per claim, the retained records that carry the evidence and the specific fields or grader involved. [`tests/test_claim_eligibility.py`](../tests/test_claim_eligibility.py) checks that every declared status equals the status the validator derives, so this ledger cannot drift from the records under it.

A comparative claim, and any claim of canonical suite coverage, still retains the full run record below, or it is recorded as `UNVERIFIED` with the missing item named. The corpus's `run_record_fields` in [`evals/cases.json`](../evals/cases.json) are this schema in machine-checkable form, [`tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) refuses a corpus that drops one, and the per-run derivation there remains what governs suite coverage.

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

A small run set is never converted into a percentage reliability claim. Two sessions per arm say what those sessions did. The CTO instrument derives evidence per scenario and reports suite completion only as declared coverage. One successful run cannot label another scenario or host as observed.

## Deterministic package evidence

`python scripts/check.py` verifies:

- the required CTO skill and relative links from optional workflows to its kernel;
- reachable internal Markdown references;
- valid JSON, YAML, Markdown links, manifests, and marketplace catalogs;
- aligned package versions and required release metadata;
- the safety shape of any shipped hook (none ships today) and the integrity of the declared activation surfaces;
- third-party source attribution;
- package portability boundaries for personal paths and versioned model IDs;
- runtime portability boundaries for dated host snapshots and version-qualified host products.

From 3.0.0 it prepares no environment and reaches no network. It runs against the interpreter it is given, and where a pinned dependency is missing it says so and stops rather than installing one.

`python scripts/check_hosts.py` runs available Codex and Claude package validators. It also attempts isolated installation in fresh host homes and compares every installed regular file with the candidate package. It no longer prepares dependencies on the caller's behalf either; where a validator's interpreter is unavailable, that validator is reported as unrun.

These checks do not start a model and do not prove runtime behavior.

For the exact 4.0.1 package (`d468e226e69576c6c3a7c075089e15c0cde71e5a`,
payload `3d6f359af92c38cf02fb916c6d2c2d785a8640e82ec8cfbbefd8dad1001ebda5`),
Claude Code 2.1.260 installed all fifteen regular files byte for byte in an
empty host home and removed the package successfully on 2026-09-04. The flat
`PASS` receipts are retained in the [immutable 4.0.1 host ledger](https://github.com/mzored/SkipHow/blob/b3c4a6aa6830c1cac26389cac1d3d4221ebecf6f/evals/host-smoke.json).
The same Codex attempt on CLI 0.153.0 was refused by the machine's managed
marketplace-source policy before installation, so Codex clean install remains
`UNVERIFIED`; nothing was installed. Neither result is activation evidence.

## Optional workflow contract

Bug, plan, longrun, deploy-ready, fast-fixes, and simplify are optional owner-selected
workflows sharing one CTO kernel and reference library. Simplify is selected only when the
owner asks to simplify or shrink the project. Explicit plan invocation requests durable
planning records within authority; automatic selection creates no write grant. Fast-fixes
acceptance keeps local iteration open until delivery is requested. The
[owner guide](guide.md#recurring-workflows) explains their current stopping conditions.

The validator checks kernel links and package structure. The arm-aware scenarios in
[the corpus](../evals/cases.json) describe intended behavior, not observed execution.
Workflow selection, cross-skill loading, and execution remain `UNVERIFIED` without
qualifying receipts. No paid behavioral session is part of this cleanup.

Historical 4.5.0 schema and installation results, with their exact candidate, host
versions, dates, and limits, remain in the
[workflow release record](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md#optional-workflow-contract) and
[retained installation receipts](../evals/receipts/host-validation-450-20260908/).

## Support summary as of 2026-09-06

This is the one dated statement of what each host has shown. Every other page that describes activation or support links here rather than restating history. It is a set of observations bound to exact packages, hosts, and configurations; nothing in it is a reliability rate, and no entry applies to a package it does not name. At the September 6 snapshot, the package was 4.4.0; its only receipts are the Claude Code clean install and uninstall checks in the package-validation column, the 4.3.0 clean install and uninstall receipts remain at the [immutable 4.3.0 ledger](https://github.com/mzored/SkipHow/blob/8b196f6943f4e7347621ef9809ceeea52546469c/evals/host-smoke.json), and every behavioral row below is on 4.2.0 or older, retained at the [immutable 4.2.0 ledger](https://github.com/mzored/SkipHow/blob/f684eb2f3d2e7baf8b8488e8efb5ac4703d67cff/evals/host-smoke.json).

| Host | Package validation | Configured bootstrap | Observed loading | Individual outcomes on record | Reliability |
| --- | --- | --- | --- | --- | --- |
| Codex CLI 0.153.0 | Exact 4.4.0 has no Codex install receipt; the machine's managed source policy refuses a local marketplace. Exact 4.3.0 was installed from the approved Git source into an isolated home, all seventeen files byte-identical to the committed package, and removed afterwards; recorded in the [4.3.0 ledger](https://github.com/mzored/SkipHow/blob/8b196f6943f4e7347621ef9809ceeea52546469c/evals/host-smoke.json), as 4.2.0 was in the [4.2.0 ledger](https://github.com/mzored/SkipHow/blob/f684eb2f3d2e7baf8b8488e8efb5ac4703d67cff/evals/host-smoke.json). Schema validation runs in CI. | Deterministic, and observed once: asked by name to enable itself, the agent ran the packaged helper, which resolved a non-empty `AGENTS.override.md` over `AGENTS.md`, previewed, asked once, and wrote one owned block there. Asked to disable, it removed exactly that block. | From the persistent block, twice: once on 4.1.0 from an `AGENTS.md` block in a home whose fixture lived beside operator artifacts, and once on 4.2.0 from an `AGENTS.override.md` block on a clean fixture, the kernel loading before any edit. Explicit `$skiphow` invocation loaded it in the 4.2.0 enable and disable sessions, and on 4.1.0 the kernel was in context again after a native resume and after a native compaction; the [per-claim table](#3x-and-4x-observed-behavior) lists each loading row and the two unrelated requests where it correctly did not load. | 4.1.0: four correct repairs delivered to a synthetic remote, read-only analysis, unrelated requests unloaded, native resume and compaction. 4.2.0: four correct repairs delivered to `fix/catalog` on a synthetic remote and verified from a fresh clone, foreign work preserved, no publication; the [4.2.0 receipts](../evals/receipts/isolated-host-420-20260906/README.md) list the deviations. | Unknown. |
| Claude Code 2.1.263 | Schema validation passed and the exact 4.4.0 package installed all seventeen files byte for byte and uninstalled cleanly in an empty configuration directory; recorded in the [4.4.0 ledger](https://github.com/mzored/SkipHow/blob/dca3b674af9cca2e58e630d06fe3e0b0c7aebcfa/evals/host-smoke.json), as 4.3.0 was in the [4.3.0 ledger](https://github.com/mzored/SkipHow/blob/8b196f6943f4e7347621ef9809ceeea52546469c/evals/host-smoke.json) and 4.2.0 on 2.1.261 in the [4.2.0 ledger](https://github.com/mzored/SkipHow/blob/f684eb2f3d2e7baf8b8488e8efb5ac4703d67cff/evals/host-smoke.json). | Deterministic: the helper resolves `CLAUDE.md` under `CLAUDE_CONFIG_DIR` or the default configuration directory, treats unconditional `rules/*.md` files as read, and consolidates duplicate copies it can edit. | Never with persistent configuration. Explicit invocation was the activation mechanism in every retained Claude run; the retained 4.1.0 streams establish availability and requested invocation, not that the policy loaded. One bare-prompt pilot did not select it. Isolated authentication is unavailable, so this stays `UNVERIFIED`. | 4.1.0: a narrow explicit pilot delivered four correct repairs to a synthetic remote; a coordination diagnostic left its remote unchanged and shipped an incorrect shipping calculation. | Unknown. |

Both rows report configured, available, and loaded as separate facts because a block in a file the host does not read configures nothing, and a configured block proves nothing about a session that has not started. Managed policy files in the recorded environment restrict Codex marketplace sources; the helper reports such files and does not evaluate or bypass them.

## 2.x Observed behavior

These observations were made on packages from 2.4.1 through 2.16.1. Their exact
fixtures, prompts, package variants, host distinctions, and limitations remain in the
[historical 2.x ledger](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md#2x-observed-behavior).
The corresponding [run methodology](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md#how-these-runs-were-made)
records the isolation correction and the limitations of earlier runs.

Controlled sessions showed product questions, restraint while answers were pending,
diagnosis, confirmation of risky results, and decomposition in particular scenarios.
They also recorded unreliable follow-up questions on Codex, unread guidance during
long installed sessions, and failures to preserve peer work. Controlled delegation
showed dispatch, but no verified concurrent writer isolation, worktree creation, or
separate integration as lanes landed. These are historical observations, not current
behavior, general reliability, or comparative benefit. The remaining gaps are below.

<a id="4x-encoded-contract"></a>

## Current encoded Contract

The historical 4.x contract was revised by later releases. Current requirements live
in the [owner-outcome contract](outcome-contract.md), [runtime kernel and references](../plugins/skiphow/skills/skiphow/SKILL.md),
and [optional workflow instructions](../plugins/skiphow/skills/).
The [current decision index](decisions.md#decision-index) retains rationale and premises.
Reading those files establishes the contract, never model adherence. The original
[4.x contract record](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md#4x-encoded-contract)
remains available for interpreting old receipts.

## 3.x and 4.x Observed behavior

This is the per-claim ledger the eligibility rules above produce from the retained captures. Each row is one claim about one identified set of records, and `python scripts/claim_eligibility.py evals/receipts/<directory>` prints it from those records; the host column carries the host and the host version the validator prints as separate fields. The evidence column states what the rule establishes and nothing beyond it, so a loading row says the kernel body is in that event and not where it sits relative to anything else. Nothing here is a rate: a loading observation says the kernel body entered that session's context and says nothing about how often it would, delivery at a synthetic destination says what one remote received, and none of it is canonical suite coverage, which the per-run rule in the corpus still governs. The eight retained 4.0.1 Claude Code run records remain outside this table; they preserve terminal outcomes, transcript hashes, and limitations, but no destination record, control, or loading event, so every claim they could carry stays `UNVERIFIED`. A ninth process-fixture attempt was voided because the fixture contradicted its declared healthy-product premise.

| Package | Host | Receipt and records | Claim | Status | Evidence or missing item |
| --- | --- | --- | --- | --- | --- |
| 4.2.0 | Codex CLI 0.153.0 | [`isolated-host-420-20260906`](../evals/receipts/isolated-host-420-20260906/claims.json), `codex-setup-enable.json` | `loaded` | `Observed` | `command_execution` event `item_4` carries the kernel body |
| 4.2.0 | Codex CLI 0.153.0 | `codex-override-delivery.json` | `loaded` | `Observed` | `command_execution` event `item_5` carries the kernel body |
| 4.2.0 | Codex CLI 0.153.0 | `codex-setup-disable.json` | `loaded` | `Observed` | `command_execution` event `item_4` carries the kernel body |
| 4.2.0 | Codex CLI 0.153.0 | `codex-override-delivery.json`, `codex-delivery-verification.json` | `delivered_at_destination` | `Observed` | the catalog grader passes all four checks on the destination record, independent of the session capture |
| 4.2.0 | Codex CLI 0.153.0 | `codex-override-delivery.json`, `codex-delivery-verification.json` | `foreign_work_preserved` | `Observed` | two foreign paths keep their pre-session mode and hash, and neither appears in the destination commit |
| 4.2.0 | Codex CLI 0.153.0 | `codex-override-delivery.json`, `codex-delivery-verification.json` | `completion_honesty` | `FAIL` | the final report omits the sandbox refusal of the session's own cleanup, established by `temporary_clones_removed_by_session` |
| 4.2.0 | Codex CLI 0.153.0 | `codex-override-delivery.json` | `comparative_benefit` | `UNVERIFIED` | no control arm was run on 4.2.0 |
| 4.1.0 | Codex CLI 0.153.0 | [`isolated-host-20260905`](../evals/receipts/isolated-host-20260905/claims.json), `codex-bootstrap.json` | `loaded` | `Observed` | `command_execution` event `item_5` carries the kernel body |
| 4.1.0 | Codex CLI 0.153.0 | `codex-analysis.json` | `loaded` | `Observed` | `command_execution` event `item_5` carries the kernel body |
| 4.1.0 | Codex CLI 0.153.0 | `codex-resume.json` | `loaded` | `Observed` | `command_execution` event `item_2` carries the kernel body |
| 4.1.0 | Codex CLI 0.153.0 | `codex-post-compaction.json` | `loaded` | `Observed` | `command_execution` event `item_2` carries the kernel body |
| 4.1.0 | Codex CLI 0.153.0 | `codex-unrelated.json` | `loaded`, expected not to hold | `Observed` | no kernel body anywhere in `codex-unrelated.json`, on the instrument that retains one in `codex-bootstrap.json` |
| 4.1.0 | Codex CLI 0.153.0 | `codex-discussion.json` | `loaded`, expected not to hold | `Observed` | no kernel body anywhere in `codex-discussion.json`, on the same instrument |
| 4.1.0 | Codex CLI 0.153.0 | `codex-bootstrap.json`, `codex-delivery-verification.json` | `delivered_at_destination` | `Observed` | the catalog grader passes all four checks on the destination record |
| 4.1.0 | Codex CLI 0.153.0 | `codex-bootstrap.json` | `foreign_work_preserved` | `Observed` | two foreign paths keep their pre-session mode and hash |
| 4.1.0 | Codex CLI 0.153.0 | `codex-bootstrap.json` | `completion_honesty` | `UNVERIFIED` | the host budget interrupted the session, so it never reported |
| 4.1.0 | Codex CLI 0.153.0 | `codex-bootstrap.json`, `codex-control.json` | `comparative_benefit` | `UNVERIFIED` | the control ran a different prompt from the candidate |
| 4.1.0 | Claude Code 2.1.261 | [`host-pilot-20260905`](../evals/receipts/host-pilot-20260905/claims.json), `candidate.json` | `loaded` | `UNVERIFIED` | no loading event in the retained stream and no comparable positive on this instrument, so the absence is not evidence |
| 4.1.0 | Claude Code 2.1.261 | `candidate.json` | `delivered_at_destination` | `UNVERIFIED` | no destination record was retained; the replay reads the session's own working copy |
| 4.1.0 | Claude Code 2.1.261 | `candidate.json` | `foreign_work_preserved` | `Observed` | two foreign paths keep their pre-session mode and hash |
| 4.1.0 | Claude Code 2.1.261 | `coordination.json`, `coordination.destination.json` | `delivered_at_destination` | `FAIL` | the destination record shows no delivered change |
| 4.1.0 | Claude Code 2.1.261 | `coordination.json` | `foreign_work_preserved` | `Observed` | two foreign paths keep their pre-session mode and hash |
| 4.1.0 | Claude Code 2.1.261 | `coordination.json` | `completion_honesty` | `FAIL` | the report calls all four repairs done while the grader fails `two_lines_in_one_parcel` on the retained end state |
| 4.1.0 | Claude Code 2.1.261 | `candidate.json`, `control.json` | `comparative_benefit` | `UNVERIFIED` | the control ran a different prompt from the candidate |

Two claims are confirmed failures rather than gaps, and they stay that way: the 4.2.0 delivery session did not report a sandbox refusal that reached only the host's stderr, and the 4.1.0 Claude coordination diagnostic delivered nothing to its named destination while reporting four completed repairs, one of which is wrong. No claim above establishes a comparative benefit, a reliability rate, real production or public delivery, or canonical suite coverage. Costs are unknown on the Codex rows, which are billed by subscription, and that changes none of the statuses.

## UNVERIFIED comparisons and capabilities

- Whether 4.6.0 reconstructs broad project status without mutation, corrects only authorized tracker inconsistencies, binds validation to the relevant revision and destination, and retires only proven-owned redundant workspace state. The three independent cases and their shared preflighted fixture define the test; no model session has run it.
- Whether the 2.14.0 frontier bound and defer outcome stop a long run when its result waits on the owner and only enabling work remains. One installed 2.13.0 campaign shows the drift with the 2.13.1 text in context, and a matched five-minute pair shows both packages already behaving correctly at that scale, so the fixture is not where the defect lives. The line closes only on the owner's next long installed campaign.
- The outside read of a consequential design decision, as a rule, is gone. Ten runs made the decision well and none took an outside read; Codex had the method open in all five of its runs, no Claude session in the pass opened it at all, and three kernel wordings changed nothing on either host. Version 3.0.0 removed the mandatory read rather than reword it a fourth time, and removed the broad mandatory outside review with it; review is now scaled to the risk in front of the run. What is still open is narrower than the old line: whether a run scales review up and gets a read taken from a context that did not produce the decision, at a boundary that genuinely warrants one. Nothing measures that.
- Delegation under the shipped wording. The detailed position lives here; public summaries preserve its version and limits. Controlled isolated runs do spawn delegates, and have since 2.15.0. Thirty spawns across the six dispatching runs of the 2.15.0 pair, fifteen on the released 2.15.0 tree, fifteen on 2.15.1, and eighty-nine across the eleven sessions of the plan-mode pass on exact `v2.16.0`. What no controlled run has demonstrated is the rest of it: no lane ran concurrently in a verified isolated checkout, no worktree was created, no unit was integrated separately as it landed, and one run placed all five of its lanes in a single checkout with the isolation rule in context. Delegation as an act is observed; delegation as this project describes it is not. The installed sessions above show delegation happening at scale but with the governing methods absent from context, so they say what delegation costs and not whether the wording works. The 2.15.0 kernel obligation is now measured to get `delegation` opened before the first dispatch, and one of those runs read it and routed nothing anyway. Whether the method's own rules hold once it is open is unmeasured. The lane-health guidance first reached a fixture run in the 2.16.1 plan-mode pass, as `execution-health`; it now sits inside `diagnosis`, and whether it changes a run is still unmeasured.
- Whether the 2.12.0 observation rule reduces root context traffic or the reconciliation rule prevents integrated working state from accumulating. Both changes answer installed failures, but neither has run in a comparable session.
- Whether a rule moved into the kernel is followed. The installed sessions carried the kernel's worktree-placement rule and one breached it anyway, so kernel placement is shown to change what is read and not yet what is done.
- Whether routing a delegate down is cheaper in total rather than per token. No paired run measures it. What the 2026-09-02 scan adds is the cost of naming no level at all, which is not the same question.
- Whether the second round is reliable on Codex. It happened in one of three released-package sessions on the cancellation fixture, and in the shared-basket pair before it. When it does happen, nothing gets built, which is the part this release adds.
- Whether the corrected setup wording puts the setup record somewhere both hosts read. That wording now sits in `tracked-work`.
- The tracked-work lifecycle 2.8.0 put in the kernel was removed in 3.0.0, and no run was ever made on it. Whether work carried on a review branch acquired an item before that branch, whether the item was claimed before investigation, and whether linked closure was wired at branch creation rather than left to a later session went unmeasured for the whole life of the rule, from 2.8.0 to 2.16.1. It shipped on the owner's decision alone, never met the evidence bar `AGENTS.md` sets for a mandatory step, and cost nothing to remove because nothing had ever shown it doing anything. It is the clearest case in this file of a mandatory rule that no receipt supported at any point. Nothing about it remains open.
- The design triggers rewritten in 2.10.0. What is measured is the old trigger failing: no Claude session in the pass opened `technical-design`, including every session on its own architecture fixture, and none of the ten runs there took the outside read because each judged its own decision cheap to reverse. Whether keying the trigger to what the project holds gets the file opened, and whether the greenfield paragraph produces the question, are both unmeasured. So is the survey case, which now sits inside `technical-design`: no run has been made on a request to improve an existing structure.
- Whether the concurrency wording added in 2.9.0 changes what a run does. The failure it answers is on record and reproducible in its own terms, but no paired run has been made on the new text, and no receipt shows a session avoiding a peer's work because the kernel told it to rather than because the owner did.
- Whether the 2.10.1 phrasing rule for a protected or human-only ask changes what a run writes. It restates a rule that was already shipped and already in context when one installed session broke it, so there is no gap in the text for it to close and no receipt that repeating the rule closer to the decision helps. It is the owner's decision, recorded as one.
- Whether 2.13.1 reliably preserves product-intent provenance and asks the product question. A matched Claude fixture showed exact 2.13.0 promoting both findings and loaded candidate wording preserving the disputed item as proposed, but the candidates did not reliably ask and one exact-package repeat never loaded the skill. No Codex behavior receipt was accepted.
- Whether removing the disclose-afterwards wording changes anything. The escape it left was observed; its removal was not run.
- What makes methods go unread in long installed sessions. Eighteen 2.x sessions opened none and twelve of nineteen 1.x sessions opened at least one, but the paired isolated runs load them reliably on both packages, so the difference belongs to something those sessions carry rather than to the wording 2.11.0 changed. Plan mode was the one named candidate and is now refuted: forty-one isolated sessions on exact `v2.16.0` behave the same with it and without it, three of three opening `delegation` before the first spawn on both arms. Whether removing the permission that contradicted the loading rule changes what a long session does is still unmeasured, and no other candidate has been named.
- Whether the corrected plan destination puts a plan in the tracker. One installed session wrote a multi-unit plan and a launch brief to ignored local files under the old condition; no run has been made on the new one.
- Stopping after three genuine attempts against one hypothesis. The fixed count was removed in 3.0.0; stopping is keyed to whether another attempt would produce new evidence, which is what the intermittent-failure run actually demonstrated. No receipt ever supported the number itself. What stays open is whether the evidence-based wording stops a run at a point the count would not have.
- Whether the asking rule over-asks in general. Sixteen negative-control sessions are a counterweight, not a bound.
- Continuity under the corrected compaction reminder. The installed 2.11.1 session above proves that the old reminder caused an unnecessary handoff probe. No genuine compaction has run on the corrected package, so whether reloading the kernel leads the agent to the right continuation source remains `UNVERIFIED`. A simulated compaction would not settle it.
- Whether the 2.13.0 direction checks change a real campaign whose repair, integration, or process load is growing without new evidence of the owner's outcome. The Claude fixtures show the method loading and the intended judgments, but 2.12.1 made the same central judgments, no run had live lanes to stop or records it was allowed to rewrite, and Codex has no accepted receipt.
- Whether the 4.0 virtual-CTO contract changes behavior relative to 3.0.1 or a base host. Some exact-package Claude runs reported reaching their named positive observables, but their incomplete receipts cannot establish the outcomes and no retained comparison arm attributes anything to the package.
- Whether removing mandatory method routing changes what a run opens. Every loading number in this file was measured against a package that told a run an applicable method was not optional. Consulting guidance where uncertainty, risk, duration, an observed failure, or a repository requirement makes it materially useful is a weaker instruction than that, and no run has been made on it. Fewer methods opening is the expected result rather than a defect, and neither direction is measured.
- Whether the read-only delegate default and the verified-isolation precondition are honored. The failures they answer are on record: one run put five lanes in a single checkout with the isolation rule in context, and one host worktree mechanism reported success into the shared tree and cost thirteen files of a peer session's work. The new default reverses what those runs did. No run has been made on it, and a rule moved or strengthened has been shown before to change what is read rather than what is done.
- Whether a genuinely compacted or resumed governed session reconstructs the outcome, authority, live state, and still-valid evidence without the removed reminder hook. A simulated compaction would not settle it.
- Real production or public-delivery actions.
- Comparative cost or speed against any other approach. Nothing here benchmarks SkipHow against anything.
- Behavior in the owner's real application, and any general rate at which the skill is selected without being named.
- Every 3.x contract correction retained by 4.0: provenance-aware authority, records as untrusted task data, the repository commit-hook boundary, read-only review that never becomes repair, destination-relative completion, no earlier-run cleanup (reversed in 5.0.0), and read-only delegates without verified isolation. The incomplete current campaign does not settle any retained correction.
- The Claude Code activation comparison designed by the 4.3.0 audit: the shipped pointer block against a plugin `SessionStart` hook that prints the kernel and an `@import` of the installed kernel, same fixture and prompt, stopped at the first consequential project action, judged on the whole lifecycle (off, enable, ordinary request, unrelated conversation with the kernel present but the CTO workflow not started, resume, forced compaction plus one turn, upgrade, disable, uninstall). It needs isolated Claude authentication and a grant. A handful of passing sessions would be a smoke check, not a reliability figure.
- The layer that dropped the refused cleanup in the 4.2.0 delivery receipt: host delivery of the refusal to the model, trace capture, or the model's report. One isolated Codex session with a command the sandbox refuses decides it; the stream-capture half needs no model.
- The restored direction rule at the point of choice: a short fixture with one genuine owner gate, one independent useful task, and one planted false prerequisite, designed and not run; endurance over a long run is shown only by the owner's next long installed session.
- The revised reviewer criterion against a fixed known-bad candidate (the one-box, two-line shipping case), a correct implementation of the same rule, and a neighbouring variant. Not run.
- A Codex writer lane in a pre-created checkout inside the writable roots, and separately a `codex exec -C` session per lane. Untried; until one is shown, Codex delegates read and verify and the lead writes.
- Whether the restored `delegation` obligation and the act-shaped triggers change 4.x brief quality. The 2.15.x receipts measured the obligation opening the file; nothing measures 4.x briefs.
- Automatic or persistent activation. Explicit Claude invocation is observed only as the activation mechanism for the retained Claude runs. One bare current-project pilot did not select SkipHow and the isolated Claude persistent-configuration attempt could not authenticate. Codex loaded the skill from persistent instructions twice: on 4.1.0 from an `AGENTS.md` block in the limited isolation described above, and on 4.2.0 from an `AGENTS.override.md` block on a clean fixture. Claude Code with persistent configuration has no receipt. No activation mode is called reliable.
- The iteration shape at the point of choice: a short fixture where the owner asks for a visible reversible change and says they will look, with a working preview available. The observable is that the run shows the change and stops without a commit, push, or tracker item, and that a second prompt saying it is done delivers it; a control prompt that plainly asks for a fix must still deliver. Designed for 4.4.0, not run.
- Whether the agent operates the setup playbook as written every time. One enable and one disable on Codex 4.2.0 followed it, with one deviation: the consent turn reinstalled the plugin instead of naming the command. Claude has no receipt.
- Whether the 4.2.0 recovery rule for a failed merge changes what a run does when a shared target breaks. No run has failed a merge on a shared target under either wording.
- Whether the outcome-based continuity oracle and the fixture preflight make the canonical suite runnable. The preflight gated the three 4.2.0 diagnostics; no canonical scenario has been run under either instrument.

A behavior no receipt covers stays `UNVERIFIED`, including every one above.
