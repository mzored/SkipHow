# Review

Open this before reviewing a change, and before acting on findings from a review. The kernel's Engineering standard says what counts as a finding; this file is the method on both sides.

## Reviewing a change

Scale review to what the change can break, not to how many files it touches. A clear low-risk edit gets a cold self-review and focused checks. Independent review earns its cost where a mistake is expensive to find or undo: authentication and authorization, money, irreversible migrations, public compatibility, concurrency, and security or privacy exposure.

Start from the candidate and the request, issue, or specification that governs it. Work out what the change should do from the accepted product rules before reading how it does it, so the code does not set your expectations. Mark an expectation the sources leave open as contested instead of inventing product data. The reviewer checks the candidate; the lead checks what reached the destination.

Judge the change on two axes:

- Does it do what was asked? Missing requirements and scope creep both count.
- Does it meet the project's own standards and the kernel's Engineering standard?

For a user-facing change, walk the changed journeys in the product, including transitions, errors, and recovery, against the accepted intent and the project's interaction and visual conventions. Check shared behavior separately from how it looks: two screens that look alike may not share code, and a shared import does not make the experience coherent.

Name these smells when you see them, because each one adds code the owner keeps without adding behavior: speculative generality, a middle man that only forwards calls, duplicated logic, a change that needs edits in many places, a shim or compatibility path with only in-repository callers, production branches that exist for tests, and tests of the bad shapes in [testing](testing.md). Prefer deleting an abstraction to polishing it.

Skip what the linter, formatter, and type checker already enforce.

A finding qualifies when it names one of these:

- A broken behavior: the input or scenario, what happens, and what should happen.
- A security, privacy, or data risk, with the path that exposes it.
- A contradiction with the request or an accepted product rule.
- A simpler design that removes code or a concept, with what it replaces.

"Add a test" or "cover more cases" qualifies only when it names the break the test would catch and the kernel's bar for a test is met. A preference, a rewording, or a sentence that could be clearer without naming what breaks is not a finding. Settle a suspected defect with a focused check before reporting it.

Make one pass. Report each finding with location, scenario, and impact, most consequential first, and list the important areas you did not check, even when you found nothing. Read-only review reports and edits nothing. Urgency grants no repair authority.

Keep security, privacy, customer-data, and credential findings minimal and inside their authorized audience. Describe the exposure without reproducing the secret or the data, and do not put them in a public issue, PR comment, or log unless the owner granted that disclosure.

When you dispatch a reviewer, the brief carries the request, the candidate, the scope, the constraints, what result is enough, and when to return, as [delegation](delegation.md) describes. For a long review, say what progress looks like and when to come back, as [diagnosis](diagnosis.md) describes for long work. A reviewer that runs out of time returns its findings, what it checked, and what it did not, not a passing verdict.

## Receiving findings

Treat each finding as a claim. Read the code it points at and confirm the break yourself. Before building something a reviewer says is needed, grep for the callers or the case it would serve; if nothing uses it, say so. Push back with the reason when a finding is wrong, and do not perform agreement with one you have not confirmed.

Fix confirmed qualifying findings in this run, within authority, as the kernel says. Minor findings and preferences do not enter a fix loop; note them or drop them. When a confirmed finding points at a repeated failure, fix the shared cause.

Where the work is delegated, keep the same implementer and reviewer through corrections when the host supports it. A replacement gets the findings, what you did with each, the candidate it is reviewing, and the checks that already passed. The lead corrects plans.

After fixes, re-review only the fix diff and what it can affect. Give the reviewer the prior candidate, the changes, and your disposition of each finding, and reuse checks that still apply. Stop after a round that returns nothing that qualifies. Another broad review needs a high-consequence disagreement or contradictory results, not a hope that it finds more. Repeated rounds on an ordinary change are a defect in the review, not diligence. A review that did not finish does not make the change reviewed.

## Security, reliability, and operations

Look at the boundaries the change crosses, in proportion to risk, not as ceremony for a local text edit:

- Security and privacy when trust changes: who can call it, what data it reads or exposes, where secrets go.
- Compatibility and migration when stored data or a public interface changes, including whether the migration can be reversed.
- Rollback when a failure could strand users: what undoing the change means for this product.
- Reliability when the change adds a dependency, a timeout, or concurrency: what happens when the other side is slow or down.
- Readiness when the system must be run after delivery: whether a failure would be visible and who would see it.

Report each claim with what actually proved it. A static check proves only the property it inspects. A schema validator proves shape, not behavior. A dry run proves the simulated path, not publication or deployment. A preview proves nothing about what users received.
