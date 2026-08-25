# Testing

Use tests when they add durable evidence for observable behavior. The owner does not need to choose the seam, test style, or mocking plan.

## Choose a stable seam

Test through an interface a caller or user observes and that should survive an internal refactor. State the chosen seam and why it can catch the original defect or requirement. If no such seam exists, record the verification gap instead of adding a brittle private-method test.

Use test-first work when it clarifies uncertain behavior, prevents a plausible regression, or guides a meaningful interface. It is optional for visual-only changes, generated files, disposable experiments, and configuration with a stronger direct validator.

## Build trustworthy evidence

- Use a literal worked example, specification, captured known-good result, or another independent source for expected values. Do not reproduce the implementation algorithm inside the test.
- Prefer integration through the public interface. Test one behavior at a time and name it in domain language.
- Use a real local dependency when it is practical. Mock only a true external boundary, and assert the result rather than incidental call order.
- Inject time, randomness, filesystem, network, or third-party clients at the boundary that varies. Keep the product interface free of test-only controls.
- For a bug, prove that the test fails for the expected reason before the fix, then rerun the original reproduction after it passes.

Run the smallest relevant check while editing. Before delivery, run the affected integration and repository-required gates. A green command is not enough if a material regression would still pass it.
