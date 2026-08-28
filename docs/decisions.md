# Decision history

This page records the choices that still matter when SkipHow changes. Read it before reopening an old design argument.

The complete decision archive remains available in the immutable [`v2.0.1` source snapshot](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/decisions). The matching [research and receipts](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/research) preserve the full evidence behind the summaries below.

## One owner entry

SkipHow exposes one plain-language skill. Focused methods remain internal references.

Earlier versions tried named routes, separate commands, role files, and sibling method skills. Those shapes either exposed engineering workflow to the owner or allowed a method to load without the authority kernel.

Version 2.6.0 considered a command surface for four owner-facing entries and did not ship one. Two of the four restated policy the methods already carried, which is duplication that drifts at the first edit to either copy. The other two would have earned their place only by naming a method file so its loading stopped being the model's decision, and the evidence for that is the general non-loading measured in 2.5.0 rather than anything about these methods. Codex plugins also support no command surface at all, so anything a command carried would have existed on one host and not the other. What the owner asked for is now two methods with triggers stated in their own words, reached the same way on both hosts.

Revisit this if a portable skill standard adds required skill dependencies, if receipts show the new methods going unread from a plain-language request, or if repeated receipts show one entry causing missed outcomes or unauthorized actions.

## Host-native execution

SkipHow relies on host sessions, worktrees, subagents, permissions, and continuation. It does not ship a runner or coordinator.

The project built and removed Python runtime machinery. It duplicated host state, increased failure modes, and made a small instruction package responsible for orchestration.

Revisit this if supported hosts lose required durability, or verified demand appears for provider-neutral unattended work on hosts without native continuation.

## Authority follows the requested outcome

Read-only requests stay read-only. Record requests grant only the record. Project changes include edits, checks, a clean local commit, and the durable records the project keeps for that work: the agreed outcome, the state needed to resume it, and one carry-forward record for a material problem left unfixed. Shared delivery must be requested. Protected actions need an explicit grant.

Earlier versions tried magic phrases, fixed routes, tracker markers, and GitHub lifecycle rules. They made wording and procedure more important than the owner's actual outcome.

Version 2.1.0 added the durable records because the earlier contract met this section's own revisit condition: a separable finding that reached only the chat transcript was a dropped material outcome, and the next session paid to rediscover it. The records use the project's own tracker and classification, so no SkipHow schema returns with them.

Version 2.5.0 named where the largest of those records goes. The contract already granted "the state a later session needs to continue it" without saying where, and installed sessions read it as a local file: in two of them the plan driving the whole run was untracked, invisible on the project's own tracker, and never brought current — one a seventeen-kilobyte specification carrying the owner's own pricing and legal decisions, whose file was last written ninety minutes before the two-hour session that executed it and never again, while that session's context was compacted mid-run. Where an authorized change runs across several units and needs a plan to finish safely, that plan now belongs in the place the project already keeps tracked work. This names a destination the grant did not, and it is new policy to that extent; it leaves `continuity` to decide when a checkpoint exists at all, introduces no format, schema, or file of SkipHow's own, and reaches only work the owner already authorized as a change.

Revisit this if a receipt shows an unauthorized protected action, a dropped material outcome, or repeated questions about routine engineering mechanics.

## An unstated choice is an unfinished result

Where the owner's request leaves open a material choice in what a person using the product gets, and available project evidence cannot settle it, the agent asks before building and reports any choice it made instead, named with the alternative it did not take. A result that hides such a choice is not finished. What the project cannot do yet settles nothing: it is a cost for the owner to weigh, and treating it as an answer was the escape that survived the first two drafts.

Receipts against 2.3.0 showed the opposite three times. Given "let someone share their cart with a friend", the agent picked one reading of sharing, built it, and described the behavior as though it were the request. Executing tracked work, it took an item recorded as `Blocked: needs a decision on how long notes can be`, invented a limit, shipped it, marked the item done, and deleted the note that a decision was owed.

The first draft of the fix put the rule in the kernel's autonomy section as a pre-build trigger. An independent review argued the trigger was the agent's own estimate of novelty, which is exactly the shape 1.9.0 identified as unusable, and that a reporting duty without a completion consequence changes nothing. Receipts agreed: the tracker case was fixed, the underspecified-idea case was not. Binding it to the definition of done, and closing the escape where a technical limit stands in for a product answer, is what held.

