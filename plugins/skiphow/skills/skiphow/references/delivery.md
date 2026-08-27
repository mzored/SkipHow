# Delivery

Use this reference for a `DELIVER` that is not a clear bounded change. Carry the authorized outcome through implementation and fresh verification.

## Ground the work

Read repository instructions, inspect the relevant implementation, and preserve unrelated changes. Settle routine reversible details from project evidence; ask only when a missing product choice changes scope, cost, risk, or the public result.

A bounded task runs in the current session. Read [long work](long-work.md) for a selected queue, an external wait, unattended work, or recovery, and [GitHub](github.md) when the repository tracks delivery. A repository rule that requires an Issue-linked branch or pull request owns the delivery shape even for a small change.

Treat tests, package scripts, build hooks, and changed executables as repository-controlled code: inspect an unfamiliar entry point before running it, use the host sandbox with the narrowest practical access, and keep credentials out of the command environment. If the host cannot enforce a boundary the risk requires, use a safer check or mark the claim `UNVERIFIED`; never accept an unsandboxed fallback to get a green result.

## Reuse before building

Before writing a new module, feature, or abstraction, search by domain concept, not request wording: the project itself, its dependencies, the platform, and maintained libraries or services. Compare fit, license, security, maintenance, and migration cost, and reuse when adapting costs less than owning new code. State in the report where you looked and what you reused or why nothing fit. Read [engineering methods](engineering.md) when a seam, module boundary, prototype, or conflict needs more care.

## Change and verify

Make the smallest coherent change that solves the whole request. Add or update evidence that would fail for the original defect or requirement, preferring observable behavior. Run focused checks while working and the repository-required checks before completion.

If touched files already hold unrelated changes, record their pre-change state and attribute your diff, checks, and claims to your delta only. Inspect the final diff, security boundaries, public contracts, failure paths, and cleanup. A value crossing from private or internal to public changes the data boundary; reconcile the owning durable decision (read [product decisions](decision.md)) before delivery.

Read `git log` on the base branch before the first commit and match the message form and granularity its recent history uses. Commit through the ordinary project path and hooks before closing review. Name the exact aggregate candidate for the root's review: target-base commit, source head, and resulting committed tree. Compare the committed tree with the tree checks and review judged; any hook, formatter, generator, target movement, or later integration that changes it invalidates applicable evidence and requires fresh affected checks and review. Read [engineering methods](engineering.md) for what that review owes and when a fix reopens it.

After a second failure with the same cause, stop retrying unchanged. Add the smallest durable prevention within scope (a test, a lint rule, a check, a skill correction) or save one finding if that prevention is outside authority.

## Findings

A problem outside the request is fixed if it blocks the outcome or cannot be separated; otherwise it is already tracked, saved once after a duplicate search through [intake](intake.md), or dismissed with its reason. A warning on the changed surface can weaken a green claim; triage it before claiming success. Do not save benign expected output, and do not implement or reprioritize a saved finding.

## Finish

Recheck the request against the final state and report under the skill's headings: the result, fresh evidence, the rulings you made and findings you triaged, the follow-ups you saved (or that none were material), and every missing check or external blocker. Never call an unavailable or stale check passed.
