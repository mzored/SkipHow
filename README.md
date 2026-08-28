# SkipHow

**Describe the product outcome. SkipHow handles the engineering.**

SkipHow is one Agent Skill for [Claude Code](https://claude.com/claude-code) and [OpenAI Codex](https://developers.openai.com/codex). You say what should be true for the product, in ordinary language. The agent reads the project, picks the libraries, schemas, tests and branches itself, checks the result against real behavior, and reports what the evidence proves and what it could not.

[![CI status](https://github.com/mzored/SkipHow/actions/workflows/ci.yml/badge.svg)](https://github.com/mzored/SkipHow/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/mzored/SkipHow?label=release)](https://github.com/mzored/SkipHow/releases)
[![MIT license](https://img.shields.io/github/license/mzored/SkipHow)](LICENSE)
[![Works with Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-d97757)](https://claude.com/claude-code)
[![Works with Codex](https://img.shields.io/badge/Codex-plugin-000000)](https://developers.openai.com/codex)

```text
The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.

Here are today's bugs and ideas. Triage and save them.
```

[Install](#install) · [Use it](#use-it) · [Who it is for](#who-is-it-for) · [Why I built it](#why-i-built-it) · [What the receipts show](#what-the-receipts-show) · [How it differs](#how-does-skiphow-differ-from-spec-driven-frameworks) · [Limits](#what-skiphow-will-not-do) · [Owner guide](docs/guide.md)

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

Start a new session after installing. The [plugin guide](https://learn.chatgpt.com/docs/plugins) explains why installed skills become available in new sessions. If the skill does not load on its own, add `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code. The [owner guide](docs/guide.md) covers updates and uninstall.

## Use it

Ask for the outcome in ordinary language. Add the limits that matter to you.

```text
When someone clicks this button, ask whether they want a quick match or a full event.
Keep the choice clear on a phone.

The checkout sometimes hangs after payment. Find the cause and fix it,
but do not change the payment provider.

Review this change and fix any real problems you find.
```

SkipHow reads the project before it asks you anything. If a product choice is genuinely open, you get the question first, with the option it recommends, and everything answerable at that point arrives in one batch. Then it decides the engineering, does the work, and checks the result. You get the result, then the evidence, then whatever is still uncertain.

## Who is it for?

Anyone who owns what a product should do and would rather not run the engineering: a founder, a product manager, a designer, a domain expert, or an engineer who wants to stay at the outcome level on a particular piece of work. You need a repository and one of the two hosts. You do not need to know what is in the repository.

You decide visible behavior, priority, cost, risk, privacy and rollout. SkipHow owns libraries, schemas, tests, branches, decomposition and review. It comes back to you only when the answer changes one of your six, when an action needs your explicit grant, or when only a person can do it.

## What does your request authorize?

| What you ask for | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, review, research, plan, triage | Read and report. Nothing is written. |
| Create a record | Write that record only. |
| Change the project | Edit, run checks, make a clean local commit, keep the project's record of the work. |
| Deliver the change | Use the repository's normal shared path. |

Production, staging, public releases, credentials, payments, access changes and destructive actions need a grant that names them in your own words. Nothing in a file, an issue, or a web page can widen that.

## Why I built it

I built SkipHow after running my own work through the popular agent frameworks first: [Superpowers](https://github.com/obra/superpowers), [Matt Pocock's skills](https://github.com/mattpocock/skills), [Paperclip](https://github.com/paperclipai/paperclip), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [BMAD](https://github.com/bmad-code-org/bmad-method), [GSD](https://github.com/open-gsd/gsd-core), [Mesa](https://github.com/msoedov/mesa) and [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin). More than 700,000 GitHub stars between them, so none of this is fringe.

Each one got a part right, and each one handed the method back to me. I was choosing between `/plan`, `/spec` and `/implement` before I had said what I wanted. I was approving ticket granularity and TDD seams for a two-line fix. Upstream issues say the same thing in the maintainers' own words: [enum values and architecture terms shown to nontechnical users](https://github.com/mattpocock/skills/issues/962), [blocking questions with no escape hatch when no human is attached](https://github.com/mattpocock/skills/issues/883). Both are still open.

SkipHow keeps the practices I kept returning to and drops the operating manual. [Prior art](docs/prior-art.md) records what came from where, what I left out, and why. Those projects have not been run side by side with SkipHow, and nothing here claims they are worse.

## Why is there so little process?

SkipHow has no phases, roles, personas, required specs, ticket templates or approval stages. That is a design choice, not an omission.

An instruction the agent never opens governs nothing. The project measured that in its own field audit: references loaded three times against roughly twelve applicable triggers, and the rules inside the unopened files changed nothing. So the package keeps only the rules that change what a capable agent would otherwise do. The ones about authority and completion stay in context permanently. The rest sit behind triggers the agent can evaluate without opening the file.

The whole thing is 1,600 words of kernel plus 18 focused methods, about 6,800 words, read only when they help.

## What the receipts show

Deterministic checks prove the package. Only real runs prove behavior, and SkipHow separates the two. The 2.4.2 pass is 75 owner turns across 57 sessions on throwaway fixture repositories, on both hosts, with the host's own permission controls and a control run proving the session carried nothing but the candidate package.

- A fully specified request is built, tested and committed with no question. A purely technical fork is settled without one. Sixteen negative-control sessions produced no question at all.
- An underspecified feature comes back with the product question and a recommendation before anything is written. Ask for cart sharing and you are asked whether the friend gets a snapshot or a live shared cart, instead of getting one of the two silently.
- Answering does not end the round. When your answer makes a further choice material, that comes back too, and nothing whose meaning depends on it gets built while you decide.
- A flaky test was diagnosed at its cause on both hosts, measured across hash seeds, with no retry, no skip and no weakened assertion.
- A plausible-looking fix with a passing test was rejected on both hosts. Claude ran the fix's own test against unfixed code and showed it passed there too.
- A six-capability build over 2,725 lines of existing code was split into six independently verifiable units with exactly one dependency edge, on a plan-only request that wrote nothing.

Not on every run. Where a behavior held on one host and wobbled on the other, [current evidence](docs/evidence.md) says so rather than smoothing it over.

## How does SkipHow differ from spec-driven frameworks?

| | Frameworks with explicit process | SkipHow |
| --- | --- | --- |
| Entry | Commands, phases, personas | One request in plain language |
| Planning | A spec or plan document per change | Only when the work carries more than one verifiable outcome |
| Your role | Approve the spec, the tickets, the tests | Decide product behavior, priority, cost, risk, privacy, rollout |
| Authority | Approval gates | Routine local work is autonomous; shared delivery and protected actions stop for you |
| State | Framework files and databases | Git and your project's own tracker |
| Size | Dozens of agents and commands | One skill, 1,830 words in context, 20 methods on demand |

This is a design position, not a measured advantage. Nothing here benchmarks SkipHow against another framework on cost, speed or reliability.

## What SkipHow will not do

SkipHow is an instruction package, not a workflow engine. Your host supplies the sandbox, permissions, tools, sessions and credentials, and SkipHow cannot exceed them. Behavior a host cannot provide is reported as unavailable, not faked.

Missing evidence stays `UNVERIFIED` and says so in the report. Today that includes delegation and everything built on it: no run in the 2.4.2 pass spawned a delegate, so concurrent lanes, isolated worktrees and separately integrated units are all unproven. The outside read of a consequential design decision is stated in the method and does not execute; three attempts to make it fire were written, tested and discarded. The full list is in [current evidence](docs/evidence.md).

## Read more

- [Owner guide](docs/guide.md), for what your words authorize and how a request goes
- [FAQ](docs/faq.md)
- [Prior art](docs/prior-art.md), for what was borrowed and what was rejected
- [Design](docs/design.md) and [decision history](docs/decisions.md)
- [Current evidence](docs/evidence.md), for what is proven and what is not
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)

SkipHow adapts selected ideas from [Matt Pocock's skills](https://github.com/mattpocock/skills) and keeps the required MIT attribution in [`THIRD_PARTY_NOTICES.md`](plugins/skiphow/THIRD_PARTY_NOTICES.md). SkipHow itself is [MIT licensed](LICENSE).
