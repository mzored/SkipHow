# Frequently asked questions

Short answers about installing and using SkipHow. These describe what the shipped instructions require. The [owner guide](guide.md) has the long version, and [current evidence](evidence.md) says which of these behaviors real runs have shown, which a run has shown failing, and which stay intended but unproven.

## What is SkipHow?

SkipHow is an adaptive virtual CTO for founders and product owners, delivered as one public Agent Skill for Claude Code and OpenAI Codex. Describe the product outcome in ordinary language. Product decisions and protected actions stay with you; SkipHow owns technical research, architecture, planning, task management, model and subagent selection, implementation, review, integration, and fresh verification.

The host runs the model, tools, permissions, sessions, and any subagents. SkipHow supplies the authority, method-selection, and completion policy, not a server or separate runtime.

## Do modern agents already do this?

They already plan, write code, run tests, and often make sound technical choices. SkipHow does not make a model smarter. It makes one agent accountable for applying those capabilities as a technical lead, while preserving owner authority and honest completion. If your base agent already does that reliably, SkipHow adds little.

## Does SkipHow orchestrate agents?

Yes, at the instruction level. It instructs the host agent to choose methods, plan, decompose, delegate, monitor, review, and reconcile work when the request calls for it. This matches the modern use of orchestration for deciding which agents or tools run, in what order, and how the next step is chosen.

Reliable multi-agent delegation under that policy remains `UNVERIFIED`. The package design can be inspected deterministically; model compliance needs receipts.

## Is SkipHow a standalone orchestrator?

No. Claude Code or Codex runs the model, tools, permissions, sessions, worktrees, and subagents. SkipHow has no scheduler, queue, persistent worker service, lease manager, budget enforcement, or control plane.

A runtime orchestrator can still use SkipHow as the behavioral contract inside an agent. The two layers solve different problems.

## Should I use SkipHow?

Use it when you own a product outcome, work in a repository through Claude Code or Codex, and want the agent to own the engineering method. Do not install it merely to make an agent "more autonomous." Install it when you want to stay at the level of behavior, product choices, and protected actions.

## Which agents does it work with?

