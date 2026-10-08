# Verification

Open this for tests, final review, security, privacy, reliability, migration, rollback, observability, or operational readiness.

## Choosing the test

For read-only design or coverage, propose tests without edits. Test observable behavior, not call order or private state, using the repository's test layout and vocabulary.

Name what each durable check proves and use the narrowest stable boundary with the required fidelity. Broader checks earn their cost when real integration, browser or runtime behavior, persistence, rendering, infrastructure, external protocols, or important cross-boundary outcomes provide evidence a narrower check cannot. Preserve that evidence. Repeat a business invariant at costlier boundaries only for distinct failure modes.

Prefer stable product contracts over incidental presentation or implementation. Unrelated test rewrites after behavior-preserving changes indicate coupling; repair the responsible boundary. Use mocks or internal seams where they materially improve isolation, determinism, cost, or safety, often for external systems, time, randomness, legacy or tightly coupled code.

When setup or an earlier journey is not under test, establish the required state through an existing reliable cheaper path instead of replaying it through an expensive one. Keep direct coverage of a setup journey that is itself important.

Derive expected values independently of the implementation. Fixed examples from product rules can make a test clear; repeating the production algorithm can share its bug. Repeated test data or coverage is useful when it improves clarity or protects a distinct failure mode. Judge by evidence, not literals or repetition alone. Never satisfy a test with a hard-coded test-only path.

## When the test comes first

Write the failing test first when it gives a useful red signal and the interface it needs already exists. For exploratory work, legacy behavior, or a change with no honest test seam, establish the behavior first and add the durable check at the right level.

## Regression tests

A regression test should close the class of bug. Assert the rule the defect broke rather than the literal inputs that exposed it, place the test at the lowest layer that owns that rule, and confirm its failure message names the violated invariant. When a bad value crossed several boundaries, cover the boundaries where a check would have stopped it. Observe the test failing against the unfixed code before trusting it. Where reproducing the defect is unsafe or impractical, rebuild and exercise the broken condition at the layer that owns the rule, and say which part of the real path went unexercised.

## How much to run

Preserve proof of every required property and distinct failure mode. Within authority, consolidate, replace, or remove checks shown redundant, obsolete, or coupled to incidental implementation, retaining equivalent reliable coverage. Age or cost alone justifies no deletion.

The CTO selects the smallest reliable evidence for changed behavior, widening for reachable behavior, crossed boundaries, uncertainty, and consequence. Cheap checks can support refactoring. Inspect command selection, cost, and effects; use [operations](operations.md) for material friction. Satisfy required delivery evidence before integration or release. Prefer reliable native affected-test or dependency selection; improving missing selection is legitimate engineering when verification cost is material. Brittle path heuristics and skipped required gates provide no substitute.

### Reusing a verification record

Keep the command and arguments, checked tree fingerprint, terminal exit status, completion time, checkout, and accessible evidence location in an existing log or handoff. Include relevant environment context: dependencies, configuration, external or ignored inputs, services, and destination. No new file or ledger is required. The fingerprint must identify the state actually checked; source changes during execution or an uncertain capture leave applicability unverified.

Delegates, leads, and reviewers inspect and reuse a recorded pass for the same command and fingerprint while the relevant environment is unchanged. Accepting a return, reviewing, integrating, or reporting requires inspecting that record and current inputs, not another execution. Rerun only for changed inputs, missing or unverifiable evidence, or a concrete named doubt. Scratch files or service state may change without changing the repository fingerprint. A different tree requires evidence for that candidate, including revision-bound CI where available. Role and stage transitions invalidate nothing by themselves. Required coverage, independent review, and destination checks remain necessary.

Preserve the check's own terminal status and relevant failures when filtering or shortening output. A filter's success proves no check passed. Unknown status or inaccessible evidence stays `UNVERIFIED` until established. An intermittent test remains a defect or explicit blocker until classified under [diagnosis](diagnosis.md).

## Reviewing a change

Scale review to behavior and consequences, not file or element counts. Clear low-risk edits may use cold self-review and focused evidence, including visual edits across files. Use independent review for consequential shared blind spots in substantive behavior, interactions, dependencies, or integration. Architecture, security, authentication, payments, privacy, migration, concurrency, and public contracts need stronger challenge.

Establish the candidate and governing request, issue, or specification. Derive expectations independently from accepted product rules and constraints; another reading order or stronger model does not remove inherited expectations. Mark contested expectations without inventing product data. Read repository standards and the change in context, then probe consequential boundaries. The reviewer checks the candidate; the lead checks the authorized destination.

Use [delegation's brief contract](delegation.md#the-brief): request, constraints, candidate, scope, sufficient evidence, and return conditions. For lengthy review convey [diagnosis's progress expectation](diagnosis.md#long-work-that-stops-producing-evidence). A missed expectation prompts reassessment and return of findings, evidence, and unchecked scope, not a passing verdict or a universal deadline.

Verify changed journeys in product context, including transitions and recovery, against accepted intent and interaction and visual conventions. Inspect required shared behavior and compositions separately: visual similarity proves no reuse, and shared imports prove no coherent experience. Prototype or compare visually to resolve a specific uncertainty.

Check behavior, missing cases, scope, security and data risks, compatibility, error handling, tests, and project rules. Settle suspected defects with focused checks. A finding names a consequence, broken contract, or evidenced duplication; otherwise it is taste. Complexity findings identify redundancy, consequence, a cheaper replacement or justified deletion, and surviving responsibilities. Report location, scenario, and impact, most consequential first, plus important unchecked areas even when there are no findings.

Read-only review reports defects without edits. Urgency grants no repair authority; sensitive findings stay private unless disclosure is granted. When repair is authorized, the lead confirms findings against evidence and has qualifying in-scope defects repaired. Retain implementer and reviewer through corrections where supported; replacements receive findings, dispositions, candidate identity, and evidence. The lead corrects plans.

After independent review, obtain targeted independent review of material corrections and affected consequences. Supply the prior candidate, changes, and dispositions. Reuse still-applicable evidence; widen for a concrete risk or invalidated evidence, not repeated unchanged investigation. Establish applicable evidence for affected checks on the final candidate. Stop when no supported material defect remains, or report unresolved work and affected readiness limits. Another broad reviewer needs high-consequence disagreement or contradictory evidence. Incomplete review never establishes reviewed readiness.

## Security, reliability, and operations

Review the boundaries the change crosses. Check authorization and data handling when trust changes, compatibility and migration when stored state or public interfaces change, rollback when failure could strand users, and observability and failure handling when the system must be operated after delivery. Apply these in proportion to risk, not as ceremony for a local text edit. Static checks prove only the properties they inspect. A schema validator proves shape, not model behavior. A dry run proves the simulated path, not publication or deployment. Keep activation, policy adherence, product task success, technical quality, proportionality, and completion honesty as separate evidence claims.
