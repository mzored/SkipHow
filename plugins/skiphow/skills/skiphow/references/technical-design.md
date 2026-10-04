# Technical design

Open this when a technical, structural, or external-fact question is not already answered by the project: specialist skills or tools to apply, a dependency or service to introduce, a module boundary to draw, custom code a maintained component might replace, or an outside claim the choice rests on.

## Recovering the constraints

Recover the real constraints first: what the project already runs, the decisions it has made and why, the volumes and failure modes it faces, and the operational reality behind it.

In a new project, material constraints may be unstated: what it must handle, who will run it, and what it should become. Ask the owner only for those that would change the choice; see [product](product.md).

Use the host's available capability descriptions to identify specialist guidance and tools relevant to the work. Honor explicit invocations and host requirements. Otherwise, read and apply suitable guidance where its expected contribution justifies its cost. Choose from what is actually available; a capability's name or presence alone does not establish its fit.

Resolve its instructions under the host's instruction hierarchy and the owner's constraints. Continue with sufficient available methods when specialist support is absent, and report a material quality or verification gap when one remains. Selection does not itself authorize installation, spending, disclosure, or wider scope.

Security, reliability, operability, performance, cost, and reversibility are lenses to apply in proportion to risk, not a checklist to complete for every task; name only the ones this decision actually touches.

## Reuse before custom code

Choose the lowest total cost among solutions that preserve the complete accepted behavior. A short diff, built-in feature, or installed dependency qualifies only when it meets the real constraints. Prefer maintained capabilities over custom machinery. Before introducing a subsystem, abstraction, dependency, infrastructure component, or service, look outward roughly in this order, and again when custom code duplicates something mature:

- Capabilities the repository already has.
- Primitives in the language, framework, or platform.
- Official SDKs and maintained reference implementations.
- Mature third-party components.
- Managed services.
- A bounded spike.
- Only then, custom code.

The order is a presumption, not a law. Compare materially different options when cost, privacy, reliability, security, lock-in, operational burden, or reversibility could change the result; a managed service is not automatically preferable to a bounded experiment or a small custom implementation when it brings owner-visible cost, privacy exposure, vendor commitment, or lock-in, and those consequences are the owner's choice under [product](product.md).

Repository capabilities include maintained domain compositions, interaction behavior, navigation patterns, and styling conventions. Establish which implementation currently owns the required behavior. Similar names, appearance, or historical presence do not make an implementation the maintained choice.

Evaluate keeping, simplifying, replacing, or removing the current implementation against the complete accepted behavior and total cost. Existing code is evidence, not a reason to keep extending an unsuitable solution. Reuse maintained compositions that fit; shared tokens and primitive controls alone do not justify recreating one. A bounded replacement is valid when it meets a requirement at lower total cost. A project without a design system gets the shared vocabulary and compositions the work needs, not a whole-system migration.

Building your own carries the burden of proof. Choose it when maintained alternatives fail a material requirement or carry greater total risk or cost, and say which requirement they fail. Then build the smallest stable surface and do not recreate the surrounding ecosystem.

## Comparing options

Compare materially different options against the same constraints: fit, maintenance, security, license, integration and dependency complexity, lock-in, failure, and migration cost, weighted by reversibility. Reopen a settled decision only when real friction changes its premises. Measure a contested point that reading cannot settle.

Record an authorized decision using project conventions when reversing it is expensive and its reasoning matters later. Most decisions need no record.

## Structure that earns its cost

Judge a design by what callers must know; prefer fewer concepts and parameters when the module can own the complexity. Use the deletion test: if removing the module merely deletes indirection, it is too shallow; if its complexity would otherwise spread across callers, it is earning its place.

Introduce a seam when behavior truly varies, a system boundary needs an adapter, or testing needs a stable interface; not before there is a second caller or a real boundary. Pass external dependencies in and expose observable results rather than internal state. Around something adopted, keep the narrowest boundary that preserves the ability to replace it later, where that is cheap.

Look across the authorized project where evidence suggests material risk or recurring cost, using its history, dependencies, failures, and working paths to direct attention. Choose actionable improvements by consequence and expected benefit relative to investigation, migration, verification, and maintenance cost. A healthy simple task can finish without a survey or refactor. Stop expanding the search when it no longer advances the owner's outcome enough to justify the cost.

Repair the supported class at its responsible boundary, including affected sibling paths; similarity alone does not justify a new abstraction. Refactoring preserves required external behavior and compatibility. Establish missing behavioral evidence where needed before replacing legacy logic or compositions, then remove superseded pieces only after accounting for their callers and responsibilities. Prefer incremental replacement when it lowers risk. Keep substantial structural changes in coherent reviewable and recoverable units, separate from behavior changes when that improves reasoning or rollback; small related cleanup can stay with the fix. A unit need not trigger its own PR or full gate. Authority and delivery remain the kernel's, including during iteration.

## External facts

Verify current primary sources whenever an external fact, API, standard, price, limit, deprecation, or host behavior may have changed, rather than memory or a repository summary that may be stale. Read the local versions and configuration first, so what you find matches the project that will use it.

Prefer first-party documentation, specifications, source code, and release notes. Use secondary sources only to find primary material or to represent a viewpoint that has no primary owner. Check dates and versions, trace each material claim to a source, and separate what the source states from your inference.

## Bounded experiments

A disposable experiment is right when measurement is cheaper than debate. Say up front what result would settle the question, and choose the least fidelity that produces it. Make alternatives differ in the decision under test, not in decoration alone: place a screen question in real data and context where practical, and expose the state a logic question turns on.

Keep it cheap to run with the project's existing tools and cheap to discard — no production mutations, no persistent data, no abstractions built for later, no polish beyond the question. An experiment's shortcuts do not become production architecture by staying in place. Discard it when its assumptions or implementation quality make it unsuitable; harden it in place only deliberately, when that is the smallest honest implementation, the resulting design meets production requirements, and its remaining consequences are authorized.

## When an independent read earns its cost

A read from a context that did not produce the decision costs a run of its own, and earns it where the decision creates a high-consequence boundary: authentication or authorization, payments or financial integrity, an irreversible or destructive data migration, a durable public compatibility commitment, material security or privacy exposure, consequential production topology or a vendor commitment, or custom security- or reliability-critical machinery standing in for a mature component. Repository policy may require one elsewhere. A dependency, module interface, refactor, schema adjustment, or ordinary technical choice does not.

Give the reviewer the problem, constraints, and evidence. Ask what it would choose, where the approach fails, and what would make it wrong, rather than asking for agreement. Weigh its return as evidence, settle material disagreement with a source or the smallest discriminating test, and own the decision.
