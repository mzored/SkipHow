# Live evaluation host contract

- Date: 2026-08-25
- Repository revision: `edb069900799e59e24752b684d065cce06f08c52`
- Codex CLI: `0.149.1`
- Claude Code: `2.1.240`
- Status: implementation input; no model trial was run

This file records the evaluator at the revision above. The later [release-readiness audit](release-readiness-audit.md) found that remote Codex installation can materialize a Git repository, installed inventory did not prove candidate bytes, nested receipt evidence was not fully redacted, and the mutable GitHub gate lacked repository-deletion enforcement. [ADR 0005](../../decisions/0005-fail-closed-release-evaluation.md) supersedes those parts of the implemented contract. Keep the commands below as historical evidence, not current release instructions.

## Scope

This check defines the replacement for the removed live evaluator. It covers exact plugin loading, noninteractive host execution, budget controls, event collection, and the boundary between deterministic checks and paid outcome trials.

It does not prove that either host will follow SkipHow, finish a multi-Issue run, resume after a crash, or save money through model routing. Those results need opt-in trials with separate credentials and a positive budget.

## Commands checked

The review ran these read-only help and package commands:

```sh
codex --version
codex plugin marketplace add --help
codex plugin add --help
codex exec --help
codex exec resume --help
claude --version
claude plugin marketplace add --help
claude plugin install --help
claude plugin list --help
claude --help
```

The 0.9 plugin candidate at commit `e91aa78359060223c8b62402a52f8659badf8724` was also installed from its exact remote branch before PR #18 merged:

```sh
python scripts/check_hosts.py \
  --require-codex-validator \
  --require-claude \
  --require-codex-install \
  --require-claude-install \
  --codex-marketplace-source https://github.com/mzored/SkipHow.git \
  --codex-marketplace-ref codex/issue-15-plugin
```

Both validators and both isolated installations passed. GitHub then squash-merged that head as `edb069900799e59e24752b684d065cce06f08c52`. The source and merged trees matched. Package installation is not behavioral evidence.

## Verified host facts

### Codex

Codex installs plugins through a configured marketplace:

```text
codex plugin marketplace add SOURCE [--ref REF] [--json]
codex plugin add PLUGIN@MARKETPLACE [--json]
codex plugin list [--json]
```

`SOURCE` may be a local path or Git source. For Git, the evaluator resolves the requested ref to the clean candidate `HEAD` before passing it to Codex. A branch name worked as `--ref`. The full `refs/heads/...` name did not work with the installed CLI.

`codex exec` supports noninteractive execution, JSONL events, a final-output schema, an explicit model, and an explicit working directory. It also supports `read-only` or `workspace-write` sandboxing, session resume, and ignoring user config. Its help states that auth still comes from `CODEX_HOME` when user config is ignored.

The inspected CLI exposes no dollar cap, token cap, or documented reasoning-effort flag for `codex exec`. The evaluator can require an operator budget and stop between calls. It cannot claim a hard Codex spend limit. Codex budget enforcement remains `UNVERIFIED`.

Codex skills can be selected explicitly with `$skiphow`. Plugin skills become available to new sessions after installation. The host help does not promise an event that proves implicit or explicit skill loading.

### Claude Code

Claude installs plugins through a marketplace or loads a plugin directory for one session:

```text
claude plugin marketplace add SOURCE
claude plugin install PLUGIN@MARKETPLACE --scope user --yes
claude plugin list --json
claude --print --output-format stream-json
```

`CLAUDE_CONFIG_DIR` relocates user settings, sessions, and installed plugins. Project instructions and managed policy remain separate inputs. A fresh config directory gives useful isolation. It is not a complete security boundary.

Claude noninteractive mode exposes an explicit model, reasoning effort, session ID and resume, structured streaming output, a plugin directory, and `--max-budget-usd`. Plugin skills use the namespaced form `/skiphow:skiphow`.

The budget flag is a stronger per-run guard than Codex provides, but the final receipt must still distinguish requested cap, host-reported cost, and independently verified provider billing.

## Evidence limits

Host JSON or JSONL is a host observation, not provider-side proof. The evaluator may use present fields for session IDs, tool events, input requests, command exits, reported model, and reported usage.

