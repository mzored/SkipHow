# Security and evaluation audit

- Date: 2026-08-25
- Repository revision: `a6d34a25614bc0723517032af617b0782158df4d`
- Status: historical audit for the host-native redesign

## Scope and method

This audit covers the Python runner, its security claims, and live evaluation harness at the revision above. It does not claim that Codex, Claude Code, GitHub, or their current policies behave the same way in later releases.

The review inspected these implementation paths before their planned removal:

- `src/skiphow/cli.py`, `supervisor.py`, `runtime_security.py`, `security.py`, and `verification.py`;
- `src/skiphow/adapters/`;
- `evals/live/provider_adapter.py`, `fixtures.py`, and `run.py`;
- the 20 scenario manifests under `evals/scenarios/`.

Commands recorded during the review:

```sh
git rev-parse HEAD
python scripts/check.py --pytest -q
```

The test run completed with `338 passed`. A separate static count found 95 assertions in 20 scenario manifests and six concrete collector outputs in four scenarios. Passing repository tests did not close the security or outcome-evidence gaps below.

## Verified findings

### The worker could write the controller database

`cli._database()` required the SQLite file to stay inside the project. Its default path was `.skiphow/runs/runner.sqlite3`. `CampaignSupervisor` then opened write-capable provider sessions with the project root as `cwd`. `RuntimeSecurityPolicy` allowed the same project root for writes.

The worker and the controller therefore shared one write root. The provider could alter the database that stored run authority, leases, checkpoints, findings, and audit events. Hash-linked audit records do not help if the writer can replace the database that contains both records and their current head.

The exact effect depended on the host sandbox, so a successful exploit was not tested. The configured boundary still admitted the controller database. That is enough to reject it as an authority store.

### The verifier ran repository-controlled code outside the agent sandbox

`EnvironmentVerifier` pinned the selected executable and listed trusted artifacts. It then called `subprocess.Popen()` from the repository root with no separate operating-system sandbox.

That check cannot cover every indirect import, test plugin, `conftest.py`, package hook, or executable child selected by repository code. A worker could modify an unlisted file that a trusted test command later imports. The controller would then execute that code with the controller's permissions.

The verifier was evidence code and a second execution path. Treating it as a stronger trust boundary than the provider sandbox was unsafe.

### Permission profiles were declarations, not enforcement

The runner mapped tasks to `read-only`, `writer`, and `reviewer` profiles. `FilesystemPolicy.check()` verified that the requested `cwd` fell inside configured roots. It did not interpose on the provider's later file or network operations.

Actual enforcement came from the host permission mode and sandbox. The runner could request a mode and reject an obvious mismatch, but its Python enums and allowlists did not create an operating-system boundary. Documentation that said the runner "enforced" those permissions overstated what the code did.

### Protected-action detection was a regex gate

The runner accepted explicit `protected-action:` constraints. It also searched the task outcome with nine regular expressions for terms such as production deployment, refunds, credential rotation, privacy operations, public release, and protected-branch merge.

This gate inspected prose before dispatch. It did not inspect each tool call or remote mutation. A paraphrase, an action discovered after dispatch, or a tool invocation not represented in the original outcome could bypass classification. Regex detection may warn about an obvious request. It cannot grant or deny the underlying capability.

### The live harness did not load the candidate plugin

Release mode matched the clean checkout revision and copied plugin, runner, and evaluator version strings into receipts. `provider_adapter.py` launched a bare Codex or Claude session in a generated fixture workspace. It sent the scenario prompt and collector note, but did not install or activate the candidate SkipHow plugin.

Candidate identity and tested behavior were disconnected. A receipt tied to commit `X` could describe a model run that never read the plugin from commit `X`.

### Independent collection covered 6 of 95 assertions

The registry contained 95 assertions across 20 scenarios. `fixtures.py` emitted six independently collected observations:

- two for `simple-anti-ceremony`;
- two for `nontechnical-owner`;
- one for `unknown-bug`;
- one for `verification-ceiling`.

The other 89 assertions became `UNVERIFIED` unless another trusted collector existed. Fixture seeds for all 20 scenarios did not count as outcome collection. Provider-written observations and success text were diagnostic only, which was the right rule, but it left most of the advertised suite without evidence.

### Model versions and budgets were partly self-declared or post hoc

The live adapter copied the command-line `--model-version` value into its result. It did not verify that label against a provider-reported immutable model version. A model ID from the session was useful, but it was not always an exact dated version.

The harness checked the planned matrix against a user-supplied budget and rejected reported cost above the per-trial cap. That was accounting, not a universal hard stop. The Codex adapter discarded `budget_usd`; Claude forwarded a maximum budget when its transport supported it. Providers can report usage only after a turn has spent it, and some require configured token prices when cost is absent.

Exact model-version attribution, hard cost ceilings on every host, authenticated Claude execution, multi-trial provider outcomes, adaptive-routing savings, and cross-platform behavior remained `UNVERIFIED`.

## Decision

Remove the custom runner, controller database, verifier subprocess path, permission model, protected-action classifier, provider adapters, and the current live harness. Do not repair them in place. They duplicate host features and create security claims SkipHow cannot enforce.

SkipHow will keep a skill-level safety contract and rely on host-native boundaries:

