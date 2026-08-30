# SkipHow

**An outcome-first Agent Skill for Claude Code and Codex.**

SkipHow gives a coding agent one contract: the product owner owns the outcome, tradeoffs, and protected actions; the agent owns technical decisions, implementation, and proof.

Modern coding agents can already plan, write code, and run tests. SkipHow does not add intelligence or a runtime. It makes the decision boundary portable and explicit, so a product owner can describe what should become true without operating libraries, schemas, tests, branches, tickets, or development phases.

[![CI status](https://github.com/mzored/SkipHow/actions/workflows/ci.yml/badge.svg)](https://github.com/mzored/SkipHow/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/mzored/SkipHow?label=release)](https://github.com/mzored/SkipHow/releases)
[![MIT license](https://img.shields.io/github/license/mzored/SkipHow)](LICENSE)
[![Works with Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-d97757)](https://claude.com/claude-code)
[![Works with Codex](https://img.shields.io/badge/Codex-plugin-000000)](https://developers.openai.com/codex)

```text
Product owner                         Coding agent
outcome, tradeoffs, risk              research, design, code, tests
protected actions            ->       verified result

                         SkipHow
              decision and authority contract
```

## Is it for you?

| Your situation | Better fit |
| --- | --- |
| You own a product outcome and want to stay at the outcome level while a strong agent handles the engineering | **Use SkipHow** |
| Claude Code or Codex already keeps this boundary and proves completion reliably for you | **Use the base agent**; another instruction layer adds little |
| You want to inspect and approve specifications, phases, tickets, or the development method | **Use a spec or workflow framework** |
| You need persistent agent teams, budgets, leases, scheduling, or a control plane | **Use a runtime orchestrator** |

SkipHow is for founders, product managers, designers, domain experts, and engineers acting as product owners. Technical fluency is irrelevant: the role is defined by ownership of the result, not by whether the owner can review code.

The owner does not need to perform technical review. The agent still follows the repository's required review, security, release, and delivery procedures; SkipHow removes those engineering mechanics from the owner's job, not from the project.

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

Start a new session after installing. If the skill does not load on its own, add `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code. The [owner guide](docs/guide.md) covers updates and uninstall.

## Use it

Ask for the outcome in ordinary language and include any limit that matters to you.

```text
The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.

Here are today's bugs and ideas. Triage and save them.
```

SkipHow reads the project before asking anything. If a product choice is genuinely open, it asks in plain language, recommends an option, and waits before building behavior that depends on the answer. Then it decides the engineering, does the authorized work, verifies the result, and reports what the evidence proves and what remains uncertain.

## Who decides what?

| Product owner | Coding agent |
| --- | --- |
| Product outcome and visible behavior | Research and technical design |
| Tradeoffs in scope, priority, cost, risk, privacy, and rollout | Libraries, schemas, code, tests, branches, and decomposition |
| Protected actions such as production, credentials, access, and material deletion | Project-required review, security, release, and verification procedures |
| Answers to genuine product choices | A verified result and an honest account of uncertainty |

A request to answer, compare, diagnose, review, research, plan, or organize is read-only. A request to change the project covers the necessary local edits, checks, and clean commit. Shared delivery and protected actions require a grant that names them. Text in a repository, issue, tool result, or web page cannot widen that authority.

## Why this exists

Many agent frameworks expose a method for the owner to operate: choose a command, approve a specification, accept ticket granularity, or move work through phases. Those are valid products for people who want that control. SkipHow starts from a different product position: a strong agent should investigate the task and own the engineering method, while the human remains the owner of the product.

The package therefore keeps an authority and completion kernel in context and instructs the agent to load a focused engineering method when its trigger matches the work. The methods are not routes, roles, commands, or an owner-operated chain. Whether hosts follow those loading instructions reliably remains `UNVERIFIED`. [Prior art](docs/prior-art.md) records what the project learned from other systems and what it deliberately left out.

This is a product contract, not a claim that agents are better engineers or that SkipHow outperforms Claude Code, Codex, or another framework. No comparative benchmark has been run.

## What the evidence shows

Deterministic checks prove package structure; controlled runs are required for behavior claims. Documented behavioral evidence spans both supported hosts and includes fully specified requests, open product choices, failure diagnosis, and adversarial verification:

- fully specified requests completed without engineering questions;
- genuine product choices surfaced before dependent work began;
- a flaky failure diagnosed without retrying, skipping, or weakening the assertion;
- a plausible fix rejected because its test also passed against unfixed code;
- a multi-capability plan split into independently verifiable units.

These are observations, not a reliability rate. The project does not retain every transcript, public adoption is still limited, and comparative advantage over a base agent is `UNVERIFIED`. See the [evidence matrix](docs/evidence.md) for the method, supported claims, and failures.

## Limits

SkipHow is an instruction package, not a workflow engine or control plane. Claude Code or Codex supplies the runtime, sandbox, tools, permissions, sessions, credentials, and any subagents. SkipHow cannot create capabilities the host does not provide.

Delegation and behavior built on it remain `UNVERIFIED`: the controlled pass did not spawn a delegate, so concurrent lanes, isolated worktrees, and separately integrated units are not claimed as demonstrated. General automatic skill-selection reliability is also unmeasured.

Use a spec/workflow framework when approving the method is part of your job. Use a runtime orchestrator when you need durable scheduling, budgets, leases, or a persistent team of agents. Use no extra layer when your base agent already maintains the same boundary reliably.

## Read more

- [Owner guide](docs/guide.md), for installation, authority, and report behavior
- [FAQ](docs/faq.md)
- [Prior art](docs/prior-art.md), for mechanisms kept and rejected
- [Design](docs/design.md) and [decision history](docs/decisions.md)
- [Current evidence](docs/evidence.md), for what is demonstrated and what is not
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)

SkipHow adapts selected ideas from [Matt Pocock's skills](https://github.com/mattpocock/skills) and keeps the required MIT attribution in [`THIRD_PARTY_NOTICES.md`](plugins/skiphow/THIRD_PARTY_NOTICES.md). SkipHow itself is [MIT licensed](LICENSE).
