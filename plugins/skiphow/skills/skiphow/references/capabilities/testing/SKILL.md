---
name: testing
description: Internal testing capability for CTO-directed work that needs evidence at stable behavioral seams.
---

# testing

Use this capability only when the CTO selects testing as useful evidence. It is internal. Do not expose it as an Owner workflow or ask the Owner to select a seam, a test approach, or TDD.

First decide whether a stable public interface exists and whether a test adds durable value beyond available verification. State the selected seam and reason in technical working notes. The test should exercise behavior a caller or user can observe and survive an internal refactor.

Use TDD when it will clarify uncertain behavior, prevent a plausible regression, or guide a meaningful interface. It is optional. Do not use it as ceremony for visual-only work, configuration-only changes, generated artifacts, throwaway spikes, or work where a durable behavioral seam does not exist. Use the smallest relevant non-test evidence for those cases.

When TDD is useful, work in vertical slices:

1. Add one focused test for one observable behavior and run it red for the expected reason.
2. Make the smallest implementation change that turns it green.
3. Refactor only while the test stays green, then repeat for the next behavior.

Prefer integration-style coverage through public interfaces. Use known literals, worked examples, or another independent source for expected results. Do not recompute the expectation with the same algorithm as the implementation.

Do not test private methods, mock collaborators owned by the code, assert incidental call order, or verify through a side channel when the public interface can show the result. Mock only a true external boundary when a real local substitute is impractical. Inject time, randomness, filesystem, network, or third-party clients at that boundary. Prefer a local test database or in-memory adapter when it preserves real behavior.

Keep each test focused on one behavior. Place it beside the repository's existing tests, use domain language in its name, and run the smallest relevant test command after every change. Before delivery, run the affected broader checks required by repository policy. If no stable seam exists, record the verification gap instead of adding a brittle test.
