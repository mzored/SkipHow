# SkipHow

Describe what you want. SkipHow works out how.

SkipHow is one Agent Skill for Codex and Claude Code. You write the outcome in plain language. It picks the smallest path that gets there, makes the routine engineering decisions itself, tracks bigger work in GitHub, and reports what it did, how it checked, and what it could not prove.

```text
Here are eight bugs and ideas from today. Triage them and save them as Issues.

Finish today's batch end to end. Merge what passes.

The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.
```

No methodology to choose. No commands to chain. No technical questions back at you unless the answer changes the product.

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

Start a new session and describe the work. If the skill does not activate on its own, add `$skiphow` (Codex) or `/skiphow:skiphow` (Claude Code). The [owner guide](docs/guide.md) covers updates, unattended runs, and uninstall.

## Why this exists

I tried [GSD](https://github.com/open-gsd/gsd-core), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [Spec Kit](https://github.com/github/spec-kit), [Superpowers](https://github.com/obra/superpowers), [Matt Pocock's skills](https://github.com/mattpocock/skills), [BMAD](https://github.com/bmad-code-org/bmad-method), [Paperclip](https://github.com/paperclipai/paperclip), [Mesa](https://github.com/msoedov/mesa), and [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin). Each gets something right. Most were built for models that skipped steps, so they wrap every task in phases, personas, and approval gates. The rest assume you are an engineer who wants to make the technical calls.

I am a product owner. I want to say what is wrong or what to build, then let the work happen. SkipHow keeps the handful of rules that still matter with strong models and drops the ceremony. That is a design bet, not a measurement: Anthropic's own guidance is to [start with the simplest workflow that works](https://www.anthropic.com/research/building-effective-agents), and I have not seen the extra process pay for itself. The [prior-art notes](docs/prior-art.md) say what was taken from each project.

## How it works

Your words set the boundary. "Research" reads and reports. "Save" creates the records. "Fix" or "implement" changes the project and runs the checks. "Finish end to end" adds merge and cleanup for the named work. Production, payments, credentials, private data, releases, and repository settings always need you to say so.

A small request stays in the session with no Issue, branch, or plan unless your repository requires one. A large one becomes a queue of GitHub Issues that one root agent works through, delegating bounded pieces to subagents in isolated worktrees, re-reading Git and GitHub before every merge, and deleting only the branches it created and GitHub confirms merged.

Subagents get the model their job needs: a cheap read-only scout for search and inventory, a standard builder for implementation, the strongest reviewer for planning and independent review. Shared policy names only the roles. On Claude Code the plugin ships the three roles using the vendor's stable family aliases; on Codex, where plugins cannot ship agents, it tells you the one setting to add. This follows Anthropic's [orchestrator-worker pattern](https://www.anthropic.com/research/building-effective-agents) and their [multi-agent findings](https://www.anthropic.com/engineering/built-multi-agent-research-system), and it respects Superpowers' [caveat](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md) that a cheap model on an ambiguous task costs more in turns than it saves in tokens.

Long work survives compaction and restarts. The root writes an eight-line checkpoint at every item boundary; one read-only hook prints it back after the host compacts or resumes. State lives in Git and GitHub, never in a SkipHow database.

Before building anything lasting, SkipHow searches the project, its dependencies, and the platform for something that already does the job, and says where it looked. A problem it finds outside your request is fixed if it blocks the work, saved once as an Issue if it matters, and named in the report either way.

Every report ends the same way: result, evidence, the rulings it made on your behalf, the follow-ups it saved, and what it could not verify.

## Honest limits

SkipHow is instructions, not a runtime. Your host's sandbox and permissions are the real boundary. Behavior a host cannot provide (background work, resume, worktree isolation, per-agent model choice) is reported as unavailable, not faked. Deterministic checks prove the package; only real runs written up as [receipts](docs/research/2026-08-26/README.md) prove the model's behavior, and anything without one is `UNVERIFIED`. Cost savings from routing are a design hypothesis until paired runs measure them.

## Docs

- [Owner guide](docs/guide.md) and [how it works](docs/how-it-works.md)
- [Decisions](docs/decisions/README.md) and [research](docs/research/2026-08-26/README.md)
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)
