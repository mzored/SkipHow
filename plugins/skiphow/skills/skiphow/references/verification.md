# Verification

Open this when a change needs durable automated coverage, or when a review has been asked for or the repository requires one.

## Choosing the test

For a read-only design or coverage request, propose the tests without changing the project. Test observable behavior through the narrowest stable interface that gives confidence in the requested result, rather than internal shape. Follow the repository's existing test layout and vocabulary.

Use the narrowest stable test that would catch the real defect and remain useful. Prefer real integration across the behavior being proved; introduce mocks or internal seams only where they materially improve isolation, determinism, cost, or safety — external systems, time, and randomness are the usual cases, and a legacy or tightly coupled system may need more — without asserting call order, private state, or other implementation trivia.

Derive the expected value independently of the implementation under test. A test that repeats the production algorithm can agree with the same bug.

A test is evidence about the system, not the definition of the solution. Never satisfy one with a hard-coded test-only path.

## When the test comes first

Write the failing test first when it gives a useful red signal and the interface it needs already exists. For exploratory work, legacy behavior, or a change with no honest test seam, establish the behavior first and add the durable check at the right level. Test-first is a tool, not a ceremony.

## Regression tests

A regression test should close the class of bug, not the one reproduction. Assert the rule the defect broke rather than the literal inputs that exposed it, place the test at the lowest layer that owns that rule, and confirm its failure message names the violated invariant. When a bad value crossed several boundaries, cover the boundaries where a check would have stopped it.

Observe the test failing against the unfixed code before trusting it. Where reproducing the defect is unsafe or impractical, rebuild the broken condition at the layer that owns the rule, exercise that layer instead, and say which part of the real path went unexercised. Do not assume the test would have failed.

## How much to run

Keep tests that protect behavior; remove only temporary harnesses and implementation-coupled checks owned by this work.

Scale the run to what the change can reach rather than rerunning everything after every edit. Start with the smallest targeted check that covers the change. Widen to the affected module or contract, then to cross-boundary behavior where the change crosses one, then to whatever the repository requires before integration. Rerun anything a rebase, merge, dependency change, or generated artifact has invalidated.

An intermittent test is a defect or an explicit blocker until it is classified; [diagnosis](diagnosis.md) covers that.

## Reviewing a change

A review is warranted when the owner asked for one, when repository policy requires it, or when the change sits at a boundary where a mistake is expensive to undo. Ordinary work does not earn a separate pass. A justified review earns its cost by starting from a different account of the change than the one that produced it, whether it runs here or through a delegate.

Establish the exact change under review and the request, issue, or specification it should satisfy. Read the repository's applicable standards and inspect the diff in its surrounding code. Review the change against those requirements and that diff rather than against the author's summary of it. Tool output supports review but does not replace reading the change.

Look for incorrect behavior, missing cases, scope creep, security or data risks, broken compatibility, weak error handling, misleading tests, and violations of documented project rules.

Verify a suspected issue before reporting it when a focused check can settle it. Distinguish a real defect from a preference: a finding names a concrete defect, and a reviewer who cannot point at what breaks is reporting taste. State each actionable finding with its location, triggering scenario, and impact, most consequential first. If there are no material findings, say so and name any important area that remained unverified.

On a read-only review, report confirmed defects without modifying the project; urgency, including a security finding, does not widen the request, and a sensitive finding stays private unless disclosure is granted. When repair is authorized, fix confirmed in-scope defects before completion and verify the repaired final state, and do not carry an important defect forward as accepted.
