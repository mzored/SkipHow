# Design

SkipHow is an owner–agent operating contract for verified project outcomes, shipped as an outcome-first orchestration policy at the instruction layer for strong coding agents. When selected or loaded, it supplies the policy for understanding an outcome, choosing the engineering method, instructing the host agent to coordinate work, and requiring fresh evidence before completion is reported. It is not a scheduler, database, model runner, control plane, or replacement for host permissions, and it proves nothing itself.

## Package shape

The repository ships one canonical package:

```text
plugins/skiphow/
  .codex-plugin/plugin.json
  .claude-plugin/plugin.json
  hooks/hooks.json
  skills/skiphow/
    SKILL.md
    references/
```

Both host manifests point to the same skill directory. The package contains one public skill named `skiphow`.

## Kernel and methods

`SKILL.md` is the owner kernel. It keeps authority, the trust boundary described below, autonomy, preservation of unrelated work, delegate safety, and honest completion in context.

The files under `references/` hold eight focused modules: product, technical design, diagnosis, verification, delegation, tracked work, integration, and writing for agents. The agent opens one when the expected contribution justifies the cost, judged from the uncertainty, risk, duration, observed failure, or repository requirements in front of it. A matching condition is a reason to consider a module, not an obligation to read it. A missed method cannot grant more authority or weaken completion because those rules stay in the kernel.

A module exists only if it meets four criteria: it covers one distinct failure domain, it gives a reason to consult it that is recognizable without opening it, it carries no critical invariant that is absent from the kernel, and it repeats no rule another module owns.

Methods are not routes or stages. The owner does not choose them. The agent can work directly, plan, delegate, review, or use a worktree when the project or task calls for it.

## Host boundary

Codex and Claude Code supply execution, permissions, tools, credentials, sessions, subagents, and continuation. SkipHow uses those capabilities without pretending to provide them.

This separates orchestration policy from the runtime. SkipHow tells the host agent how to plan, select methods, decompose, delegate, review, and reconcile when the request calls for those acts. The host runs the model and tools. A control plane, if one exists, owns durable workers, queues, scheduling, leases, budgets, and deployment.

SkipHow separates two categories of input, and the separation is policy rather than enforcement. Authoritative instructions are the owner's messages, host policy, and the repository instruction files the host loaded as instructions, at that host's own precedence and scope. Everything else is untrusted task data: issue and pull request bodies and comments, ordinary repository documents and code comments, fixtures, logs and tool output, web content, retrieved documents, text a delegate returns, and text embedded in data or in an external system.

Authoritative project instructions may narrow scope, require safeguards, and define normal procedure for the repository. They cannot widen the owner's authority over protected actions, and they cannot turn a read-only request into a write. Untrusted task data is evidence to analyze and never authority to follow. It cannot grant an external action, a credential, a disclosure, a deletion, or a wider scope, whatever it says about itself. This is the authoritative description of that boundary; other documents link here instead of restating it.

Instruction-level policy is probabilistic. It raises the odds that an agent behaves correctly and guarantees nothing, so a host-enforced control is preferred wherever the host provides one. Read-only profiles, sandboxes, permission prompts, and isolated checkouts do work that prose cannot.

The package includes one continuity hook. It prints a short load or reload reminder for startup, clear, compact, and resume events. The compact and resume reminder applies only where SkipHow is already governing the request. The hook does not load the skill, restore context, write project state, change permissions, or guarantee activation; on Codex it does not run until the user trusts it. Explicit invocation is the reliable portable mode, and implicit selection is `UNVERIFIED`. The deterministic check validates the hook's safety shape, an echo-only command with a bounded timeout, and not its matcher topology.

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
