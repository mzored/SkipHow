# Prior-art mechanics research

## Record

- Reviewed on 2026-08-26.
- Method: primary files (README, SKILL.md, agent definitions, hooks, CLAUDE.md) were fetched for GSD, OpenSpec, Superpowers, Matt Pocock's skills, BMAD, and Paperclip. For Spec Kit, Mesa, and Autonomous PM only the root README was read, so their findings are README-level.
- Purpose: the 2026-08-25 prior-art note recorded what to keep and leave out. This note records the concrete mechanics behind those choices so the next release can borrow them without re-reading nine repositories.

## Findings by concern

### Model routing

Superpowers has the most reasoned policy. Its subagent-driven-development skill says to use the least powerful model that can do each role: cheap for one- or two-file mechanical work, standard for multi-file judgment and debugging, strongest for architecture and final whole-branch review, and one tier up when a fix loop is stuck. Two details matter. The cheapest model often takes two or three times the turns and costs more in total, so turn count beats token price. And omitting the model field silently inherits the caller's tier, so a dispatch must always name one.

Paperclip shows the simplest mechanic: `.claude/agents/token-auditor.md` and `codemod-runner.md` set `model: sonnet` plus a `tools:` allowlist. Narrow mechanical agents get a middle tier and a small toolset; the orchestrator keeps the strong default.

GSD keeps a resolver table (`model-profiles.md`, `resolve-model <agent>` returning `opus|sonnet|haiku|inherit`) and gives each role card a tier. That is a config-driven variant of the same idea.

OpenSpec, Matt Pocock's skills, BMAD, and Spec Kit do not route models. Mesa routes by vendor CLI per agent, not by cost tier.

### Long work and compaction

Superpowers keeps a git-ignored `progress.md` ledger per plan and states the problem plainly: conversation memory does not survive compaction, and controllers that lost their place re-dispatched whole task sequences. Ledger plus `git log` outrank the model's memory. Dispatch prompts come from single-purpose brief files, never pasted history. Reports go to files, not into the controller's context. A fix loop stops after five rounds and requires a recorded ruling. Only four things justify stopping: an irreversible or destructive operation, a security-sensitive action, an external side effect such as push or merge, or a plan so broken that every path is a guess. Everything else gets a ledgered ruling and the work continues.

BMAD's `bmad-build-auto` is a single-iteration worker driven by an external loop. It stores `status` (`draft`, `ready-for-dev`, `in-progress`, `in-review`, `done`, `blocked`) in the spec's frontmatter, records `baseline_revision` before implementation, and enumerates a closed set of `blocked` reasons such as "review repair loop exceeded 5 iterations".

Paperclip's `pr-gardening` stores workflow state as HTML-comment markers on GitHub issue comments, limits itself to three rounds with a 48-hour cooldown, and re-reads the live head SHA on every pass because issue comments are not proof.

GSD runs dependency waves with a fresh context per executor, an `O_EXCL` lockfile around shared `STATE.md`, and a `WINDOWS.md` ledger of deferred defects that blocks shipping until resolved.

### GitHub tracking and cleanup

Matt Pocock's `wayfinder` maps a large effort as one GitHub issue with child tickets typed `research`, `prototype`, `grilling`, or `task`, each sized to about one session, claimed through the assignee field and blocked through GitHub's native issue-dependency API (the blocker must be the numeric database ID, not `#number`). `triage` moves issues through `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`, prefixes AI comments with a disclaimer, and separates "already implemented" closes from "rejected" closes.

Paperclip never gardens community PRs, dedupes follow-ups by searching open issues for the exact branch name, requires a typed confirmation before destructive cleanup, and never merges or closes a PR itself.

Superpowers' finishing skill offers exactly three endings after tests pass (merge locally, push and open a PR, keep the branch), removes only worktrees it created, and requires the literal word "discard" before discarding work.

Spec Kit's `/speckit.taskstoissues` turns a generated task list into GitHub issues. `/speckit.converge` diffs the implementation against the spec and appends gaps as new tasks.

### Reuse before building

Matt Pocock's triage step one searches for an existing implementation by domain concept rather than request wording, reports where it looked, and checks `.out-of-scope/*.md` before reopening a settled question. Superpowers searches open and closed PRs and stops when it finds a duplicate. Mesa promotes patterns that worked into a shared skills library. Nobody else treats reuse as a first-class step.

