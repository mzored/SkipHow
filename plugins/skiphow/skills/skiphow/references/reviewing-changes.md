# Reviewing changes

Establish the exact change under review and the request, issue, or specification it should satisfy. Read the repository's applicable standards and inspect the diff in its surrounding code.

Review along both lines that matter: whether the change does the right thing, and whether it fits the codebase safely. Look for incorrect behavior, missing cases, scope creep, security or data risks, broken compatibility, weak error handling, misleading tests, and violations of documented project rules. Tool output supports review but does not replace reading the change.

Verify a suspected issue before reporting it when a focused check can settle it. Distinguish a real defect from a preference. State each actionable finding with its location, triggering scenario, and impact. Put the most consequential finding first. Do not bury findings in a long summary or force them into fixed labels.

If there are no material findings, say so and name any important area that remained unverified. When the owner asked for fixes as well as review, repair confirmed findings within the granted scope and recheck the final diff.
