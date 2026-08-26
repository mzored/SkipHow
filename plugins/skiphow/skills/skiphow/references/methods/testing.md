# Testing

Use tests when they add durable evidence for observable behavior. The owner never chooses the seam, style, or mocking plan.

## Choose a stable seam

Test through an interface a caller or user observes and that survives an internal refactor. State why that seam can catch the original defect or requirement; if none exists, record the verification gap instead of adding a brittle private-method test. Write the test first when it clarifies uncertain behavior, guards a plausible regression, or shapes an interface; skip that for visual-only changes, generated files, disposable experiments, and configuration with a stronger direct validator.

## Build trustworthy evidence

- Take expected values from a worked example, specification, captured known-good result, or another independent source. Do not restate the implementation inside the test.
- Prefer the public interface. Test one behavior at a time and name it in domain language.
- Use a real local dependency when practical. Mock only a true external boundary, and assert the result rather than call order.
- Inject time, randomness, filesystem, network, or third-party clients at the boundary that varies; keep test-only controls out of the product interface.
- For a bug, prove the test fails for the expected reason before the fix, then rerun the original reproduction after it passes.

Run the smallest relevant check while editing and the affected integration and repository-required gates before delivery. A green command is not enough if a material regression would still pass it.
