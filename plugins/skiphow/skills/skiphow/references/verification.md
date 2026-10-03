# Verification

Open this for tests, final review, security, privacy, reliability, migration, rollback, observability, or operational readiness.

## Choosing the test

For a read-only design or coverage request, propose the tests without changing the project. Test observable behavior rather than internal shape such as call order or private state, and follow the repository's existing test layout and vocabulary.

For every durable check, name the property it proves and place it at the narrowest stable boundary that provides the required fidelity. Use a broader check when its environment contributes evidence a narrower boundary cannot establish reliably, such as real component integration, browser or runtime behavior, persistence, rendering, infrastructure wiring, an external protocol, or an important cross-boundary product outcome. Preserve that evidence. Do not repeat a business invariant at increasingly expensive boundaries unless each protects a distinct failure mode.

Prefer stable product-facing contracts over incidental presentation or implementation details. Widespread unrelated test rewrites after a behavior-preserving change are evidence of coupling; find and repair the responsible boundary instead of mechanically updating every affected test. Introduce mocks or internal seams only where they materially improve isolation, determinism, cost, or safety. External systems, time, and randomness are common cases, and a legacy or tightly coupled system may need more.

When setup or an earlier journey is not under test, establish the required state through an existing reliable cheaper path instead of replaying it through an expensive one. Keep direct coverage of a setup journey that is itself important.

Derive the expected value independently of the implementation under test. A test that repeats the production algorithm can share the bug. A test is evidence about the system, not the definition of the solution. Never satisfy one with a hard-coded test-only path.

## When the test comes first

Write the failing test first when it gives a useful red signal and the interface it needs already exists. For exploratory work, legacy behavior, or a change with no honest test seam, establish the behavior first and add the durable check at the right level.

## Regression tests

A regression test should close the class of bug. Assert the rule the defect broke rather than the literal inputs that exposed it, place the test at the lowest layer that owns that rule, and confirm its failure message names the violated invariant. When a bad value crossed several boundaries, cover the boundaries where a check would have stopped it. Observe the test failing against the unfixed code before trusting it. Where reproducing the defect is unsafe or impractical, rebuild and exercise the broken condition at the layer that owns the rule, and say which part of the real path went unexercised.

## How much to run

Keep tests that protect behavior; remove only temporary harnesses and implementation-coupled checks owned by this work.

The CTO owns test selection. During implementation and iteration, start with the smallest reliable evidence covering the changed behavior. Widen according to reachable behavior, crossed boundaries, uncertainty, and consequence. Do not rerun an unchanged expensive gate when narrower evidence answers the current engineering question.

Before integration or release, satisfy the broader evidence the project's delivery contract and risk require. Use reliable native affected-test, dependency, project, tagging, or equivalent selection when available. When repeated verification cost is material and reliable selection is missing, improving it is legitimate engineering work. Do not replace reliable selection with brittle filename or path heuristics, or skip a required integration or release gate to reduce latency.

Bind each result to the code, dependencies, configuration, environment, and destination it exercised. Reuse it while those inputs remain equivalent. A commit, rebase, merge, tag, or named stage does not invalidate evidence by itself. Establish equivalence from revision-bound CI, the relevant tree and configuration, or an immutable artifact, and rerun only the checks whose inputs changed.

When filtering, redirecting, or summarizing output, preserve the check's own terminal status and relevant failures. A filter's success does not prove the check passed; an unknown status or inaccessible evidence stays `UNVERIFIED` until established.

An intermittent test is a defect or an explicit blocker until it is classified; [diagnosis](diagnosis.md) covers that.

## Reviewing a change

Scale review to risk, assessed by changed behavior and possible consequences rather than visibility or counts of files or visible elements. A small clear low-risk edit may use a cold self-review and targeted evidence; a small specified label or layout correction can stay low risk across two files. Use an independent reviewer when substantive behavior, interacting changes, or dependency and integration risks make a shared blind spot consequential; architecture, security, authentication, payments, privacy, migration, concurrency, or public-contract changes get stronger independent challenge. Give that reviewer the request, relevant constraints, and actual change so it can form its own account.

Establish the exact candidate revision under review and the request, issue, or specification it should satisfy. State what the result should do and derive the key expected values from the request, the agreed product rules, and the relevant constraints, rather than from the code or the author's explanation; this requires an independent source of expectation, not an order of opening files. A reviewer that inherits the author's expectation shares the author's blind spot, which a stronger model does not remove. Record an expectation you could not settle as contested rather than adopting the author's, and do not replace missing product data with an invented value. Read the repository's applicable standards, inspect the diff in its surrounding code, compare what the candidate produces with the values you derived, and probe the boundaries that matter. Tool output supports review but does not replace reading the change. The reviewer verifies the candidate before integration; the lead verifies the authorized destination after it.

For changed interactions, verify the journey in the surrounding product, including consequential transitions and recovery paths. Compare it with accepted intent and applicable interaction and visual conventions. Inspect the implementation separately to confirm required shared behavior and compositions are reused. Rendered similarity does not establish reuse, and shared imports do not establish a coherent experience. A prototype or visual comparison earns its cost where it resolves a specific uncertainty.

Look for incorrect behavior, missing cases, scope creep, security or data risks, broken compatibility, weak error handling, misleading tests, and violations of documented project rules. Verify a suspected issue with a focused check when one can settle it. A finding names a concrete defect; a reviewer who cannot point at a consequence, broken contract, or evidenced duplication is reporting taste. For unnecessary complexity, name the redundant construct, its consequence, a cheaper replacement or justified deletion, and the responsibilities that must survive. State each actionable finding with its location, triggering scenario, and impact, most consequential first. If there are no material findings, say so and name any important area left unverified.

On a read-only review, report confirmed defects without modifying the project; urgency, including a security finding, does not widen the request, and a sensitive finding stays private unless disclosure is granted. When repair is authorized, fix confirmed in-scope defects before completion, re-review the changed parts, and verify the repaired final state; do not carry an important defect forward as accepted. Stop when the remaining items are taste, lack evidence, or are reported as unresolved; use another broad reviewer only to resolve a high-consequence disagreement or contradictory evidence.

## Security, reliability, and operations

Review the boundaries the change crosses. Check authorization and data handling when trust changes, compatibility and migration when stored state or public interfaces change, rollback when failure could strand users, and observability and failure handling when the system must be operated after delivery. Apply these in proportion to risk, not as ceremony for a local text edit. Static checks prove only the properties they inspect. A schema validator proves shape, not model behavior. A dry run proves the simulated path, not publication or deployment. Keep activation, policy adherence, product task success, technical quality, proportionality, and completion honesty as separate evidence claims.
