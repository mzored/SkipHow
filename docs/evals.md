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

The release-only evaluator is under `evals/live`. Local manifest operations do not start a host:

```sh
python evals/live/run.py validate
python evals/live/run.py plan
```

`run` must execute from the clean committed candidate that it grades. Work and receipt directories must already exist outside that checkout. The command also needs the host credential, an explicit root model and effort, a positive total budget, a per-invocation budget, and `--confirm-live`.

A Codex run needs an exact remote marketplace source and ref plus `--accept-advisory-codex-budget`. The installed CLI does not expose a hard dollar cap. Claude receives the per-invocation limit through `--max-budget-usd`.

For example, after pushing the exact candidate ref:

```sh
python evals/live/run.py run \
  --host codex \
  --candidate "$PWD" \
  --scenario small-fix \
  --model <root-model> \
  --effort <root-effort> \
  --trials 3 \
  --work-root <existing-plain-directory> \
  --receipt-root <existing-plain-directory> \
  --total-budget-usd <total> \
  --per-invocation-budget-usd <limit> \
  --codex-marketplace-source <git-source> \
  --codex-marketplace-ref <exact-ref> \
  --accept-advisory-codex-budget \
  --confirm-live
```

The evaluator gives the host runtime basics, the selected provider credential, and an isolated host config. The GitHub scenario also receives the scoped GitHub App token. The evaluator never executes code written into a trial workspace.

Collectors read bounded file deltas, JSON, the versioned Markdown inbox, fixed Git state, read-only GitHub API state, and host telemetry. The evaluator preserves raw events, failed workspaces, and receipts. It does not remove them automatically.

The restart scenario uses two fresh host processes and reconstructs work from an external checkpoint. This can verify restart reconstruction, not host session resume or compaction.

The routing scenario creates adaptive and all-`DEEP` arms from equivalent fixtures. It needs an operator-owned `--route-map` outside the candidate. A savings claim remains `UNVERIFIED` unless at least three paired trials preserve the same checked outcome. Host telemetry must also identify root and delegated model routes, effort, and complete cost.

```json
{
  "FAST": {"model": "<current-fast-model>", "effort": "medium"},
  "STANDARD": {"model": "<current-standard-model>", "effort": "medium"},
  "DEEP": {"model": "<current-deep-model>", "effort": "high"}
}
```

GitHub evaluation requires one existing clean sandbox clone. Its GitHub App installation token must be restricted to that repository. The only permitted write permissions are `contents`, `issues`, and `pull_requests`.

The marker file supplied through `--github-expected-state` names at least two existing open Issues and required checks. It also gives a unique operation marker already present in those Issue bodies and an unused owned branch prefix. Preflight rejects an existing pull request with that marker or any existing branch with that prefix. The receipt preserves this initial state.

The evaluator does not create, clone, reset, repair, merge, or delete a repository. It observes the final Issue, pull-request, exact-head check, merge, branch, and local cleanup state.

```json
{
  "run_marker": {
    "operation": "skiphow-eval:<unique-id>",
    "issues": [101, 102],
    "required_checks": ["test"],
    "branch_prefix": "skiphow-eval-"
  }
}
```

The GitHub run also requires `--github-sandbox-path`, `--github-sandbox-repo`, `--github-token-env`, `--confirm-github-sandbox`, and `--confirm-github-mutation`.

The candidate repository must be publicly readable. This lets the evaluator compare repository IDs without granting the sandbox token access to the candidate.

Receipts separate `outcome_status`, `process_status`, `metrics_status`, and `claim_status`. `status` covers the checked final state and host process. `claim_status` also covers workflow properties that the collectors cannot prove. `limitations` names each missing proof. A run exits successfully only when both statuses pass.

Missing telemetry does not turn a correct file outcome into failure, and it cannot support a routing or cost claim. A host or credential problem before execution is `BLOCKED`. An observed wrong state or failed invocation is `FAILED`. Missing evidence is `UNVERIFIED`.

## Behavior set

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

Run nondeterministic cases several times. Routing comparisons use the same versioned tasks, root model, and reasoning-effort rules. Cost includes the root session, subagents, transferred context, retries, and review.

## Metrics and claims

Grade product outcome before cost:

- did the final state satisfy the request;
- did intake retain every signal and finding;
- did the agent avoid unauthorized mutations;
- does the evidence match the exact final state;
- did resume and cleanup preserve user work.

Then record tokens, provider-reported cost, latency, retries, and model changes. Do not trade a failed or unauthorized outcome for a cheaper run.

No published live receipt currently proves cross-host behavior, restart recovery, full multi-Issue GitHub delivery, or routing savings for the exact package. Those claims remain `UNVERIFIED`.
