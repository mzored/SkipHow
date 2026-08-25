# Evaluation policy

SkipHow separates deterministic repository checks, host package checks, and live outcome evaluation. They answer different questions and must remain separate in reports.

## Deterministic checks

Run focused tests through the repository-managed environment:

```sh
python scripts/check.py --pytest <pytest-arguments>
```

Before completion, run:

```sh
python scripts/check.py
git diff --check
```

These checks stay local and deterministic. They do not start Codex, Claude Code, another model, or a live GitHub workflow. They may validate:

- the single canonical skill and both host manifests;
- progressive-disclosure links and instruction budgets;
- JSON, YAML, Markdown, portability, and repository tests;
- the absence of a custom runner, provider bridge, model IDs, personal paths, credentials, hooks, and private dependencies.

A passing check proves only those contracts. It does not prove that a model will follow the skill or finish a product task.

## Host package checks

Run package validation after packaging changes:

```sh
python scripts/check_hosts.py
```

The check validates structure and isolated installation in each available supported host. Report an unavailable host as `UNVERIFIED`. Installation success is package evidence, not behavioral evidence.

## Live outcome evaluation

Live evaluation is an opt-in release activity. It never runs from `scripts/check.py` or normal CI. Each run needs explicit credentials, a cost budget, exact provider and host versions, and an exact packaged SkipHow candidate.

A valid run must:

- install and activate the exact candidate in a fresh host environment;
- keep grading rules, expected results, and collectors outside the agent's writable files;
- collect final files, Git state, GitHub state, and host events independently of the model's report;
- publish failed trials and mark unsupported assertions `UNVERIFIED`;
- write a machine-readable receipt outside the candidate checkout;
- keep fixtures synthetic and avoid customer or production data.

A live GitHub test may mutate only an explicitly named pre-provisioned sandbox repository. The sandbox must differ from the candidate repository. Its credentials must not have repository creation or deletion authority.

## First behavior set

The first release-quality suite should cover:

1. a small fix without added ceremony;
2. an unknown bug with a reproduced cause and checked repair;
3. a material feature that researches reuse before adding a lasting subsystem;
4. mixed intake with provenance and semantic duplicate handling;
5. work for a nontechnical owner without technical-choice questions;
6. persistence of a valid finding outside the current scope;
7. several Issues through pull requests, CI, guarded merge, and safe cleanup;
8. reconstruction after compaction or restart;
9. refusal of an ungranted protected action;
10. semantic routing compared with an all-`DEEP` baseline.

Run nondeterministic cases several times. Routing comparisons use the same versioned tasks and the same reasoning-effort rules. Cost includes the root session, subagents, transferred context, retries, and review.

## Metrics and claims

Grade product outcome before cost:

- did the final state satisfy the request;
- did intake retain every signal and finding;
- did the agent avoid unauthorized mutations;
- does the evidence match the exact final state;
- did resume and cleanup preserve user work.

Then record tokens, provider-reported cost, latency, retries, and model changes. Do not trade a failed or unauthorized outcome for a cheaper run.

No published live receipt currently proves cross-host behavior, restart recovery, full multi-Issue GitHub delivery, or routing savings for the exact package. Those claims remain `UNVERIFIED`.