Version 2.4.2 amended the round. "Ask in one round" was written against interrogation, and it worked, but it also reads as a budget the owner's first answer spends. Paired receipts showed both hosts spending it. Asked to build order cancellation, each asked how far cancellation should reach; told "also after it has shipped", each then settled on its own what happens when the carrier cannot stop the parcel, who absorbs the recall fee, and how many attempts a customer gets. None of those choices existed before that answer, and the project settles none of them. Claude named them and framed the answer as permission, "rather than come back to you". Codex reported them as the behavior it had built. One round is now the shape of a batch and not a limit: ask together everything that can be asked now, and when an answer makes a further choice material, ask that one too. The bar for asking is unchanged, so work the project already defines still starts no round.

The same release found the rule needing one more clause, and the receipt for it is the candidate's own. Having asked the two questions its new frontier had opened, Claude then built both answers anyway — the fee absorbed, a failed recall leaving the order standing — committed them, and reported the second one as "the failure case your answer opened, and I had to pick something to ship", offering to switch it. Making a product choice reversible does not make it yours. A default is that choice made for the owner, and a switch only offers them the chance to notice. Having asked, nothing whose product meaning depends on the answer is built, committed, or treated as settled; the parts that do not depend on it carry on as before, and a reversible technical choice was never in scope. The paired run under the new clause committed the decision and the two open questions to the project's own record and wrote no behavior, in its own commit message "since either choice would otherwise be settled by whatever default was written".

The wording that made the escape available went with it. Both the kernel and the method still said that a choice made instead of asking belongs in the report, and that a reading taken because no answer was available is the owner's to overturn — which is the sentence the failing run quoted back as "I chose, you can overturn". Disclosure is not a substitute for asking. What gets reported is a reading the project settled; a material choice the project settles nothing about is not made available by the absence of an answer; and a result that already contains such a choice is unfinished until the owner answers and the behavior agrees with them. That removal is a contradiction closed, not a behavior receipted.

The frontier is adapted from Matt Pocock's `grilling`, which asks each round the decisions whose prerequisites are settled and recomputes after the answers. The interview around it is not adapted. `grilling` runs until every branch of a design tree is visited; SkipHow stops at the first point where nothing material is open, and never opens a round for a choice the project or a source can settle. Superpowers' `brainstorming` was read and rejected whole: it gates every task behind a human approval of the design, including the ones it calls too simple to need one, which is the opposite of this project's boundary. `to-spec` and `to-tickets` were re-read for the same reason and rejected again; both require the owner to approve engineering shape, one a spec and the other ticket granularity, which SkipHow owns.

Revisit this if receipts show questions on work the product already defines, an owner asked about engineering mechanics, or a small change acquiring a round of clarification.

## What the owner decided is a record, not a message

An answer the owner gives is a decision the project carries. Where the request authorizes a record, it is written where the work is tracked, with what it settled and the option they turned down, before anything depending on it is built. When the owner asks to settle what they want before work starts, `product-spec` turns that into a document they can read back: a vocabulary in their own words settled before the outcomes, the outcome stated as what a person will be able to do, each decision with its rejected alternative, and what is deliberately out of scope.

The kernel already required naming the alternative for a reading the agent took on the owner's behalf. It said nothing about the answers the owner gave. Installed sessions recorded them well anyway — one wrote "Решение владельца 2026-08-28" into the issue it opened for the work — but that was good practice rather than a rule, and the seventeen-kilobyte specification carrying the same owner's pricing and legal decisions stayed an untracked local file that its own executing session never reopened.

Version 2.5.0 adds the rule and the method. The method fires on the owner's own request and not on the agent's judgment that a result was broadly stated: that case was already covered, by asking under `product-decisions` and recording the agreed outcome, and making it a second trigger would have added a procedure the receipts do not support. Only the documentary half of `grill-with-docs` is adapted; its interview is the `grilling` frontier already adopted in the section above, and that section's stopping rule is restated in the method so the spec cannot become an interview that runs until a design tree is exhausted. The standing rejection of `to-spec` and `to-tickets` is intact: the owner reads and checks the product they want, never the engineering shape, and the method forbids prescribing files, structure, steps, or ticket granularity. What is new and not adapted from anywhere is the vocabulary rule; nothing in the package had one, and a term that carries two meanings is a defect that reaches every delegate reading the spec.

