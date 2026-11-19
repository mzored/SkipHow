# Behavioral eval corpus

The corpus holds three offline instruments for the shipped contract: activation cases, forced-activation virtual-CTO behavior cases, and a host smoke checklist. Every case states its required absences, and every success observable is a positive act.

Everything here is data. Nothing starts a model, and the shipped package never reads it.

Every case and scenario in the current files is unrun and `UNVERIFIED`. The 4.0.1 ledger, at the source each file names under `historical_evidence`, keeps eight Claude Code runs across seven of the eight minimum CTO scenarios, and five voided setup attempts. None of its runs retained the fixture manifest and end-state artifact an `Observed` receipt needs. [`../docs/evidence.md`](../docs/evidence.md#three-labels) defines the labels and the receipt a run must leave.

## Files

| File | Holds |
|---|---|
| [`cases.json`](cases.json) | The arm-aware catalog: arms, scoring, terminal states, conditions, run limits, run record fields, and cases. |
| [`cto-cases.json`](cto-cases.json) | Twelve CTO scenarios. Eight neutral autonomy cases form the minimum suite. |
| [`host-smoke.json`](host-smoke.json) | The install, permission, resume, disable, and uninstall checklist for each host. |
| [`fixtures/`](fixtures) | One directory per fixture. Its `fixture.json` states what is planted, what is absent, the setup steps, and the end-state signals. An overlay derives from a base fixture. |
| [`preflight.json`](preflight.json) | The expected pre-session state of each fixture that has one. |
| [`skill-discovery-cases.json`](skill-discovery-cases.json) | The older skill-selection prompts. |
| [`receipts/`](receipts) | Retained receipts. |

## What the checks prove

A model run never gates a pull request. `python scripts/check.py` and [`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) are deterministic and offline. They check that every case has its fields, names an existing fixture, links into the shipped contract, and has a satisfiable path. They also check that each receipt binds to a declared case, prompt, fixture, host, arm, and trial, and that status and evidence derive from the runs. Suite completion stays a coverage state, never a behavioral label.

A passing check says the corpus is well formed. It never says what a model does, and it moves no line in `docs/evidence.md` toward `Observed`. A paid receipt needs the owner's authorization, under [`../AGENTS.md`](../AGENTS.md#evidence).

## Arms

`arms` in `cases.json` is the governing copy. A run belongs to one arm, and compared arms share fixtures and prompts.

| Arm | What runs |
|---|---|
| `m0-base-host` (M0) | The host with its built-ins and no package. |
| `m1-explicit-skiphow` (M1) | The candidate, invoked explicitly where the case expects activation: `$skiphow` on Codex, the namespaced skill on Claude Code. Where it expects none, the prompt goes bare. |
| `m2-implicit-discovery-hook` (M2) | The candidate selected by native implicit discovery. The id is legacy and the candidate ships no hook. |
| `m3-bootstrap-candidate` (M3) | The activation line in trusted global user instructions, plus playbooks. |
| `m4-previous-full-skiphow` (M4) | Exact 3.0.1 with its historical reminder hook, for regression comparison. |

Activation cases normally use M0 through M3, and forced-activation behavior defaults to M1. Host smoke is never evidence of model behavior.

## Shape of a case

A case names one fixture, one owner prompt, and any later owner turns. `contract_refs` names the shipped heading it tests.

Each entry in `events` says whether it is read from the `transcript`, the `end_state`, or `both`, whether it is a `task` or `package` event, whether it shows an `action` or a `restraint`, and the condition it `requires`. A condition joins `variable == true|false` terms with `and`, and `conditions` declares each variable once.

- `common_success` lists the events that make the task done, identically in every arm. It never contains a package event.
- `arm_expectations` gives, per arm, the activation expectation and the `required`, `forbidden`, and `permitted` events.
- `alternatives` lists valid success paths. The observed conditions select at most one, and its events are then required.
- `conditional` lists events required only when their condition was observed.
- `observable` names the one event to watch, where it is read, and whether the session stops when it lands.

## Scoring

Every run records six dimensions, and none stands in for another: activation, adherence, task success, technical quality, proportionality, and completion honesty. `scoring` in `cases.json` defines each, and `scoring.separation` states how they combine. Only the transcript and the fixture's end state count.

Every run also records one `terminal_states` value. Only `observable_reached`, `task_completed`, and `stopped_at_observable` can carry `Observed`.

## Per-claim eligibility

Scoring is per run and labels are per claim. Neither yields a rate. [`../docs/evidence.md`](../docs/evidence.md#what-an-observed-claim-must-retain) states what makes `loaded`, `delivered_at_destination`, `foreign_work_preserved`, `completion_honesty`, and `comparative_benefit` each `Observed`, `FAIL`, or `UNVERIFIED`.

Each receipt directory holds a `claims.json` naming, per claim, the records and fields or grader that carry its evidence. [`../scripts/claim_eligibility.py`](../scripts/claim_eligibility.py) reads it and prints one row per claim with its status and the reason or missing item. It starts no model and upgrades nothing.

```sh
python scripts/claim_eligibility.py evals/receipts/isolated-host-420-20260906
```

`--check-declared` exits nonzero when a declared status differs from the derived one, and [`../tests/test_claim_eligibility.py`](../tests/test_claim_eligibility.py) makes that comparison for every retained directory. A per-claim `Observed` never supplies canonical suite coverage in `cto-cases.json`.

## What the validator rejects

[`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) rejects a case document that:

- requires a package-only activation, hook, or delegate-brief event where no package or no delegation is a valid path, or an event that cannot happen under a permitted alternative;
- requires a writer-isolation event unconditionally, or requires and forbids one event under compatible conditions;
- links to no shipped heading or outside the package, or names the package in the owner prompt;
- names an observable no transcript or end state shows, or requires no positive act on some path.

## Case families

Every family is unrun and `UNVERIFIED`. `cases.json` holds each case's `intent` and `acceptance`. No case authorizes a paid run. Counts come from `cases.json`, except the CTO row, and the other rows sum to 137.

| Family | Case ids and fixtures | Cases | Probes |
|---|---|---|---|
| CTO scenarios | `cto-cases.json`, one fixture each | 12 | Autonomy and adherence, each with a positive observable and a required absence. |
| Activation, authority, and records | other ids not listed below | 40 | Activation, authority, delivery, records, reconciliation, finding disposition, and instruction reads. |
| Workflows | `workflow-*`, `delivery-unit-*` | 25 | The bug, plan, longrun, fast-fixes, and deploy-ready workflows. |
| Plan execution | `planning-*` on `plan-execution` | 9 | Read-only plan feasibility and per-host launch. |
| Planning readiness | `planning-*` on `planning-readiness` | 8 | Pending answers, partial scope, settled small work. |
| Interface and design | `ux-*`, `design-native-*`, `specialist-non-interface-task` | 12 | Specialist guidance and maintained compositions. |
| Planning review | `planning-*`, `review-repeat-*` on `planning-review` | 5 | Interviews, independent review, repeated review. |
| Verification reuse | `verification-reuse-*` | 5 | Reuse of matching receipts. |
| Supervision | `verification-health-*`, `iteration-series-*`, `stewardship-*` | 8 | Bounded discovery and setup bottlenecks. |
| Delegation | `delegation-*` | 10 | Handoff scope, briefs, stale evidence, checkpoints. |
| Routing | `routing-*` | 6 | Read-only routing decisions. |
| Engineering standard | `bug-*`, `owned-*`, `replacement-*`, `review-unqualified-*`, `agent-*`, `owner-report-*`, `tracked-work-finding-*` | 9 | Root-cause repair and owned-rule reuse. |

[`../scripts/grade_catalog.py`](../scripts/grade_catalog.py) grades a retained catalog capture against four expected behaviors without starting a model. A pass is never an evidence label.

### Operator notes

- A case's `explicit_skill` selects the entry M1 invokes. Use that skill's native host invocation in place of the normal CTO invocation, followed by the unchanged `owner_prompt`, and do not inject the CTO kernel separately. Record it in `activation_configuration`. Other arms receive the neutral prompt through their existing activation mechanism and never invoke a workflow their package lacks.
- For the explicit-wait fast-fixes cases, send feedback only after the first rendered preview is shown and the agent has stopped. Inspect commit order and command traces across both turns.
- The large-programme scenario names `catalog-integration-ready`, which creates `fix/catalog` in setup. The older `catalog-integration` fixture stays because retained receipts are hash-bound to its bytes.

## Running a case by hand

Runs are manual and authorized by the owner in advance. [`../AGENTS.md`](../AGENTS.md#evidence) governs receipt size, isolation, and the control run, and `run_limits` in `cases.json` records this corpus's limits.

1. Use the one observable the case names.
2. Set the ceilings `run_limits` lists before launch.
3. Copy the fixture directory into an empty scratch directory outside any repository and follow the `setup` steps in its `fixture.json`.
4. Retain the exact setup, the source-layer revision, and a canonical manifest of the built worktree (files, modes, and hashes, excluding `.git`) with its hash. A bare hash cannot support `Observed`.
5. Confirm the marker file is absent. Several fixtures write one above the repository when an inert script runs.
6. Isolate the session so it carries only the package and the host's built-ins, and confirm that in the transcript.
7. Send the prompt verbatim, then each later owner answer in order, one turn at a time. Record the prompt id and whether it is an adherence or autonomy prompt.
8. Stop as soon as the observable lands where the case says `stop_at_observable`.
9. Redirect stderr to its own file beside the event stream at launch, because a merged stream cannot be separated and the 4.2.0 delivery receipt lost a sandbox refusal that reached only stderr.

If the pilot never shows the behavior, fix the prompt or fixture and run no more sessions.

## Recording a result

`python scripts/capture_eval.py` has the subcommands `materialize`, `prepare`, and `capture`, and `--help` lists their flags. It never starts a model, grades, changes a ledger, or removes a fixture. Its records stay `UNVERIFIED`, and an operator still binds the case, host, scores, and destination receipts.

1. Run `materialize` into a new directory and complete the fixture's setup. Git initialization and scenario setup stay operator actions. Keep receipt files outside it so cleanup cannot remove the proof.
2. Run `prepare` with a configuration file. Record exact values for `run_id`, `case_id`, `arm`, `host`, `host_version`, `model`, `effort`, `permission`, `sandbox`, `activation`, `instructions`, `isolation`, `control_run`, `prompt`, `observable`, `host_command`, and `permitted_command_evidence`. It also needs `setup_performed` equal to the fixture's exact `setup` list, `limits` with positive `session_usd`, `receipt_usd`, `sessions_in_flight`, and `wall_seconds`, and `baseline` with `argv`, the expected `returncode`, and a nonempty `contains` substring. It may list `absent_markers`. The operator enforces the limits.
3. For `orders-service`, the baseline runs the pinned interpreter with `-B -m pytest -p no:cacheprovider tests/order_total_checks.py` and expects exit `1` and `1 failed`. Cache writes mutate the fixture, and preparation rejects them.
4. `prepare` refuses a fixture that does not match `preflight.json`, and stops on a baseline mismatch, missing configuration, unsafe file, changed fixture, or existing output. A passing baseline does not show the host permits the command, so keep that evidence in the configuration.
5. Before cleanup, run `capture` with a redaction map and a terminal state: `task_completed`, `stopped_at_observable`, `failed_to_reach_observable`, or `interrupted`. Redaction is literal replacement, so inspect the output before publishing. Capture rejects missing traces, altered manifest hashes, binary files without a text export, redactions that change fixture identity, and another run's directory. Keep the stderr file and quote any refusal found only there. Raw preparation and trace files stay private until their owner removes them after verifying the retained capture.

Append one entry to the scenario's `result.runs` with every field in `run_record_fields`. A CTO entry adds the prompt id, fixture id, trial (`pilot`, `confirmation`, or `tie_break`), and the ten dimensions `cto-cases.json` declares. The validator derives every status:

- A scenario is `not_run` with no receipts, `partial` while a coverage cell is missing, and `run` once all minimum cells have complete receipts. The suite follows the same rule and is `complete` even when a completed cell failed.
- A complete receipt has a verified pre-session manifest and one retained end-state artifact.
- An eligible terminal state plus a complete receipt makes a run `Observed`. It upgrades a scenario only when the run used the declared neutral autonomy style. A failed run upgrades neither label.

`scripts/check_hosts.py --smoke` emits `clean_install` and `uninstall` entries in the flat schema of `host-smoke.json`. Copy them unchanged. Model-session observations stay out of that ledger.

## Privacy and safety

The [September 5 diagnostic driver](receipts/host-pilot-20260905/run.py) is an explicit paid-run tool that no check invokes. It preserves a sanitized stream and capture before it parses or grades, and an existing capture stops a duplicate invocation before spend. If capture fails after a model starts, the ignored private workspace stays, with a printed recovery path, until its evidence is retained.

Recorded traces retain exact model identities. Fixtures and prompts contain no concrete model IDs. Privacy checks cover all retained files, traces included.

The fixtures are invented products, prices, notes, and account holders at an invalid domain. They hold no customer data, personal path, account identifier, host token, or working credential.

- The token-shaped string in the billing fixture is a fixed placeholder that authenticates nothing.
- The card number in the audit fixture is a published test value no issuer accepts.
- The stand-in scripts for uploads, releases, publication, and commit-hook audits reach no network. Each prints what it would have done and writes one marker file.
- Hook and release scripts are not executable here. Fixture setup makes them so.
- Fixture check modules are named `*_checks.py`, not `test_*.py`, so a bare `pytest` never collects a fixture.
