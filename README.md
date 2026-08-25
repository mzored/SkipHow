# SkipHow

SkipHow is one Agent Skill for product and project work in Codex and Claude Code. Describe the outcome. It chooses the smallest sufficient path and finishes only the work your request allows.

```text
The totals overlap on small screens. Find the cause and fix it.

Research our caching options. Record the decision, but do not change code.

Finish GitHub issues #41, #44, and #48 end to end. Merge accepted pull requests.
```

## Why I built it

I built SkipHow after trying [GSD](https://github.com/open-gsd/gsd-core), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [Superpowers](https://github.com/obra/superpowers), [Matt Pocock's skills](https://github.com/mattpocock/skills), [BMAD](https://github.com/bmad-code-org/bmad-method), [Paperclip](https://github.com/paperclipai/paperclip), [Mesa](https://github.com/msoedov/mesa), and [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin). Each got a different part right. SkipHow brings the practices I kept returning to into one skill, so I no longer have to choose a method before every task. [Prior art](docs/prior-art.md) records what came from where and what I deliberately left out.

## Install

### Codex

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Start a new task and describe the work. If SkipHow does not activate, include `$skiphow`.

### Claude Code

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Start a new session and describe the work. If SkipHow does not activate, use `/skiphow:skiphow`.

The [getting started guide](docs/getting-started.md) covers prerequisites, updates, uninstall, and troubleshooting.

## How it works

A small task stays in one session. If a bug's cause is unknown, SkipHow reproduces and diagnoses it before changing code. When several selected items need coordination, it can use the host's subagents, worktrees, background tasks, and checkpoints.

SkipHow installs instructions, not a separate runtime. Codex or Claude Code executes the work and enforces permissions. SkipHow uses host, Git, and GitHub state for recovery.

## What your request authorizes

| Example wording | What SkipHow does |
| --- | --- |
| `research`, `review`, `assess` | Reads and reports. It does not change the project. |
| `save`, `create Issues` | Creates the requested records. It does not implement them. |
| `fix`, `implement`, `deliver` | Changes the project and runs relevant checks. |
| `finish end to end`, `run unattended` | Allows guarded merge and cleanup for the selected work. |
| `pause`, `cancel`, `do not merge` | Stops or narrows the remaining work. |

Production changes, payments, credential changes, operations on private data, repository settings, public releases, and irreversible actions require a direct request from the owner. Host permissions and project rules still apply.

## Docs

- [User guide](docs/user-guide.md) for request patterns and tracked work
- [Trust](docs/trust.md) and [evaluation policy](docs/evals.md) for authority, safety, current evidence, and known limits
- [Documentation index](docs/README.md) for architecture, security, research, and contributor docs
