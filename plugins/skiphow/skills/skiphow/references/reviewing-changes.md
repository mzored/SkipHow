# Reviewing changes

Use this for an explicitly requested or repository-required review.

Establish the exact change under review and the request, issue, or specification it should satisfy. Read the repository's applicable standards and inspect the diff in its surrounding code.

Review along both lines that matter: whether the change does the right thing, and whether it fits the codebase safely. Look for incorrect behavior, missing cases, scope creep, security or data risks, broken compatibility, weak error handling, misleading tests, and violations of documented project rules. Tool output supports review but does not replace reading the change.

Verify a suspected issue before reporting it when a focused check can settle it. Distinguish a real defect from a preference. State each actionable finding with its location, triggering scenario, and impact. Put the most consequential finding first. Do not bury findings in a long summary or force them into fixed labels.

If there are no material findings, say so and name any important area that remained unverified. When the owner asked for fixes as well as review, repair confirmed findings within the granted scope and recheck the final diff.

Whoever made a change is the worst judge of whether it works. For anything risky enough to matter, verify the result independently of the account that produced it. Reproduce the original failure against the fixed code yourself, or have a delegate do it from the requirements and the diff rather than from the author's summary or the conversation so far. A report of success is a claim to check, not evidence.

Act on findings by consequence. Fix what is wrong or unsafe before going further, and do not carry an important defect forward as accepted. Note minor preferences without letting them block the result.
