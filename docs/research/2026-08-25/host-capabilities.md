# Host capability research

## Review record

- Reviewed on 2026-08-25.
- Repository commit: `a6d34a25614bc0723517032af617b0782158df4d`.
- Local versions inspected: Codex CLI `0.149.1` and Claude Code `2.1.240`.
- Sources: current OpenAI and Anthropic product documentation, fetched on the review date.
- Scope: goals, subagents, worktrees, progress controls, session resume, and compaction.

The local version check confirms that both commands were installed. It does not prove every documented UI or account feature was available to this session.

## Verification record

The following non-mutating checks ran on 2026-08-25 in a worktree at repository commit `b679bbb923bce1865fa9b130d74d811e55187ba9`:

```bash
codex --version
codex features list | rg '^(goals|multi_agent|plugins|remote_compaction_v2)\s'
codex --help | rg '^  (features|resume|fork|mcp|app|exec)\b'
claude --version
claude --help | rg -- '--(continue|resume|worktree|agent|plugin-dir)\b'
```

Observed results:

- `codex --version` returned `codex-cli 0.149.1`.
- The local Codex feature registry returned `stable true` for `goals`, `multi_agent`, `plugins`, and `remote_compaction_v2`.
- Codex help listed the `resume`, `fork`, and `features` commands.
- `claude --version` returned `2.1.240 (Claude Code)`.
- Claude help listed `--agent`, `--continue`, `--resume`, `--worktree`, and `--plugin-dir`.

These checks read local command metadata. They did not start a model session. Goal execution, subagent delegation, worktree isolation, compaction, restart recovery, account entitlements, and UI controls remain `UNVERIFIED` by this record.

Use the same commands after a host upgrade. Also rerun the package checks and the opt-in live scenarios before changing a support claim.

## Decision

SkipHow uses the host's execution features. It does not implement its own scheduler, worker protocol, provider transport, session store, context monitor, or task database.

For a bounded task, SkipHow stays in the current session. For several independent investigations, it may use subagents. For concurrent writes, it must use separate worktrees. For substantial work with a testable end condition, it should use the host's goal or background-task facility when available.

Git, GitHub, and the host task hold recoverable state. If a host lacks a required facility, SkipHow completes a safe bounded portion, writes a handoff to the canonical tracker, and marks the missing behavior `UNVERIFIED`. It must not pretend that a foreground loop is durable.

## Codex facts

### Goal mode

