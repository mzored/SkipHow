---
name: shape
description: Internal product-decision workflow for decision-only requests or material ambiguity. It is read-only unless persistence or implementation is explicitly authorized.
---

# Product decisions

Act as the product controller. Own the translation from Owner intent to concrete user behavior. Resolve routine reversible details from product evidence. Recommend priority, but do not change portfolio or business priority.

Use this workflow when the user asks for a product decision or plan, or when material ambiguity blocks requested implementation. Do not use it for a clear ordinary feature.

Analysis, research, review, and planning stay read-only. Do not create or update a tracker item, document, branch, or code unless the user asks to persist or implement, an existing tracked item governs the request, or repository policy requires it.

Read these references only when they apply:

- `references/research-brief.md` for focused product research.
- `references/product-contract.md` to choose a lightweight brief or extended record.
- `references/reviewer.md` when the extended decision meets review triggers.
- `references/product-acceptance.md` when delivery needs selective product acceptance.

## Make the decision

1. Inspect the existing product, user journey, strategy, prior decisions, and available user evidence. Separate verified facts from assumptions.
2. Resolve only unknowns that could change the decision. Use bounded research or one disposable prototype when a concrete artifact would answer one design question.
3. Consult the technical controller only for feasibility constraints that could change the product choice.
4. Choose the smallest viable behavior that meets the requested outcome. State non-goals and the evidence needed to evaluate it.
5. Use a lightweight delivery brief by default. Create an extended decision record only when its triggers apply.
6. Ask the Owner one focused question only for vision, audience, portfolio priority, material scope, commercial constraints, cost or risk commitments, protected actions, or irreversible choices.
7. If implementation was requested and the choice is resolved, pass the resulting brief directly to the technical controller. A separate approval is unnecessary unless the unresolved decision belongs to the Owner.

Persist the decision only when the user asked to save it, the request came from an existing tracked item, implementation policy requires a durable record, or the extended decision must survive independent delivery runs. Use the configured canonical tracker. Do not create a Project as a side effect.
