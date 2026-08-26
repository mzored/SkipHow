# Diagnosis and repair

Use this reference when behavior is broken and the cause is unknown. A diagnosis-only request stays read-only; a repair request grants the changes and checks the fix needs.

## Get a signal first

Build one repeatable check that reaches the reported behavior and tells failure from success: an existing or focused test, a CLI or HTTP call, a headless UI check, a redacted trace replay, a small harness, or a structured human reproduction, in that order of preference. Prefer synthetic fixtures and redacted identifiers over private or production-derived data. Run it before forming a theory; it must hit the exact symptom, not a nearby failure. For intermittent behavior, measure repeated runs. For performance, record a baseline.

If no signal is possible, record what was tried and what evidence is missing, and exhaust safe project evidence before asking for protected access.

## Reduce and test explanations

Minimize the case one input, caller, configuration value, or step at a time, re-running the signal after each removal. Rank falsifiable explanations, and for each name the observation or controlled change that would support or reject it. Test one prediction and vary one condition at a time; prefer a debugger or REPL, then narrow tagged logging. Stop when one probe separates the confirmed cause from the credible alternatives and the original signal agrees. Record the minimal case, the cause, the rejected alternatives, and any `UNVERIFIED` limit.

## Repair the cause

Add a check that fails for the original defect before the fix when a stable seam exists (read [testing](methods/testing.md) if the seam is unclear). Repair at the narrowest stable boundary and preserve compatibility unless the owner authorized a contract change. Rerun the minimal case, the original reproduction, focused tests, and nearby failure paths. Remove instrumentation and disposable harnesses. If the evidence proves only a mitigation, say so and record the unresolved cause.
