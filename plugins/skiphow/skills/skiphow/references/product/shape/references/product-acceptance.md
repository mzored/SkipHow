# Selective product acceptance

Product acceptance is conditional. Use it when an extended product decision, campaign, regulated or high-impact flow, or repository policy requires an explicit product check. Do not create an acceptance receipt for an ordinary clear change.

Before delivery, name only the contract-visible scenarios that require acceptance and the evidence for each one. After technical verification, compare the affected scenarios with the governing decision record. Return concrete mismatches to the technical controller. Return desired behavior changes to product decision work.

Store a receipt only when a durable record is required. Record the decision revision, delivered-state identity, affected scenarios, evidence, reviewer, date, and `accepted` or `returned`. Use `carried-forward` only when a later delta changed neither product semantics nor the evidence for accepted scenarios.

A new state identity does not invalidate acceptance by itself. Recheck only scenarios whose journey, output, error state, accessibility behavior, or other contract-visible result changed. CI, metadata, test harness, validator, and behavior-preserving implementation changes do not require a new product pass.