The requested model name is not proof of the model that ran. A model-written summary is not proof of skill use, routing, cost, or outcome. Missing event fields stay `UNVERIFIED`.

The evaluator must not execute agent-written repository code as a privileged verifier. Portable collectors read file inventories and hashes, structured data, Git state with hooks disabled, read-only GitHub state, and host or provider events. A scenario that needs stronger evidence stays `UNVERIFIED` unless it runs inside a separate trusted execution sandbox.

## Implemented release contract

The replacement is opt-in release tooling, not a SkipHow runtime. It:

- keeps one versioned manifest for ten scenarios;
- requires each packaged plugin file, live evaluator file, and `VERSION` to match the committed candidate, then hashes them;
- installs and lists the exact candidate in a fresh host configuration;
- keeps fixtures, expected results, and collectors outside the agent's writable workspace;
- preserves failed workspaces and raw events;
- uses `PASSED`, `FAILED`, `BLOCKED`, and `UNVERIFIED` without converting missing evidence into success;
- requires explicit credentials, positive total and per-invocation budgets, and a separate receipts directory;
- requires an existing named GitHub sandbox and rejects repository administration for the GitHub scenario;
- never creates, clones, initializes, resets, or deletes a repository;
- stays out of `scripts/check.py` and CI.

Codex trials require an explicit acknowledgement that their dollar budget is advisory. Claude receives its per-invocation cap through the host. The restart scenario uses two fresh host processes.

The routing scenario creates paired adaptive and all-`DEEP` arms from equivalent fixtures. It cannot support a cost claim without complete host telemetry. No live call ran during this implementation because no release budget or credentials were supplied.

The GitHub gate starts the host in the pre-provisioned sandbox clone. Its selected-repository GitHub App token can access one repository. Write access is limited to contents, Issues, and pull requests.

Preflight records open Issues, the absence of an operation PR, and the absence of owned branches. The post-run collector reads selected Issues, operation-marked pull requests, checks at their immutable head SHAs, `merged_at`, and remote branch absence. It also reads the local base branch, worktrees, and owned local branches. The collector does not audit every possible remote side effect, so out-of-scope remote mutation remains `UNVERIFIED` and lowers `claim_status`.

One plain-language scenario omits the explicit skill syntax. A correct outcome does not prove that the host loaded SkipHow. The inspected hosts do not expose a portable skill-loading event. Implicit skill loading remains `UNVERIFIED` unless future host telemetry supplies that evidence.

## Local verification

The replacement evaluator was checked without starting a model:

```sh
python scripts/check.py --pytest tests/test_live_evals.py -q
python evals/live/run.py validate
python scripts/check.py
python scripts/check_hosts.py
git diff --check
```

The focused suite passed 18 tests. Manifest validation, the full deterministic gate, and `git diff --check` passed. Claude validation and isolated installation passed. Codex local validation was `UNVERIFIED`, and its local isolated install failed because managed policy rejects a filesystem marketplace. This environment requires an exact remote ref for the Codex package check.

These commands did not run a model. No outcome, restart, GitHub delivery, or routing claim follows from them.

## Rejected alternatives

- Reusing the deleted provider adapter would again test a bare model session instead of the installed product.
- Allowing arbitrary collector commands would recreate the unsafe verifier path under a new name.
- Treating requested model labels, model prose, or a handwritten price table as provider receipts would create false precision.
- Creating a disposable repository inside the evaluator would violate the repository safety contract. GitHub trials must use a pre-provisioned sandbox.
- Adding live execution to deterministic CI would spend credentials and make normal checks nondeterministic.

## Primary sources

- [Codex developer commands](https://developers.openai.com/codex/cli/reference)
- [Codex plugins](https://learn.chatgpt.com/docs/plugins)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude plugin discovery and install](https://code.claude.com/docs/en/discover-plugins)
- [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude noninteractive mode](https://code.claude.com/docs/en/headless)

## Revalidation triggers

Repeat this check when a host changes plugin installation, noninteractive output, session resume, sandbox flags, model or effort flags, budget controls, or event fields. Revalidate before claiming hard budget enforcement, exact delegated model identity, or proven skill invocation.
