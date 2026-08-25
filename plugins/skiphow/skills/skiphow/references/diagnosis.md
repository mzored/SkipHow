# Diagnosis and repair

Use this reference when behavior is broken and the cause is unknown. A diagnosis-only request stays read-only. A repair request grants the changes and checks needed for the fix.

## Build the signal first

Create one repeatable check that reaches the reported behavior and distinguishes failure from success. Prefer an existing or focused test, a CLI or HTTP call, a headless UI check, a redacted trace replay, a small harness, a differential check, or a structured human reproduction in that order when practical. Prefer synthetic fixtures and redacted identifiers when they can prove the same behavior; do not query private or production-derived data merely for convenience.

Run the check before forming a theory. It must exercise the exact symptom, not a nearby failure. For intermittent behavior, measure repeated runs and raise the reproduction rate. For performance, record a baseline with a timing harness, profiler, or query plan.

If no usable signal is possible, record what was tried and the missing evidence. Exhaust safe project evidence and available tools before asking for protected access or a redacted artifact.

## Reduce and test explanations

Minimize the case one input, caller, configuration value, data item, or step at a time. Re-run the signal after each removal.

When evidence permits, rank several falsifiable explanations. For each one, name the observation or controlled change that would support or reject it. Test one prediction and vary one condition at a time. Prefer debugger or REPL inspection, then narrow tagged logging. Broad logging creates noise and often leaks data.

Stop when one probe separates the verified cause from credible alternatives and the original signal supports the result. Record the minimal case, confirmed cause, rejected alternatives, and any `UNVERIFIED` limit.

## Repair the cause

Read [testing](methods/testing.md) when the correct regression seam is unclear. Add a check that fails for the original defect before the fix when a stable seam exists. Repair the cause at the narrowest stable boundary and preserve compatibility unless the owner authorized a contract change.

Rerun the minimal case, the original unminimized reproduction, focused tests, and nearby failure cases affected by the cause. Remove tagged instrumentation and disposable harnesses unless the repository deliberately keeps one as regression evidence. If the evidence proves only a mitigation, say so and record the unresolved cause.
