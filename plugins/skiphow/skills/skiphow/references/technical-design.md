# Technical design

Open this when a technical, structural, or external-fact question is not already answered by the project: a dependency or service to introduce, a module boundary to draw, custom code a maintained component might replace, or an outside claim the choice rests on.

## Recovering the constraints

Recover the real constraints first: what the project already runs, the decisions it has made and why, the volumes and failure modes it faces, and the operational reality behind it.

Where that read comes back empty because the project is new, the constraints are not absent but unstated. What the thing has to handle, who will run it, and what it is expected to become are the owner's to supply. A shape chosen without them is chosen for a guess, and the first weeks of work harden that guess. Worth raising are the ones that would change the shape you would otherwise choose; those are product questions rather than technical ones — see [product](product.md).

Security, reliability, operability, performance, cost, and reversibility are lenses to apply in proportion to risk, not a checklist to complete for every task; name only the ones this decision actually touches.

## Reuse before custom code

Before introducing a subsystem, abstraction, dependency, infrastructure component, or service, work outward in this order and stop at the first level that genuinely fits — and again whenever existing custom code looks like it duplicates something mature.

- Capabilities the repository already has.
- Primitives in the language, framework, or platform.
- Official SDKs and maintained reference implementations.
- Mature third-party components.
- Managed services.
- A bounded spike.
- Only then, custom code.

Building your own carries the burden of proof. Choose it when maintained alternatives fail a material requirement or carry greater total risk or cost, and say which requirement they fail. Then build the smallest stable surface and do not recreate the surrounding ecosystem.

## Comparing options

Compare options that genuinely differ, against the same constraints. Two variants of one idea are not alternatives. Judge each on fit, maintenance health, security posture, license, integration complexity, the transitive surface it pulls in, lock-in, how it fails, and what migrating away would cost — weighted by how expensive the decision is to undo. Decisions the project has already recorded are settled; reopen one only when the friction against it is real. Where reading cannot settle a contested point, measure it.

A durable record earns its cost only where the choice is expensive to reverse, would look arbitrary later without its reasoning, and writing one is authorized; then follow the project's convention. Most decisions owe none.

## Structure that earns its cost

Judge a design by what callers must know; prefer fewer concepts and parameters when the module can own the complexity. Use the deletion test: if removing the module merely deletes indirection, it is too shallow; if its complexity would otherwise spread across callers, it is earning its place.

Introduce a seam when behavior truly varies, a system boundary needs an adapter, or testing needs a stable interface; not before there is a second caller or a real boundary. Pass external dependencies in and expose observable results rather than internal state. Around something adopted, keep the narrowest boundary that preserves the ability to replace it later, where that is cheap.

Where the work is to improve structure that already exists, scope the look before taking it: what the project's own history keeps returning to, and what the outcome has to touch. A deeper module pays for itself only where more change is coming, and a survey over the whole repository returns candidates nobody will act on.

## External facts

Verify current primary sources whenever an external fact, API, standard, price, limit, deprecation, or host behavior may have changed, rather than memory or a repository summary that may be stale. Read the local versions and configuration first, so what you find matches the project that will use it.

Prefer first-party documentation, specifications, source code, and release notes. Use secondary sources only to find primary material or to represent a viewpoint that has no primary owner. Check dates and versions, trace each material claim to a source, and separate what the source states from your inference.

## Bounded experiments

A disposable experiment is right when measurement is cheaper than debate. Say up front what result would settle the question, and choose the least fidelity that produces it. Make alternatives differ in the decision under test, not in decoration alone: place a screen question in real data and context where practical, and expose the state a logic question turns on.

Keep it cheap to run with the project's existing tools and cheap to discard — no production mutations, no persistent data, no abstractions built for later, no polish beyond the question. Throw the prototype away once it has answered, and implement the validated behavior properly rather than promoting the experiment.

## When an independent read earns its cost

A read from a context that did not produce the decision costs a run of its own, and earns it where the decision creates a high-consequence boundary: authentication or authorization, payments or financial integrity, an irreversible or destructive data migration, a durable public compatibility commitment, material security or privacy exposure, consequential production topology or a vendor commitment, or custom security- or reliability-critical machinery standing in for a mature component. Repository policy may require one elsewhere. A dependency, module interface, refactor, schema adjustment, or ordinary technical choice does not.

When you take one, hand over the problem, the constraints, and the evidence, and ask for independent analysis of it: what that context would choose, under what conditions the approach fails, and what would make the choice wrong. Asking whether it agrees mostly returns your own reasoning in someone else's words. Weigh what comes back as evidence rather than a vote, settle a material disagreement with a source or the smallest test that separates the two, and own the decision either way.
