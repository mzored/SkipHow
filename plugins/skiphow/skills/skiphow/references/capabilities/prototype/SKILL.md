---
name: prototype
description: Internal disposable-prototype capability for resolving one uncertain UI, interaction, logic, or state-model question before production implementation.
---

# Prototype

Use this capability only when the unknown is the desired interaction or state model. Unknown causes belong to `../../engineering/diagnose/SKILL.md`; known behavior with an uncertain implementation remains a CTO engineering decision.

Name one design question and the evidence that would answer it. Build the smallest disposable artifact that lets the relevant person compare behavior or drive difficult states. Prefer the project's existing runtime and conventions, keep state in memory, expose the relevant state after each action, and make the artifact runnable with one obvious command or action.

Mark the artifact as a prototype. Do not add production abstractions, persistence, comprehensive error handling, or tests unless one of those is itself the question being tested. Do not silently turn prototype code into production code.

Present the alternatives or walkthrough to the Product Director or Owner whose product judgment is required. Record the question, observed evidence, verdict, and any remaining uncertainty. Then remove the prototype from the production candidate and carry only the validated decision into normal `EXECUTE`. Preserve the prototype outside the delivery branch only when it remains useful primary evidence and the repository has an approved place for disposable artifacts.

This adaptation is informed by the pinned source described in `upstream/SOURCE.md`. SkipHow's authority, scope, and lifecycle policy take priority.
