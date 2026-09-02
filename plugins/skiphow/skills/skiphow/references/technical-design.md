# Technical design

Use this for a technology, architecture, or system-shape choice that nothing already in the project answers, or for a maintained capability that may replace existing custom code. Own the choice. A material decision about technology, architecture, or the shape of a system belongs to the agent, not to the owner.

## Recovering the constraints

Recover the real constraints first: what the project already runs, the decisions it has already made and why, the volumes and failure modes it actually faces, and the operational reality behind it. Check the facts that move against current primary sources rather than memory: versions, limits, pricing, deprecations, platform behavior.

Where that read comes back empty because the project is new, the constraints are not absent but unstated. What the thing has to handle, who will run it, and what it is expected to become are the owner's to supply. A shape chosen without them is chosen for a guess, and the first weeks of work then harden that guess.

Ask only for the ones that would change the shape you would otherwise choose. Ask once, with the recommendation, inside the round [product decisions](product-decisions.md) already runs. Where the request already implies them, take that and ask nothing. Keep the question to what the product has to do rather than to how it would be built.

Name only the qualities this decision actually touches. Security, reliability, operability, performance, cost, and reversibility are lenses to apply in proportion to risk, not a checklist to complete for every task.

## Reuse before custom code

Before introducing a subsystem, abstraction, dependency, infrastructure component, or service, work outward in this order and stop at the first level that genuinely fits. Do the same whenever existing custom code looks like it duplicates something mature.

- Capabilities the repository already has.
- Primitives in the language, framework, or platform.
- Official SDKs and maintained reference implementations.
- Mature third-party components.
- Managed services.
- A bounded spike.
- Only then, custom code.

Building your own carries the burden of proof. Choose it when maintained alternatives fail a material requirement or carry greater total risk or cost, and say which requirement they fail. When you do build, build the smallest stable surface and do not recreate the surrounding ecosystem. When you adopt something, keep the narrowest boundary that preserves the ability to replace it later, where that boundary is cheap.

## Comparing options

Compare options that genuinely differ, against the same constraints. Two variants of one idea are not alternatives. Judge each on functional and architectural fit, maintenance health, security posture, license, and integration complexity. Judge it as well on the transitive surface it pulls in, operability, lock-in, what it forces future work to do, how it fails, and what it would cost to migrate away. Weight those in proportion to how expensive the decision is to undo. When reading cannot settle a contested point, measure it or build the smallest disposable experiment that can.

## What the owner settles

An option that commits money, an account, credentials, or a vendor relationship is not yours to accept on technical merit alone. Recommend it with its consequence and let the owner commit, and treat the account, credential, and payment steps as the protected actions they are.

Decide, then act. Bring the owner only what changes visible behavior, priority, cost, risk, privacy, or rollout, expressed as consequences rather than technology names.

## The outside read

Take one read from a context that did not produce the decision whenever the choice becomes something later work has to build on: a dependency or service the project then runs on, a schema or a data migration, an interface other code calls across a module or a network, a security, concurrency, or deployment boundary, or custom code chosen over a maintained alternative. An implementation choice that lives in one file is outside this rule while nothing outside that file depends on it: no other code, no data, no configuration, no deployed behavior, and nothing this same change establishes as a boundary for later work. Each of those is a fact about what you are about to do rather than your own estimate of what it would cost to undo, and the estimate is the part a run gets wrong about its own decision. Hand over the problem, the constraints, and the evidence, and ask what it would choose and what would make that choice wrong. Asking whether it agrees with you mostly returns your own reasoning in someone else's words.

Where the host offers a second agent runtime or model family, prefer it, because your own second pass carries your first pass's assumptions. Where it offers neither, a fresh context given the problem and the evidence alone is still worth more than rereading your own reasoning. Weigh what comes back as evidence rather than a vote. Settle a material disagreement with a source or the smallest test that separates the two, and own the decision either way.

## Recording the decision

Record a decision durably only when it is expensive to reverse and would look arbitrary later without its reasoning. Follow the project's existing convention for such records.
