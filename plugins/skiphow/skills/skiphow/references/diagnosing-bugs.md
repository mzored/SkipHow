# Diagnosing bugs

Start from the reported symptom. Inspect the real path that produces it and build the tightest practical feedback signal. Prefer a focused test, repeatable command, browser interaction, captured input, trace, or measurement that can distinguish the broken behavior from the expected result.

Confirm that the signal represents the owner's problem, then reduce noise around it. For intermittent failures, improve the reproduction rate or collect enough repeated evidence to compare hypotheses. For performance problems, measure a baseline before changing code.

When the cause is ambiguous, write down competing explanations and the observation that would disprove each one. Design the cheapest high-value observation so it isolates the competing explanation it tests. Add targeted instrumentation only when the requested outcome authorizes project changes, and remove it before finishing.

When the requested outcome authorizes project changes, fix the cause rather than hiding the symptom. Add a regression test at an observable, stable interface when it would catch this failure and remain useful after refactoring. Do not force a shallow test when the project has no honest seam for it. For diagnosis-only work, leave the project unchanged and report the verified cause, evidence, and repair direction.

Rerun the original signal after the fix, not only the new test. If the environment prevents a faithful reproduction, use the strongest available evidence, state the uncertainty, and identify the missing access or artifact. Never present a plausible theory as a verified cause.

Write the hypothesis down before testing it, and test one variable at a time. When it proves wrong, replace it with a new one rather than stacking another change on top of the last. Three genuine attempts that fail against the same hypothesis mean the hypothesis or the design under it is wrong; stop and question the approach instead of trying a fourth time.

Some defects recur across unrelated projects and are worth checking directly when the symptom fits: work that is not idempotent on rerun; partial success that reports completion while silently skipping items; first-match rules misfiring on overlapping cases; a default or fallback branch quietly absorbing what belongs elsewhere; sign, unit, or direction errors that balance out by coincidence; a filter or time window hiding the real population; a manual override masking broken automation; and tests that pass because a mock has drifted from the behavior it stands for.

Look for a working sibling in the same codebase before inventing an explanation. A path that already handles the same class of problem correctly is the cheapest reference available, and the difference between it and the broken path is often the defect.
