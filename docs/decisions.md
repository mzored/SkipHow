# Decision history

This page records the choices that still matter when SkipHow changes. Read it before reopening an old design argument.

The complete decision archive remains available in the immutable [`v2.0.1` source snapshot](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/decisions). The matching [research and receipts](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/research) preserve the full evidence behind the summaries below.

## One owner entry

SkipHow exposes one plain-language skill. Focused methods remain internal references.

Earlier versions tried named routes, separate commands, role files, and sibling method skills. Those shapes either exposed engineering workflow to the owner or allowed a method to load without the authority kernel.

Revisit this if a portable skill standard adds required skill dependencies, or repeated receipts show one entry causing missed outcomes or unauthorized actions.

## Host-native execution

SkipHow relies on host sessions, worktrees, subagents, permissions, and continuation. It does not ship a runner or coordinator.

The project built and removed Python runtime machinery. It duplicated host state, increased failure modes, and made a small instruction package responsible for orchestration.

Revisit this if supported hosts lose required durability, or verified demand appears for provider-neutral unattended work on hosts without native continuation.

## Authority follows the requested outcome

Read-only requests stay read-only. Record requests grant only the record. Project changes include edits, checks, a clean local commit, and the durable records the project keeps for that work: the agreed outcome, the state needed to resume it, and one carry-forward record for a material problem left unfixed. Shared delivery must be requested. Protected actions need an explicit grant.

Earlier versions tried magic phrases, fixed routes, tracker markers, and GitHub lifecycle rules. They made wording and procedure more important than the owner's actual outcome.

Version 2.1.0 added the durable records because the earlier contract met this section's own revisit condition: a separable finding that reached only the chat transcript was a dropped material outcome, and the next session paid to rediscover it. The records use the project's own tracker and classification, so no SkipHow schema returns with them.

Revisit this if a receipt shows an unauthorized protected action, a dropped material outcome, or repeated questions about routine engineering mechanics.

## No universal engineering workflow

Planning, TDD, review, worktrees, delegation, and pull requests are tools. None is a mandatory stage for every request.

The 1.x contract accumulated planner, builder, reviewer, model tier, queue, timeout, diff, and prose rules. The root grew while small work still stalled on mechanics. Version 2.0 removed those gates.

Reconsider one method only when paired evidence shows that it adds cost or delay without improving the result. Add a universal rule only when capable agents repeatedly miss a high-risk boundary without it.

## Tracked work is configured once, not re-derived

A project settles where its tracked work lives and who may see it in one owner question, recorded in the project's own agent instructions. Later sessions follow that record instead of inspecting again.

This reverses an alternative ADR 0014 rejected, and the ground has changed. That rejection covered classification, which a live read does recover. Destination and visibility cannot be read out of a repository at all: nothing in the code says whether the owner accepts a public record. Staleness is answered by refreshing the note when a write is rejected or the convention has visibly moved, not by inspecting every time.

Revisit this if a receipt shows a record written to a destination the owner did not choose, a stale note surviving a real convention change, or the setup question repeating in a configured project.

## Method depth is limited by loading, not by length

Methods carry the detail that changes what a capable agent does: the order to search before building something custom, what stops a lane from repeating a failed attempt, what makes a regression test close a bug class, what does not count as evidence.

Version 2.0 cut this material along with the workflow machinery it was tangled in, on the reasoning that shorter instructions cost less attention. That traded away substance for a saving the project never measured. What the project did measure, in the 1.8.0 audit, is that a reference which does not load governs nothing.

The constraint is therefore the trigger and the kernel, not the word count. Keep a method's trigger decidable without reading the file, keep anything that changes authority or the definition of done in the kernel, and let the method itself be as detailed as the discipline requires.

Revisit this if receipts show applicable methods going unread, a kernel rule displaced into a reference, or added depth producing no change in outcome.

## Decomposition is decided before the work, by verifiability

Work splits when it carries more than one independently verifiable outcome and carrying the whole result at once would cost more than the split does. A unit is right-sized when one person can observe its behavior end to end, verify it alone, and review it in one pass. Parts that land, get verified, and get reviewed together stay one unit whatever they touch.

Version 1.9.0 established that decomposition needs a trigger a run can evaluate, and 2.0 removed it with the rest of that contract. What replaced it fired on work "too large for one pass", which a run can only judge after the pass has failed, and it lived inside the delegation method, so work that was not delegated was never split at all. The sizing rule that remained, that a delegate's task be narrow enough to finish and verify on its own, named verification but left the shape of a unit open, and an agent choosing a shape freely splits along layers. Layer-shaped units cannot be demonstrated or verified alone, so review necessarily waits for all of them and happens once, at full size.

The verifiability test is decidable in advance, and the proportionality it is paired with compares the cost of carrying the whole result against the cost of splitting it, rather than estimating how long the work will take. Mechanical changes with a wide blast radius have no honest vertical slice and are sequenced expand, migrate, contract instead.

Revisit this if receipts show work split into units that cannot be verified alone, invented dependencies serializing independent work, or the test producing units too small to demonstrate.

## Critical rules stay in the kernel

Authority, autonomy, preservation, and completion remain in `SKILL.md`. Conditional technique belongs in a focused reference.

Earlier designs put mandatory behavior behind conditional reads. Missing one reference could change what the agent was allowed or required to do.

Revisit this if a critical rule moves behind a reference, or installed receipts repeatedly miss a method needed for correct work.

## Provider-independent policy

The shared skill contains no versioned provider model IDs, cost tables, or host-specific routing tiers. Hosts choose models and effort.

Several releases tried semantic tiers and adapter files. Host metadata changed too quickly, and the package had no reliable cost signal for a portable router.

Revisit this if hosts publish a stable portable capability interface and paired runs show a material quality or total-cost benefit.

## Receipts prove model behavior

Deterministic checks prove package structure. They do not prove how a model behaves. Deliberate runs with retained receipts support behavior claims.

The project removed a live evaluation harness because it could mutate repositories, spend budget, and still fail to prove the exact installed package. A later contributor-only transcript parser became larger than the product and coupled maintenance to private host log formats. Version 2.0.2 removes that parser from the repository.

Revisit automated evaluation when a host offers repository-preserving runs against an exact installed package with trustworthy receipts.

## Keep the current tree current

Current design, decisions, and evidence stay in four small documents. Superseded raw material remains in immutable commits, tags, pull requests, and releases.

Do not add one ADR or research file per release. Update this page when a decision changes. Update [`evidence.md`](evidence.md) when the set of supported claims changes. Link to durable source material instead of copying it into the current tree.