[OpenAI's long-running work guide](https://learn.chatgpt.com/docs/long-running-work) documents `/goal` in the ChatGPT desktop app, Codex CLI, and Codex IDE extension.

- The goal text is both the first prompt and the completion criterion.
- A useful goal names the outcome, constraints, and verification.
- The desktop progress row can pause, resume, edit, or clear a goal.
- The same chat can accept status questions and new constraints while work continues.
- Goal mode keeps the current sandbox and approval policy. It pauses when it needs a decision.
- Each chat has its own goal and context. OpenAI warns against two chats changing the same files.

The guide confirms resuming a paused goal in the active product experience. It does not state that Codex CLI restores an active goal after the process exits and later restarts. Cross-process goal restoration is therefore `UNVERIFIED`.

### Subagents

[OpenAI's subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents) says current Codex releases enable subagent workflows by default.

- Codex can delegate after a direct request or an applicable project or skill instruction.
- Subagents run in separate agent threads. Supported clients expose their status and results.
- Codex can steer, stop, or close agent threads.
- Custom agents can select a model and reasoning effort. Without an override, the subagent inherits both from its parent.
- Subagents inherit the active permission and sandbox policy unless a custom agent narrows its sandbox.
- OpenAI recommends parallel agents first for read-heavy exploration, tests, triage, and summarization. It warns that parallel writes add conflicts and coordination cost.
- Each subagent performs its own model and tool work, so parallel use can consume more tokens than one agent.

The documented orchestration includes spawn, follow-up routing, waiting, and thread closure. It does not promise that every client persists a live subagent across an application restart. That behavior is `UNVERIFIED` until a live host test proves it.

### Worktrees

[OpenAI's worktree guide](https://learn.chatgpt.com/docs/environments/git-worktrees) documents managed worktrees in the ChatGPT desktop app.

- Each worktree gives a chat a separate checkout. This permits parallel work without sharing modified files.
- A managed worktree starts in detached `HEAD` state. The user or agent can create a branch, commit, push, and open a pull request.
- Handoff moves a chat and its code between a worktree and the local checkout.
- A chat returns to its associated worktree when handed back later.
- Managed worktrees copy only tracked files and ignored files named in `.worktreeinclude`.
- Worktrees require Git.

The current source describes the desktop product. Host-managed worktree creation from Codex CLI or the IDE is `UNVERIFIED`. SkipHow may still use ordinary Git worktrees there when project policy and permissions allow it, but it must not call that a Codex-managed capability.

### Codex limits

- Account level and client version can affect subagent UI and available models.
- Goal mode does not widen permissions.
- Worktrees isolate files, not remote systems, credentials, databases, or deployment targets.
- A goal does not itself prove completion. Repository checks and exact final-state inspection remain necessary.
- Restart recovery for active goals and live subagents remains `UNVERIFIED` in the reviewed official sources.

## Claude Code facts

### Goal mode

[Anthropic's Goal mode guide](https://code.claude.com/docs/en/goal) documents `/goal` as a session-scoped completion loop.

- One goal can be active per session.
- A separate small, fast evaluator checks the condition after each turn.
- The evaluator reads evidence that Claude surfaced in the conversation. It does not run commands or inspect files itself.
- `/goal` reports the condition, elapsed time, evaluated turns, token spend, and latest evaluator reason.
- Goal mode does not change permission mode. Auto mode and Goal mode solve different problems.
- An active goal is restored through `--continue`, `--resume`, and the session picker.
- On resume, Claude keeps the condition but resets the timer, turn count, and token-spend baseline.
- A cleared or completed goal is not restored.

This is stronger restart documentation than the reviewed Codex source. It still depends on resuming the same stored Claude session.

### Sessions and compaction

[Anthropic's session guide](https://code.claude.com/docs/en/sessions) documents stored local conversations and resume.

- Standard settings files are read again when Claude resumes.
- Some launch-only settings must be passed again, including `--plugin-dir`, `--mcp-config`, `--settings`, `--fallback-model`, and directories supplied through `--add-dir`.
- Large inactive sessions may offer resume from summary. That option compacts the conversation before further work.
- A resumed goal keeps its condition but resets its counters.

SkipHow must reconstruct the active issue, branch, checks, and authority from GitHub and Git after resume. A transcript summary is helpful context, but it is not the source of truth.

### Subagents

[Anthropic's subagent guide](https://code.claude.com/docs/en/sub-agents) documents automatic and explicit delegation.

- A subagent starts with a fresh context unless it is a fork of the current conversation.
- A custom subagent can use a model alias, a full model ID, or `inherit`. Omission defaults to `inherit`.
- The host resolves allowlisted model substitutions. SkipHow should request a semantic role and avoid pinning a long-lived shared policy to a model ID.
- Subagents can run in the foreground or background.
- A named subagent can receive follow-up work and resume after completion.
- Subagent transcripts persist separately from main-conversation compaction.
- A subagent can resume after restarting Claude Code when the same main session is resumed.
- Current Claude Code supports nested delegation with host limits. SkipHow does not need nested delegation by default.
- Parallel agents multiply token use.

### Worktrees

[Anthropic's worktree guide](https://code.claude.com/docs/en/worktrees) documents three native paths.

- `claude --worktree <name>` starts a session in a separate Git worktree.
- `EnterWorktree` moves the current session into a managed worktree.
- A custom subagent can set `isolation: worktree`.

Claude Code blocks supported edit and shell operations that resolve back to the main checkout from an isolated worktree. It removes an unchanged temporary subagent worktree. A worktree with changes stays until cleanup can remove it without losing work. The cleanup sweep skips changed files, untracked files, and unpushed commits.

Worktree isolation does not isolate external services. Parallel agents must still avoid sharing a mutable database, deployment, issue, or branch unless the task has an explicit coordination rule.

### Claude limits

- Goal evaluation relies on evidence in the transcript. A vague condition can produce a bad stop decision.
- Resume works only when the relevant stored session remains available.
- Launch-only plugin and directory flags may need to be supplied again.
- Agent teams and some background interfaces have separate maturity and account constraints. SkipHow must not require them for its normal path.
- Host cleanup preserves changed worktrees, so SkipHow still has to merge or report them. It cannot assume every finished agent leaves no local state.

## Capability matrix

| Capability | Codex reviewed state | Claude Code reviewed state | SkipHow behavior |
| --- | --- | --- | --- |
| Natural skill selection | Documented | Documented | Prefer normal language |
| Explicit skill selection | `$skiphow` | `/skiphow:skiphow` | Document as a fallback |
| Goal loop | Documented in desktop, CLI, and IDE | Documented | Use for verifiable long work |
| Status | Documented | Documented | Map natural-language status requests |
| Pause with preserved goal state | Documented in product | `UNVERIFIED` | Use only after a capability check |
| Goal restoration after process restart | `UNVERIFIED` | Documented for resumed session | Check capability before promising recovery |
| Parallel subagents | Documented | Documented | Prefer independent read-heavy work |
| Per-subagent model choice | Documented | Documented | Resolve semantic tiers in the host |
| Subagent resume after process restart | `UNVERIFIED` | Documented for resumed session | Persist work state outside transcripts |
| Managed write isolation | Desktop worktrees documented | CLI, desktop, and subagent worktrees documented | Require worktrees for parallel writes |
| Permission expansion through a goal | Not supported | Not supported | Stop for missing authority |

## Product rules derived from the facts

- Keep one root agent responsible for owner intent, authority, integration, and the final report.
- Use no subagent for a short task that already fits the current context.
- Use parallel subagents for independent searches, repository inventory, log analysis, tests, and focused review.
- Use separate worktrees for concurrent writes. If worktrees are unavailable, serialize writes.
- Keep mutable work with one agent until a verification boundary. Do not hand the same half-finished edit among models to chase a lower token price.
- At every issue boundary, update the canonical tracker and record the exact branch or pull request. This makes compaction and resume recoverable.
- After resume, re-read permissions, the active goal, Git status, issue state, pull request head, and required checks before changing anything.
- If the host cannot restore work, write `.skiphow/handoff.md` or a tracker comment and report the limitation. Do not add a SkipHow daemon.

## Rejected alternatives

- A custom runner around both providers. It would duplicate goals, subagent control, worktrees, sessions, and permission handling.
- A SkipHow SQLite queue as a second source of truth. It can drift from GitHub and can sit inside a worker's write scope.
- Parallel writes in one checkout. Both vendors warn about conflicts or provide worktrees to prevent them.
- Assuming that Goal mode grants unattended authority. Both vendors keep existing permission boundaries.
- Treating compaction as durable task state. Compaction preserves a summary, not the exact current GitHub or Git state.
- Requiring experimental agent teams. Subagents and isolated sessions cover the initial product without that dependency.

## Unverified items

- `UNVERIFIED`: Codex restores an active CLI goal after a full process restart.
- `UNVERIFIED`: Codex restores running or completed subagent threads after a full process restart in every client.
- `UNVERIFIED`: Codex CLI and IDE expose the same managed worktree behavior as the desktop app.
- `UNVERIFIED`: either host can finish the SkipHow multi-Issue scenario without user steering.
- `UNVERIFIED`: model selection requested by semantic tier maps to a suitable current model on every account.
- `UNVERIFIED`: package installation restores all required skill references after host resume.
- `UNVERIFIED`: compaction preserves every product decision needed for an unattended run.

Run opt-in live checks against the exact packaged candidate before making support claims. A missing host, account feature, credential, or receipt stays `UNVERIFIED`.

## Revalidation triggers

Review this note again when any of these events occurs:

- Codex or Claude changes Goal mode, session resume, compaction, subagent, or worktree documentation.
- A supported host release changes explicit skill syntax or plugin loading.
- Project tests add a new long-running or parallel-write scenario.
- A live run loses authority, issue identity, branch identity, or verification state after resume.
- A host adds a stable durable task API that can replace tracker handoffs.
- A host removes or narrows a capability listed as documented here.

## Primary sources

- [OpenAI, Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- [OpenAI, Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [OpenAI, Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)
- [OpenAI, Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Anthropic, Keep Claude working toward a goal](https://code.claude.com/docs/en/goal)
- [Anthropic, Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Anthropic, Run parallel sessions with worktrees](https://code.claude.com/docs/en/worktrees)
- [Anthropic, Manage sessions](https://code.claude.com/docs/en/sessions)
