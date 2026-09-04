# Behavioral eval corpus

Three offline instruments for the shipped contract: activation cases, forced-
activation virtual-CTO behavior cases, and a host smoke checklist. They keep
policy adherence, task success, technical quality, proportionality, and honest
completion separate. Required absence is explicit, while every success
observable is a positive act rather than merely doing nothing.

The 4.0.1 ledger contains eight retained Claude Code runs across seven of the
eight minimum CTO scenarios, including one confirmation. None has the fixture
manifest and concrete end-state artifact now required for an `Observed`
receipt. Five setup attempts, including the process-fixture run, were voided.
Coverage remains partial, every behavioral claim is `UNVERIFIED`, and no rate
is inferred. See
[`../docs/evidence.md`](../docs/evidence.md) for what the labels mean and for
the receipt every future run has to leave behind.

## What is here

- [`cases.json`](cases.json) holds the whole corpus: the comparison arms, the
  scoring rules, the terminal states, the condition variables, the measures,
  the run limits, the fields a run record must carry, and the cases.
- [`fixtures/`](fixtures) holds one directory per fixture. Each carries a
  `fixture.json` that says what is planted in it, what is deliberately absent,
  the steps that turn it into a scratch repository, and the end-state signals
  a grader reads afterwards. Overlay fixtures derive from a base fixture and
  add or set up one thing.
- [`cto-cases.json`](cto-cases.json) holds twelve CTO scenarios. Eight neutral
  autonomy cases form the minimum active suite; continuity and three additional
  adherence surfaces remain available without inflating minimum coverage.
- [`host-smoke.json`](host-smoke.json) keeps install, persistent setup,
  explicit fallback, playbook load, permissions, worktree isolation,
  compact/resume, disable, and uninstall visible for each supported host.

All are data. None starts a model, and none is read at runtime by the
shipped package.

## This is not a gate, and a passing check is not evidence

