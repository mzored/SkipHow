# Diagnosis

Open this for a bug, an unexplained or recurring failure, a performance problem, work that runs without getting closer to the result, or pressure to raise a timeout, retry, skip a check, or weaken an assertion.

## Build a signal before naming a cause

Start from the reported symptom and the real path that produces it. Build the fastest feedback loop that tells the broken behavior from the expected one: a repeatable command or script, a focused test, a captured input, an interaction, a trace, or a measurement. Confirm it shows the owner's problem before you trust it. A loop that runs in seconds settles more than long reading does.

Minimize the case. Cut input, steps, and environment until removing anything more makes the failure vanish; the small case often names the cause by itself. For an intermittent failure, raise the reproduction rate or repeat enough to compare explanations, because it is a defect, not something to retry past. For performance, measure a baseline before changing anything. When local results, the shared branch, and an outside system disagree, explain the disagreement instead of trusting one of them.

A plausible theory is not a cause. A cause is confirmed when the signal responds to it the way the theory predicts.

## Carry competing explanations

When the cause is unclear, write down three to five explanations ranked by likelihood, each with the observation that would disprove it. Run the cheapest observation most likely to eliminate one, and let the result choose rather than confirming your first idea.

Change one variable at a time. When an observation kills a hypothesis, revert its change and replace the hypothesis instead of stacking another change on top. Tag temporary logging with one unique marker so you can find and remove all of it before you finish.

Look for a working sibling early. A path in the same codebase that already handles the same kind of case correctly is the cheapest reference, and the difference is often the defect.

## When to stop repeating an approach

Count new information, not attempts. Stop when another attempt would tell you nothing the last one did not, when an observation has falsified its premise, or when switching approach is worth more. After three failed fixes, stop fixing and question the architecture, because the design under the hypotheses is now the likelier fault. When you stop, say what the attempts ruled out.

## Fix at the source

Classify the failure before choosing the remedy: product ambiguity, code, architecture, environment, host, missing capability, or process. Each needs a different remedy, and a code change for a process or environment failure only moves it. Product ambiguity goes to the owner under [product](product.md). A missing capability is reported with its consequence for the product and the exact expertise or access needed; ordinary technical review never goes back to the owner.

Fix where the cause lives, not where the symptom shows, and fix the shared cause when several symptoms trace to it. Then rerun the original signal, not only the check that came with the fix.

A regression test follows [testing](testing.md): write one only at a correct seam where it would catch a recurrence nobody would otherwise see. When no correct seam exists, that is an architecture finding, not a reason to test at a wrong one.

## What you may not do to a failure

Never silence a failure you cannot explain. Raising a timeout, adding a retry, skipping or disabling a check, weakening an assertion, and accepting an intermittent pass each need a diagnosis that shows the change is the fix rather than a cover. Never use a bypass flag or a destructive reset to make a failing path go quiet.

Repeated workarounds point at the system. When the same failure, manual step, or coordination defect keeps returning, fix what produces it; if that lies outside the request, handle it as the [kernel](../SKILL.md) handles a confirmed finding.

## Learn from a repeated failure

After a repeated failure, keep the smallest lasting fact that stops the next agent from repeating the investigation. Usually that fact is the fix in code, or one line in existing docs where the next agent will look, not a new test, guard, or document. Delete temporary diagnostics, debug logging, reproduction scripts, and stale recovery notes when the fix lands. A transcript is not documentation.

## Defects worth checking directly

Some defects recur across unrelated projects and are cheap to check when the symptom fits:

- work that is not idempotent on rerun
- partial success reported as completion while items are silently skipped
- a first-match rule misfiring on overlapping cases
- a default or fallback branch quietly absorbing what belongs elsewhere
- sign, unit, or direction errors that cancel out
- a filter or time window hiding the real population
- a manual override masking broken automation
- a mock that has drifted from the behavior it stands for

## Long work that stops producing evidence

Give a step that could take real time an expectation of healthy progress, and treat a breach as information, not a reason to wait longer. Count progress toward acceptance, such as parts checked or fewer relevant failures. Process liveness, tool calls, and commit counts show neither progress nor a stall. When monitoring delegated work, prefer host waits or events to repeated status reads or a sleep loop that holds your turn open. A long synchronous build or test with a sensible expectation is fine. An unchanged timeout tells you nothing new: reuse the wait once without narration. After another expiry, a stated deadline, an error, or a missed expectation, inspect state once and decide whether to continue, change approach, stop affected work, or report a blocker.

Reassess direction when repairs, conflicts, or process work keep growing while the owner's result does not. Ask of the next piece of work whether it removes a named obstacle to that result, delivers a needed part of it, or only adds mechanism and checks around the mechanism. Work that only adds mechanism is a reason to change direction, not to continue more carefully. Make this judgment when the signal appears; nothing tracks it for you. Stop affected work at its next safe boundary, keep independent work moving, keep what it established, and do not add a review pass to decide it.
