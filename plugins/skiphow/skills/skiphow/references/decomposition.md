# Decomposition

Use this for work whose parts would land, be verified, or be reviewed separately.

## When to split

Split work when it carries more than one independently verifiable outcome. Decide that from the requested result, before starting, rather than discovering it when a single pass runs out of room. Work with one observable outcome stays one unit however long it takes.

Splitting is judgment about the work, not a stage to perform. Two small edits that one pass finishes and one check proves are one unit, whatever they touch. Split when carrying the whole result at once would cost more than the split does: when the parts land, get verified, or get reviewed at different times, when different people or lanes must work on them, or when one part could ship while another waits. Below that, name the parts in the plan and get on with it.

## The size of a unit

A unit is the right size when it delivers one behavior someone can observe end to end, can be verified on its own, and can be reviewed in one pass. Cut through the layers rather than along them. A unit named for a layer, a schema, an endpoint, or a screen cannot be demonstrated or verified alone. Nothing can be judged until every sibling lands and the whole result arrives for review at once. That is what makes large work slow and expensive, not the amount of code in it.

Too small is also wrong. Something that cannot be shown true by itself is a step inside a unit, not a unit. Do not split work into parts whose only boundary is the order you imagined doing them in.

A mechanical change with a wide blast radius is the exception, because it has no honest vertical slice. Renaming a shared symbol, changing a type every caller uses, or moving a module cannot deliver partial behavior. Sequence it instead: add the new form beside the old one, move call sites in batches, then delete the old form. Each step leaves the project working, which is the property the vertical slice was protecting.

State each unit as the outcome and what would show it true. Do not prescribe files, names, structure, or steps. That is the work of whoever implements it, and dictating it wastes the judgment you delegated. Name a constraint only when getting it wrong would produce the wrong product.

## Dependencies

A unit is blocked when it needs another's result, and not when you would rather do it first. Record only those edges. Order presented as dependency is the most common reason work that could have run concurrently runs in a line.

Decompose only as far as the next outcome that can be verified. Where later work depends on what the earlier work reveals, leave it as an outcome with its open questions attached rather than inventing units whose shape that work will change.

## Checking the split

Check the decomposition before acting on it, against the original request and the records themselves rather than against the reasoning that produced them. Whoever drew the split is the worst judge of whether it holds, so have a delegate check it from the request and the records alone, or failing that read it back cold. Look for:

- a unit with no observable outcome
- a unit no one can verify without another
- an invented dependency
- a prescribed implementation
- any part of the requested result that no unit covers
- two units that would end up doing the same work
- a common direction that live evidence already contradicts

A complete split of an unsupported solution is still the wrong plan, and discovering that after launch costs every unit already running.

## Where the split lives

Where the request authorizes recording the decomposition and the project keeps tracked work, it belongs there in the tracker's own hierarchy rather than only in the conversation, and [tracked work](tracked-work.md) governs that write, including the difference between a sub-item and a real dependency. A record the request authorizes for something else is not permission to write the split beside it. A request only to plan, compare, or advise records nothing and returns the split in the answer.

When the decomposition is recorded but not yet carried out, say plainly where it lives and what continues it, so continuing does not depend on this conversation surviving. Use [delegation](delegation.md) to run it.
