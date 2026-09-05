# Design

SkipHow is an adaptive virtual CTO for founders and product owners, currently shipped as one Agent Skill for strong coding agents. The [owner-outcome contract](outcome-contract.md) governs this design. The owner states a product outcome and keeps product decisions. The CTO kernel makes the lead agent accountable for translating the outcome, selecting the engineering method, managing durable work when warranted, choosing and supervising delegates, reviewing the result, integrating it, and showing fresh evidence. It is not a scheduler, database, model runner, control plane, or replacement for host permissions, and it proves nothing itself. A native host binding or thin adapter may replace a mechanism when controlled evidence shows it preserves these outcomes at lower total cost.

## Package shape

The repository ships one canonical package:

```text
plugins/skiphow/
  .codex-plugin/plugin.json
  .claude-plugin/plugin.json
  skills/skiphow/
    SKILL.md
    references/
```

Both host manifests point to the same skill directory. The package contains one public skill named `skiphow`.

## Kernel and playbooks

`SKILL.md` is the CTO kernel. It keeps the mission, decision rights, adaptive routing triggers, authority, trust, preservation of unrelated work, delegate safety, risk-scaled review, persistence, and honest completion in context.

The files under `references/` hold eight focused playbooks: product, technical design, diagnosis, tracked work, delegation, integration, verification, and operations. Their observable triggers live in the kernel. A playbook carries technique, not a product-defining duty whose absence would erase CTO behavior.

A module exists only if it meets four criteria: it covers one distinct failure domain, it gives a reason to consult it that is recognizable without opening it, it carries no critical invariant that is absent from the kernel, and it repeats no rule another module owns.

Methods are not routes or stages. The owner does not choose them. The agent can work directly, plan, delegate, review, or use a worktree when the project or task calls for it.

## Host boundary

Codex and Claude Code supply execution, permissions, tools, credentials, sessions, subagents, and continuation. SkipHow uses those capabilities without pretending to provide them.

This separates orchestration policy from the runtime. SkipHow tells the host agent how to plan, select methods, decompose, delegate, review, and reconcile when the request calls for those acts. The host runs the model and tools. A control plane, if one exists, owns durable workers, queues, scheduling, leases, budgets, and deployment.

SkipHow separates authority from task data, and the separation is policy rather than enforcement. Authority comes from the owner's messages and trusted host, user, organization, or administrator policy, at the host's precedence and scope. Applicable repository instructions supply procedure within granted authority. Their location alone proves no trust; instructions in an untrusted revision remain evidence to inspect. Issue and pull request bodies and comments, ordinary repository documents and code comments, fixtures, logs and tool output, web content, retrieved documents, delegate returns, and external records are untrusted task data.

Applicable project instructions may narrow scope, require safeguards, and define normal procedure for the repository. An established owner-authorized non-production workflow can cover routine shared delivery without renewed permission. Verify that authorization still covers the project, destination, audience, and downstream effects, including production changes triggered by CI. Project procedure cannot create a protected-action grant or turn a read-only request into a write. Untrusted task data is evidence to analyze and cannot grant external actions, credentials, disclosure, deletion, or wider scope. The runtime kernel implements this boundary.

Instruction-level policy is probabilistic. It raises the odds that an agent behaves correctly and guarantees nothing, so a host-enforced control is preferred wherever the host provides one. Read-only profiles, sandboxes, permission prompts, and isolated checkouts do work that prose cannot.

The package ships no hook. The former reminder did not load the skill or restore state, and no controlled comparison showed a benefit worth an executable surface. Default ordinary-language governance uses a reversible line in each host's trusted user instructions. Codex reads global `AGENTS.md`; Claude Code reads user `CLAUDE.md` and rules. This is the thinnest host-specific adapter available without a runtime or silent configuration mutation. Explicit invocation remains the fallback, and automatic selection stays `UNVERIFIED` until a retained run proves it.

## Public site visual system

Historical, non-normative: presentation collateral kept for reference. The deterministic check no longer fails on any of it; site presentation is a non-blocking lint.

The canonical site is a static editorial proof surface, not a second product specification. Its visible claims summarize and link back to the README, evidence, decisions, releases, and installation instructions.

The reusable visual rules are warm paper, dark ink, one vermilion accent, serif display type, sans-serif reading text, thin rules, and evidence presented as matrices or field notes. The responsibility handoff is the primary visual motif. No robot imagery, neon AI decoration, synthetic dashboard, ornamental gradients, or stock illustration enters the system.

Every page has one clear heading, a constrained reading measure, keyboard-visible focus, semantic landmarks, and responsive layouts that collapse without changing reading order. The homepage keeps GitHub as a visible secondary action beside installation and evidence, without mutable popularity counts. The site ships plain HTML and CSS with no client runtime, cookies, tracking, or external font dependency. Structured data matches visible text and exists for classification, not as a ranking claim.

## Why one public skill

Separate public methods look tidy, but a host can select one without loading the owner kernel. That can drop the authority and completion rules. Agent Skills has no portable dependency that forces a leaf skill to load another skill first.

Keeping focused methods inside one owner skill avoids that gap. It also gives the owner one plain-language entry instead of a menu of engineering commands.

## Prior art

[Matt Pocock's skills](https://github.com/mattpocock/skills) showed that small engineering methods can stay useful without becoming one large workflow. SkipHow adapts selected method ideas but keeps a different product boundary: one product-owner entry, no setup interview, and no required chain of specs, tickets, TDD, implementation, and review.

The exact adapted paths and inspected revision live in [`SOURCES.json`](../plugins/skiphow/SOURCES.json). The distributed package keeps the source license and copyright notice in [`THIRD_PARTY_NOTICES.md`](../plugins/skiphow/THIRD_PARTY_NOTICES.md).

[Prior art](prior-art.md) records the other projects this one learned from, what each contributed, and which of their ideas were read and rejected.

## Packaging

The plugin root follows the [OpenAI plugin package layout](https://developers.openai.com/plugins/build/plugins): a required `.codex-plugin/plugin.json` beside optional skills and hooks. Root marketplace catalogs expose only `plugins/skiphow/`.
