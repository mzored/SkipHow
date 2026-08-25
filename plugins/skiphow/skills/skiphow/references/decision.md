# Product decisions

Use this reference when a choice changes product behavior, audience, scope, priority, commercial commitments, privacy, rollout, or another material risk. Do not turn routine engineering choices into owner questions.

## Find the decision

State the desired outcome and the smallest unresolved choice that blocks it. Inspect current behavior, repository history, prior decisions, user evidence, and current primary sources when facts may have changed.

Separate verified facts, assumptions, and preferences. Seek evidence that could disprove the preferred choice before an expensive or hard-to-reverse commitment. Give a recommendation with its reason and concrete tradeoff. Ask the owner only when evidence cannot settle a product choice or the action needs direct authority.

If the owner need not decide now, choose the safest reversible default and record the assumption. A read-only decision request does not authorize implementation.

## Scale the record

Keep routine reasoning in the working brief. Use a durable extended record only when the decision is consequential, disputed, regulated, measured over time, or must survive across teams or sessions. Record only fields that affect the decision:

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

## Use selective acceptance

Product acceptance is conditional. Use it for a material contract change, a regulated or high-impact flow, or an explicit repository gate. Before delivery, name only the user-visible scenarios that require acceptance and the evidence for each.

After technical verification, recheck scenarios whose journey, output, error state, accessibility behavior, privacy behavior, or other contract-visible result changed. Carry unaffected acceptance forward. Do not create an acceptance receipt for an ordinary clear change or rerun product acceptance because only implementation details changed.
