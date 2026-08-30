# Design

SkipHow is a small instruction package for strong coding agents. It is not a scheduler, database, model router, or replacement for host permissions.

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

`SKILL.md` is the owner kernel. It keeps authority, autonomy, preservation of unrelated work, and honest completion in context.

The files under `references/` hold focused methods for diagnosis, research, testing, review, delivery, and other tasks. The agent reads one when it helps the current request. A missed method cannot grant more authority or weaken completion because those rules stay in the kernel.

Methods are not routes or stages. The owner does not choose them. The agent can work directly, plan, delegate, review, or use a worktree when the project or task calls for it.

## Host boundary

Codex and Claude Code supply execution, permissions, tools, credentials, sessions, and continuation. SkipHow uses those capabilities without pretending to provide them.

The package includes one continuity hook. It prints a short load or reload reminder for startup, clear, compact, and resume events. The hook does not load the skill, restore context, write project state, or change permissions.

## Public site visual system

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
