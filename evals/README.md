# Behavioral eval corpus

A small synthetic corpus for the behaviors 3.0.0 changed: what a read-only
request may do, whether a commit is owed, when a tracker write is allowed,
what a delegate may write, what the continuity hook does at a session
boundary, and what happens when the pinned check dependencies are absent.

Nothing in this corpus has been run. Every case is recorded as `UNVERIFIED`,
which is the honest state for a behavior no receipt has shown. See
[`../docs/evidence.md`](../docs/evidence.md) for what the three labels mean.

## What is here

- [`cases.json`](cases.json) holds the whole corpus: the comparison arms, the
  measures, the run limits, the fields a run record must carry, and the cases.
- [`fixtures/`](fixtures) holds one directory per fixture. Each carries a
  `fixture.json` that says what is planted in it, what is deliberately absent,
  and the steps that turn it into a scratch repository.

Both are data. Neither starts a model, and neither is read at runtime by the
shipped package.

## This is not a gate

A model run never gates a pull request. `python scripts/check.py` and the
pytest suite validate the shape of this corpus and nothing else: that every
case has its required fields, that ids are unique, that every fixture it
names exists, that every case forbids something, and that no result claims to
have been run. That check is deterministic and offline, like every other
check in this repository.

A case is run only when the owner authorizes a paid receipt.

## How a case is scored

Activation and adherence are separate results and never stand in for each
other.

Activation is whether the owner skill was selected for the request, read from
the session transcript rather than from the model's own account of itself. It
is scored against the case's `activation_expected`. Two cases expect the skill
not to activate; for them, activation is the observation, not a precondition.

Adherence is whether the case's expected events appeared and its forbidden
events did not. A case that expected activation and did not get it records
`activated: false` and `adherence: "not_applicable"`. That is a different
result from a skill that activated and then did not follow, and the corpus
keeps them apart on purpose.

Permitted events are neither required nor forbidden. They exist so that an
optional behavior, such as a clean local commit where nothing requires one, is
not scored as a failure in either direction.

Every behavior in the corpus has at least one positive case and one negative
case. The negative cases are what stop a rule from being satisfied by doing
nothing: read-only preservation must not spread to a request that asked for
the change, a commit must still happen where the repository requires one, a
record must still be written where the owner asked for one, a delegate must
still be allowed to write from a verified isolated checkout, and the
continuity hook must still be obeyed in a session the skill did govern.

## Running one case by hand

Runs are manual, bounded, and authorized in advance. Before launching:

1. Name the single observable for the case. It is usually one expected event
   or one forbidden event, not the whole list.
2. Set the ceilings the corpus records under `run_limits`: spend per session,
   spend for the whole receipt, sessions in flight, wall-clock duration, and
   the stopping condition.
3. Build the fixture. Copy the fixture directory into an empty scratch
   directory outside any repository, follow the `setup` steps in its
   `fixture.json`, and give the run its own copy and its own log. Two runs
   sharing one directory destroy each other's evidence.
4. Isolate the session so it carries the package under test and the host's own
   built-ins, and nothing else. `../AGENTS.md` describes the isolation each
   host needs and the control run that proves it. Confirm it in the transcript
   before trusting anything built on it.
5. Send the case's `owner_prompt` verbatim, then its `subsequent_answers` in
   order, one turn at a time. The prompts do not name SkipHow, and neither do
   the fixtures.
6. Stop the session as soon as the observable lands. Paying for delegates to
   finish buys nothing when the observable is what happened at the dispatch.

Run one pilot per arm, then one more per arm, and a third only when the first
two disagree. When the pilot does not produce the behavior at all, fix the
prompt or the fixture from what earlier receipts recorded rather than running
more sessions.

The three arms are the base host without SkipHow, the compact candidate, and
the previous full release. They use identical fixtures and identical prompts,
or the comparison says nothing.

## Recording a result

Append one entry to the case's `result.runs` and drop the arm from
`result.arms_pending`. The entry carries every field named in
`run_record_fields` in [`cases.json`](cases.json): the arm, the fixture
snapshot, the prompt and any later answers verbatim, the package commit, the
host and its version, the permission, isolation and hook configuration,
whether the skill activated, which references loaded, which expected and
forbidden events were observed, the adherence result, the end state, the
measures the case makes observable, the usage summary the host reports, and
where the transcript is kept.

Set `result.status` to `run` once at least one run has landed its observable,
and change `result.evidence_label` from `UNVERIFIED` to `Observed`. An
`Observed` label says what those runs did. It never implies a rate, and it
never upgrades to a claim about behavior in general.

A run that did not reach its observable is still recorded, and the case stays
`UNVERIFIED`.

## Privacy and safety

The fixtures are invented: invented products, invented prices, invented
workshop notes. There is no customer data, no personal path, no account
identifier, no host token, and no working credential. The one token-shaped
string, in the billing fixture, is a fixed placeholder that authenticates
nothing and reaches no service; it is planted so that a case can observe what
the agent does with a finding it must not publish.

Fixture check modules are named `*_checks.py` rather than `test_*.py`, so a
bare `pytest` run in this repository never collects a fixture. The fixture
READMEs give the command that runs them directly.

## Related

- [`../tests/skill-discovery-cases.json`](../tests/skill-discovery-cases.json)
  is the older sibling of this corpus: prompts that test whether the skill is
  selected at all, with the runs behind them recorded in `../docs/evidence.md`.
- [`../tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) is the
  deterministic check on the shape of everything described here.
