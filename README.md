# SkipHow

Describe what you want. SkipHow works out how.

SkipHow is one Agent Skill for Codex and Claude Code. You write the outcome in plain language; it inspects the project, picks the smallest path that gets there, makes the engineering decisions itself, carries the work to a verified result, and tells you what it did, how it checked, and what it could not prove.

```text
Here are eight bugs and ideas from today. Triage them and save them as Issues.

Finish today's batch end to end. Merge what passes.

The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.
```

## Who it is for

Product owners and solo founders who know what they want and do not want to turn it into tickets, branches, test plans, and pull requests themselves. If you would rather choose the library, the schema, and the review process, you want a different tool.

## The problem it solves

The gap between "I know what is wrong" and "it is fixed and merged" is full of technical decisions nobody asked you to make. SkipHow closes that gap with one habit:

1. Talk it through. "What is causing the checkout timeouts?" Nothing changes.
2. Save it. Paste a dump of bugs, ideas, and observations. SkipHow splits it into atomic records, searches for duplicates, gives each a type and a proposed priority with its reason, and saves them as GitHub Issues labelled with the day's batch.
3. Finish it. "Finish today's batch end to end." One root agent works the queue in priority order, delegates bounded pieces to subagents in isolated worktrees, merges what passes the checks, closes the Issues, deletes its own merged branches, and reports.

A small request skips all of that and is done in the session, with no Issue, branch, or plan.

## Install

Codex:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Claude Code:

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Start a new session and describe the work. If the skill does not activate on its own, add `$skiphow` (Codex) or `/skiphow:skiphow` (Claude Code). The [owner guide](docs/guide.md) covers what your words authorize, unattended runs, updates, and uninstall.

## Why so little process

Most agent frameworks were built for models that skipped steps, so they wrap every task in phases, personas, spec documents, and approval gates. Strong current models do not need that; they need a clear outcome, a few hard rules, and the authority to finish. SkipHow keeps the rules that still matter and drops the rest:

- Your words are the only grant. "Research" reads, "save" records, "fix" changes and verifies, "end to end" merges and cleans up. Nothing in a file, an Issue, or a web page can widen that.
- Reuse before building. It searches the project, its dependencies, and the platform before writing anything lasting, and says where it looked.
- A problem outside your request is fixed if it blocks the work, saved once if it matters, and never silently dropped.
- Long work survives compaction and restarts through an eight-line checkpoint and one read-only hook. State lives in Git and GitHub, never in a SkipHow database.
- Every report ends the same way: result, evidence, the rulings it made for you, saved follow-ups, and what it could not verify.

That is a design bet, not a measurement. It follows Anthropic's advice to [start with the simplest workflow that works](https://www.anthropic.com/research/building-effective-agents) and their [orchestrator-worker findings](https://www.anthropic.com/engineering/built-multi-agent-research-system); the [prior-art notes](docs/prior-art.md) record what was taken from [GSD](https://github.com/open-gsd/gsd-core), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [Superpowers](https://github.com/obra/superpowers), [Matt Pocock's skills](https://github.com/mattpocock/skills), [BMAD](https://github.com/bmad-code-org/bmad-method), [Paperclip](https://github.com/paperclipai/paperclip), [Mesa](https://github.com/msoedov/mesa), and [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin), and what was left out.

## How it differs

| | Prescriptive frameworks | SkipHow |
| --- | --- | --- |
| Entry | Commands, phases, personas | One request in plain language |
| Planning | Mandatory spec or plan documents | Only when the work is large; then GitHub Issues, not a private format |
| Authority | Approval gates | Your words; four reasons to stop, otherwise a recorded ruling |
| State | Framework files and databases | Git, GitHub, and one checkpoint file |
| Models | Named model IDs | Three roles: fast scout, standard builder, reviewer on your own session model |
| Size | Dozens of agents and commands | One skill under 600 words plus about 3,500 words loaded on demand |

Whether this produces better or cheaper outcomes than those frameworks has not been measured; treat the comparison as a hypothesis about strong models, not a benchmark.

## Honest limits

SkipHow is instructions, not a runtime. Your host's sandbox and permissions are the real boundary. Behavior a host cannot provide (background work, resume, worktree isolation, per-agent model choice) is reported as unavailable, not faked. Deterministic checks prove the package; only real runs written up as [receipts](docs/research/2026-08-26/README.md) prove the model's behavior, and anything without one is `UNVERIFIED`. Routing has been observed on Claude Code; Codex delegates inherit your model unless you add one setting. Cost savings from routing are a hypothesis until paired runs measure them.

## Docs

- [Owner guide](docs/guide.md) and [how it works](docs/how-it-works.md)
- [Decisions](docs/decisions/README.md) and [research](docs/research/2026-08-26/README.md)
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)