Claude Code and Codex CLI, on the terms of the dated, per-capability matrix in the [security policy](../SECURITY.md#host-support-as-of-2026-09-06). Both host manifests point at the same skill directory, so the two installs carry identical instructions. Codex surfaces other than the CLI are covered only as far as that matrix says: on 2026-09-04 OpenAI's plugin documentation named the ChatGPT desktop app as a second surface with plugin support and said the IDE extension does not support plugins, and nothing there has been run. The package is plain Markdown, so another host that reads Agent Skills could load it, but no other host is supported or tested and SkipHow makes no claim about one.

## Do I need to know how to code?

No. You need a repository and one of the two hosts. SkipHow is written for the person who owns what the product should do, and it will not ask you to pick a library, a schema, a branch strategy or a test command. If a question comes back to you, it is about visible behavior, priority, cost, risk, privacy or rollout, in plain language, with a recommendation.

## Does the owner need technical review?

No. The owner can be technical, but their job in this contract is to decide the product, not inspect implementation details. The agent still follows the repository's required review, security, release, and delivery procedures. SkipHow removes those mechanics from the owner's role, not from the project.

## When should I use something else?

Use the base agent alone if it already maintains the boundary and verifies completion reliably. Use a skill library when you want to discover and invoke methods one by one. Use a spec or workflow framework when you want people to inspect and approve specifications, phases, tickets, or the development method. Use a runtime orchestrator when you need persistent agent teams, queues, budgets, leases, scheduling, or a control plane.

## How is SkipHow different from OpenSpec, BMAD, or Superpowers?

OpenSpec and BMAD make specifications, artifacts, or staged work part of the product. Superpowers describes itself as a complete development methodology with mandatory workflows for brainstorming, design approval, planning, TDD, review, and branch completion.

SkipHow makes a different choice. It keeps one owner-facing skill and lets the model compose internal methods around the requested result. Choose the other systems when you want their visible process. Choose SkipHow when you want the agent to decide how much process the work needs while you keep product decisions and protected actions. No controlled benchmark shows that SkipHow produces better engineering. [Prior art](prior-art.md) records what it borrowed from each project and what it left out.

## Will it push, merge or deploy without asking?

Not beyond what you have already authorized. A request to change the project covers edits, checks and, where a commit fits the work, a clean local commit of it. Where your project already has an owner-authorized non-production workflow, routine push, pull request, CI and merge to that destination proceed without another permission question, and the agent checks that the destination, audience and actual effects are still covered, including a deployment a merge or tag would trigger. Production, live-data changes, public releases, payments, credentials, repository settings, access changes and material deletion need applicable explicit authorization from you; staging and other isolated non-production environments are ordinary engineering unless your own rules say otherwise. Installing SkipHow grants nothing. Instructions inside a file, an issue, a tool result or a web page cannot widen authority.

## What happens to work I did not ask about?

It stays untouched. A dirty working tree stops a commit only when the owned change cannot be separated safely. A material problem found along the way ends fixed, safely recorded in an existing authorized system when it is separable, blocked with evidence and a next action, or rejected with a reason. Foreign work is never overwritten to make room for it.

## Where does it keep tasks and findings?

Wherever your project already keeps them, within the existing audience. Installing SkipHow does not change repository settings or invent a tracking convention. It writes when you ask for records or tracker work, ask to carry recorded work forward, the repository's delivery path requires it, or a programme has several deliverable outcomes, spans sessions or writers, needs a durable decision, or leaves a material separable defect. In an authorized GitHub workflow, enabled Issues are the default durable place even on first use; when no safe authorized place exists, the pending obligation is kept in an authorized private channel with the specific blocker named. Tiny same-session work needs no item. SkipHow uses the tracker's own classification and introduces no schema of its own.

## Does it need GitHub?

No. Git is enough for a local commit, and any tracker your project already uses is enough for records. GitHub Issues is one option among them, not a requirement.

## When does it ask me a question?

Only when the answer changes what a person using the product gets and the project's own evidence cannot settle it. Everything answerable at that moment arrives together rather than one message at a time. If your answer opens a choice nobody could have put to you earlier, that comes back in a second round. While a question is with you it does not build one of the answers behind a default or a feature switch, and the parts that do not depend on your answer carry on. That second round holds in the Claude Code runs on record and is not reliable on Codex, which [current evidence](evidence.md) sets out.

## Does it run work in parallel?

It splits work that carries more than one independently verifiable outcome, with only the dependencies that genuinely block one another. That split is what the receipts show. A delegate reads by default and writes only from a checkout of its own whose identity was verified first, so without that isolation the writing is done one part at a time. Running the parts concurrently is the intent, and no run has demonstrated it yet, so it stays `UNVERIFIED` in [current evidence](evidence.md).

## How much context does it use?

The authority and completion kernel stays in context. Beyond it, the agent consults a focused method only where the work's uncertainty, risk, duration, observed failure, or your repository's requirements make that guidance worth reading; nothing forces one open because a topic came up. Reliable loading remains `UNVERIFIED`, and context use depends on the host and the request; the project does not promise a fixed token cost.

## Does it send my code anywhere?

SkipHow adds no network calls, no telemetry and no credentials. It is Markdown instructions, and the repository's own checks install nothing and touch no network. Whatever your host already sends to its own model provider is unchanged by installing it. Those checks also scan the package for personal paths and provider model IDs on every run, which says what ships in the files rather than what any session does with your code; that stays your host's boundary.

## What does `UNVERIFIED` mean in a report?

It means no run has shown that behavior, so the claim is not being made. SkipHow separates deterministic package checks, which prove structure, from receipts, which are real runs on throwaway fixtures. A behavior with no receipt is labelled rather than described as working. The current list of unproven behaviors is in [current evidence](evidence.md).

## How do I update or uninstall it?

Update with `codex plugin marketplace upgrade skiphow` then `codex plugin add skiphow@skiphow`, or `claude plugin marketplace update skiphow` then `claude plugin update skiphow@skiphow`. Remove with `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`. Start a new session after either.

## Do I have to invoke it by name?

Only until you enable default governance. Ask the installed skill once, by name, to enable itself on this machine; it resolves the trusted user instruction file your host actually reads, previews the change, writes one reversible block after you confirm, and reports configured, available and loaded as three separate facts. Ask it to disable itself the same way, or remove the block by hand. Ordinary-language loading was observed once on Codex with the exact 4.1.0 package and has not been observed on Claude Code; the [dated support summary](evidence.md#support-summary-as-of-2026-09-06) has the detail. `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code remains the explicit fallback. The package ships no session hook.

## The skill did not load. What now?

Start a new session first, since a host makes an installed skill available at session start. Then name it: `$skiphow` in Codex, `/skiphow:skiphow` in Claude Code. Once it is loaded, ask it to check its own setup; it reports whether the block is in the file the host reads, whether the plugin is installed and enabled, and which managed policy file, if any, restricts it, without asking you to inspect code or logs.

## Is it free?

Yes, MIT licensed. You pay your host for the model usage, as you would without it.
