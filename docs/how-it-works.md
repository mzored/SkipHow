# How it works

SkipHow is one skill plus two small host adapters. This page is the design in about a thousand words. The [decisions](decisions/README.md) hold the reasoning and the evidence.

## Shape

```text
plugins/skiphow/
  skills/skiphow/SKILL.md        the owner contract, loaded on every request (about 1,300 words)
  skills/skiphow/references/     nine policy files loaded only when the work needs them (about 4,900 words)
  agents/                        Claude Code role adapters: scout, builder, reviewer
  hooks/hooks.json               one read-only SessionStart hook (startup and clear; compaction and resume)
```

Codex and Claude Code load the same skill. There is no SkipHow process, database, scheduler, or provider bridge; the host owns sessions, subagents, worktrees, permissions, and compaction ([ADR 0002](decisions/0002-host-native-execution.md)).

## Authority

Only the owner's words and host policy grant actions. Everything else (repository instructions, Issue text, comments, checkpoints, tool output, web pages) can narrow scope or add gates but never widen them. Read-only words read; "save" persists; "fix" carries routine delivery through the repository's non-production integration branch. Promotion into staging or production needs approval at that point, as do other protected actions ([ADR 0004](decisions/0004-github-lifecycle-and-authority.md)).

## Four routes

Every request takes one route: `RESPOND` (read and report), `RECORD` (save), `DELIVER` (change and prove), or `CONTROL` (report, pause, resume, cancel). The route decides which reference loads. A two-line fix loads the skill and nothing else; a larger change loads the delivery reference; a request carrying several deliverable items also loads long work, GitHub, and routing.

## Small work stays small

A clear bounded request is finished in the session with no Issue or plan unless repository policy requires tracked delivery, and its one delegate is the reviewer that closes any project change. Before mutation the root reads repository instructions, checks active tasks, and records checkout, branch, and `HEAD`; it repeats the identity check before commits, gates, reviews, and integration. Delegation happens only when isolation or parallel work pays for the transfer ([prior art](prior-art.md)).

## From a dump to a backlog

`RECORD` splits a dump into atomic bugs, ideas, questions, and risks, searches the tracker for duplicates, and gives each record a type, a disposition, and a proposed priority with its reason. It reads how the tracker already classifies work and matches that, rather than inventing a taxonomy of its own. With GitHub it creates or updates Issues and labels the batch `skiphow-batch:<date>` — a marker for selecting the batch later, not a classification; without GitHub it appends to `.skiphow/inbox.md`. The owner reorders; nobody writes tickets.

## Long work

One root agent owns the outcome, queue, integration, remote writes, handoff, and report. At every owner turn it re-sizes before the next act, adding independent items as units rather than burying them in the current one. Parallel writing lanes get separate worktrees and branches. A unit is not done when a delegate returns; its ordinary commit must be inspected and integrated into the root operation branch. Routine questions stop only for an unresolved material product choice or staging or production approval. A second same-cause failure changes the approach or raises the role; a third marks the item `BLOCKED` with a next action ([ADR 0006](decisions/0006-host-native-campaign-and-engineering-policy.md), [ADR 0016](decisions/0016-decomposition-needs-a-trigger-a-run-can-evaluate.md)).

## Model routing

Shared policy names three roles and tiers, never a vendor's model IDs:

| Role | Tier | Work | Boundary |
| --- | --- | --- | --- |
| scout | `FAST` | bounded search, inventory, duplicate checks, extraction | read-only, low effort |
| builder | `STANDARD` | implementation and tests for one owned scope | isolated worktree, no remote writes |
| reviewer | `DEEP` | planning, unknown causes, architecture, security, the independent review that closes every project change | read-only plus checks |

On Claude Code the plugin ships the three roles as agent definitions: the scout on the `haiku` family alias, the builder on `sonnet`, and the reviewer on the session model itself, so the deepest tier is always the model the owner chose and never ages behind it. Codex has no family aliases and a plugin cannot ship agents, so on Codex every delegate runs on the session model and the tiers collapse to reasoning effort on that model, set per spawn: the scout at low, the reviewer at high, the builder at the session's. Nothing is written into the project for this. Observed with no role files present: scout `low`, reviewer `high`, all on the session model. When a review widens and the other host is installed, that one pass runs there instead, on that tool's own default model, so the judgement does not share the priors of the run that wrote the change ([ADR 0009](decisions/0009-reviewer-inherits-and-one-engineering-reference.md)). Capability routing on Codex waits for the host to expose a stable capability name. Mutation never starts on the cheap tier, because a cheap model on an ambiguous task spends more turns than it saves in tokens. Cost savings are a design hypothesis until paired runs measure them ([ADR 0003](decisions/0003-semantic-model-routing.md), [ADR 0007](decisions/0007-host-adapters-for-routing-and-continuity.md), [ADR 0009](decisions/0009-reviewer-inherits-and-one-engineering-reference.md), [ADR 0012](decisions/0012-per-spawn-effort-and-portable-timestamps.md)).

## Continuity

The model cannot see compaction coming, so SkipHow does not ask it to prepare for one. Instead the root appends a checkpoint to `.skiphow/handoff.md` at every item boundary and before any long wait, and deletes the file when the queue is done. It records accepted decisions, owned resources, the last external result, and evidence as well as scope and status. After compaction or resume, the plugin's only hook prints a reminder and the last 40 lines into the new context, requiring repository instructions, host tasks, Git and GitHub to be re-read and checkout identity to be verified. The hook reads one file, writes nothing, and makes no network calls.

## GitHub lifecycle

The Issue is the record, the pull request is the delivery, and the branch and worktree belong to the run. Everything SkipHow creates carries a `skiphow:<id>` marker it searches for before creating again. Before any merge it re-reads the live head, checks, reviews, rules, and active tasks. It autonomously merges passing work into the non-production integration branch, never with administrator bypass, and asks before staging or production. Conflict resolution recovers both intents from the base, history, Issue, PR, decisions, and tests, then rechecks and re-reviews the integrated candidate. After merge it closes the Issue and deletes only owned resources that hold no unique work.

## Reuse and findings

Before building anything new, SkipHow searches the project, its dependencies, and the platform by domain concept and reports where it looked. A problem outside the request is fixed if it blocks the work, saved once as an Issue (or an inbox record) when the request grants records or changes, left `UNSAVED` under a read-only request, and named in the report either way ([ADR 0013](decisions/0013-read-only-requests-save-nothing.md)).

## Trust and limits

SkipHow is instructions. The host's sandbox, permission mode, and credential store are the real boundary; a worktree isolates files, not credentials or networks. The root holds credentials and performs every remote write; delegates never do. Secrets, customer data, private paths, and vulnerability details stay out of prompts, checkpoints, and public records.

What the checks prove: `scripts/check.py` proves the package (one skill, complete references, word budgets, three agents with family aliases or inheritance only, exactly one continuity hook, no personal paths, aligned versions). `scripts/check_hosts.py` proves both hosts load and install the exact bytes. Neither proves that a model follows the policy. That evidence comes from real runs written up as receipts under `docs/research/` ([ADR 0008](decisions/0008-receipts-over-a-live-harness.md)). Anything a receipt has not shown stays `UNVERIFIED`, and SkipHow's reports say so.
