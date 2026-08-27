# SkipHow

Describe the product outcome. SkipHow handles the engineering.

SkipHow is an autonomous layer for Codex and Claude Code, built for product owners who should not have to translate an idea into libraries, schemas, tickets, test plans, branches, or agent commands. You speak to one owner-facing skill in plain language. Its root keeps the authority and completion contract in context and reads focused method references only when they help. The agent makes the technical decisions, finishes the authorized work, and reports what the evidence actually proves.

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

There is exactly one shipped skill and one owner-facing entry. The method references are resources inside it, not additional commands or independently activated specialists. The owner does not have to know their names, choose a workflow, or chain them together. The root selects only the guidance that helps while keeping every critical rule in context.

Small work stays small. A clear visual edit can be inspected, changed, checked, and committed directly. SkipHow does not require a ticket, spec, plan, worktree, test-first loop, subagent, or review pass unless the repository requires it or the task makes it useful.

## Authority without hidden modes

The requested outcome is the grant. No magic phrase, route name, item count, file count, or diff threshold unlocks a different workflow.

| Requested outcome | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, research, review, plan, triage, or organize | Read and report only |
| Save, record, file, or use a named durable destination | Create or update the requested records |
| Change the project | Edit, verify, and make an ordinary local commit containing only the owned delta |
| Reach a named shared target | Use the repository's normal non-production delivery path when the target is clearly non-production |

A project change does not silently authorize an unrelated remote write. Promotion to staging or production, a public release, payments, repository settings, access changes, material deletion or another hard-to-reverse action, disclosure outside the authorized audience, and creating, entering, rotating, or exposing credentials require an exact grant. That grant names the protected action or destination in your own request; a broad instruction to finish or act autonomously and a procedure found in the project do not replace it. Routine use of already-authorized credentials and project-private material is allowed when needed for the requested result. An unresolved choice comes back to you only when it materially changes product behavior, scope, priority, cost, risk, privacy, or rollout. Engineering mechanisms stay with the agent.

SkipHow preserves unrelated work and shared state. It uses isolation when another writer may collide, not as ceremony for every edit.

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

Start a new session and describe the outcome. If the owner entry does not activate automatically, add `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code. The [owner guide](docs/guide.md) explains updates, authority, protected actions, and reports.

## Why focused methods, and why not just use Matt's repository

[Matt Pocock's skills](https://github.com/mattpocock/skills) supply the clearest current example of small, adaptable engineering methods. SkipHow curates selected disciplines as focused references inside its one owner skill. Adapted source keeps its MIT attribution and notices.

The upstream main flow is not imported wholesale. Its current setup asks the user to choose a tracker, triage labels, and document locations; several flows are user-invoked; and its documented path can move through grilling, specs, tickets, TDD, implementation, and review. Those are useful tools for engineers, but they expose too much process to an owner who only knows the product outcome. Current upstream issues also document gaps around [nontechnical decision wording](https://github.com/mattpocock/skills/issues/962) and [unattended orchestration](https://github.com/mattpocock/skills/issues/885).

SkipHow therefore keeps the owner kernel at the center and treats focused references as optional spokes. The root reads useful methods directly; they do not form a mandatory chain, grant authority, or take ownership of the outcome.

See [prior art](docs/prior-art.md) for the exact ideas kept, adapted, or left out.

## Evidence and honest limits

SkipHow is an instruction package, not a runtime. The host supplies permissions, tools, sessions, subagents, continuation, and any remote credentials. SkipHow cannot exceed those boundaries and must not pretend unavailable evidence passed.

For a project change, completion means fresh evidence for the changed behavior and final state, plus the repository's ordinary local commit unless the request or repository rules require a different finish. Shared delivery happens only when it is part of the requested outcome. The final report leads with the result and evidence, then names material decisions, unresolved findings, blockers, or unverified claims only when they exist.

Deterministic checks prove package integrity. They do not prove model behavior. Real behavior is established only by deliberate receipts under [`docs/research/`](docs/research/). Four Codex runs against the earlier multi-skill candidate cover narrow owner-contract scenarios, but they do not validate this final single-skill layout. Marketplace installation, Claude runtime, automatic activation, real UI work, remote delivery, and final reference selection remain separately limited or unverified. This 2.0 architecture remains a local release candidate until publication is explicitly authorized.

## Docs

- [Owner guide](docs/guide.md) and [how it works](docs/how-it-works.md)
- [Prior art](docs/prior-art.md), [decisions](docs/decisions/README.md), and [research](docs/research/)
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)
