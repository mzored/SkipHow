# Evaluation and release evidence

SkipHow separates deterministic repository checks from live model evaluation. Pull requests and normal release checks run locally and make no paid model calls. Live evaluation is an explicit, budgeted operation for nightly runs, release candidates, or manual investigation.

Neither package validation nor a single successful model run proves behavioral support. Support claims need outcome evidence from several trials against exact component and provider versions.

## Deterministic checks

Run the repository-managed check suite:

```sh
python scripts/check.py
git diff --check
```

Focused tests use the same environment:

```sh
python scripts/check.py --pytest <pytest-arguments>
```

These checks validate local contracts such as schemas, scenario manifests, graders, package structure, portability, and instruction budgets. They must not call Codex, Claude Code, or another model. A missing optional dependency or unavailable network path must be reported as `UNVERIFIED` or `BLOCKED`, not disguised as a project test failure.

Grade an existing scenario receipt without executing an agent or using the network:

```sh
python -m evals.graders evals/scenarios/<scenario>.json path/to/receipt.json
```

## Scenario registry

`evals/scenarios/` contains 20 versioned JSON manifests:

1. `simple-anti-ceremony`
2. `nontechnical-owner`
3. `reuse-first`
4. `trivial-local-logic`
5. `unknown-bug`
6. `batch-intake`
7. `no-orphan-finding`
8. `scoped-re-review`
9. `verification-ceiling`
10. `long-campaign`
11. `github-lifecycle`
12. `idempotent-rerun`
13. `pause-resume-cancel`
14. `prompt-injection`
15. `protected-action`
16. `model-routing`
17. `escalation`
18. `scope-restraint`
19. `context-handoff`
20. `cleanup-safety`

Each schema-v1 manifest records the intent, fixture, request, preconditions, execution shape, pass condition, required outcomes, and forbidden effects. Assertions name the observation, operator, expected value, and required evidence. Graders evaluate an observation receipt and do not reward a prescribed chain of thought or workflow. Trusted fixture and observation code must establish that the receipt represents the final environment.

`evals/deterministic/rules.json` links every kernel rule to its owner, failure mode, scenario, measured effect, and last revalidated model and evaluator versions. A rule without a demonstrated failure and an evaluation case does not belong in the kernel.

## Live harness v2

The live suite is outside deterministic CI. Harness v2 has subprocess bridges for Codex App Server and Claude Code. `evals/live/generate_config.py` creates a provider-specific config containing all twenty registered scenarios, three semantic profiles, exact model labels, and per-trial cost caps. Put both the generated config and the isolated scenario workspace outside the candidate checkout. Run the generator with `--help` for the required model, version, and cost arguments.

Inspect the matrix and worst-case cost without invoking an adapter:

```sh
python evals/live/run.py \
  --config path/to/local-config.json \
  --routing-mode adaptive \
  --release
```

Live execution needs three independent opt-ins: `--live`, a positive `--budget-usd`, and `SKIPHOW_LIVE_EVALS=1`. The harness also checks every `required_env` name before starting:

```sh
SKIPHOW_LIVE_EVALS=1 python evals/live/run.py \
  --config path/to/local-config.json \
  --routing-mode adaptive \
  --budget-usd 25 \
  --release \
  --live
```

Release mode requires a clean checkout whose revision and component versions match the config. It also requires the exact twenty-scenario registry and complete code-owned fixture coverage. The harness rejects a budget below the configured worst case and fails the aggregate if any planned trial is missing or fails. Results go to `evals/live/results/` by default as append-only JSONL and an atomic summary.

Every registered trial gets a fresh harness-owned temporary workspace. The provider receives the request and visible fixture facts, but not grading rules, expected values, or collector internals. Hidden oracle and baseline data stay outside the writable workspace. After the provider exits, versioned collectors inspect concrete files and harness state and create content-addressed evidence receipts. Provider-written summary files and provider-reported observations, evidence, and success claims remain diagnostic. They cannot satisfy the gate. A rule with no independent collector makes the trial `UNVERIFIED`; it can never become a pass through a writable summary. Collector or teardown failure fails the trial, and teardown removes the isolated workspace before the receipt is committed.

The registry maps all twenty scenarios and all ninety-five rules, but the current concrete collectors cover only facts derived from a few synthetic project files and harness capabilities. Rules that require Git or GitHub service history, tracker, deploy, or network audit, conversation and tool events, controller kill and restart, provider compaction, or task-level routing remain `UNVERIFIED` until dedicated collectors exist. Per-trial isolation, cleanup, unsupported-rule handling, and resistance to forged provider summaries have deterministic coverage. Authenticated Claude execution, multi-trial real provider and service outcomes, adaptive-routing ablation, and cross-platform operation remain `UNVERIFIED` for this release candidate.

Use several trials for nondeterministic behavior. A release comparison runs the same real project tasks and fixtures for each candidate configuration. For routing, compare at least:

- all tasks on `FRONTIER`;
- all eligible tasks on `BALANCED`;
- adaptive profile routing with bounded escalation.

Compare the prompt-only baseline, the thin kernel, and the kernel with durable runner and routing on the same provisioned task set. The adaptive-routing ablation has not yet produced release evidence.

## GitHub lifecycle gate

The live GitHub gate is separate from the model harness. `scripts/check_github_e2e.py` creates an owned disposable private repository, records two Issues and a native blocking dependency, pushes a delivery branch, opens a pull request, waits for exact-head CI, merges, verifies the default branch and closed Issue, and removes the merged branch. A valid receipt requires an injected process exit and a resumed run. The script reconciles every completed phase from persisted state before continuing.

The gate requires `--live`, `SKIPHOW_GITHUB_E2E=1`, an authenticated `gh`, a clean committed candidate, and state and receipt paths outside the candidate repository. It is never called by `scripts/check.py`. See [GitHub lifecycle](github-lifecycle.md) for the command sequence and cleanup rules.

## Metrics

Primary metrics determine whether a run succeeded:

- terminal task success and final environment correctness;
- unauthorized mutations and unresolved blocking findings;
- recovery after interruption or context loss;
- safe cleanup and preservation of user state.

Economy metrics explain the cost of that outcome. Record tokens, provider-reported or estimated cost, latency, tool calls, model promotions, duplicate external actions, tracker touches, campaign creation, generated artifacts, and questions sent to the Owner. Do not trade a primary success metric for a cheaper run.

## Release receipts

A machine-readable receipt must bind every result to:

- scenario and trial identifiers;
- repository revision and plugin, runner, evaluator, and schema versions;
- provider, model identifier, and model version when the provider exposes it;
- route profile and reason;
- timestamps, usage, cost, latency, verifier results, retries, and promotions;
- terminal outcome, grader result, and evidence references.

Receipts must redact secrets and raw prompt content. The live config requires the repository revision and exact plugin, runner, and evaluator versions. The harness copies this candidate identity into its plan, start record, trial requests, and summary. Publish an aggregate only after all required scenarios have enough trials in independently provisioned fixtures. State unavailable checks as `UNVERIFIED`. State failed required checks as failed. Do not claim live model coverage unless the published receipt identifies the exact tested versions and date.

The live harness writes run, scenario hash, profile, model, cost, latency, outcome, content-addressed evidence references, verifier summaries, retries, grader result, collector identity, and allowlisted economy fields. Repository tests exercise this format with adversarial fake adapters whose self-reported success cannot override trusted collection. These fixtures prove the harness contract, not provider behavior.
