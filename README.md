# SkipHow

Describe what you want. SkipHow works out how.

SkipHow is one Agent Skill for Codex and Claude Code. You write the outcome in plain language. It picks the smallest path that gets there, makes the routine engineering decisions itself, tracks bigger work in GitHub, and reports what it did, how it checked, and what it could not prove.

```text
Here are eight bugs and ideas from today. Triage them and save them as Issues.

Finish Issues #41, #44, and #48 end to end. Merge what passes.

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

Start a new session and describe the work. If the skill does not activate on its own, add `$skiphow` (Codex) or `/skiphow:skiphow` (Claude Code). The [getting started guide](docs/getting-started.md) covers updates, uninstall, and troubleshooting.

## Why this exists

I tried [GSD](https://github.com/open-gsd/gsd-core), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [Spec Kit](https://github.com/github/spec-kit), [Superpowers](https://github.com/obra/superpowers), [Matt Pocock's skills](https://github.com/mattpocock/skills), [BMAD](https://github.com/bmad-code-org/bmad-method), [Paperclip](https://github.com/paperclipai/paperclip), [Mesa](https://github.com/msoedov/mesa), and [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin). Each gets something right. Most were built for models that skipped steps, so they wrap every task in phases, personas, and approval gates. Current models do not need that, and the extra instruction makes them slower and worse. The rest assume you are an engineer who wants to make the technical calls.

I am a product owner. I want to say what is wrong or what to build, then let the work happen. SkipHow keeps the handful of rules that still matter with strong models and drops the ceremony. The [prior-art notes](docs/prior-art.md) say what was taken from each project.

## How it works

Your words set the boundary. "Research" reads and reports. "Save" creates the records. "Fix" or "implement" changes the project and runs the checks. "Finish end to end" adds merge and cleanup for the named work. Production, payments, credentials, private data, releases, and repository settings always need you to say so.

A small request stays in the session with no Issue, branch, or plan unless your repository requires one. A large one becomes a queue of GitHub Issues that one root agent works through, delegating bounded pieces to subagents in isolated worktrees, re-reading Git and GitHub before every merge, and deleting only the branches it created and GitHub confirms merged. State lives in Git and GitHub, not in a SkipHow database. After compaction or restart it re-reads the owner request and the handoff and carries on.

Subagents are meant to get the model their job needs. Search and inventory go to the cheapest tier, implementation to the standard one, planning and independent review to the strongest. Shared policy names only the tiers, never a vendor's model IDs, so nothing goes stale when a model is renamed. The host adapters that make this routing real on Claude Code and Codex are the headline of the next release; see the [1.1 brief](docs/research/2026-08-26/v1.1-brief.md). Until then delegates inherit your session model. This follows Anthropic's [orchestrator-worker guidance](https://www.anthropic.com/research/building-effective-agents) and their [multi-agent research findings](https://www.anthropic.com/engineering/built-multi-agent-research-system), and it respects the [measured caveat](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md) that a cheap model on an ambiguous task costs more in turns than it saves in tokens.

Before building anything lasting, SkipHow searches the project, its dependencies, and the platform for something that already does the job, and says where it looked. A problem it finds outside your request is fixed if it blocks the work, saved once as an Issue if it matters, and named in the report either way. Nothing is swallowed.

The report ends with fresh evidence for the final state, the rulings it made on your behalf, the follow-ups it saved, and anything it could not verify. A model saying "done" is not evidence; the diff, the checks, and the merged pull request are.

## Honest limits

SkipHow is instructions, not a runtime. Your host's sandbox and permissions are the real boundary. Behavior that a host cannot provide (background work, resume, worktree isolation, per-agent model choice) is reported as unavailable, not faked. Deterministic checks prove the package, not the model's judgment. Cost savings from routing are a design goal until paired runs measure them.

## Docs

- [User guide](docs/user-guide.md) for what your words authorize, tracked work, and pause and resume
- [Architecture](docs/architecture.md) and [trust](docs/trust.md) for routing, the GitHub lifecycle, and limits
- [Decisions](docs/decisions/README.md) and [research](docs/research/2026-08-26/README.md) for the reasoning
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)