### Findings outside scope

BMAD's `deferred` frontmatter array (`summary`, `evidence`, optional `location` and `severity`) is explicitly "not a backlog"; the orchestrator decides. Superpowers ledgers minor findings and surfaces load-bearing decisions in a final "Rulings I made" section, because a roll-up nobody reads is a silent discard. Matt Pocock separates fog of war (unspecified but in scope), out of scope (ruled out, with a "revisit if" condition), and decisions so far. GSD's `.out-of-scope/` keeps one file per rejected proposal with the reopening criteria.

## What is worth borrowing

1. Name the model for every dispatch. Never inherit by omission. (Superpowers, Paperclip)
2. Cheap tier only for narrow work with a direct check; count turns, not tokens. (Superpowers)
3. A ledger file that survives compaction, written at boundaries, read back before acting. (Superpowers, BMAD)
4. Brief files for dispatch; summaries back, never transcripts. (Superpowers, Anthropic)
5. Four reasons to stop; otherwise record a ruling and continue. (Superpowers)
6. A closed set of blocked reasons and a hard cap on repair loops. (BMAD, Superpowers)
7. Native GitHub sub-issues and dependencies instead of labels as a workflow engine. (Matt Pocock)
8. Search by domain concept before building; report where you looked. (Matt Pocock, Superpowers)
9. Deferred findings with evidence, routed to the owner, never self-actioned. (BMAD)
10. "Rulings I made" in the final report. (Superpowers)
11. Re-read live state before every protected action; comments are not proof. (Paperclip)

## What is bloat for strong models

Persona theatre (BMAD's five named agents, Mesa's 21 archetypes, Autonomous PM's 17 roles), four-phase document pipelines for every change, 34-agent and 71-command rosters (GSD), embedded decision-tree diagrams and anti-rationalization tables in every skill (Superpowers), relentless interview ceremony before any work (Matt Pocock's grilling), and control-plane platforms with budgets and org charts (Paperclip, Mesa). All of these compensate for models that skip steps or lose scope. A capable model with a clear owner outcome and a short set of hard rules does not need them.

SkipHow already leaves those out. The gap is the opposite one: SkipHow's own references have grown as dense as the frameworks it rejects. See the [system review](system-review.md).

## Files read

GSD: README, `agents/gsd-executor.md`, `agents/gsd-planner.md`, `commands/gsd/execute-phase.md`, `commands/gsd/ship.md`, `commands/gsd/cleanup.md`, `docs/ARCHITECTURE.md`, `docs/AGENTS.md`, `CONTEXT.md`, `.out-of-scope/general-purpose-agent-prompt-skills.md`.
OpenSpec: README, `skills/openspec-propose/SKILL.md`, `skills/openspec-apply-change/SKILL.md`, `skills/openspec-archive-change/SKILL.md`, `docs/agent-contract.md`, `docs/workflows.md`, `docs/team-workflow.md` (partial).
Superpowers: README, `CLAUDE.md`, `hooks/hooks.json`, `skills/dispatching-parallel-agents/SKILL.md`, `skills/subagent-driven-development/SKILL.md`, `skills/using-superpowers/SKILL.md`, `skills/finishing-a-development-branch/SKILL.md`, `skills/writing-plans/SKILL.md` (partial).
Matt Pocock's skills: README, `AGENTS.md`, `CLAUDE.md`, `skills/engineering/wayfinder/SKILL.md`, `skills/productivity/handoff/SKILL.md`, `skills/engineering/triage/SKILL.md`, `skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md`, `skills/engineering/code-review/SKILL.md`, `skills/misc/git-guardrails-claude-code/`, `skills/engineering/research/SKILL.md`.
BMAD: README, `AGENTS.md`, `docs/reference/agents.md`, `docs/reference/workflow-map.md`, `docs/reference/build-auto.md`, `src/bmm-skills/agents/bmad-agent-dev/customize.toml`.
Paperclip: README, `AGENTS.md` (partial), `.claude/agents/codemod-runner.md`, `.claude/agents/token-auditor.md`, `.agents/skills/pr-gardening/SKILL.md`, `.agents/skills/diagnose-why-work-stopped/SKILL.md`, `.agents/skills/garden-inbox/SKILL.md`, `.agents/skills/prepare-paperclip-pr/SKILL.md` (partial).
Spec Kit, Mesa, Autonomous PM: root README only.
