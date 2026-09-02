# Campaign direction

Use this for multi-unit work, active or recorded, where live evidence shows any of these:

- repeated repairs
- competing implementations of one product behavior
- internal machinery delaying the outcome it protects, or expanding after its stated target was met
- technical and process growth without new evidence of the requested result
- a unit that must create a new prerequisite of its own before it can finish
- active work the current integration and verification path cannot absorb

Measure the direction against the owner's requested result. Inspect only the proposed or active work. Do not turn this check into a repository survey or absorb adjacent cleanup.

## Recovering the premise

Recover the shared premise from the owner's request as stated, the decisions the owner recorded, and live project state. A parent record or an audit finding says what somebody proposed. A record this run wrote says what this run decided, apart from an answer the owner gave that it carries. Neither is the premise, and a record's claim that its work must precede the result is a proposal like any other.

For an existing direction, count evidence produced or discovered since the premise or its affected records were last settled. Mere size is not evidence, and code and tests normally grow while a result is being built. The question is whether the next work removes a named obstacle to the result, proves a needed part of it, or only extends the mechanism and its own assurance. Security, money, recovery, and operational work answer it the same way as any other work, by naming the obstacle to the stated result that they remove. Producing no customer-visible change is not itself an answer.

## The read

When the signal appears during decomposition's existing cold read, include the direction there. Otherwise read the owner's outcome, live constraints, proposed or recorded units, recent repairs and conflicts, current product evidence, and relevant maintained capabilities without adopting the argument that produced the plan. Name the simplest coherent direction, which work to keep, replace, or retire, and what evidence would make that answer wrong. Do not add a second review pass. When the replacement becomes something later work has to build on, use [technical design](technical-design.md)'s existing outside read for that decision.

## Choosing the direction

The agent owns whether to keep, simplify, replace, retire, or defer a technical direction when accepted product behavior stays the same. A direction that is not on the path from live state to the requested result is deferred, not rebuilt. Stop its lanes at their next safe boundary. Record what it established and what it waits on where the request authorizes that record, and report it otherwise. Then take the next unit that reaches the result.

Replacing the architecture of off-path work is not a response to its being off-path. Apply [technical design](technical-design.md) to the replacement choice and [codebase design](codebase-design.md) when competing implementations or compatibility layers are the problem. Compare the options against the same constraints without treating sunk work as a reason to keep it. Reopen the decision when new evidence changes the engineering judgment.

## When to ask the owner

Ask only when no technically adequate option stays within the product behavior, scope, priority, committed cost, risk, privacy, and rollout the project has already settled, or when the next act is protected or human-only. Use [product decisions](product-decisions.md), bring one recommendation in product consequences, and keep technical alternatives out of the question. Ask for the unresolved product consequence, not approval of the architecture that produced it.

Where deferring would carry the result past a risk or rollout consequence the owner has not settled, such as launching without a safeguard a record said must come first, that consequence is the question. Put it in product terms with one recommendation. The mechanism behind it is not the question. A technical correction that stays inside settled product bounds needs no approval.

## Admission capacity

Readiness does not create admission capacity. Admit only as many independent units as the run can keep isolated, integrate one by one, and revalidate against live state without sibling work invalidating their evidence. Prefer the next unit that can prove the owner's result over another unit that only expands enabling machinery. When no takeable unit reaches the result, admission stops there. Spare capacity admits nothing. No fixed number is portable, and instruction text cannot impose a global limit across sessions it cannot see.

## When a signal appears

When a direction signal appears, stop affected lanes at their next safe boundary, keep independent work moving, and reconcile what active lanes established. Do not interrupt a non-idempotent external action halfway through.

Where the request authorizes the affected records, correct or supersede them before recomputing the frontier. Otherwise report what the evidence invalidated. If the evidence opens a product choice, leave dependent records blocked on the owner's answer instead of rewriting the product outcome. Resume under [execution health](execution-health.md), which owns stopping a stream and starting it again. Without new evidence, continue without re-arguing settled direction.
