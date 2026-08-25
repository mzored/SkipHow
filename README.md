# SkipHow

Tell SkipHow what you want to improve. It inspects the project, makes routine product and technical decisions, does the work you authorized, and checks the result.

```text
Add a way to pause a subscription.

The totals overlap on small screens. Find the cause and fix it.

Save these customer notes as GitHub Issues and merge real duplicates.

Could we make error logging more useful here?

Finish the ready Issues end to end. Merge green pull requests and clean up your branches.
```

## One request, different depth

You describe the outcome in ordinary language. A clear local change stays in the current session. An uncertain bug gets diagnosis before repair. Several tracked items can use the host's goals, subagents, and isolated worktrees. SkipHow adds that coordination only when the work needs it.

SkipHow is an Agent Skill for Codex and Claude Code. Explicit invocation follows each host's syntax. It has no runner, daemon, task database, hosted service, or model catalog.

## Install in Codex CLI

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Start a new session, then describe the work. Use `$skiphow` when you want to select the skill explicitly. See the [Codex plugin guide](https://learn.chatgpt.com/docs/plugins).

## Install with Claude Code

```sh
claude plugin marketplace add mzored/SkipHow
claude plugin install skiphow@skiphow
```

Start a new session, then describe the work. Use `/skiphow:skiphow` for explicit selection. See the [Claude Code plugin guide](https://code.claude.com/docs/en/plugins).

## What SkipHow decides

SkipHow chooses libraries, code structure, tests, model roles, subagents, branches, and review depth from the project and the task. It asks you when a choice changes product behavior, scope, priority, cost, privacy, production, or another hard-to-reverse commitment.

Your words set the authority boundary:

- `discuss`, `assess`, and `research` are read-only;
- `save` and `create Issues` allow the requested records, but do not start implementation;
- `fix`, `implement`, and `deliver` allow project changes and verification;
- `finish end to end` and `run unattended` also allow guarded merge and cleanup for the named work;
- `do not merge`, `pause`, and `cancel` narrow that authority immediately.

A bare idea or question stays read-only. Say `save` to create a record, or `implement` to change the product. During delivery, SkipHow may save one deduplicated record for a material finding outside the task, but it does not implement or reprioritize that finding.

SkipHow's policy forbids bypassing repository protections or deleting dirty, unmerged, unique, or unowned work. Host approvals and repository rules remain the enforcement boundary.

## Current limits

Version 0.9.0 is a preview release, not SkipHow 1.0.

Direct plugin work needs no Python package or separate setup. GitHub delivery still needs host access to the repository. Background work, restart recovery, and per-agent model selection depend on the installed host and account.

Package checks prove that a host can validate or install the plugin. They do not prove that a model will interpret every request correctly. Implicit skill selection, the distinction between saving and implementing, multi-Issue unattended delivery, recovery across a full restart, autonomous per-agent model selection, and routing savings remain `UNVERIFIED` until opt-in evidence covers the exact packaged version.

## Why this shape

The project's owner started SkipHow after trying GSD, OpenSpec, Superpowers, Matt Pocock's skills, BMAD, Paperclip, Mesa, and Autonomous PM. Copying all of their process would recreate the problem SkipHow is meant to remove.

The current design keeps one owner-facing entry, proportional planning, research before a lasting new subsystem, evidence after changes, tracked findings, and host-native support for long work. The detailed comparison, reviewed commits, and limits are in [prior art](docs/prior-art.md) and the dated [research record](docs/research/2026-08-25/README.md).

Start with [architecture](docs/architecture.md) or [prior art](docs/prior-art.md). See [contributing](CONTRIBUTING.md), [security](SECURITY.md), and the [MIT license](LICENSE).
