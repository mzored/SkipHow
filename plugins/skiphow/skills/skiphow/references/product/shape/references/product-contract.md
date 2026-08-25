# Product briefs

## Lightweight delivery brief

Use this for ordinary changes. It may remain ephemeral in working context.

```text
Outcome
The result requested by the user or business.

Required behavior
The observable behavior needed for that outcome.

Non-goals or constraints
Material exclusions and product constraints.

Acceptance evidence
The scenarios or observations that prove delivery.
```

Do not add a document, tracker body, baseline, measurement window, guardrail, or technical design unless the request needs it.

## Extended product decision record

Use an extended record only when the decision changes a core journey or business model, affects billing, pricing, permissions, privacy, policy, or legal exposure, creates a public contract or migration, needs an expensive rollout, is hard to reverse, contains a material product trade-off, or must survive several independent delivery runs.

Include only applicable fields:

```text
Outcome
User and trigger
Required behavior and material states
Scope
Non-goals
Product constraints
Evidence and assumptions
Success signal, baseline, window, and guardrails when measurable and decision-relevant
Rollout or migration constraints when needed
Acceptance scenarios when selective product acceptance is required
Owner decision, only when authority requires it
```

When a consequential or ambiguous change needs behavior alignment across sessions, repositories, or teams, add only the touched behavior:

```text
Current behavior
ADDED behavior
MODIFIED behavior
REMOVED behavior
Concrete scenarios
Unchanged behavior or non-goals
Acceptance evidence
```

This behavior delta is optional. Do not create a proposal directory or expand it into a mandatory design and task workflow for ordinary changes.

Every material score, verdict, or priority claim in an extended decision cites source-backed evidence. Before an expensive or irreversible decision, look for evidence that would disconfirm the preferred choice. If measurement is part of a launch or experiment decision, define the target and decision date before declaring success. Do not add measurement fields when measurement is not part of the decision.

Keep architecture, schemas, libraries, file paths, state management, and test strategy out of the product record. Store portfolio priority only when the Owner or an existing ordered queue establishes it.
