---
name: testing
description: Internal testing capability for CTO-directed work that needs evidence at stable behavioral seams.
---

# testing

Use this capability only when the CTO selects testing as useful evidence. It is internal. Do not expose it as an Owner workflow or ask the Owner to select a seam, a test approach, or TDD.

First decide whether a stable public interface exists and whether a test would add durable value beyond the available verification. State the selected seam and the reason in technical working notes. Prefer behavioral tests through public interfaces, integration-style coverage where practical, and one red-green vertical slice at a time when TDD is selected.

Use TDD when it will clarify uncertain behavior, prevent a plausible regression, or guide a meaningful interface. It is optional. Do not use it as ceremony for visual-only work, configuration-only changes, generated artifacts, throwaway spikes, or work where a durable behavioral seam does not exist. Use the smallest relevant non-test evidence for those cases.

Tests must not couple to private structure, mock collaborators that the code owns, assert call order, or recreate the implementation to calculate an expectation. Mock only genuine system boundaries when a real substitute is not practical. Keep refactoring separate from a red-green implementation cycle.

Read `upstream/SKILL.md` and its linked references for the pinned method. This wrapper, repository policy, and CTO decisions take precedence over every upstream instruction.