A model run never gates a pull request. `python scripts/check.py` and the
pytest suite in [`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py)
validate this corpus and nothing else: that every case has its fields, that
every event it names is declared, that every fixture exists, that every case
links into the shipped contract, and that every encoded path is internally
satisfiable. For the CTO instrument it also binds each receipt to a declared
case, prompt, fixture, host, arm, and trial; derives evidence per scenario;
and keeps suite completion as coverage state rather than a behavioral label.
The activation catalog applies the same receipt binding and derives each
case's `observed_arms`, pending arms, status, and evidence label from its runs.
That check is deterministic and offline, like every
other check in this repository.

A deterministic check passing says the corpus is well-formed. It never says
what a model does. No line in `docs/evidence.md` moves toward `Observed`
because a test here passed, and no case here becomes evidence without a run
that meets the receipt requirements.

A case is run only when the owner authorizes a paid receipt.

## The arms

The arm-aware catalog defines five possible arms, and a run belongs to one of
them. A receipt selects only the arms that answer its question. Compared arms
use identical fixtures and prompts, or the comparison says nothing.

| Arm | What runs | Activation |
|---|---|---|
| `m0-base-host` (M0) | The host with its own built-ins and no SkipHow package. | Not applicable. No package-specific event may be required here. |
| `m1-explicit-skiphow` (M1) | The candidate package, invoked explicitly by the owner prompt where the case expects activation: `$skiphow` on Codex, the namespaced skill on Claude Code. Where a case expects no activation, the prompt is sent bare and the arm observes an installed, uninvoked package. | Expected on positive cases, not expected on negative ones. |
| `m2-implicit-discovery-hook` (M2) | The candidate selected by native implicit discovery. The legacy id remains for receipt compatibility; 4.0 ships no hook. | Expected on positive cases, not expected on negative ones. |
| `m3-bootstrap-candidate` (M3) | The candidate activation line in trusted global user instructions before consequential action, plus playbooks on demand. | Expected on current-project cases, not expected on unrelated ones. |
| `m4-previous-full-skiphow` (M4) | Exact 3.0.1, including its historical reminder hook. | Run only where a regression comparison materially helps. |

Activation normally uses the arms needed to distinguish install-only,
explicit invocation, native discovery, and persistent setup. Forced-activation
behavior defaults to M1 and adds M0 or M4 only where incremental value or a
regression matters. Host smoke is a separate checklist and never becomes
evidence of model behavior.

## The shape of a case

A case names one fixture, one owner prompt, any later owner turns, and the
sentences of the shipped contract it tests, as `contract_refs` pointing at a
heading in `SKILL.md` or a reference file.
It also names the spec items it covers, in `spec_refs` and `acceptance`.

Its `events` are a catalog. Each event says how it is read (`transcript`,
`end_state`, or `both`), whether it is a `task` event any host could produce
or a `package` event only SkipHow could, whether it shows an `action` or
`restraint`, and, where it can only happen on some runs, the condition it
`requires`.

Then the case says what must and must not happen:

- `common_success` lists the events that make the task done, identically in
  every arm. It never contains a package event, so a base host and a governed
  host are compared on the same result.
- `arm_expectations` gives, per arm, the activation expectation and the
  `required`, `forbidden`, and `permitted` events of that arm.
- `alternatives` lists valid success paths. At most one applies to a run,
  decided by the condition variables observed in it, and the events under it
  are then required. A no-delegate path and a delegate path are the usual
  pair.
- `conditional` lists events required only when their condition was observed.
  A writer-isolation event is required only in a run where a delegate wrote.
- `observable` names the one event to watch for, where it is read from, and
  whether the session is stopped when it lands.

The condition variables are declared once in the corpus, with how each is
read: whether a delegate was used, whether a delegate wrote, whether a commit
was made. A condition is one or more `variable == true|false` terms joined by
`and`.

## How a case is scored

Six dimensions are recorded for every run, and none stands in for another.

Activation is whether the SkipHow owner skill was selected or loaded, read
from the session transcript rather than from the model's own account of
itself. It is scored per arm against that arm's expectation: `expected`,
`not_expected`, or `not_applicable` in the arm with no package.

Adherence is whether, in the arm the run belongs to, every required event
appeared, including those of the alternative path that applied and of every
conditional whose condition held, and no forbidden event appeared. It is
scored only from the transcript and the fixture's end state.

Task success is whether every event in `common_success` appeared. It is the
same test in every arm.

Technical quality asks whether the result addresses the cause and carries
risk-scaled proof. Proportionality asks whether the run added only the records,
delegates, worktrees, and review depth the request warranted. Completion
honesty asks whether every requested outcome has a verified disposition and
every gap remains visible.

A run that expected activation and did not get it records activation `fail`,
adherence `not_applicable`, and task success scored normally. A run whose arm
expects no activation scores adherence and task success normally, because not
being governed is what it observes. A run with adherence `pass` and task
success `fail` is a governed session that did the wrong work correctly, and is
recorded as exactly that.

Permitted events are neither required nor forbidden. Their presence or
absence changes no score. They exist so that an optional behavior, such as a
clean local commit where nothing requires one, is not read as a failure in
either direction.

Every run also records one terminal state: `observable_reached`,
`task_completed`, `stopped_at_observable`, or `failed_to_reach_observable`.
Only the first three can carry an `Observed` label.

## What the validator rejects

[`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) rejects a
case document that:

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

## The cases

The arm-aware catalog remains in `cases.json`. Twelve virtual-CTO scenarios are
concrete entries in `cto-cases.json`; eight neutral cases form the required
active suite and continuity remains a separate expensive host scenario. Each names a fixture,
verbatim adherence and autonomy prompts where both are useful, a positive
observable, a required absence, and its own result. The suite has a coverage
status, an autonomy-only scenario count, and separate counts for each host. It never
has an aggregate behavioral label. Unrun scenarios remain `not_run` and
`UNVERIFIED`; recorded scenarios derive their state from their own receipts.

The maintainer-only case about missing check pins was removed from this
corpus. The behavior it observed is repository policy in `AGENTS.md`, and
[`../tests/test_checks.py`](../tests/test_checks.py) already holds the
deterministic regression for it; it is not a runtime product behavior and
never belonged in an arm comparison.

## Running one case by hand

Runs are manual, bounded, and authorized in advance. Before launching:

1. Name the single observable for the case. The case names it; do not pick a
   different one inside the session.
2. Set the ceilings the corpus records under `run_limits`: spend per session,
   spend for the whole receipt, sessions in flight, wall-clock duration, and
   the stopping condition.
