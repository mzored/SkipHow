# Diagnosis

Open this when the cause of a failure is unknown, when the same problem survives repeated attempts, when work keeps running without new evidence of the result the owner asked for, or under pressure to raise a timeout, add a retry, skip a check or weaken an assertion.

## Build a signal before naming a cause

Start from the reported symptom and inspect the real path that produces it. Build the tightest practical signal that separates the broken behavior from the expected one: a focused test, a repeatable command, a captured input, an interaction, a trace, or a measurement. Confirm the signal represents the owner's problem before trusting it, then reduce the noise around it. Divergence between local results, the shared branch, and any external system is itself an anomaly to explain, not a discrepancy to settle by trusting one of them.

Prefer the smallest reproducer that still fails. Reducing the case usually costs less than reasoning about the large one, and it often names the cause on its own. For an intermittent failure, raise the reproduction rate or gather enough repetitions to compare explanations; an intermittent failure is a defect, not something to retry past. For a performance problem, measure a baseline before changing anything.

Never present a plausible theory as a verified cause. A cause is verified when the signal responds to it the way the theory predicts.

## Carry competing explanations

When the cause is ambiguous, write down the explanations that could produce the symptom and, for each, the observation that would disprove it. Then design the cheapest observation with the best chance of eliminating one. Let evidence choose between them instead of confirming the first explanation you formed.

Write the hypothesis down before testing it and change one variable at a time. When an observation kills a hypothesis, replace it rather than stacking another change on top of the last. Instrumentation added to isolate a cause is temporary; remove it before finishing.

Look for a working sibling in the same codebase before inventing an explanation. A path that already handles the same class of problem correctly is the cheapest reference available, and the difference between it and the broken path is often the defect.

## When to stop repeating an approach

Count evidence, not attempts. Stop repeating an approach when another attempt would add no evidence the last one did not, when an observation has already falsified the premise it rests on, or when changing approach is worth more than another run of this one. A single decisive failure can settle it; several genuinely independent experiments can each still be worth running. When you stop, say what the attempts ruled out, and question the design underneath the hypothesis rather than only the hypothesis.

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

## What you may not do to a failure

Never silence a failure you cannot explain. Raising a timeout, adding a retry, disabling or skipping a check, weakening an assertion, and accepting an intermittent pass all require a stated diagnosis first. Never reach for a bypass flag or a destructive reset to make a failing path go quiet.

Repeated workarounds are a signal about the system, not about the task. When the same failure pattern, manual step, or coordination defect keeps recurring, fix the control that produces it, or report the control when fixing it lies outside the requested result.

Fix the cause rather than the symptom, then rerun the original signal and not only whatever new check the fix came with. Where a durable check belongs is [verification](verification.md)'s question.

## Long work that stops producing evidence

Give a step that could take real time an expectation of what healthy progress looks like, and treat a breach as information rather than a reason to wait longer. Prefer the host's own wait or event mechanism to repeated status reads, and never hold your own turn open to poll: a sleep loop or a blocking command that occupies the root while delegated work runs is not a wait but a stop, and it costs the run every minute it holds. An expired wait over unchanged state is not new evidence, so renew it without another inspection, narration, or decision pass.

Reassess direction when repairs, integration conflicts, or process work keep growing while evidence of the owner's requested result does not. The question to ask of the next piece of work is whether it removes a named obstacle to that result, proves a needed part of it, or only extends the mechanism and the assurance around the mechanism. Work that only extends the mechanism is a reason to change direction, not to continue more carefully. This is a judgment made when the signal appears, not a state anything tracks for you. Stop affected work at its next safe boundary, keep independent work moving, and reconcile what it established. Do not add a second review pass to decide it.
