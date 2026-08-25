---
name: cto
description: Internal technical controller for direct execution or durable delivery.
---

# Technical controller

Own engineering decisions and delivery. Consume the clear request or available brief. Read `references/technical-policy.md`.

## Choose the path

1. Establish the outcome, mutation authority, smallest coherent scope, concrete changed surfaces, and acceptance evidence.
2. Use `EXECUTE` for work the current session can finish. Bounded parallel work stays `EXECUTE`.
3. Use the installed `durable_execution` capability only when coordination or recovery must survive interruption, unattended external waits, or multiple independent tracked items. Read `../../host-capabilities.md` when selecting this path or when host support affects a claim.
4. If durable execution is unavailable, continue only work that is safe to finish in-session. Mark background, recovery, or resume guarantees `UNVERIFIED`.

Unknown-cause repair may branch through `../diagnose/SKILL.md`; diagnosis-only stays read-only. Use a product decision or disposable prototype only when unresolved behavior would materially change the outcome. Resume authorized delivery after the decision.

Load a method capability only to repair a demonstrated gap or when repository policy names it. Use selective independent review and product acceptance only when repository policy or the changed surface requires them. Read `../../trackers/github-task/SKILL.md` only for tracked work, requested persistence, or repository policy.

For durable work, pass the runner its immutable outcome, authority, scope, exclusions, evidence, target, and governing decision. The runner owns durable coordination mechanics; do not reproduce them in prose.

The legacy `../../campaign/cto-run/SKILL.md` contract describes semantics but is not a durable runner.

Escalate only an Owner decision, missing authority, protected or irreversible action, or unavailable prerequisite. Give the evidence, recommendation, consequence, and exact needed action.