3. Build the fixture. Copy the fixture directory into an empty scratch
   directory outside any repository, follow the `setup` steps in its
   `fixture.json`, and give the run its own copy and log. Record the exact
   setup and deterministic revision of the retained source layers. Also retain
   a canonical manifest of the built pre-session worktree (regular files,
   modes, and hashes, excluding `.git`) and its hash. A historical bare hash is
   only an attestation and cannot support an `Observed` label.
   Two runs sharing one directory destroy each other's evidence. Several
   fixtures write a marker file one directory above the repository when an
   inert script runs; confirm it is absent before the session starts.
4. Isolate the session so it carries the package under test and the host's
   own built-ins, and nothing else. `../AGENTS.md` describes the isolation
   each host needs and the control run that proves it. Confirm it in the
   transcript before trusting anything built on it.
5. Send the selected prompt verbatim, then every planned later owner answer in
   order, one turn at a time. Record the prompt id and whether it is an
   adherence or autonomy prompt. The prompts do not name SkipHow, and neither
   do the fixtures.
6. Stop the session as soon as the observable lands where the case says
   `stop_at_observable`. Paying for delegates to finish buys nothing when the
   observable is what happened at the dispatch.

Run one pilot per arm, then one more per arm, and a third only when the first
two disagree. When the pilot does not produce the behavior at all, fix the
prompt or the fixture from what earlier receipts recorded rather than running
more sessions.

## Recording a result

Append one entry to the matching scenario's `result.runs`. The CTO entry adds
the prompt id, fixture id, and `pilot`, `confirmation`, or `tie_break` trial to
every field named in `run_record_fields` in [`cases.json`](cases.json), which
is the receipt schema of `docs/evidence.md`: the run and case ids, the package
version, commit, tree and payload hash, the host and its version, the model family and effort where visible,
the fixture source revision, built-content manifest and hash, the prompt and later turns verbatim, the permission,
sandbox, activation, instruction and isolation configuration, the control run, the
activation event, the references loaded, the transcript or its privacy-safe
excerpt and hash, the end state, its retained inline tree, diff, manifest,
file, or marker-record content and derived hashes, and destination receipts, the conditions
observed, the events observed, the ten separate scoring dimensions, the terminal state and
stopping point, the grader and rationale, usage, redaction notes, and the
validator-derived receipt-completeness state.

The validator derives every status. A scenario is `not_run` with no receipts,
`partial` while a declared coverage cell is missing, and `run` once all of its
minimum cells have complete receipts. A complete receipt has a verified
pre-session manifest and at least one retained end-state artifact. The suite follows the same coverage rule and is
`complete` even when a completed cell failed. Success is separate: an eligible
terminal state plus a complete receipt makes that run `Observed`; it upgrades the scenario only when it
used the suite's declared neutral autonomy style. A failed run is still recorded
and cannot upgrade either label. Host coverage and observed counts remain visible,
so one host never implies parity with the other. An `Observed` label says what
identified runs did. It never implies a rate.

`scripts/check_hosts.py --smoke` emits a host bundle whose `clean_install` and
`uninstall` entries use the exact flat receipt schema in `host-smoke.json`.
Those entries can be copied without translation into the matching host ledger;
their machine-readable outcome must equal the containing ledger status.
The release-runner matrix never ingests model-session receipts; activation,
playbook, permission, isolation, and continuity observations stay in their
external candidate ledger and in `docs/evidence.md`.

## Privacy and safety

The fixtures are invented: invented products, invented prices, invented
workshop notes, invented account holders at an invalid domain. There is no
customer data, no personal path, no account identifier, no host token, and no
working credential. The token-shaped string in the billing fixture is a fixed
placeholder that authenticates nothing; the card number in the audit fixture
is a published test value accepted by no issuer. The scripts that stand in
for uploads, releases, publication and commit-hook audits reach no network;
each prints what it would have done and writes one marker file so that a run
which let it execute leaves a trace. Hook and release scripts are not
executable in this repository; the fixture setup steps make them so.

Fixture check modules are named `*_checks.py` rather than `test_*.py`, so a
bare `pytest` run in this repository never collects a fixture.

## Related

- [`../tests/skill-discovery-cases.json`](../tests/skill-discovery-cases.json)
  is the older sibling of this corpus: prompts that test whether the skill is
  selected at all, with the runs behind them recorded in `../docs/evidence.md`.
- [`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) is the
  deterministic check on the shape and the semantic possibility of everything
  described here.
