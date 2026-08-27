# Diagnosing bugs

Start from the reported symptom. Inspect the real path that produces it and build the tightest practical feedback signal. Prefer a focused test, repeatable command, browser interaction, captured input, trace, or measurement that can distinguish the broken behavior from the expected result.

Confirm that the signal represents the owner's problem, then reduce noise around it. For intermittent failures, improve the reproduction rate or collect enough repeated evidence to compare hypotheses. For performance problems, measure a baseline before changing code.

When the cause is ambiguous, write down competing explanations and the observation that would disprove each one. Test the cheapest high-value distinction first. Change one variable at a time. Add targeted instrumentation only when the requested outcome authorizes project changes, and remove it before finishing.

When the requested outcome authorizes project changes, fix the cause rather than hiding the symptom. Add a regression test at an observable, stable interface when it would catch this failure and remain useful after refactoring. Do not force a shallow test when the project has no honest seam for it. For diagnosis-only work, leave the project unchanged and report the verified cause, evidence, and repair direction.

Rerun the original signal after the fix, not only the new test. If the environment prevents a faithful reproduction, use the strongest available evidence, state the uncertainty, and identify the missing access or artifact. Never present a plausible theory as a verified cause.
