# SkipHow

Describe the product outcome. SkipHow handles the engineering.

SkipHow is an autonomous layer for Codex and Claude Code, built for product owners who should not have to translate an idea into libraries, schemas, tickets, test plans, branches, or agent commands. You speak to one owner-facing skill in plain language. Its root keeps the authority and completion contract in context and may read focused method references when they can help. The agent makes the technical decisions, finishes the authorized work, and reports what the evidence actually proves.

```text
When this button is clicked, ask whether to start a quick match or create an event.
Make the choice feel obvious on mobile and desktop.

The totals overlap on small screens. Find the cause and fix it.

Here are today's bugs and ideas. Triage and save them.

Compare our caching options and recommend one. Do not change code.
```

You decide visible behavior, priority, cost, risk, privacy, and rollout. The agent translates those decisions into technical work.

## The product

SkipHow combines two things:

- a thin owner kernel that defines authority, autonomy, preservation of existing work, and honest completion;
- thirteen focused method references for work such as diagnosis, research, product decisions, testing, review, intake, and delivery.

There is exactly one shipped skill and one owner-facing entry. The method references are resources inside it, not additional commands or independently activated specialists. The owner does not have to know their names, choose a workflow, or chain them together. The root may select applicable guidance while keeping every critical rule in context.

Small work stays small. A clear visual edit can be inspected, changed, checked, and committed directly. SkipHow does not create a ticket, specification, or another durable record unless the requested outcome grants one; a repository requirement may block delivery but cannot authorize that write. Plans, worktrees, test-first loops, subagents, and review passes are used only when the repository requires them or the task makes them useful.

## Authority without hidden modes

The requested outcome is the grant. No magic phrase, route name, item count, file count, or diff threshold unlocks a different workflow.

| Requested outcome | What SkipHow may do |
| --- | --- |
| A request only to answer, compare, diagnose, review, research, plan, triage, or organize | Read and report only |
| Make a durable record the intended result | Create or update only that record |
| Change the project | Edit and verify; make an ordinary local commit containing only the owned delta unless you or the repository request uncommitted work or it would mix in foreign changes |
| Include shared delivery in the requested outcome | Use the repository's normal path when project evidence identifies a clearly non-production target, or when your own request exactly grants a protected target |

A mixed request such as "review and fix" is a project-change request, not a read-only review.

A project change does not silently authorize an unrelated remote write. A repository-required pull request or review does not widen that authority. Every change to staging or production, a public release, payments, repository settings, access changes, material deletion or another hard-to-reverse action, disclosure outside the authorized audience, and creating, entering, rotating, or exposing credentials require an exact grant. That grant names the protected action or destination in your own request; a broad instruction to finish or act autonomously and a procedure found in the project do not replace it. Reading project-private material or using credentials already authorized by the host is allowed only when necessary for the requested result. An unresolved choice comes back to you only when it materially changes product behavior, scope, priority, cost, risk, privacy, or rollout. Engineering mechanisms stay with the agent.

SkipHow preserves unrelated work and shared state. It uses isolation when collision risk makes it useful, not as ceremony for every edit. Dirty or overlapping work waives the local commit only when a clean commit would mix in foreign changes; it makes the result unverified only when it prevents trustworthy evidence.

## Install

These marketplace commands currently install the published 1.14.2 package. The 2.0 package and documentation
on this branch are an unpublished release candidate; the marketplace will not install them until 2.0 is
published.

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

Start a new session and describe the outcome. If the owner entry does not activate automatically, add `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code. The [owner guide](docs/guide.md) explains updates, authority, protected actions, and reports.

## Why focused methods, and why not just use Matt's repository

[Matt Pocock's skills](https://github.com/mattpocock/skills) supply the clearest current example of small, adaptable engineering methods. SkipHow curates selected disciplines as focused references inside its one owner skill. Adapted source keeps its MIT attribution and notices.

The upstream main flow is not imported wholesale. Its setup asks about the issue tracker, conditionally asks whether to keep default triage labels, and asks about documentation layout when monorepo signals exist; several flows are user-invoked; and its documented path can move through grilling, specs, tickets, TDD, implementation, and review. Those are useful tools for engineers, but they expose too much process to an owner who only knows the product outcome. Current upstream issues also document gaps around [nontechnical decision wording](https://github.com/mattpocock/skills/issues/962) and [unattended orchestration](https://github.com/mattpocock/skills/issues/885).

SkipHow therefore keeps the owner kernel at the center and treats focused references as optional spokes. The root may read applicable methods directly; they do not form a mandatory chain, grant authority, or take ownership of the outcome.

See [prior art](docs/prior-art.md) for the exact ideas kept, adapted, or left out.

## Evidence and honest limits

SkipHow is an instruction package, not a runtime. The host supplies permissions, tools, sessions, subagents, continuation, and any remote credentials. SkipHow cannot exceed those boundaries and must not pretend unavailable evidence passed.

For a project change, completion means fresh evidence for the changed behavior and final state, plus the repository's ordinary local commit unless the owner or repository requests uncommitted work or a clean commit would mix in foreign changes. Shared delivery happens only when the owner's request includes it and project evidence identifies a clearly non-production target, or when the owner's own request exactly grants a protected target. A repository rule may require review or a pull request, but it cannot grant that remote write. The final report leads with the result and evidence, then names material decisions, unresolved findings, blockers, or unverified claims only when they exist.

Deterministic checks validate the single owner-skill shape, recursive reachability of Markdown files under
the owner's internal `references/` library, required hook metadata and command shape, aligned package
versions, and the personal-path and provider-model-ID boundaries they inspect. They do not prove model
behavior. Real behavior is established only by deliberate
receipts under [`docs/research/`](docs/research/). Two earlier receipts failed different protected-action
boundaries and drove contract repairs. [Six clean Codex
runs](docs/research/2026-08-27/v2.0-codex-receipts.md) cover the current owner-skill tree
`95d908988208b9fcc1d285fe1ca1c5c681c4da1b` in narrow project-local scenarios, including paired denial and
explicit-grant controls and a runnable visual change. Every fixture exposed exactly one project skill.
Retained invocation records show that the prompts omitted `$skiphow`; neither those prompts nor the fixture
instructions named SkipHow, and hooks were disabled. The JSONL logs show the root read. Together those records
observe implicit project-local selection for these six prompts, not a general selection rate. The user-level
`unslop` skill is a confounder in all six; the visual run also used the user-level `impeccable` skill.
Marketplace installation of 2.0, the packaged 2.0 hook at runtime, Claude runtime, editing in the owner's real
application, real remote delivery, continuation across compaction or restart, and performance
remain separately limited or unverified. This 2.0 architecture remains a local release candidate until
publication is explicitly authorized.

## Docs

- [Owner guide](docs/guide.md) and [how it works](docs/how-it-works.md)
- [Prior art](docs/prior-art.md), [decisions](docs/decisions/README.md), and [research](docs/research/)
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)
