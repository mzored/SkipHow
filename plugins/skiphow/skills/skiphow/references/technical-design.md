# Technical design

Open this before adding a dependency, service, module, abstraction, or tooling, and when a choice rests on an outside fact. The [kernel](../SKILL.md)'s Engineering standard sets the bar; this file is method for meeting it.

## Recovering the constraints

Start from what the project already runs, the decisions it made and why, the volumes and failure modes it faces, and who operates it. In a new project some constraints may be unstated: what it must handle, who will run it, and what it should become. Ask the owner only for the ones that would change the choice; see [product](product.md).

Use host skills and tools when their benefit warrants the cost. Honor an explicit invocation or a host requirement. Otherwise read the available capability descriptions and pick what fits the work, because a capability's name alone does not prove fit. Resolve its instructions under the host's instruction hierarchy and the owner's constraints. When no specialist support fits, continue with what you have and report a material quality or verification gap if one remains. Selecting a capability authorizes no installation, spending, disclosure, or wider scope.

Security, reliability, operability, performance, cost, and reversibility are lenses, not a checklist. Name only the ones this decision touches, in proportion to its risk.

## Reuse before custom code

Pick the option with the lowest total cost that delivers the accepted behavior. Look in this order, and look again when custom code turns out to duplicate something mature:

- what the repository already has
- the language, framework, or platform
- official SDKs and maintained reference implementations
- mature third-party components
- managed services
- a small disposable spike
- custom code

The order is a presumption. A managed service or new dependency can bring recurring cost, privacy exposure, vendor commitment, or lock-in. Those consequences are the owner's call under [product](product.md), and a small custom implementation can beat them.

Find which implementation currently owns the behavior before you build. Similar names, appearance, or age do not make code the maintained choice. Existing code is a fact about the project, not a reason to keep extending something that no longer fits. Reuse a maintained composition that fits; shared tokens and primitive controls alone do not justify recreating one. A project without a design system gets the shared pieces this work needs, not a migration.

Custom code must name the requirement the maintained options fail. Then build the smallest stable surface and do not recreate the ecosystem around it. Custom tooling for the project itself, such as a test selector, gate, queue, wrapper, or report generator, needs a measured need that the runner, CI provider, or linter cannot meet through its own configuration.

## Comparing options

Compare materially different options against the same constraints: fit, maintenance, security, license, integration and dependency weight, lock-in, failure behavior, and migration cost, weighted by how hard each is to reverse. Measure a contested point that reading cannot settle.

Design it twice for a consequential interface, one that many callers, stored data, or outside consumers will depend on. Sketch two materially different shapes, compare what each makes callers know, then build one. An ordinary internal function does not need this.

Reopen a settled decision when real friction changes its premises. Record a decision only when reversing it is expensive and the reason will matter later, and put it where the project already keeps such reasons. Most decisions need no record; the code and the commit message carry them.

## Structure that earns its cost

Judge a design by what callers must know. Prefer fewer concepts and parameters when the module can own the complexity. Apply the deletion test: if removing a module only deletes indirection, it is too shallow and should go; if its complexity would otherwise spread across callers, it earns its place. Pass outside dependencies in and expose observable results rather than internal state.

One adapter is a hypothetical seam. Wait for a second real implementation or a real system boundary before adding the interface. Around something adopted, keep the narrowest boundary that still lets you replace it, where that is cheap. Similarity between two pieces of code is not by itself a reason for an abstraction.

Where one implementation must keep owning a behavior, make the owner obvious in code: one module, one name, and callers that go through it. If a mechanical rule is needed, such as a forbidden import, wire it into the existing linter or type checker rather than writing a test that reads source.

Refactoring keeps behavior and compatibility for the outside consumers the kernel names. Before deleting, check what still calls it. Keep a large structural change in reviewable, recoverable units, separate from behavior changes when that makes review or rollback easier; small related cleanup stays with the fix. A unit needs no PR or full gate of its own.

Passing checks do not prove the project is healthy. While you work, notice material risks and costs that accumulate across the authorized project: a rule copied in several places, tests or tooling outgrowing the product, dependencies drifting, paths nobody uses. Ask whether an existing solution still fits the problem it now serves. Choose an improvement by its benefit against the cost of investigating, migrating, and checking it, and handle it as the kernel handles a confirmed finding. A healthy simple task finishes without a survey.

## Data lifecycle

Use the simplest mechanism that meets the requirement. A retention job that deletes expired rows beats a journal of deletions. Add history, audit trails, or soft deletes only when a requirement such as law, money, or customer support needs them.

## External facts

Verify current primary sources whenever an external fact, API, standard, price, limit, deprecation, or host behavior may have changed, because memory and repository summaries go stale. Read the local versions and configuration first so what you find matches what the project runs. Prefer first-party documentation, specifications, source, and release notes. Use secondary sources to find primary material or for a viewpoint no one owns. Check dates and versions, trace each material claim to its source, and keep what the source says apart from what you infer.

## Bounded experiments

Run a disposable experiment when measuring is cheaper than debating. Say first what result would settle the question, and choose the least fidelity that produces it. Make the alternatives differ in the decision under test: put a screen question in real data and context where practical, and expose the state a logic question turns on.

Keep it cheap to run and to throw away: the project's existing tools, no production changes, no persistent data, no abstractions for later, no polish, and no tests. Its shortcuts do not become architecture by staying. Throw it away when its assumptions or quality fall short of production needs. Harden it in place only as a deliberate choice, when that is the smallest honest implementation and its remaining consequences are authorized.

## When an independent read earns its cost

A read from a context that did not make the decision costs a run of its own. It earns that where a mistake is expensive to find or undo: authentication or authorization, money, an irreversible data migration, a lasting public compatibility promise, security or privacy exposure, production topology or a vendor commitment, or custom machinery standing in for a mature security or reliability component. Repository policy may require one elsewhere. An ordinary dependency, interface, refactor, or schema change does not.

Give the reviewer the problem, the constraints, and what you found. Ask what it would choose, where the approach fails, and what would make it wrong, not whether it agrees. Treat the answer as claims to check, settle a real disagreement with a source or the smallest experiment that tells the options apart, and own the decision.
