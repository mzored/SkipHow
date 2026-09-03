# Product

Use this when the outcome itself is in question: a new or broadly stated result, a user-visible choice the project cannot settle on its own, settling what the owner wants before work starts, or more work on record than can be done soon.

## What the evidence settles

A request to audit, organize, plan, or carry material forward does not adopt the proposals that material contains. A finding, an issue, an audit, or a plan becomes product intent only where the current request chooses that outcome, an authoritative product brief carries it, or a recorded owner decision adopts it. Everything else in those sources stays a proposal, however confidently it is written and however long it has sat there. Carrying one forward intact, into a summary or a roadmap position or a tracked item, preserves it rather than accepts it.

## Naming the choice

Name a choice in terms of what a person will see, understand, or be able to do, reading the current product, the language around it, and the owner's stated goal first.

A question is askable now when nothing you would need to put it correctly is still open. One whose options only exist under a particular answer is not askable now; it belongs to the round after that answer arrives.

When current code or a proposal carries a capability that the accepted product intent does not, ask whether the capability belongs in the product, not how to implement or consolidate it.

Where a choice does reach the owner, ask the smallest question that separates the outcomes, recommend one option first, and give its consequence in plain language rather than by its technical name. Do not turn a reversible detail into a gate. Being able to change something later is not what makes a choice yours.

## After the answer

Translate the answer into acceptance conditions observable in the product. Read it for what it opened as well as what it closed: where it makes material a choice that could not have been put earlier, that one goes back with its own recommendation. Where it does not, build.

## When a durable record is warranted

A durable product specification exists where the owner asked for one or where authoritative project workflow requires one. Whether anything else authorizes writing one, and where it may go, is [tracked work](tracked-work.md)'s question. Otherwise the settled outcome lives in the work itself. It is a document the owner can read back, and it need not become a parent item to count.

What the record captures:

- The owner-visible outcome: what a person using the product will be able to do.
- The conditions that would show it met, observable in the product rather than in the code.
- The decisions the owner settled, each with the meaningful alternative turned down. A decision written without its alternative reads later as a fact about the product rather than a choice somebody made.
- The decisions still open, and who has to settle them.
- What is deliberately excluded. The thing most likely to be built by mistake later is the thing nobody wrote down as absent on purpose.

Engineering mechanics stay out of the owner-facing record unless one of them carries an owner-facing commitment of its own, such as a limit, a cost, or a behavior a person will meet. [Technical design](technical-design.md) settles and records the rest.

A glossary is worth writing only where terminology is materially ambiguous or inconsistent across the people or documents involved: one word covering two things, two words covering one, or the owner's term and the code's term diverging where both appear. Then give one entry each, in the owner's term, with the code's named once beside it. A glossary is not a precondition for stating outcomes, and most outcomes need none.

## Ordering work that competes

Order comes from explicit owner priority; then from authoritative product priority or the ordering the repository already keeps; then from true dependencies; then from impact on the result currently being requested; then from risk and unblock value. Tracker age is not priority: how long an item has sat says nothing about what it is worth.

Some positions are not argued at all. An item that blocks others inherits their position rather than earning its own. A defect that loses data, exposes it, or leaves the project unable to ship goes next whatever the argument says. An idea the owner already refused is reported as refused, with the reason, rather than scored back onto the list.

Where positions do have to be argued, argue reach, impact, confidence, and effort in sentences. Reach and impact are judgments about the people using the product, usually answerable from the record's own text, the specification the work came from, or whatever usage evidence the project keeps. Effort comes from reading the code the change would touch. Confidence measures the evidence behind reach and impact, not whether the repair will work: a well-understood fix nobody has established the value of ranks low on confidence, and saying so is the point of the factor. State the basis of an estimate beside it and keep one scale across a pass; items ordered in separate passes are not comparable. A ranked table of scores presents arithmetic over guesses as measurement, and it is harder to correct than a sentence.

Before taking an uncertainty to the owner, sweep that factor across the range their answer could plausibly take. Where the order holds across that range, the question is not material and is not asked. Where it flips, that is the one worth their attention. When genuinely competing outcomes remain and evidence cannot settle the order, recommend an order and say what it rests on, asking only where the difference is material. What comes back is a list they can reorder: their order stands over any argument, and no reason is owed for it.

## What ordering does not apply to

Ordering by value never runs inside one outcome. The parts of a single decomposition are sequenced by what blocks what, and whichever is more valuable, the one that unblocks the other still goes first. Where a project holds both shapes, the competing things are the outcomes, and one outcome's internal parts are never ranked against another's. Putting an order on record belongs to [tracked work](tracked-work.md).
