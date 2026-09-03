# Writing for agents

Open this when writing or revising instructions a coding agent will read: a skill, a reference, a project policy, or a delegate brief.

## Start from a behavior change

Start with the behavior the instruction must change and the evidence that the default behavior is insufficient. Leave tools and implementation to the agent unless a mechanism is itself required.

Define success before tuning wording: the behavioral criterion, the current text and its observed failure, and a realistic check on representative cases. Change one variable at a time and compare quality and cost. Wording is not always the mechanism; host enforcement, a better tool contract, clearer project state, or a different model often is.

## Shape

Write outcome-first: the goal, the context that matters, the hard constraints and invariants, the authority or approval boundary, the evidence required, the success criteria, and the shape of the report. Do not prescribe a long method a capable model can choose for itself.

Use steps only where order is part of correctness: release mechanics, a bounded migration, an installation sequence, a reproducible evaluation. Not as a universal development lifecycle.

Prefer positive, concrete instructions in project language over a collection of prohibitions. Negative rules stay appropriate for high-consequence boundaries, such as taking no protected action without an exact grant.

Structure proportionately. Markdown headings carry a static policy with one semantic layer; heavier delimiters earn their place when a prompt mixes large dynamic documents, instructions, examples, and variable inputs. In long multi-document analysis, put the sources first and the question and output requirements last.

## State each instruction once

Give each rule one authoritative home. Repeated instructions and duplicated tool descriptions spend context and raise the risk of contradiction; prefer deleting an obsolete rule to qualifying it in three places. Remove contradictions when behavior changes, and do not copy facts the agent can read from configuration, source, or command help.

Define action semantics once — what an inspect-and-report request, a change request, an exact grant, an owner question, and an agent decision each cover — and keep that policy compact and in one place. Restating "ask first", "do not mutate", or "wait for approval" produces approval requests for safe, expected actions, and asking for a question whenever anything is ambiguous does the same; ask only where a reading changes an owner-owned consequence.

## What not to ask for

Avoid fixed counts, magic phrases, provider-specific commands, and mandatory process unless evidence proves the constraint necessary.

No reasoning rituals. Use the host's own model and effort controls, evaluated on representative tasks, rather than telling a model to think harder, reveal its reasoning, produce candidate answers by default, or follow an authored reasoning script. Ask for observable analysis quality: decision, alternatives weighed, evidence, uncertainty, failure conditions, final verification.

No universal self-review. Require proof of the final state; add a second pass, verifier delegate, or cold read where risk, evidence of a recurring miss, or repository policy justifies it, not as a standing step.

No forceful framing on ordinary guidance. Blanket defaults such as "always use this", "if in doubt, use it", or "you MUST" make a capability fire when it should not. Reserve imperative force for high-consequence boundaries.

## Triggers, briefs, examples

For an automatically discovered skill, make the description a precise trigger: the situations that should load it and the nearby ones that should not. Keep universally needed rules in the main file, and move conditional material behind a clear pointer only when the branch saves attention without hiding a requirement.

In a delegate's brief, a link to a policy file changes nothing unless the host demonstrably preloads it. The kernel states what that brief carries in its own text.

Examples are targeted instruments: use one to encode a product requirement, demonstrate a strict output schema, separate close positive and negative cases, or repair a measured failure. Keep the smallest set that closes the gap and vary edge conditions enough to prevent accidental pattern matching; a large permanent example set can overfit behavior. Where software consumes the result, use the host's schema or structured-output mechanism rather than prose asking for valid output.

## Check the result

Write completion conditions the agent can verify, explain uncommon terms once, and keep related rules together. Read the finished document as an instruction system: trigger, authority, action, stopping condition, and conflicts with nearby or higher-priority instructions. Validate syntax and links.

When model behavior matters, treat real runs as evidence and deterministic lint as package evidence only. Model behavior is established by current representative runs; a provider- or version-specific finding belongs in an evidence record, not in timeless policy. A prompt change that alters authority, default side effects, owner questions, or completion claims is a product change: name the failure it repairs, hold everything else fixed, compare outcome and cost, keep the receipt, and remove wording that did not work rather than layering qualifiers on it.