Revisit this if receipts show the record duplicating what the tracker already holds, a spec written for work the owner had already stated plainly, or the vocabulary list growing past what the outcome needs.

## A consequential decision gets one outside read

A technology, architecture, or system-shape decision that is expensive to undo gets one read from a context that did not produce it, given the problem and the evidence rather than the preferred answer, and asked what it would choose and what would make that choice wrong. The rule lives in the method that owns those decisions, so its reach is that method's trigger and no wider. A second host or model family is preferred over a second pass by the same context. The result is evidence to weigh, not a vote.

Version 1.12 had this as cross-host escalation with named commands, and 2.0 removed it with the rest of that machinery. The mechanics were the defect: they encoded one host's invocation into portable policy. The invariant survives the implementation, because whoever made a decision is the worst judge of it. The project keeps paying for that. Version 2.3.0 shipped only after two independent reviews found roughly twenty defects in a hundred lines, and this release's own kernel wording was rewritten after a review contradicted it.

Version 2.4.2 tried to make the rule execute and failed, which is worth recording so the next attempt starts further along. Ten runs on an order service that charges the card inside the same transaction as the warehouse call — a decision that commits the project to a schema, a retry loop, and an operational dependency — produced ten sound transactional-outbox designs and not one outside read, five runs on each host, with `technical-design` demonstrably open in all five on Codex. Three kernel wordings were tried and discarded: the read as a condition of finishing, the same with the host's own delegate named, and the same as a step before building on the decision. None changed the behavior on either host, and none of the runs mentioned the rule. What the runs did say points at the trigger rather than the wording: each treated its own choice as ordinary and cheap to reverse, and one listed its remaining choices as "both reversible". "Expensive to undo" is the agent's own estimate of its own decision, which is the shape 1.9.0 identified as unusable. So nothing was promoted, the rule stays where it was, and the behavior stays `UNVERIFIED`. A future attempt should replace the trigger, not restate the duty.

Revisit this if a trigger appears that a run can evaluate without grading its own decision, if receipts show the outside read returning agreement without finding anything, or if its cost exceeds the rework it prevents.

## Ordering applies only to work that competes

A roadmap is produced where more candidates are on record than can be done soon and no order settles them: accumulated ideas, feature requests, user feedback. Units belonging to one outcome the owner already authorized are not ranked. They are sequenced by what blocks what, and whichever is more valuable, the one that unblocks the other still goes first, so a ranking over siblings inside a decomposition is arithmetic that dependency then overrules.

The owner raised this against the first draft of `prioritization`, which scored recorded work generally. The risk they named is the one that would have made the method worthless: run over the epics and tasks of one large piece of work, it spends a pass to rediscover the dependency edges the decomposition already wrote down. The method now checks which shape is in front of it before scoring anything, and a project holding both ranks the competing outcomes while never ranking one outcome's internal parts against another's.

What comes out is a short roadmap in the project's own tracker that the owner reorders without owing a reason, not a scored table. RICE is how a position is argued when they ask why, not the artifact. Effort is the agent's and never asked; reach and impact are theirs and usually already answered by the project's records; a question reaches them only where sweeping the uncertain factor across its plausible range actually changes the order.

Revisit this if receipts show a roadmap the owner never reorders, ordering questions reaching them on work the project already settles, or competing candidates going unordered because the shape test read them as one outcome.

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

Version 2.5.0 acted on this condition on the loading half of it. Across four installed 2.x sessions on two repositories, two of them dispatching eighteen and eight delegates, none of `decomposition`, `delegation`, or `execution-health` ever reached context — established by searching the transcripts for the files' own sentences, not only for their paths. What those receipts show is non-loading, not a wrong result traced to it; the condition as written asks for a method "needed for correct work", and that half stays inferred. Two rules moved into the kernel in their delegate-facing minimum form, both about a delegate rather than about technique: the size of the outcome one delegate carries, and naming the level it runs at. The technique behind each stayed in its method. The kernel also gained a requirement to read a method whose trigger plainly matches before acting on that work. That is an addition, not a narrowing: the sentence it replaced barred loading a method "merely because it exists", which left an applicable method optional, and optional is what the receipts measured.

