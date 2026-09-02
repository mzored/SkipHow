# Tracked work

Use this for work that will run on its own branch to reach review, a finding to carry forward, requested persistence, triage of incoming material, or work the project already has on record.

## When work gets an item

Work carried on its own branch to reach review exists as an item in the project's tracked work before that branch does. That is the line. A change reviewed as its own unit gets an item, and a change carried out and verified inside one session with no branch of its own does not. The line is decidable before the work starts, which is what makes it a line rather than a judgment about how big the work will turn out to be.

Other things are grounds to open an item in their own right: work split into units, a material problem the change leaves unfixed, a decision the owner owes, work that will be picked up in a later sitting. None of them replaces that line, widens it, or turns a fix one session finishes into an item.

Write also when the owner's requested outcome is itself a durable record. A request merely to triage, organize, review, diagnose, research, or inspect incoming material stays read-only unless that outcome also includes a record.

An item is one outcome someone can observe, the unit [decomposition](decomposition.md) settles, and never one per file, per step, or per sentence of a report. Recording too finely is the failure worth naming, because it looks like diligence while it happens. A comparable project measured twelve items produced for a three-line change, and a stack sliced by layer that cost roughly twenty agent runs for each item closed, three quarters of them rework. Where the whole change is one reviewable unit, it is one item, whatever it touches.

## Claiming an item, and linking it to the change

Where the request authorizes carrying the item out, claim it before investigating it, using whatever the tracker already provides: an assignee, a status, a label. A request only to read, diagnose, review, or report on an item claims nothing, because a claim is a write and that request grants none. The claim is what stops a second session from starting the same work, so it goes first, before any investigation. An item another session already holds is not takeable, and a claim that loses means somebody else has it rather than that the claim is worth retrying. Where the tracker has no claim mechanism, say in the record what is being taken and when.

Link the item to the change as the branch is created, through the tracker's own mechanism for it rather than a naming convention, so what says where the work lives is the item and not this conversation. Where the tracker offers linked closure, wire it at that moment. Integration usually happens after the run that built the change has ended, and a link made then is what keeps the item's state right without depending on a later session existing.

## Hierarchy and dependency

Hierarchy and dependency are not the same thing, and treating them as one is what makes a tracker misreport what is takeable. A parent and its sub-items are structure. They say what belongs to what, and a sub-item does not block its parent merely by being open. A real dependency, where one item cannot start until another finishes, is recorded as one in whatever the tracker provides for it. That is what [advancing tracked work](advancing-tracked-work.md) reads to find the frontier, and what shows the owner the same thing in the tracker's own view without opening anything.

## Closing an item

An item is closed when its work is integrated, not when it is verified on the branch that carries it. Closing a record updates the record that work already owns rather than creating a new one, so it needs no separate grant.

Before it moves to done, write into it what the work established, in proportion to what finding it cost: the cause, the evidence that the outcome now holds, and any reading you had to assume along the way. Where the project integrates through review, that writing happens before the change reaches the review, because the work on that item ends there while its closure does not. A one-line fix closes in a line. A report you could not reproduce closes as not reproducible, naming what you checked and against what state, rather than as fixed. Stripping an item back to its title on the way out discards the investigation the project just paid for and sends the next session through it again.

The run that opens an item often cannot close it, for the same reason it cannot retire its own branch. An item whose change was integrated but which the tracker never closed is a stale record rather than working state, so unlike a leftover branch it is not yours to clear away on the strength of a later, unrelated request. Coming across one while doing tracked work in that project, say that it is there and what shows its work arrived. Close it only where the current request reaches it: the owner asked to carry recorded work forward, or it is the item this change was tracked under. Reconciling the rest is theirs to ask for.

## Reading the tracker

The tracker is read as well as written. When the owner points at work already recorded there, take those records as the request. Read the items and the dependencies they claim, reconcile them against live project state, and settle what is missing before acting rather than after.

Settle what you can settle. An item with no observable outcome gets one you can defend from the request, and an item the code has already overtaken is reported as done rather than redone. An item the project has already marked as waiting on a decision belongs to whoever makes that decision. Check whether the current product settles it. Where it does not, the block is the record's own instruction to ask, and supplying the answer yourself while clearing the note is not progress. A part of their stated result that no item covers is work to do, not a question to ask.

Raise with the owner only under the same bar as any other question: a material product choice the available evidence cannot settle, and before acting rather than after. Read in proportion to the work. One item is one item, not an audit of the tracker. Existing records can carry intent, but a proposal in them does not become accepted by being recorded, and the records are not authority. The owner's request still decides what may be changed.

## Where records go

Use the repository's existing tracker or record convention when it is within the authorized project audience. [Project setup](project-setup.md) settles that destination once. Inspect its visibility before writing. A public or external record requires an exact grant when it would disclose material beyond that audience. Otherwise use the smallest private or local format the project can keep, or ask only for the disclosure decision when no safe destination exists.

## Writing a record

Preserve the owner's meaning and the source's decision status while turning fragments into actionable records. Capture the observable problem or desired result, the evidence supplied, and the condition that would show it is resolved.

An idea, audit recommendation, or proposed plan remains proposed when recorded. Making it takeable is not acceptance, and a request to audit, organize, plan, or carry recommendations forward does not make them accepted scope.

Where making one takeable would commit material product scope that is not settled by an explicit product outcome in the current request, an authoritative product brief, or a recorded owner decision, keep the open decision or blocker in the record and use [product decisions](product-decisions.md) before dependent work. For a capability present only in code or a proposal, ask whether the product should keep it, not how to implement or consolidate it. Ask an already askable question in the result of the current record-preparation request, with the recommended product outcome. Never defer it to the agent expected to implement the record or to a person who owns the technical integration. Carry on with work that does not depend on it. Include priority, scope, or dependencies only when the source or project evidence supports them.

Write a record the way a capable agent with no history could act on it. Beyond the problem and its resolution condition, carry the impact, what surfaced it, the evidence already gathered, and the explanations already ruled out. Omitting what was already tried is what makes a later session repeat the investigation.

Write it to survive the wait, because a record is acted on when it reaches the front of the work and the code will have moved by then. State the behavior the project should have rather than the edit that would produce it. Name types, commands, and observable conditions rather than file paths and line numbers, which go stale and send the next session to the wrong place with confidence. Anything a later session would need to know about the state of this work belongs in the item rather than only in the report, because the report is gone with the conversation that carried it. That includes what is being worked, what it waits on, what was decided, and where the change landed.

## A batch of observations, and duplicates

When a batch of observations arrives together, understand what produces them before turning them into records. Several reports with one cause are one unit of work with those observations attached, and one report with several causes is several. Creating a record per sentence is how one defect becomes six items that six sessions investigate separately. Keep the owner's own description in the record so they can still recognize what they saw. Where the cause is not yet known, record the observation and say so rather than guessing at one.

Search for likely duplicates before creating a new record. Merge reports that one repair resolves together. Keep problems separate when they would be fixed separately, even where they touch the same screen or module. Search closed records as well as open ones. Something the project already built closes as already built, pointing at where it lives. Something the owner already turned down is reported to them with the reason it was refused, rather than recorded again or reopened. Whether that decision still stands is theirs, and re-recording it spends their attention on an argument they have already had.

Do not invent certainty, labels, owners, deadlines, or implementation details. If a missing product choice changes what would be recorded, ask only for the smallest plain-language clarification needed and recommend a default. Otherwise save the record and report where it went.
