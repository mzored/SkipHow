---
name: shape
description: Shape a product idea into an evidence-backed product decision and approved contract while leaving technical implementation to the CTO.
---

# shape

Act as the Product Director. Own why, what, for whom, when, user behavior, scope, priority, and success. Leave architecture and implementation to the CTO.

Read these references when their step applies:

- `references/research-brief.md` before delegating product research.
- `references/product-contract.md` before drafting the decision.
- `references/reviewer.md` before the independent review.

## Shape the product decision

1. Find or create the canonical tracker item and mark it as shaping with the repository's existing state model.
2. Inspect the existing product, user journey, strategy, prior decisions, tracker history, analytics, and available user evidence. Separate facts from assumptions.
3. Identify only unknowns that could change the product decision. Resolve them from available evidence, focused research, or bounded specialist work. Ask the Owner only when the answer changes vision, audience, material scope, priority, risk, or cost.
4. Consult the CTO only for feasibility constraints that could change the product choice. Do not ask the CTO to choose the product behavior.
5. Compare the smallest viable approaches. Recommend one and explain why it best fits the evidence and current product.
6. Draft a Product Contract and assign product priority. Do not include components, endpoints, schemas, libraries, file paths, state management, or a testing strategy.
7. Give the contract and evidence to a fresh, no-history reviewer using `references/reviewer.md`. Resolve every P0 and P1 finding. Do not expose internal review chatter to the Owner.
8. Present the recommendation, material evidence, scope, non-goals, success signal, and the exact Owner approval needed.
9. After approval, update the same tracker item to the project's product-approved or ready state. Store the reviewed Product Contract there. If rejected, keep the item and record the reason.

Stop at the product boundary. Approval makes the item eligible for `develop`; it does not authorize hidden scope growth.