A third candidate was dropped for want of evidence. Neither root ever formed an expectation of how long a delegate should take, and one reported while a lane it had accepted two hours earlier was still running and unmentioned. That shows the expectation was never set; it does not show the durations were unhealthy, or that a capable agent could not infer when to intervene. Requiring a pre-dispatch duration estimate would have been a mandatory step on evidence that does not reach the bar this repository sets for one. The kernel says only what to do with a lane that has visibly stopped progressing, and the pre-dispatch technique stays in `execution-health`.

Kernel placement raises the odds; it does not settle the question. The same sessions carried the kernel's existing rule against placing an isolated checkout beside the repository, and one session created three sibling worktrees anyway. A rule in the kernel is read; whether it is followed is a separate measurement, and this one is `UNVERIFIED` until receipts.

Revisit this if a critical rule moves behind a reference, or installed receipts repeatedly miss a method needed for correct work.

## Provider-independent policy

The shared skill contains no versioned provider model IDs, cost tables, or host-specific routing tiers. Hosts choose models and effort.

Several releases tried semantic tiers and adapter files. Host metadata changed too quickly, and the package had no reliable cost signal for a portable router.

Effort is chosen relative to the current session, never in host terms. Both supported hosts expose a per-delegate reasoning control through incompatible surfaces, and neither treats a level name as meaning the same amount of work across models, so no portable absolute setting exists to name. The package therefore states only levels relative to the dispatching session and leaves the control for the agent to find in its host's current documentation.

Version 2.5.0 restored a `model-routing` method. The owner decided this, and the condition below was not met when they did: no host has published a portable capability interface, and no paired run has shown a quality or total-cost benefit. What the receipts add is a defect the earlier reasoning had not weighed. That reasoning was about the risk of naming host models; it did not consider that saying nothing is itself a routing choice. On the measured host a delegate whose level is unset inherits the session's, and across two installed sessions twenty-five of the twenty-six delegates the roots dispatched ran on the session's own model, including every implementation lane, while the single explicit downgrade went to the one delegate that was judging — the case the floor exists to protect.

The method therefore names what the work demands and never what a provider calls it: mechanical work at the cheapest sufficient level, work carrying a settled design at the ordinary one, deciding work at the strongest, and anything that reviews or judges at no less than the session. Inheritance is stated as something to check on the current host rather than as a portable fact. Where a host offers only an effort control the levels collapse onto it, and where it offers no per-delegate control the levels are unavailable. No model identifier, tier key, or cost table enters the package, so the boundary this decision protects is intact.

The cost claim is not part of this and the method says so. That routing down is cheaper in total rather than merely per token stays `UNVERIFIED` until paired runs measure it, so the method presents routing down as a judgment about how well the work is specified rather than as a saving.

The original condition — a portable capability interface and paired runs showing a benefit — is superseded rather than satisfied, because the decision to restore was the owner's. Revisit this instead if paired runs settle the total-cost question either way, or if receipts show routed-down lanes spending more than the level they saved.

## Receipts prove model behavior

Deterministic checks prove package structure. They do not prove how a model behaves. Deliberate runs with retained receipts support behavior claims.

The project removed a live evaluation harness because it could mutate repositories, spend budget, and still fail to prove the exact installed package. A later contributor-only transcript parser became larger than the product and coupled maintenance to private host log formats. Version 2.0.2 removes that parser from the repository.

Version 2.4.0 produced the first receipts since 2.0 by holding the package fixed and varying nothing else: a throwaway fixture repository per run, a host home containing only the candidate skill tree, no user-level skills, and the same prompt before and after a change. That is enough to show a defect and to show it gone. It is not a reliability rate, and one host's behavior is not the other's.

Revisit automated evaluation when a host offers repository-preserving runs against an exact installed package with trustworthy receipts.

## Keep the current tree current

Current design, decisions, and evidence stay in four small documents. Superseded raw material remains in immutable commits, tags, pull requests, and releases.

Do not add one ADR or research file per release. Update this page when a decision changes. Update [`evidence.md`](evidence.md) when the set of supported claims changes. Link to durable source material instead of copying it into the current tree.

The rule bounds per-release records, not the number of reader-facing pages. Version 2.4.3 added [`prior-art.md`](prior-art.md) and [`faq.md`](faq.md) as standing documents that answer a question a reader arrives with. The prior-art material had been written before and was deleted with the research tree it lived in, which lost the reasoning behind several rejections that this page still depends on. Both pages are revised when the answer changes and neither accumulates a section per release.
