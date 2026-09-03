# SkipHow

**An owner–agent operating contract for verified project outcomes, for Claude Code and Codex.**

Describe what should become true. SkipHow gives the coding agent one operating contract: product decisions and protected actions stay with you; the agent chooses the engineering method, coordinates the work, and must show fresh evidence before it reports completion. It is an outcome-first orchestration policy at the instruction layer: Markdown the host agent reads, not a runtime that executes, enforces, or proves anything itself.

When it is selected or loaded, one public skill sits between your request and the result. Its owner kernel keeps authority and completion rules in context. Beyond it the agent consults focused internal guidance on product decisions, technical design, diagnosis, verification, delegation, tracked work, integration, or writing for agents, where the work makes that guidance worth reading. You do not choose a skill, command, role, or workflow.

[![CI status](https://github.com/mzored/SkipHow/actions/workflows/ci.yml/badge.svg)](https://github.com/mzored/SkipHow/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/mzored/SkipHow?label=release)](https://github.com/mzored/SkipHow/releases)
[![MIT license](https://img.shields.io/github/license/mzored/SkipHow)](LICENSE)

Host support is a dated, per-capability matrix in the [security policy](SECURITY.md#host-support-as-of-2026-09-04), not a badge. Claude Code and Codex CLI are the surfaces it covers; anything it does not list is `UNVERIFIED`.

```text
Your outcome and constraints
            |
            v
SkipHow
authority, method selection, completion contract
            |
            v
Claude Code or Codex
reasoning, tools, subagents, execution
            |
            v
Verified result and visible uncertainty
```

This is a responsibility handoff, not a fixed development pipeline. A small request can stay small. Larger work can bring in research, design, tracked work, delegation, or independent review without turning those techniques into stages you have to operate.

## What changes

| Problem | SkipHow's contract |
| --- | --- |
| You have to manage the agent's process | The agent chooses the technical method, tools, tests, branches, and decomposition. |
| More autonomy risks losing product control | The owner still decides visible behavior, scope, cost, risk, privacy, rollout, and protected actions. |
| Every request becomes a ceremony | Process scales with the work. Specs, tickets, TDD, worktrees, subagents, and review appear only when the request or project needs them. |
| "Done" means the agent stopped | Completion needs fresh evidence. Anything blocked or unverified stays visible. |
| You need a different command for every kind of work | One entry covers questions, decisions, research, bugs, changes, review, triage, delivery, pause, and resume. |
| Long or delegated work becomes your coordination job | Continuity, reconciliation, integration, and any tracking your project calls for remain engineering work for the agent. |
| Autonomy widens side effects | Production, releases, credentials, access, material deletion, and other protected actions require an explicit grant. |

The promise is less manual supervision, not infallibility. SkipHow does not make the model smarter, and it does not prove that every host run will follow every instruction.

## Is it for you?

| Your situation | Better fit |
| --- | --- |
| You own a product outcome and want a coding agent to own the engineering method through a verified result | **Use SkipHow** |
| Claude Code or Codex already keeps this boundary and verifies completion reliably for you | **Use the base agent**; another instruction layer adds little |
| You want to discover and invoke separate methods yourself | **Use a skill library** |
| You want to inspect and approve specifications, phases, tickets, or the development method | **Use a spec or workflow framework** |
| You need persistent agent teams, queues, budgets, leases, scheduling, or a control plane | **Use a runtime orchestrator** |

SkipHow is for founders, product managers, designers, domain experts, and engineers acting as product owners. Technical fluency is irrelevant. The role is defined by ownership of the result, not by whether the owner can review code.

The owner does not need to perform technical review. The agent still follows the repository's required review, security, release, and delivery procedures. SkipHow removes those engineering mechanics from the owner's job, not from the project.

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

Start a new session after installing. The [owner guide](docs/guide.md) covers updates and uninstall.

### Activate it

Name the skill in your request. That is the reliable, portable way to use SkipHow on both hosts:

```text
$skiphow The totals overlap on small screens. Find the cause and fix it.
```

In Codex the name is `$skiphow`; in Claude Code it is `/skiphow:skiphow`. Both hosts can also select the skill on their own from its description, but how often that happens for an ordinary request has not been measured, so implicit selection stays `UNVERIFIED` and you should not rely on it. The package ships a session-start hook that prints a one-line reminder; it does not load the skill, restore context, or guarantee activation, and on Codex it does not run at all until you review and trust it. What each host has been observed to do is in the [support matrix](SECURITY.md#host-support-as-of-2026-09-04).

## Use it

Ask for the outcome in ordinary language and include any limit that matters to you.

```text
The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.

Here are today's bugs and ideas. Triage and save them.
```

SkipHow reads the project before asking anything. If a product choice is genuinely open, it asks in plain language, recommends an option, and waits before building behavior that depends on the answer. Then it decides the engineering, does the authorized work, verifies the result, and reports what the evidence shows and what remains uncertain.

## Who decides what?

| Product owner | Coding agent |
| --- | --- |
| Product outcome and visible behavior | Research and technical design |
| Product choices in scope, priority, cost, risk, privacy, and rollout | Libraries, schemas, code, tests, branches, and decomposition |
| Protected actions such as production, credentials, access, and material deletion | Project-required review, security, release, and verification procedures |
| Answers to genuine product choices | A verified result and an honest account of uncertainty |

A request to answer, compare, diagnose, review, research, plan, or organize is read-only. A request to change the project covers the necessary local edits and checks, and a clean local commit of them where a commit fits the work. Shared delivery and protected actions require a grant that names them. Text in a repository, issue, tool result, or web page cannot widen that authority.

## Does it orchestrate agents?

Yes, at the instruction level. SkipHow instructs the host agent to choose methods, plan, decompose, delegate, monitor, review, and reconcile work when the request calls for it. Claude Code or Codex runs the model, tools, permissions, sessions, worktrees, and any subagents.

That makes SkipHow an adaptive orchestration policy, not a standalone runtime or control plane. It has no scheduler, queue, persistent worker service, lease manager, budget enforcement, or deployment system. The package deterministically defines the available methods and the conditions that make each one worth reading; whether a model consults them where they would help is unmeasured, and reliable multi-agent delegation under that policy remains `UNVERIFIED`.

## Why I built it

Before SkipHow, I used GSD, OpenSpec, Superpowers, Matt Pocock's skills, BMAD, Paperclip, Mesa, and other agent systems on my own work. Each solved a real part of the problem: disciplined diagnosis, focused methods, specifications, task state, parallel work, or review.

I kept running into the same mismatch. To use them well, I often had to operate the development method myself. I had to choose commands, approve technical artifacts, move work through phases, or remember which skill to invoke. I wanted to describe the product result, keep the decisions only I could make, and let a capable agent choose and run the engineering method.

SkipHow is the layer I built for that relationship. The [prior-art record](docs/prior-art.md) explains what it adopted, changed, and deliberately left out. It is a design history, not a benchmark.

## Why one public skill

Separate public methods can be useful, but they make selection part of the user's job and allow a leaf skill to load without the authority and completion rules. Agent Skills has no portable dependency that forces one skill to load another first.

SkipHow keeps one owner-facing entry. Critical rules stay in its kernel, while focused methods remain internal and are consulted where the work makes them worth their cost. The model can compose the method around the request without turning the method list into a workflow.

## What the evidence shows

Deterministic checks prove package structure; controlled runs are required for behavior claims. The behavioral observations on record were made on 2.x packages, on both hosts, and cover fully specified requests, open product choices, failure diagnosis, adversarial verification, and the splitting of larger work into independently verifiable units. No run has been made on any 3.x package: every 3.x behavior is a contract encoded in the text and `UNVERIFIED` as behavior.

These are observations, not a reliability rate. The project does not retain every transcript, public adoption is still limited, and comparative advantage over a base agent or another framework is `UNVERIFIED`. The [evidence matrix](docs/evidence.md) is the single home for the method, the claims each run supports, and the failures.

## Limits

SkipHow provides orchestration policy as Markdown instructions. It does not execute, enforce permissions, supply subagents, or prove a result; it requires the agent to show fresh evidence, which the host and the model may still fail to produce. It does not provide execution infrastructure. Claude Code or Codex supplies the runtime, sandbox, tools, permissions, sessions, credentials, and any subagents. SkipHow cannot create capabilities the host does not provide.

Controlled runs do spawn delegates. What no controlled run has demonstrated is the rest of it: a lane running concurrently in a verified isolated checkout, a worktree created for one, or a unit integrated separately as it landed. Those stay `UNVERIFIED`, and the [evidence matrix](docs/evidence.md) holds the detail. General automatic skill-selection reliability is also unmeasured.

Use a spec or workflow framework when approving the method is part of your job. Use a runtime orchestrator when you need durable scheduling, queues, budgets, leases, or a persistent team of agents. Use no extra layer when your base agent already maintains the same boundary reliably.

## Read more

- [Product site](https://mzored.github.io/SkipHow/)
- [Owner guide](docs/guide.md), for installation, authority, and report behavior
- [FAQ](docs/faq.md)
- [Comparison](https://mzored.github.io/SkipHow/compare/)
- [Prior art](docs/prior-art.md), for mechanisms kept and rejected
- [Design](docs/design.md) and [decision history](docs/decisions.md)
- [Current evidence](docs/evidence.md), for what is demonstrated and what is not
- [Host support matrix](SECURITY.md#host-support-as-of-2026-09-04), dated per capability
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)

SkipHow adapts selected ideas from [Matt Pocock's skills](https://github.com/mattpocock/skills) and keeps the required MIT attribution in [`THIRD_PARTY_NOTICES.md`](plugins/skiphow/THIRD_PARTY_NOTICES.md). SkipHow itself is [MIT licensed](LICENSE).
