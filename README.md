# SkipHow

Describe the product outcome. SkipHow handles the engineering.

```text
The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.
```

SkipHow gives Codex and Claude Code one owner-facing skill. You describe what should be true for the product. The agent inspects the project, makes the technical decisions, verifies the result, and reports what the evidence proves.

## Who it is for

Anyone who owns what a product should do and would rather not run the engineering: a founder, a product manager, a designer, a domain expert, or an engineer who wants to stay at the outcome level on a particular piece of work. You need a repository and one of the two hosts. You do not need to know what is in the repository.

## The boundary

You decide visible behavior, priority, cost, risk, privacy, and rollout. SkipHow owns libraries, schemas, tests, branches, decomposition, review, and every other engineering choice.

It brings a question back only when the answer changes product behavior, scope, priority, cost, risk, privacy, or rollout, when an action needs your explicit grant, or when only a person can do it. Where your request leaves such a choice open, it asks once, with a recommendation, before building. Where it chose without asking, it tells you what it chose and what the alternative was.

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

Start a new session after installation. The [plugin guide](https://learn.chatgpt.com/docs/plugins) explains why installed skills become available in new sessions.

## Use it

Ask for the outcome in ordinary language. Add the limits that matter to you.

```text
When someone clicks this button, ask whether they want a quick match or a full event.
Keep the choice clear on a phone.

Here are today's bugs and ideas. Triage and save them.

Review this change and fix any real problems you find.
```

## How a request usually goes

You say what should be true for the product. SkipHow reads the project before it asks you anything, and if a product choice is genuinely open it asks once, with the option it recommends. Then it decides the engineering, does the work, and checks the result against real behavior. You get the result first, then the evidence, then whatever is still uncertain.

## What it does

- Read-only requests stay read-only.
- Project changes include fresh checks and a clean local commit when the repository allows one.
- Remote delivery happens only when you ask for shared delivery.
- Production, public releases, credentials, payments, access changes, and destructive actions need an explicit grant.
- A problem found along the way is fixed, or recorded where your project tracks work, so the next session picks it up.
- Work that finishes carries what it established into the record, so nobody investigates it twice.
- Large work is split into parts you can each see working, and independent parts can run at the same time.
- Unrelated work stays untouched. Missing evidence stays `UNVERIFIED`.

## Why there is so little process

SkipHow has no phases, roles, personas, required specs, ticket templates, or approval stages. That is a design choice, not an omission. A strong model does not need to be told the order of engineering work. An instruction the agent never opens governs nothing, which the project measured in its own field audit. So the package keeps only the rules that change what a capable agent would otherwise do. The ones about authority and completion stay where they are always in context. The rest sit behind triggers the agent can decide from outside the file.

Where a more prescriptive framework gives the operator a workflow to drive, SkipHow states a contract and leaves the sequence to the agent. Treat that as a design position rather than a measured comparison; nothing here benchmarks one against the other. What is measured, on both supported hosts, is that a reported bug fix finishes in about a minute with no questions, while a new feature stops to ask which product it should be, and that a fully specified request is built without asking anything. The runs are in [current evidence](docs/evidence.md).

SkipHow is an instruction package, not a workflow engine. The host still controls permissions, tools, sessions, and credentials, and SkipHow cannot exceed them.

## Read more

- [Owner guide](docs/guide.md)
- [Design](docs/design.md)
- [Decision history](docs/decisions.md)
- [Current evidence](docs/evidence.md)
- [Contributing](CONTRIBUTING.md)

SkipHow adapts selected ideas from [Matt Pocock's skills](https://github.com/mattpocock/skills). The package keeps the required MIT attribution in [`THIRD_PARTY_NOTICES.md`](plugins/skiphow/THIRD_PARTY_NOTICES.md).
