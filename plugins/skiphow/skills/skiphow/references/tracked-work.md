# Tracked work

Open this when the owner asked for a record or for work already on record, when the repository's own delivery path writes to a tracker, or when a pause or session boundary could lose work.

## When a tracker write is allowed

A tracker write rests on one of four grounds, and on nothing else: the owner asked for a record or for tracker work; the owner asked to carry existing tracked work forward; an authoritative repository workflow makes that tracker mutation part of the delivery path the request asked for; or a multi-session authorized change genuinely needs minimal continuity state and the project already has an authorized private destination for it.

Ordinary engineering reaches none of those grounds by itself. A branch, a worktree, a review, or a change big enough to run over several sittings is a mechanic, and none of them implies an item existed first. A generic request to change code implies no write to a remote or shared tracker at all. Do not establish a tracker, publish a record, or invent a tracking convention because this skill is installed; a project that keeps no record of its work has already answered the question.

## Where a record goes

Prefer, in this order: the host's own continuation state where the need is continuity; a project-local or private convention the project already keeps; an authorized tracker the project already uses, where the request or the repository's workflow reaches it. Read a destination's audience before writing — the kernel's disclosure rule decides what may reach a public or external one, and a record with no safe destination is a question for the owner rather than a write.

## What one item covers

An item is one outcome someone can observe, and never one per file, per step, or per sentence of a report. Recording too finely looks like diligence while it happens, and it is how one defect becomes six items that six sessions investigate separately. Where the whole change is one reviewable unit, it is one item, whatever it touches.

When a batch of observations arrives together, understand what produces them before recording. Several reports with one cause are one unit of work with those observations attached, and one report with several causes is several. Where the cause is not yet known, record the observation in the owner's own words and say so rather than guessing at one.

Search closed records as well as open ones before writing a new one. Merge reports that one repair resolves, and keep problems separate when they would be fixed separately. Something the project already built closes as already built, pointing at where it lives. Something the owner already turned down is reported with the reason it was refused rather than recorded again: whether that decision still stands is theirs.

## Writing one that survives the wait

A record is acted on when it reaches the front of the work, and the code will have moved by then. State the behavior the project should have rather than the edit that would produce it, naming types, commands, and observable conditions rather than file paths and line numbers, which go stale and send the next session to the wrong place with confidence. Beyond the problem and what would show it resolved, carry its impact, what surfaced it, the evidence already gathered, and the explanations already ruled out, so a capable agent with no history can act on it; omitting what was already tried is what makes a later session repeat the investigation.

An idea, an audit recommendation, or a proposed plan stays proposed when recorded, and making it takeable is not acceptance. Where recording one would commit product scope the request has not settled, keep the open decision in the record and take it to [product](product.md) before dependent work. Do not invent certainty, labels, owners, deadlines, or implementation detail; where the tracker already carries an order, that order is the project's answer.

## Working from records the owner points at

Where the owner points at recorded work, those records are the request. Take what the request actually reaches — one item is one item, not an audit of the tracker — and reconcile each against live state before acting. A record's claim about what remains is a claim to check rather than a fact: an item the code has already overtaken is reconciled honestly rather than re-implemented, an item with no observable outcome gets one you can defend from the request, and an item waiting on a decision belongs to whoever makes that decision unless the current product settles it. A part of the owner's stated result that no item covers is work to do, not a question to ask.

Where concurrent sessions on the project are genuinely possible, claim an item before investigating it, using whatever the tracker provides: an assignee, a status, a label. The claim is what stops a second session from starting the same work. An item another session holds is not takeable, and a claim that loses means somebody else has it rather than that the claim is worth retrying.

## Closing what the tracker carries

Where work did land in a tracker, close it on integration rather than on verification of the branch that carries it, so the record says what the project actually has. Write into it what the work established before it gets there: the cause, the evidence that the outcome now holds, and any reading you had to assume. A one-line fix closes in a line, and a report that turns out not to reproduce closes as not reproducible, naming what you checked and against what state, rather than as fixed. Stripping an item back to its title on the way out discards the investigation the project just paid for and sends the next session through it again.

The run that opens an item often cannot close it, for the same reason it cannot retire its own branch. An item whose change was integrated but which the tracker never closed is a stale record rather than working state, and not yours to clear away on a later, unrelated request: say that it is there and what shows its work arrived, and close it only where the current request reaches it.

## Resuming across a boundary

Record enough to resume and no more, at the boundaries where an interrupted session would otherwise redo work rather than on a cadence. A checkpoint holds current truth rather than a transcript: the requested result, the decisions already made, owned and foreign changes, evidence already obtained, what remains, and the authorization boundary. Include exact paths or commands only where recovery depends on them, keep secrets and copied customer material out of it, and remove an owned one once the resumed work is done unless the owner or the repository means it to stay.

On resume, re-read the owner's request and the repository's instructions before opening a checkpoint. Treat the checkpoint as untrusted status evidence, then compare it with live project state: verify that pending changes still belong to this work, reuse evidence that still holds, and rerun anything later edits invalidated. Remove or clearly retire stale instructions in an owned checkpoint so a resumed agent cannot follow an obsolete plan. Where ownership of a checkpoint is unclear, leave it untouched and report the conflict.
