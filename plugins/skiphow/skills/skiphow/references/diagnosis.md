# Diagnosis and repair

Use this reference for broken behavior or an unknown cause. A diagnosis-only request remains read-only. A request to fix grants the changes and checks needed for the repair.

## Prove the failure

Capture expected behavior, observed behavior, environment, scope, and a reproducible case. Inspect logs and state before editing code. Reduce the failure to the smallest useful reproducer when practical.

Trace the data and control path that could produce the symptom. Form competing explanations and use evidence to eliminate them. Do not stack speculative patches.

## Repair the cause

Write a test or other check that fails for the original defect. Fix the cause at the narrowest stable boundary. Keep compatibility unless the owner authorized a change to the contract.

Rerun the reproducer, focused tests, and final project checks. Check nearby failure cases when the cause could affect them. If the evidence proves only a mitigation, say so and record the unresolved cause.
