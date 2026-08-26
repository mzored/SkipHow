# Product decisions

Use this reference when a choice changes product behavior, audience, scope, priority, commercial commitments, privacy, rollout, or another material risk. Routine engineering choices are not owner questions.

## Find the decision

State the desired outcome and the smallest unresolved choice that blocks it. Inspect current behavior, history, prior decisions, user evidence, and current primary sources when facts may have changed. Separate verified facts from assumptions and preferences, and look for evidence that could disprove the preferred option before an expensive or hard-to-reverse commitment.

Give a recommendation with its reason and the concrete tradeoff. Ask the owner only when evidence cannot settle a product choice or the action needs direct authority. If the owner need not decide now, take the safest reversible default and record the assumption. A read-only decision request does not authorize implementation.

An exact owner grant can supersede an accepted decision, including a privacy-sensitive disclosure, but never silently: find the owning decision or policy and reconcile the new direction against it before delivery.

## Record proportionately

Routine reasoning stays in the working notes. Write a durable record when the decision is consequential, disputed, regulated, measured over time, or must outlive the session; a durable update is mandatory when data crosses a private, internal, or public boundary or a change supersedes an existing durable decision. Update the owning record rather than creating a competing one. A code comment or test alone is not the product record.

```text
Outcome and users
Current behavior and evidence
Options considered
Decision and rejected alternatives
Added, changed, and removed behavior
Non-goals
Rollout or reversal condition
Acceptance evidence
Unresolved risk
Revalidation trigger
```

Keep libraries, schemas, file paths, and test strategy out of a product record unless they create a real product tradeoff.

## Acceptance

Product acceptance is conditional. Use it for a material contract change, a regulated or high-impact flow, or an explicit repository gate: name the user-visible scenarios that need acceptance and the evidence for each, then recheck the ones whose journey, output, error state, accessibility, or privacy behavior changed. A data-boundary change includes disclosure and withdrawal scenarios. Do not create acceptance ceremony for an ordinary change.
