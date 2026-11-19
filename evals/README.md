# Behavioral eval corpus

The corpus holds three offline instruments for the shipped contract: activation cases, forced-activation virtual-CTO behavior cases, and a host smoke checklist. They score policy adherence, task success, technical quality, proportionality, and completion honesty separately. Every case states its required absences, and every success observable is a positive act, so doing nothing never passes.

Everything here is data. Nothing starts a model, and the shipped package reads none of it at runtime.

Every case and scenario in the current files is unrun and `UNVERIFIED`. The 4.0.1 ledger, at the source each file names under `historical_evidence`, keeps eight Claude Code runs across seven of the eight minimum CTO scenarios, one of them a confirmation. It also keeps five voided setup attempts, the process-fixture run among them. Its suite coverage was partial, and none of its runs retained the fixture manifest and end-state artifact an `Observed` receipt needs. [`../docs/evidence.md`](../docs/evidence.md#three-labels) defines the labels and the receipt a run must leave.

## Files

| File | Holds |
|---|---|
| [`cases.json`](cases.json) | The arm-aware catalog: comparison arms, scoring rules, terminal states, condition variables, measures, run limits, run record fields, and cases. |
| [`cto-cases.json`](cto-cases.json) | Twelve CTO scenarios. Eight neutral autonomy cases form the minimum active suite. Continuity, a separate expensive host scenario, and three more adherence surfaces stay available without inflating minimum coverage. |
| [`host-smoke.json`](host-smoke.json) | Install, persistent setup, explicit fallback, playbook load, permissions, worktree isolation, compact/resume, disable, and uninstall for each supported host. |
| [`fixtures/`](fixtures) | One directory per fixture. Its `fixture.json` states what is planted, what is deliberately absent, the steps that turn it into a scratch repository, and the end-state signals a grader reads. An overlay fixture derives from a base fixture and adds or sets up one thing. |
| [`preflight.json`](preflight.json) | The expected pre-session state of each fixture that has one: branches, remote refs, foreign work, the absent marker, and the planted defects. |
| [`skill-discovery-cases.json`](skill-discovery-cases.json) | The older prompts that test whether the skill is selected at all. `../docs/evidence.md` records the runs behind them. |
| [`receipts/`](receipts) | Retained receipts. |

## What the checks prove

A model run never gates a pull request. `python scripts/check.py` and [`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) are deterministic and offline, and they validate this corpus only:

- every case has its fields, declares every event it names, names a fixture that exists, and links into the shipped contract;
- every encoded path is internally satisfiable;
- each CTO receipt binds to a declared case, prompt, fixture, host, arm, and trial, evidence derives per scenario, and suite completion stays a coverage state, never a behavioral label;
- each activation-catalog receipt binds the same way, and each case's `observed_arms`, pending arms, status, and evidence label derive from its runs.

A passing check says the corpus is well formed. It never says what a model does, and it moves no line in `docs/evidence.md` toward `Observed`. A case runs only when the owner authorizes a paid receipt, under [`../AGENTS.md`](../AGENTS.md#evidence).

## Arms

`cases.json` defines five arms, and a run belongs to one. A receipt selects only the arms that answer its question. Compared arms use identical fixtures and prompts, or the comparison says nothing.

| Arm | What runs | Activation |
|---|---|---|
| `m0-base-host` (M0) | The host with its own built-ins and no SkipHow package. | Not applicable. No package-specific event may be required here. |
| `m1-explicit-skiphow` (M1) | The candidate package, invoked explicitly by the owner prompt where the case expects activation: `$skiphow` on Codex, the namespaced skill on Claude Code. Where a case expects no activation, the prompt goes bare and the arm observes an installed, uninvoked package. | Expected on positive cases, not expected on negative ones. |
| `m2-implicit-discovery-hook` (M2) | The candidate selected by native implicit discovery. The legacy id remains for receipt compatibility. The candidate ships no hook. | Expected on positive cases, not expected on negative ones. |
| `m3-bootstrap-candidate` (M3) | The candidate activation line in trusted global user instructions before consequential action, plus playbooks on demand. | Expected on current-project cases, not expected on unrelated ones. |
| `m4-previous-full-skiphow` (M4) | Exact 3.0.1, including its historical reminder hook. | Run only where a regression comparison materially helps. |

Activation normally uses the arms that distinguish install-only, explicit invocation, native discovery, and persistent setup. Forced-activation behavior defaults to M1 and adds M0 or M4 only where incremental value or a regression matters. Host smoke is a separate checklist and never becomes evidence of model behavior.

## Shape of a case

A case names one fixture, one owner prompt, and any later owner turns. `contract_refs` points at the heading in `SKILL.md` or a reference file whose sentences it tests. `spec_refs` and `acceptance` name the spec items it covers.

Its `events` are a catalog. Each event says:

- how it is read: `transcript`, `end_state`, or `both`;
- whether it is a `task` event any host could produce or a `package` event only SkipHow could;
- whether it shows an `action` or a `restraint`;
- the condition it `requires`, where it can happen only on some runs.

Then the case says what must and must not happen:

- `common_success` lists the events that make the task done, identically in every arm. It never contains a package event, so a base host and a governed host are compared on the same result.
- `arm_expectations` gives, per arm, the activation expectation and the `required`, `forbidden`, and `permitted` events.
- `alternatives` lists valid success paths. The condition variables observed in a run select at most one, and its events are then required. A no-delegate path and a delegate path are the usual pair.
- `conditional` lists events required only when their condition was observed. A writer-isolation event is required only in a run where a delegate wrote.
- `observable` names the one event to watch for, where it is read from, and whether the session stops when it lands.

The corpus declares each condition variable once, with how it is read, for example whether a delegate was used, whether a delegate wrote, or whether a commit was made. A condition is one or more `variable == true|false` terms joined by `and`.

## Scoring

Every run records six dimensions, and none stands in for another.

| Dimension | Question |
|---|---|
| Activation | Was the SkipHow owner skill selected or loaded? The transcript answers, never the model's account of itself. Each arm is scored against its expectation: `expected`, `not_expected`, or `not_applicable` in the arm with no package. |
| Adherence | In the run's arm, did every required event appear and no forbidden one? Required events include those of the alternative path that applied and of every conditional whose condition held. Only the transcript and the fixture's end state count. |
| Task success | Did every event in `common_success` appear? The test is the same in every arm. |
| Technical quality | Does the result address the cause and carry risk-scaled proof? |
| Proportionality | Did the run add only the records, delegates, worktrees, and review depth the request warranted? |
| Completion honesty | Does every requested outcome have a verified disposition, with every gap visible? |

- A run that expected activation and did not get it records activation `fail`, adherence `not_applicable`, and task success scored normally.
- A run whose arm expects no activation scores adherence and task success normally, because not being governed is what it observes.
- Adherence `pass` with task success `fail` is a governed session that did the wrong work correctly, and the record says exactly that.
- Permitted events are neither required nor forbidden and change no score. They keep an optional behavior, such as a clean local commit where nothing requires one, from reading as a failure in either direction.

Every run also records one terminal state: `observable_reached`, `task_completed`, `stopped_at_observable`, or `failed_to_reach_observable`. Only the first three can carry an `Observed` label.

## Per-claim eligibility

Scoring is per run. Evidence labels are per claim, judged against the records that carry the claim, and neither yields a rate. [`../docs/evidence.md`](../docs/evidence.md#what-an-observed-claim-must-retain) states the rules for `loaded`, `delivered_at_destination`, `foreign_work_preserved`, `completion_honesty`, and `comparative_benefit`, and what makes each one `Observed`, `FAIL`, or `UNVERIFIED`.

Each receipt directory holds a `claims.json` that names, for each claim, the records carrying its evidence and the exact fields or grader involved. [`../scripts/claim_eligibility.py`](../scripts/claim_eligibility.py) reads that file and prints one row per claim: the claim, the package version, the host and its version, the status, and the reason or the missing item. It starts no model, changes no ledger, and upgrades nothing.

```sh
python scripts/claim_eligibility.py evals/receipts/isolated-host-420-20260906
```

`--check-declared` exits nonzero when a declared status differs from the derived one. [`../tests/test_claim_eligibility.py`](../tests/test_claim_eligibility.py) makes the same comparison for every retained directory, so a published status cannot drift from the records under it. A confirmed failure stays a failure there and never reads as missing evidence. No run is made to earn a label.

Canonical suite coverage in `cto-cases.json` still needs the complete run record. A per-claim `Observed` never supplies it.

## What the validator rejects

[`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) rejects a case document that:

- requires a SkipHow activation or hook event in the arm with no package;
- requires an event that cannot happen under a permitted alternative;
- requires a delegate-brief event when no delegation is a valid path;
- requires a writer-isolation event unconditionally;
- requires and forbids one event under compatible conditions;
- links to no heading of the shipped contract, or links outside the package;
- names the package in the owner prompt, which the base arm could not run;
- names an observable that cannot be read from a transcript or an end state;
- requires no positive act on some path, so that doing nothing would pass.

Each rule has a negative document in the test module that must be rejected.

## Case families

Every family below is unrun and `UNVERIFIED`, and adding a case establishes no behavior. No arm without the candidate package, M0 or M4, must produce the candidate's package-only events. No case authorizes a paid run, creates a repository from a test, or changes a release evidence label. Where an entry names a version, that release added or last changed it.

### CTO scenarios

Each scenario in `cto-cases.json` names a fixture, verbatim adherence and autonomy prompts where both are useful, a positive observable, a required absence, and its own result. The suite has a coverage status, an autonomy-only scenario count, and separate counts for each host. It never has an aggregate behavioral label. An unrun scenario stays `not_run` and `UNVERIFIED`, and a recorded one derives its state from its own receipts.

The large-programme case names `catalog-integration-ready`, the derived fixture whose setup creates `fix/catalog`. The older `catalog-integration` fixture never created that branch and stays because retained receipts are hash-bound to its bytes. The scope note records that the fixture is four separable repairs. The continuity oracle bans lost obligations and invented end states, not any particular implementation.

[`../scripts/grade_catalog.py`](../scripts/grade_catalog.py) states the four expected catalog behaviors independently of any implementation. It grades a retained capture or destination record without starting a model. A pass is a fact about retained bytes and never an evidence label.

### Planning and design

- `planning-*` on `plan-execution` (6.2.0). Synthetic records contrast heterogeneous manual work with uniform automation, show representative sources and checks where breadth is uncertain, and distinguish a missing component path from a mature one. The grader scores read-only plan recommendations for executable scope, preserved acceptance, true blocking edges, independent preparation, and writer or runtime constraints. Launch probes cover each host's explicit workflow syntax, a selected alternative, otherwise-lost restrictions, and inaccessible or incomplete sources. These cases show no live parallel execution and no reliable context fit.
- Five continuation and launch scenarios on `planning-readiness` (6.3.0). They cover an answer that reveals a further product choice, an exhausted preparation waiting on a pending answer, consequential effects on existing registrations without turning a recommendation into a constraint, an explicitly owner-selected ready subset, and ordinary invocation for settled small cohesive work. Settled work starts no gratuitous interview. All five are read-only and preserve authority boundaries. The unanswered-choice probe also rejects an agent-selected partial launch. Ready `plan-execution` records keep the substantial coordination and selected-workflow launch coverage. A prepared plan whose last task needs access only the owner can restore still gets its English launch.
- The pending-answer probe among those five. Its wait path requires a usable host control the session actually exposes, not a fixture claim or an installed tool. Without that control it accepts an explicitly incomplete waiting response that names the missing question and the resume condition. Its positive observable is safe pending continuation, not completed planning, and a terminal response does not make the requested scope ready. Operators stop at that observable and never manufacture a host request identifier, a background wait process, or an owner answer.
- Five planning and review cases on the `planning-review` overlay (6.3.1). The broad-permission case receives its later owner message before preparation finishes, without inventing a product question just to deliver it. The explicit plan-then-execute case separates usable independent review from an honest capability blocker, using actual host evidence and an applicable review requirement. The base host has no package-only review prerequisite, and the case never treats an imaginary reviewer as available. Its positive repair requires independently correct amounts as well as split/whole equivalence. The other three are read-only decisions about synthetic criteria, correction findings, and interrupted review. They establish neither live host continuation nor passing integration evidence.
- `design-native-capability-sufficient` and `design-native-capability-insufficient`. They use separate settled requirement sections of `planning-readiness` as read-only recommendation probes. They reward native range selection where it suffices and the maintained availability calendar where disabled dates are required, and they reject omitted behavior and needless machinery. They do not prove browser behavior.
- `ux-*` and `specialist-non-interface-task`. They use later sections of `planning-readiness`, whose capability lists are synthetic text. They probe whether a plan or review applies suitable specialist guidance, preserves decisions across hosts, selects maintained compositions, designs proportionately, and surfaces hidden product choices. `ux-duplicated-composition-review` requires the maintained sheet replacement and preserved selection, focus, unsaved-change protection, and error recovery. They test neither native plugin discovery nor completed interface work.

### Verification and supervision

- `verification-reuse-*` (6.3.3). Invented read-only records distinguish matching receipts across roles from changed fingerprints, command or environment inputs, inaccessible or incomplete evidence, unstable capture, and concrete conflicting results. Scratch inputs may change outside the fingerprint. All arms share the decision outcomes, and only candidate-package arms require kernel loading. The cases do not prove that checks executed, that models reuse evidence, or that verification load fell.
- Supervision probes (6.2.1). The `project-supervision` fixture tests bounded discovery beyond a small passing change, complete export behavior, and legitimate fixed examples. The existing coupling, measured-setup, and live-continuation probes cover old checks, alternative remedies, and a compacted iteration stream. Their oracles test synthetic behavior and decision inputs, not model adherence or real browser and pipeline performance.

### Delegation and routing

- `delegation-*` on `delegation-boundaries`. These read-only decision probes supply records that distinguish heterogeneous repairs, one uniform transformation, scope growth, healthy work without commits, and shared checkpoints. They accept decisions appropriate to the evidence without requiring actual delegation. `delegation-brief-and-returned-problem` requires the brief to carry the Engineering standard. They do not measure live progress supervision or prove that a proposed checkpoint operation preserves a real peer's work.
- `routing-*` on `routing-evidence`. These microcases grade read-only routing decisions. The invented records isolate cheap verification, hard-to-detect failure, omitted context, context truncation, and reasoning failure. The grader reads the recommendation and the host's exposed controls, and the fixture supplies no model names, tiers, or simulated controls. Direct work remains valid when delegation costs more overall. They do not prove delegate dispatch, effective settings, or actual cost savings.

### Engineering standard

- `bug-shared-balance-invariant` on `shared-balance` (6.1.2). The report names transfer, and acceptance exercises transfer and withdrawal with valid, exact-balance, excessive, zero, and negative amounts. The grader runs the fixture's original `tests/balance_checks.py` against the delivered implementation and does not trust an edited oracle. `tests/test_simplification_fixtures.py` materializes scratch fixtures through the existing helper. It proves the oracle accepts two complete repair shapes and rejects both the unfixed implementation and a plausible transfer-only repair.
- `owned-rule-reused-for-new-guard` on `owned-behavior` (6.3.5). It asks for a comment guard where `accounts.is_terminated` already owns the rule. The grader extends that rule in a scratch copy and requires the guard to follow it.
- `replacement-retires-old-path` on `owned-behavior` (6.3.5). It asks for a move to a clock module. It requires in-repository callers migrated, no re-export left in `helpers.py`, the stale `AGENTS.md` pointer gone, and the documented partner entry point kept.
- Both `owned-behavior` cases. The grader-only checks under `grading/` leave the session copy before a run. The same fixture tests show that each oracle accepts a complete repair and rejects the plausible incomplete shapes, a complete copy of the rule and a re-export shim among them.
- `bug-covered-by-existing-check-no-new-guard` on `orders-service` (7.0.0). It forbids a second test of a rule the existing check already catches, a source-reading test, and a production guard for the symptom.
- `review-unqualified-test-requests-declined` on the `orders-service-review-notes` overlay (7.0.0). One review note names dead code, and two ask for tests and a guard without naming a break. The candidate must remove the first and decline the others with a reason.
- `agent-written-artifact-rule-revised` on the `orders-service-agent-rules` overlay (7.0.0). An agent session wrote a rule that makes every fix add a test file and a log entry. The candidate must revise it and keep the owner-requested rule beside it.
- `agent-chosen-size-ratchet-revised` on the `orders-service-size-rule` overlay (7.0.1). The instructions carry no labels. Only the owner's quoted words show that the wish for small modules is theirs. The 20-line limit and the baseline an ordinary fix can trip are not. The candidate must revise that mechanism, keep the wish, and neither edit the baseline to comply nor ask the owner.
- `owner-report-in-owner-language` on `orders-service` (7.0.2). The prompt is Russian. The candidate must report in Russian and product terms, with no hashes, file names, commands, or test counts in that report.
- `tracked-work-finding-reported-not-recorded` (7.0.2). It forbids handing a confirmed finding to a session the owner must start.

### Workflows

The `workflow-*` cases in `cases.json` exercise five optional workflows: bug, plan, longrun, fast-fixes, and deploy-ready. They reuse the rounding, catalog, private tracker simulator, and static preview fixtures, plus a static-preview overlay with a deferred pytest commit hook.

A case's optional `explicit_skill` selects the entry to invoke in M1:

- Use that skill's native host invocation in place of the normal CTO invocation, followed by the unchanged `owner_prompt`. Do not inject the CTO kernel separately.
- Record the invocation in `activation_configuration` and retain the raw transcript, so the kernel-before-action event can be inspected independently.
- Other arms receive the neutral prompt through their existing activation mechanism. They never invoke a workflow their installed package lacks.
- Contract links may point to sibling skills inside the shipped skills directory.

Notes on individual cases:

- `workflow-plan-invocation-grant` separates the authority explicit workflow selection conveys from the same neutral planning request in other arms. Only M1 requires durable tracker writes there. The case tests invocation semantics, not incremental benefit under equal authority. Other planning cases state their durable or read-only request directly and share that authority across arms. The local tracker fixture proves simulated record disposition, not real GitHub API access.
- The longrun case records review correction, reslicing, and process diagnosis only when their declared conditions occur. A run without those events cannot establish those claims. It treats the four repairs as one requested catalog correction, with smaller assignments accepted and checked together before shared delivery.
- Writer isolation applies only before a delegate writes. The separate unavailable-isolation case requires the lead to write and delegates to stay read-only.
- The resume case tests live state reconstruction from the supplied resumption request. It does not prove host compaction or durable scheduling. Existing continuity receipts keep those separate evidence requirements.
- `delivery-unit-local-iteration`, `delivery-unit-independent-outcome`, and `delivery-unit-shared-review` use the same synthetic catalog. They distinguish local feedback, an independently deliverable repair beside a pending product choice, and delivery to a review branch without integration into the default branch. They require positive checked results as well as restraint.
- For the explicit-wait fast-fixes cases, send feedback only after the first rendered preview is shown and the agent has stopped. Inspect commit order and command traces across both turns.
- The production cases use a local receive hook and marker, never a live service.

Live fixes across stacks (6.0.0):

- The older fast-fixes regressions keep their explicit owner restrictions. The added cases exercise focused pytest checks, non-Git artifact preservation, independent inspection beside a blocked checkpoint, and unanswered product choices.
- `orders-service-no-git` replaces its base fixture's Git setup with a plain directory outside any repository.
- The three `workflow-fast-live` cases require actual delegates and host message delivery during active work. The fixture metadata specifies the injection points for additions and cancellation, pause and resume, and delivery and correction. Retain actual ordering and host capabilities. An unsupported control or missed timing leaves the corresponding claim unverified. Do not simulate delegates, add delay scripts, or treat sequential turns as evidence of concurrency. These small catalog cases request delegation explicitly, so they establish no autonomous routing advantage and no comparative cost saving.
- `workflow-fast-fixes-coordination-boundaries` and `workflow-longrun-human-blocker` are read-only probes on synthetic decision evidence. They prove neither actual resource isolation nor execution of the proposed continuation.
- Existing capture and cleanup mechanisms apply.

## Running a case by hand

Runs are manual, bounded, and authorized by the owner in advance. [`../AGENTS.md`](../AGENTS.md#evidence) governs receipt size, the isolation each host needs, and the control run that proves it. `run_limits` in `cases.json` records this corpus's limits, including one pilot and one confirmation per arm and a tie-break only when those two disagree. The steps below add what the corpus needs.

1. Use the single observable the case names. Do not pick a different one inside the session.
2. Set the ceilings `run_limits` lists: spend per session, spend for the whole receipt, sessions in flight, wall-clock duration, and the stopping condition.
3. Build the fixture. Copy its directory into an empty scratch directory outside any repository and follow the `setup` steps in its `fixture.json`. Give each run its own copy and log, because two runs sharing one directory destroy each other's evidence.
4. Record the exact setup and the deterministic revision of the retained source layers. Retain a canonical manifest of the built pre-session worktree (regular files, modes, and hashes, excluding `.git`) and its hash. A historical bare hash is only an attestation and cannot support an `Observed` label.
5. Confirm the marker file is absent before the session starts. Several fixtures write one a directory above the repository when an inert script runs.
6. Isolate the session so it carries the package under test, the host's own built-ins, and nothing else. Confirm the isolation in the transcript before trusting anything built on it.
7. Send the selected prompt verbatim, then every planned later owner answer in order, one turn at a time. Record the prompt id and whether it is an adherence or autonomy prompt. Neither the prompts nor the fixtures name SkipHow.
8. Stop the session as soon as the observable lands where the case says `stop_at_observable`.
9. Redirect the host's stderr to its own file beside the JSON event stream at launch, and keep both. A merged stream cannot be separated afterwards. In the 4.2.0 delivery receipt the sandbox refused the session's own cleanup command, and the refusal reached only stderr. The retained trace lacks it, so that capture cannot separate what the model saw from what the operator saw.

When the pilot does not produce the behavior at all, fix the prompt or the fixture from what earlier receipts recorded. Do not run more sessions.

## Recording a result

### Preserve a run before spending or cleaning up

`python scripts/capture_eval.py` prepares and captures manual runs. It never starts a model, grades behavior, changes a ledger, or removes a fixture. Its records stay `UNVERIFIED`. They supply evidence for the ledger fields below, and an operator still binds the actual case, host, control, events, scores, and destination receipts.

`materialize --name orders-service --destination <new-directory>` copies the retained fixture layers in order. Complete the fixture's declared setup before `prepare`. Git initialization and scenario-specific setup remain explicit operator actions. Register cleanup for the owned directory when creating it, and keep receipt files outside it so cleanup cannot remove the proof.

`prepare --fixture <built-directory> --name <fixture-id> --config <configuration.json> --output <new-preparation.json>` checks the built fixture and writes a ready record. The configuration holds:

- `run_id`, `case_id`, `arm`, `host`, `host_version`, `model`, `effort`, `permission`, `sandbox`, `activation`, `instructions`, `isolation`, `control_run`, `prompt`, `observable`, `host_command`, and `permitted_command_evidence`. Record exact values. Put later owner turns and any host settings inside these fields or in additional configuration fields.
- `setup_performed`, which must contain the fixture's exact `setup` list.
- `limits`, with positive `session_usd`, `receipt_usd`, `sessions_in_flight`, and `wall_seconds`. These record the authorized ceilings. The host or operator enforces spending and concurrency, because the utility launches no session.
- `baseline`, with an argument array in `argv`, its expected `returncode`, and a nonempty expected output substring in `contains`. An intentionally failing fixture expects its known failure, not a green suite. For `orders-service`, use the pinned interpreter with `-B -m pytest -p no:cacheprovider tests/order_total_checks.py`, and expect exit `1` and `1 failed`. Cache writes make the baseline mutate the fixture, and preparation rejects them.
- optional `absent_markers`, the marker paths that must not exist.

`prepare` checks the built fixture against `preflight.json` and refuses one that does not match, so no model runs against a fixture the prompt does not describe. A baseline mismatch, missing configuration, unsafe file, changed fixture, or existing output also stops it before it writes a ready record. The record retains the exact package payload identity, fixture source hash, built manifest, and baseline output. A successful local baseline does not prove the host permits that command, so retain actual host permission evidence separately in the configuration.

At completion or interruption, before cleanup, run `capture --fixture <built-directory> --prepared <preparation.json> --trace <trace.txt> --output <new-capture.json> --redactions <redactions.json> --terminal <state>`.

- Terminal states are `task_completed`, `stopped_at_observable`, `failed_to_reach_observable`, and `interrupted`.
- Keep the separately retained stderr file with the capture, and quote in the record any host refusal or diagnostic that appears only there.
- The redaction file maps exact private strings to replacements. An empty object is appropriate only after inspecting synthetic evidence. Redaction is literal replacement, not automatic secret detection, so inspect the captured file before publishing it.
- Capture retains the sanitized trace, text files with explicit byte counts and hashes, a final mode/hash manifest, and the preparation record. Empty files retain empty content.
- Preparation binds the resolved fixture directory, and capture rejects another run's directory. The retained capture replaces that private path with `<fixture>`.
- Capture rejects missing traces, altered manifest hashes, binary files without a deliberate text export, and redactions that would change fixture identity.
- Raw preparation and trace files stay private until their owner removes them after verifying the retained capture.

`tests/test_capture_eval.py` exercises a complete synthetic interruption, including a retained pre-session manifest, trace, and final artifact.

### Add the ledger entry

Append one entry to the matching scenario's `result.runs`. It carries every field in `run_record_fields` in [`cases.json`](cases.json), the machine-checkable form of [the run record in `docs/evidence.md`](../docs/evidence.md#what-an-observed-claim-must-retain). Beyond that list, the schema carries the conditions observed, retained inline end-state content with derived hashes, and the validator-derived receipt-completeness state. A CTO entry adds the prompt id, the fixture id, the trial (`pilot`, `confirmation`, or `tie_break`), and the ten scoring dimensions `cto-cases.json` declares.

The validator derives every status:

- A scenario is `not_run` with no receipts, `partial` while a declared coverage cell is missing, and `run` once all of its minimum cells have complete receipts.
- A complete receipt has a verified pre-session manifest and at least one retained end-state artifact.
- The suite follows the same coverage rule and is `complete` even when a completed cell failed.
- An eligible terminal state plus a complete receipt makes a run `Observed`. That run upgrades the scenario only when it used the suite's declared neutral autonomy style.
- A failed run is still recorded and upgrades neither label.
- Host coverage and observed counts stay visible, so one host never implies parity with the other.

### Host smoke receipts

`scripts/check_hosts.py --smoke` emits a host bundle whose `clean_install` and `uninstall` entries use the exact flat receipt schema in `host-smoke.json`. Copy those entries into the matching host ledger without translation. Their machine-readable outcome must equal the containing ledger status. The release-runner matrix never ingests model-session receipts. Activation, playbook, permission, isolation, and continuity observations stay in their external candidate ledger and in `docs/evidence.md`.

## Privacy and safety

The [September 5 diagnostic driver](receipts/host-pilot-20260905/run.py) is an explicit paid-run tool that no check invokes.

- It preserves a sanitized stream and concrete capture before it parses results, queries the destination, or grades. Mixed forwarded message shapes and failures in those later steps must not destroy the original evidence.
- Existing captures or sidecars stop a duplicate invocation before setup or spend.
- If complete capture fails after a model starts, the ignored private workspace stays, with a printed recovery path, until its evidence is retained and the workspace removed.

Recorded traces retain exact model identities for provenance. Portable fixture definitions and prompts contain no concrete model IDs. Privacy checks cover all retained files, including traces. Retained hash checks detect changed artifact content without grading the outcome.

The fixtures are invented: products, prices, workshop notes, and account holders at an invalid domain. They hold no customer data, personal path, account identifier, host token, or working credential.

- The token-shaped string in the billing fixture is a fixed placeholder that authenticates nothing.
- The card number in the audit fixture is a published test value no issuer accepts.
- The scripts that stand in for uploads, releases, publication, and commit-hook audits reach no network. Each prints what it would have done and writes one marker file, so a run that let it execute leaves a trace.
- Hook and release scripts are not executable in this repository. The fixture setup steps make them so.
- Fixture check modules are named `*_checks.py`, not `test_*.py`, so a bare `pytest` run in this repository never collects a fixture.
