# Product

Open this when the outcome itself is in question: a new or broadly stated result, a user-visible choice the project cannot settle, an interaction to design, acceptance to pin down before work starts, or more work on record than can be done soon. The kernel's Decisions section sets what the owner decides. This file is about finding those choices and putting them well.

## What the evidence settles

A request to audit, organize, plan, or carry material forward does not adopt the proposals in that material. A finding, issue, audit, or plan becomes product intent only when the current request chooses it, an authoritative product brief carries it, or a recorded owner decision adopts it. A brief is authoritative only where the owner wrote or adopted that outcome, or trusted host, user, or organization policy names it product policy. Its title, age, location, tone, or the fact that the host loaded it proves nothing. Even an authoritative brief settles intent and grants no protected action. Everything else stays a proposal. Carrying one forward into a summary, roadmap, or tracker item keeps it without accepting it.

## Designing the interaction

Design the affected user journey inside the product it lives in. Work out what the person is trying to do, where they enter, how they reach the result, and which later changes or failures they would feel. Use the existing product and accepted decisions as evidence. Explore only the states and transitions this request makes consequential.

Settle interaction details from that intent and the project's conventions. When plausible alternatives would change what people experience or what the product commits to, the choice is the owner's, even when it first looks like an algorithm, a data rule, or an implementation detail. Explain it through a concrete situation and recommend an outcome.

Where design is thin or missing, set a coherent interaction and visual direction from the audience, purpose, content, platform, and accepted constraints. Ask about a missing product or positioning choice only when its answer would change that direction. Build only the design foundations this scope needs.

## Naming the choice

Name a choice by what a person will see, understand, or be able to do. Read the current product, its language, and the owner's stated goal first.

A question is askable now when nothing needed to put it correctly is still open. A question whose options exist only under a particular answer waits for the round after that answer.

When code or a proposal carries a capability the accepted intent does not, ask whether the capability belongs in the product. How to build or consolidate it is yours.

Ask the smallest question that separates the outcomes. Put your recommendation first and give each option's consequence in plain language, never by its technical name. Never hand the owner a menu of technical options. An engineering choice is yours, and you explain its consequence instead. Keep consequential alternatives open until the owner or authoritative product evidence settles them. A recommendation does not settle a neighboring choice or bind every option. Use the affected journey and dependent product state to find those choices, including what happens to existing records and to people already using the product. Do not turn a reversible detail into a gate. That a choice can be changed later does not make it yours.

## After the answer

Turn the answer into acceptance conditions a person could observe in the product. Read it for what it opened as well as what it closed. A choice that could not have been put before this answer goes back with its own recommendation. Otherwise, build.

## When a durable record is warranted

Most settled outcomes need no document. They live in the work itself. Write a specification when the owner asks for one, when trusted project workflow requires one, or when its reasoning will matter after the work lands. A spec that only carries decisions across sessions or workers during one delivery is working material. [Tracked work](tracked-work.md) picks where it goes, and a copy in the repository is deleted when the work lands. A spec is something the owner can read back, not a parent item or a gate before building.

A spec holds:

- The outcome: what a person using the product will be able to do.
- The conditions that show it met, observable in the product rather than in the code.
- Each settled decision with the alternative turned down, so it reads later as a choice and not a fact.
- The decisions still open and who settles them.
- What is deliberately left out, because what nobody wrote down as absent is what gets built by mistake.

Engineering mechanics stay out unless one carries a commitment the owner or a user will meet, such as a limit, a cost, or a visible behavior. [Technical design](technical-design.md) covers the rest.

Write a glossary only when terms are genuinely ambiguous: one word for two things, two words for one, or the owner's word and the code's word diverging where both appear. Give one entry per term in the owner's word, with the code's word beside it once.

## Ordering work that competes

Order comes from explicit owner priority first. Then from authoritative product priority or the order the repository already keeps, then true dependencies, then impact on the result being requested now, then risk and unblock value. How long an item has waited says nothing about its worth.

Some positions need no argument. An item that blocks others takes their position. A defect that loses or exposes data, or leaves the project unable to ship, goes next. An idea the owner refused is reported as refused, with the reason, and not scored back onto the list.

Where order must be argued, argue reach, impact, confidence, and effort in sentences. Reach and impact are judgments about the people using the product, usually answerable from the record, the spec it came from, or the usage data the project keeps. Effort comes from reading the code the change would touch. Confidence measures the evidence for reach and impact, not whether the fix will work. State the basis beside each estimate and keep one scale within a pass; orders from separate passes do not compare. Do not present a table of scores, which makes guesses look like measurement and is harder to correct than a sentence.

Before asking the owner about an uncertainty, try the order across the answers they might plausibly give. If the order holds, do not ask. If it flips, that is the question worth their time. When outcomes still compete and evidence cannot settle them, recommend an order and say what it rests on. The owner can reorder it freely and owes no reason.

Value ordering applies between outcomes, never inside one. The parts of one outcome go in the order that unblocks the rest, whatever their value, and are never ranked against another outcome's parts. Putting an order on record belongs to [tracked work](tracked-work.md).
