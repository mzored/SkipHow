# Real-task application audit

## Scope

This note records behavior observed while SkipHow 1.0 was used on a real product task. It evaluates SkipHow's application of its own policy, not the target project's implementation quality. Project-specific names, private data, and unrelated implementation findings are intentionally omitted.

## Verified gaps

### Repository tracking lost to the small-change shortcut

The packaged root skill said not to create an Issue or branch merely because code changes. The GitHub reference already exempted repositories whose policy requires tracking, but that constraint loaded too late and was interpreted as optional. The result could be correct local work delivered outside the repository's required Issue-linked branch lifecycle.

The root contract now states that the shortcut never overrides repository policy. The delivery and GitHub references require reconciliation before implementation when repository policy makes the work tracked.

### A privacy-boundary change did not force durable reconciliation

The decision reference treated extended records as generally proportional. That left room for an owner-approved change from private or internal data to public output to update only implementation and tests while leaving the accepted product record stale.

The decision contract now makes a durable update mandatory for audience and data-boundary changes and for changes that supersede an existing durable decision. Delivery also checks disclosure and withdrawal or exclusion behavior while preserving unaffected projections.

### Independent findings depended on explicit prompting

The previous live scenario told the agent which note was an independent finding and told it to save the note. It did not test whether normal delivery would notice a material warning, distinguish it from a duplicate and expected negative-test output, and persist only the actionable item.

SkipHow now uses a working triage with `IN_SCOPE`, `PERSIST`, `DUPLICATE`, `EXPECTED`, and `NONMATERIAL`. Pre-existing, warning-only, and outside-diff labels are evidence, not dispositions. The updated live scenario removes the finding instructions and uses an exact oracle to require one new material record without duplicate or expected-output noise.

### Dirty overlap weakened candidate attribution

Preserving unrelated changes was explicit, but the policy did not require a pre-change identity for files that delivery also touched. A broad dirty worktree could therefore blur which bytes belonged to the operation and support an overbroad review or candidate claim.

Delivery now captures the pre-change identity and diff for overlapping paths and binds evidence to the operation's delta. When required tracked delivery cannot isolate or prove that delta, it fails closed as `UNVERIFIED` or `BLOCKED` instead of bypassing the gate.

### Diagnosis could reach for unnecessary private data

The privacy boundary prohibited copying private data, but diagnosis did not prefer synthetic fixtures and redacted identifiers. The repair guidance now states that equivalent synthetic or redacted evidence takes precedence over querying private or production-derived data for convenience.

## Regression evidence

Two host-level scenarios cover the measured failures:

- `independent-finding` asks only for the requested product edit; its fixture contains one material warning, one already tracked warning, and one expected negative-test message;
- `privacy-boundary-change` asks for an explicit public projection change without telling the agent to update the existing product decision.

Deterministic repository tests keep the policy triggers and the non-spoon-fed prompts present. These checks validate the packaged contract and evaluation structure. Model interpretation remains `UNVERIFIED` until an opt-in live receipt for the exact release candidate passes.
