# Verification

Open this for tests, final review, security, privacy, reliability, migration, rollback, observability, or operational readiness.

## Choosing the test

For a read-only design or coverage request, propose the tests without changing the project. Test observable behavior rather than internal shape such as call order or private state, and follow the repository's existing test layout and vocabulary.

For every durable check, name the property it proves and place it at the narrowest stable boundary that provides the required fidelity. Use a broader check when its environment contributes evidence a narrower boundary cannot establish reliably, such as real component integration, browser or runtime behavior, persistence, rendering, infrastructure wiring, an external protocol, or an important cross-boundary product outcome. Preserve that evidence. Do not repeat a business invariant at increasingly expensive boundaries unless each protects a distinct failure mode.

Prefer stable product-facing contracts over incidental presentation or implementation details. Widespread unrelated test rewrites after a behavior-preserving change are evidence of coupling; find and repair the responsible boundary instead of mechanically updating every affected test. Introduce mocks or internal seams only where they materially improve isolation, determinism, cost, or safety. External systems, time, and randomness are common cases, and a legacy or tightly coupled system may need more.

When setup or an earlier journey is not under test, establish the required state through an existing reliable cheaper path instead of replaying it through an expensive one. Keep direct coverage of a setup journey that is itself important.

Derive expected values independently of the implementation. Fixed examples from product rules can make a test clear; repeating the production algorithm can share its bug. Repeated test data or coverage is useful when it improves clarity or protects a distinct failure mode. Judge by evidence, not literals or repetition alone. Never satisfy a test with a hard-coded test-only path.

## When the test comes first

Write the failing test first when it gives a useful red signal and the interface it needs already exists. For exploratory work, legacy behavior, or a change with no honest test seam, establish the behavior first and add the durable check at the right level.

## Regression tests

A regression test should close the class of bug. Assert the rule the defect broke rather than the literal inputs that exposed it, place the test at the lowest layer that owns that rule, and confirm its failure message names the violated invariant. When a bad value crossed several boundaries, cover the boundaries where a check would have stopped it. Observe the test failing against the unfixed code before trusting it. Where reproducing the defect is unsafe or impractical, rebuild and exercise the broken condition at the layer that owns the rule, and say which part of the real path went unexercised.

## How much to run

Preserve required behavioral evidence. Within authority, consolidate, replace, or remove pre-existing checks when evidence shows they are redundant, obsolete, or coupled to an incidental implementation; retain or establish equivalent reliable proof of every required property and distinct failure mode. A test's age or cost alone does not justify deletion.

The CTO owns test selection. During implementation and iteration, use the smallest reliable evidence covering the changed behavior, widening by reachable behavior, crossed boundaries, uncertainty, and consequence. Frequent cheap checks can support safe refactoring. Inspect what a command selects, costs, and changes; repair material friction through [operations](operations.md). Do not rerun an unchanged expensive gate when narrower evidence answers the question.

Before integration or release, satisfy the broader evidence the project's delivery contract and risk require. Use reliable native affected-test, dependency, project, tagging, or equivalent selection when available. When repeated verification cost is material and reliable selection is missing, improving it is legitimate engineering work. Do not replace reliable selection with brittle filename or path heuristics, or skip a required integration or release gate to reduce latency.

Bind each result to the code, dependencies, configuration, environment, and destination it exercised. Reuse it while those inputs remain equivalent. A commit, rebase, merge, tag, or named stage does not invalidate evidence by itself. Establish equivalence from revision-bound CI, the relevant tree and configuration, or an immutable artifact, and rerun only the checks whose inputs changed.

When filtering, redirecting, or summarizing output, preserve the check's own terminal status and relevant failures. A filter's success does not prove the check passed; an unknown status or inaccessible evidence stays `UNVERIFIED` until established.

An intermittent test is a defect or an explicit blocker until it is classified; [diagnosis](diagnosis.md) covers that.

## Reviewing a change

Scale review to behavior and consequences, not file or element counts. Clear low-risk edits may use cold self-review and focused evidence, including visual edits across files. Use independent review for consequential shared blind spots in substantive behavior, interactions, dependencies, or integration. Architecture, security, authentication, payments, privacy, migration, concurrency, and public contracts need stronger challenge.

Establish the candidate and governing request, issue, or specification. Derive expectations independently from accepted product rules and constraints; another reading order or stronger model does not remove inherited expectations. Mark contested expectations without inventing product data. Read repository standards and the change in context, then probe consequential boundaries. The reviewer checks the candidate; the lead checks the authorized destination.

Use [delegation's brief contract](delegation.md#the-brief): request, constraints, candidate, scope, sufficient evidence, and return conditions. For lengthy review convey [diagnosis's progress expectation](diagnosis.md#long-work-that-stops-producing-evidence). A missed expectation prompts reassessment and return of findings, evidence, and unchecked scope, not a passing verdict or a universal deadline.

Verify changed journeys in product context, including transitions and recovery, against accepted intent and interaction and visual conventions. Inspect required shared behavior and compositions separately: visual similarity proves no reuse, and shared imports prove no coherent experience. Prototype or compare visually to resolve a specific uncertainty.

Check behavior, missing cases, scope, security and data risks, compatibility, error handling, tests, and project rules. Settle suspected defects with focused checks. A finding names a consequence, broken contract, or evidenced duplication; otherwise it is taste. Complexity findings identify redundancy, consequence, a cheaper replacement or justified deletion, and surviving responsibilities. Report location, scenario, and impact, most consequential first, plus important unchecked areas even when there are no findings.

Read-only review reports defects without edits. Urgency grants no repair authority; sensitive findings stay private unless disclosure is granted. When repair is authorized, the lead confirms findings against evidence and has qualifying in-scope defects repaired. Retain implementer and reviewer through corrections where supported; replacements receive findings, dispositions, candidate identity, and evidence. The lead corrects plans.

After independent review, obtain targeted independent review of material corrections and affected consequences. Supply the prior candidate, changes, and dispositions. Reuse still-applicable evidence; widen for a concrete risk or invalidated evidence, not repeated unchanged investigation. Revalidate affected checks on the final candidate. Stop when no supported material defect remains, or report unresolved work and affected readiness limits. Another broad reviewer needs high-consequence disagreement or contradictory evidence. Incomplete review never establishes reviewed readiness.

## Security, reliability, and operations

Review the boundaries the change crosses. Check authorization and data handling when trust changes, compatibility and migration when stored state or public interfaces change, rollback when failure could strand users, and observability and failure handling when the system must be operated after delivery. Apply these in proportion to risk, not as ceremony for a local text edit. Static checks prove only the properties they inspect. A schema validator proves shape, not model behavior. A dry run proves the simulated path, not publication or deployment. Keep activation, policy adherence, product task success, technical quality, proportionality, and completion honesty as separate evidence claims.
