# Repository audit

Verified on 2026-08-25 at commit
[`a6d34a25614bc0723517032af617b0782158df4d`](https://github.com/mzored/SkipHow/commit/a6d34a25614bc0723517032af617b0782158df4d).
The checked branch was `codex/issue-14-research` and the worktree was clean before this document was added.

This audit records what the repository proved at that commit. It also records what the code did not prove. That distinction matters here. The runner has a large deterministic test suite, but its main product promise is autonomous delivery across several Issues. Those are different claims.

## Verified facts

### Repository size and growth

The selected product, plugin, script, test, and evaluation files contained 25,821 lines. The count covered Python, Markdown, JSON, TOML, and YAML files under `src`, `plugins`, `scripts`, `tests`, and `evals`.

- `src/skiphow` contained 8,599 lines of Python.
- `tests` contained 6,949 lines of Python.
- `plugins/skiphow/skills/skiphow` contained 2,065 lines across all files.
- The change from tag `v0.6.0` to the audited commit touched 168 files, with 27,614 insertions and 1,483 deletions.

These counts do not prove that the code is wrong. They show that most of the recent work went into a custom runtime and its policy, tests, and packaging. That is a lot to own for an optional path that still needs manual supervision.

### Deterministic checks

The focused repository test command passed:

```text
338 passed in 7.30s
```

The tests cover store transitions, leases, recovery, routing, adapters, verification, GitHub reconciliation, packaging rules, and evaluation plumbing. They prove those local contracts at the audited commit. They do not prove that SkipHow can take a live backlog through implementation, pull requests, CI, merge, and cleanup.

### Runner behavior

The runner is a foreground command. The documented flow asks the operator to run `skiphow start`, retain the run ID, then invoke `skiphow execute`. A reboot does not restart the process. The repository says so in `README.md`, `docs/architecture.md`, and `docs/operations.md`.

The supervisor works in one project checkout. `CampaignSupervisor._execute_claims` serializes claims when writers share that checkout. The code has provider session fork methods, but the supervisor does not call them. It does not create host subagents or assign mutable tasks to host-managed worktrees.

GitHub delivery is another CLI branch named `github-deliver`. The supervisor does not advance that coordinator as part of its run loop. The user or another process must invoke the delivery command with one completed task and its GitHub authority.

The result is narrower than the intended overnight workflow. The runner can persist and resume its own tasks, but it does not autonomously coordinate several Issues through separate worktrees, integration, GitHub waits, merge, and cleanup.

### Security boundaries

`src/skiphow/cli.py` requires the runner database to remain inside the project. Its default path is under `.skiphow`. The same CLI starts a write-capable provider with the project root as its working directory.

This puts controller authority, checkpoints, findings, and audit records inside the worker's writable project tree. The runtime policy checks intent before dispatch, but the filesystem boundary does not keep the authority database outside worker reach.

`src/skiphow/verification.py` fingerprints the selected executable and declared trusted artifacts. It then runs the verification command with `subprocess.Popen` from the repository root. It does not start a separate operating-system sandbox for that command. The fingerprints also do not cover every indirect import, test plugin, or configuration file that the command may load from the repository.

This creates a trust gap. A worker may be unable to forge the named executable yet still influence code that the verifier loads. The audit did not build an exploit, so exploitability remains unverified. The boundary itself is present in the code.

### Live evaluation limits

The live provider adapter starts Codex or Claude in the generated fixture workspace. It does not install or activate the candidate SkipHow plugin before the trial. Candidate revision fields in a receipt therefore identify the repository used to launch the evaluation. They do not prove that the model followed that candidate's skill.

The registry has 20 scenarios and 95 grading rules. Concrete fixture setup and collection exist for four scenarios:

- `simple-anti-ceremony`
- `nontechnical-owner`
- `unknown-bug`
- `verification-ceiling`

Those collectors emit six independent observations in total. The remaining rules stay `UNVERIFIED`, as `docs/evals.md` already states. The harness correctly refuses to turn unsupported rules into passes, but it cannot support broad behavioral claims yet.

### GitHub lifecycle record

[Issue #5](https://github.com/mzored/SkipHow/issues/5) and [Issue #6](https://github.com/mzored/SkipHow/issues/6) had the same title, "Narrow GitHub lifecycle ownership." Issue #6 was completed through [PR #7](https://github.com/mzored/SkipHow/pull/7), while #5 remained open after that work.

Issue #5 is now closed. On 2026-08-25 it received a duplicate note that links #6 and PR #7. The stale record no longer needs cleanup, but it is useful evidence. The existing lifecycle machinery did not prevent or reconcile this duplicate without a separate audit.

## Conclusions

The custom runner is tested better than many early systems. That is real work, and throwing it away is not a trivial choice. Still, it solves the wrong boundary for the product now being built.

Codex and Claude already own sessions, context management, subagents, model selection, permissions, and worktree execution. Rebuilding part of that stack gives SkipHow more state to secure and migrate while leaving the actual multi-Issue workflow split across manual commands.

The repository should keep one owner-facing skill and let the host execute bounded and long-running work. Git, GitHub, and the host task remain the sources of truth. SkipHow should define intent, authority, evidence, finding disposition, model tiers, and delivery rules. It should not own another scheduler, provider transport, task database, or model catalog.

Deleting the runner also removes the two security boundaries described above. This is preferable to adding more policy around an authority database and verifier that share a writable repository with the worker.

The evaluation code needs a smaller, stricter replacement. A live trial must load the exact candidate plugin, collect final state outside the agent's control, and leave unsupported outcomes as `UNVERIFIED`. Ten representative scenarios with complete collectors would say more than 20 manifests with six collected facts.

## Ideas adopted

- Keep one canonical `skiphow` skill and load detailed policy only when the request needs it.
- Use host-native goals, subagents, resume, permissions, and worktrees.
- Keep GitHub Issues, pull requests, Git, and host task state as the recovery record.
- Retain deterministic package and reference checks that still apply after the runner is removed.
- Keep exact-head verification, guarded merge, owned-resource cleanup, duplicate search, and truthful `UNVERIFIED` results as policy.
- Require live evaluations to install the exact candidate and grade final state with independent collectors.

## Ideas rejected

- Do not keep the Python and SQLite runner as a compatibility path.
- Do not keep custom Codex and Claude transports, provider session state, or a project-local authority database.
- Do not maintain a SkipHow model catalog or infer economic claims from provider metadata.
- Do not treat a foreground process as unattended or reboot-safe execution.
- Do not claim behavioral support from deterministic unit tests or from live prompts that did not load the candidate skill.
- Do not add more state machines to connect the current supervisor and the separate GitHub delivery command.

## Evidence commands

Run these commands from the audited checkout:

```bash
git rev-parse HEAD

find src/skiphow -type f -name '*.py' -print0 \
  | xargs -0 wc -l | tail -1

find tests -type f -name '*.py' -print0 \
  | xargs -0 wc -l | tail -1

find plugins/skiphow/skills/skiphow -type f -print0 \
  | xargs -0 wc -l | tail -1

find src plugins scripts tests evals -type f \
  \( -name '*.py' -o -name '*.md' -o -name '*.json' \
     -o -name '*.toml' -o -name '*.yaml' \) -print0 \
  | xargs -0 wc -l | tail -1

git diff --shortstat v0.6.0..HEAD

python scripts/check.py --pytest -q

rg -n "database must remain inside the project|runner.sqlite3" \
  src/skiphow/cli.py

rg -n "subprocess.Popen|cwd=self.root" src/skiphow/verification.py

rg -n "fork_session|asyncio.gather|github-deliver" src/skiphow

rg -n "simple-anti-ceremony|nontechnical-owner|unknown-bug|verification-ceiling" \
  evals/live/fixtures.py

gh issue view 5 --json number,state,closedAt,url,comments
gh issue view 6 --json number,state,closedAt,url
```

The line counts use `wc -l`. Generated files and extension choices can change the total, so future audits should run the same commands instead of comparing numbers produced by another counter.

## What remains unverified

- No authenticated Codex or Claude model run was part of this audit.
- No trial installed the candidate plugin and measured its behavior across several attempts.
- No live multi-Issue run completed implementation, pull requests, CI, merge, and cleanup.
- No real GitHub interruption and resume receipt was produced here.
- Host package installation was not rerun on Codex and Claude for this document.
- Linux and Windows behavior was not tested.
- The security review inspected trust boundaries. It did not demonstrate an exploit.
- Host-native goals may still have product gaps. Removing the runner does not prove that every host can resume after process or machine failure.
- The 338 passing tests apply only to commit `a6d34a2`. They do not transfer to the later, smaller architecture.

## Revalidation triggers

Repeat this audit when any of these conditions changes:

- A supported host removes or changes goals, subagents, resume, worktrees, or model selection.
- SkipHow adds another runtime, daemon, database, provider adapter, or background scheduler.
- The plugin gains a second policy copy or a host-specific workflow that can drift from the canonical skill.
- A release claims token or cost savings from semantic model routing.
- A release claims unattended multi-Issue delivery, recovery after interruption, or automatic GitHub cleanup.
- Verification starts running repository-controlled commands outside the host sandbox.
- A live evaluation changes how it installs the candidate, isolates fixtures, or collects evidence.
- The repository grows enough that the line counts no longer describe where maintenance work sits.

For current host behavior, consult the primary documentation before revising the architecture:

- [Codex long-running work](https://learn.chatgpt.com/docs/long-running-work)
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Claude goal mode](https://code.claude.com/docs/en/goal)
- [Claude subagents](https://code.claude.com/docs/en/sub-agents)

Provider documentation can change after this audit. A link is research input, not release evidence.
