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

## An unstated choice is an unfinished result

Where the owner's request leaves open a material choice in what a person using the product gets, and available project evidence cannot settle it, the agent asks before building and reports any choice it made instead, named with the alternative it did not take. A result that hides such a choice is not finished. What the project cannot do yet settles nothing: it is a cost for the owner to weigh, and treating it as an answer was the escape that survived the first two drafts.

Receipts against 2.3.0 showed the opposite three times. Given "let someone share their cart with a friend", the agent picked one reading of sharing, built it, and described the behavior as though it were the request. Executing tracked work, it took an item recorded as `Blocked: needs a decision on how long notes can be`, invented a limit, shipped it, marked the item done, and deleted the note that a decision was owed.

The first draft of the fix put the rule in the kernel's autonomy section as a pre-build trigger. An independent review argued the trigger was the agent's own estimate of novelty, which is exactly the shape 1.9.0 identified as unusable, and that a reporting duty without a completion consequence changes nothing. Receipts agreed: the tracker case was fixed, the underspecified-idea case was not. Binding it to the definition of done, and closing the escape where a technical limit stands in for a product answer, is what held.

Version 2.5.0 amended the round. "Ask in one round" was written against interrogation, and it worked, but it also reads as a budget the owner's first answer spends. Paired receipts showed both hosts spending it. Asked to build order cancellation, each asked how far cancellation should reach; told "also after it has shipped", each then settled on its own what happens when the carrier cannot stop the parcel, who absorbs the recall fee, and how many attempts a customer gets. None of those choices existed before that answer, and the project settles none of them. Claude named them and framed the answer as permission, "rather than come back to you". Codex reported them as the behavior it had built. One round is now the shape of a batch and not a limit: ask together everything that can be asked now, and when an answer makes a further choice material, ask that one too. The bar for asking is unchanged, so work the project already defines still starts no round.

The frontier is adapted from Matt Pocock's `grilling`, which asks each round the decisions whose prerequisites are settled and recomputes after the answers. The interview around it is not adapted. `grilling` runs until every branch of a design tree is visited; SkipHow stops at the first point where nothing material is open, and never opens a round for a choice the project or a source can settle. Superpowers' `brainstorming` was read and rejected whole: it gates every task behind a human approval of the design, including the ones it calls too simple to need one, which is the opposite of this project's boundary. `to-spec` and `to-tickets` were re-read for the same reason and rejected again; both require the owner to approve engineering shape, one a spec and the other ticket granularity, which SkipHow owns.

Revisit this if receipts show questions on work the product already defines, an owner asked about engineering mechanics, or a small change acquiring a round of clarification.

## A consequential decision gets one outside read

A technology, architecture, or system-shape decision that is expensive to undo gets one read from a context that did not produce it, given the problem and the evidence rather than the preferred answer, and asked what it would choose and what would make that choice wrong. The rule lives in the method that owns those decisions, so its reach is that method's trigger and no wider. A second host or model family is preferred over a second pass by the same context. The result is evidence to weigh, not a vote.

Version 1.12 had this as cross-host escalation with named commands, and 2.0 removed it with the rest of that machinery. The mechanics were the defect: they encoded one host's invocation into portable policy. The invariant survives the implementation, because whoever made a decision is the worst judge of it. The project keeps paying for that. Version 2.3.0 shipped only after two independent reviews found roughly twenty defects in a hundred lines, and this release's own kernel wording was rewritten after a review contradicted it.

Revisit this if receipts show the outside read returning agreement without finding anything, or its cost exceeding the rework it prevents.

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

Effort is chosen relative to the current session, never in host terms. Both supported hosts expose a per-delegate reasoning control through incompatible surfaces, and neither treats a level name as meaning the same amount of work across models, so no portable absolute setting exists to name. The package therefore states only a floor relative to the dispatching session and leaves the control for the agent to find in its host's current documentation. A relative floor is not a routing tier, and the revisit condition below stays unmet.

Revisit this if hosts publish a stable portable capability interface and paired runs show a material quality or total-cost benefit.

## Receipts prove model behavior

Deterministic checks prove package structure. They do not prove how a model behaves. Deliberate runs with retained receipts support behavior claims.

The project removed a live evaluation harness because it could mutate repositories, spend budget, and still fail to prove the exact installed package. A later contributor-only transcript parser became larger than the product and coupled maintenance to private host log formats. Version 2.0.2 removes that parser from the repository.

Version 2.4.0 produced the first receipts since 2.0 by holding the package fixed and varying nothing else: a throwaway fixture repository per run, a host home containing only the candidate skill tree, no user-level skills, and the same prompt before and after a change. That is enough to show a defect and to show it gone. It is not a reliability rate, and one host's behavior is not the other's.

Revisit automated evaluation when a host offers repository-preserving runs against an exact installed package with trustworthy receipts.

## Keep the current tree current

Current design, decisions, and evidence stay in four small documents. Superseded raw material remains in immutable commits, tags, pull requests, and releases.

Do not add one ADR or research file per release. Update this page when a decision changes. Update [`evidence.md`](evidence.md) when the set of supported claims changes. Link to durable source material instead of copying it into the current tree.