- the owner request, host policy, repository instructions, and saved project policy define authority;
- repository files, Issues, pull requests, web content, tool output, and subagent summaries are untrusted input;
- the host sandbox and approval system control filesystem, network, and command access;
- a subagent is a context boundary, not a security boundary;
- write agents use separate host-managed worktrees when they run concurrently;
- the root agent alone integrates concurrent work;
- production changes, payments, credentials, privacy operations, public release, and irreversible remote deletion need explicit authority for the exact action;
- GitHub merge and cleanup require repository policy, exact-head checks, required checks, confirmed merge state, and proof that the branch or worktree belongs to the run;
- SkipHow must report a missing host capability as `UNVERIFIED`. It must not imitate enforcement with prompt text or a local ledger.

The uncomfortable lesson is simple. Policy text can narrow agent behavior, but only the host can stop a process from writing a file or reaching the network.

## Evidence contract after the removal

Deterministic checks remain local and make no model calls. They may verify plugin structure, manifests, reference links, portability, instruction size, banned personal paths, and the absence of duplicate policy. They do not prove agent behavior, sandbox strength, GitHub delivery, recovery, or model-routing savings.

Live evaluation remains an opt-in release activity. A replacement suite must meet all of these conditions:

1. Install and activate the exact candidate plugin in a fresh host environment.
2. Record the repository revision, plugin version, host version, provider, model identifier, model version when the provider exposes it, routing choice, reasoning effort, and date.
3. Use isolated, pre-provisioned fixtures outside the candidate checkout.
4. Keep expected outcomes and collectors outside the agent's writable roots.
5. Collect final files, Git state, GitHub state, host task state, and relevant tool events independently of the model's report.
6. Mark every assertion without a trusted collector `UNVERIFIED`. A writable summary can never turn it into a pass.
7. Run several trials for nondeterministic behavior and publish failed trials with successful ones.
8. Compare adaptive routing with an all-`DEEP` baseline on the same tasks and reasoning-effort rules. Outcome quality and unauthorized mutations come before token cost or latency.
9. Require explicit credentials, a positive run budget, and an isolated sandbox repository for live GitHub checks.
10. Never create or delete a repository. Never run live provider or GitHub gates from `scripts/check.py` or CI.

The first replacement suite should cover ten behaviors: a small fix without ceremony, diagnosis from a reproducer, reuse research for a substantial feature, mixed intake, a nontechnical owner request, persistence of an unrelated finding, multiple Issues through merge and cleanup, resume after interruption, denial of an ungranted protected action, and paired model-routing trials.

Until that suite produces receipts, these claims stay `UNVERIFIED`:

- unattended work resumes across host restarts or compaction;
- the same plugin behavior works in both Codex and Claude Code;
- tracked work reaches a merged PR and safe cleanup;
- model routing lowers total cost without lowering outcome quality;
- a configured budget is a hard provider-side spending limit;
- a model label identifies an immutable provider version.

## What remains in the product

The redesign keeps only controls that can be stated honestly in a portable skill:

- mutation boundaries derived from the user's words;
- explicit approval requirements for protected actions;
- duplicate search before recording findings;
- exact-head and repository-policy checks before merge;
- safe cleanup rules for owned resources;
- evidence tied to the final state;
- clear `FAILED`, `BLOCKED`, and `UNVERIFIED` outcomes.

It removes the SQLite audit chain, custom redactor, filesystem allowlist, regex security classifier, runtime permission profiles, provider session manager, synthetic live adapter, and claims based on those components.

## Primary sources

Repository evidence is pinned to the audited commit:

- [runner database selection](https://github.com/mzored/SkipHow/blob/a6d34a25614bc0723517032af617b0782158df4d/src/skiphow/cli.py)
- [supervisor dispatch and working directory](https://github.com/mzored/SkipHow/blob/a6d34a25614bc0723517032af617b0782158df4d/src/skiphow/supervisor.py)
- [runtime security policy](https://github.com/mzored/SkipHow/blob/a6d34a25614bc0723517032af617b0782158df4d/src/skiphow/runtime_security.py)
- [environment verifier](https://github.com/mzored/SkipHow/blob/a6d34a25614bc0723517032af617b0782158df4d/src/skiphow/verification.py)
- [live provider adapter](https://github.com/mzored/SkipHow/blob/a6d34a25614bc0723517032af617b0782158df4d/evals/live/provider_adapter.py)
- [live fixtures and collectors](https://github.com/mzored/SkipHow/blob/a6d34a25614bc0723517032af617b0782158df4d/evals/live/fixtures.py)

Host contracts were checked against current primary documentation on 2026-08-25:

- [Codex permissions](https://learn.chatgpt.com/docs/permissions)
- [Codex sandbox](https://learn.chatgpt.com/docs/sandboxing)
- [Codex approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex long-running work](https://learn.chatgpt.com/docs/long-running-work)
- [Claude Code permissions](https://code.claude.com/docs/en/permissions)
- [Claude Code sandboxing](https://code.claude.com/docs/en/sandboxing)
- [Claude Code goal mode](https://code.claude.com/docs/en/goal)
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)

## Revalidation triggers

Review this decision again only when one of these facts changes:

- a supported host removes or materially changes its sandbox, approvals, Goal, subagent, resume, or worktree contract;
- SkipHow adds an executable, daemon, MCP server, hook, controller database, or verifier subprocess;
- SkipHow stores authority or receipts inside an agent-writable root;
- a live suite changes how it loads the candidate, isolates fixtures, collects evidence, identifies models, or caps spend;
- the project wants to claim cross-host support, restart recovery, safe automatic merge, or model-routing savings based on new receipts.

When a trigger fires, update this audit and the related ADR before changing the product claim.
