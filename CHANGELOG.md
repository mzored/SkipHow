# Changelog

All notable changes to SkipHow 2.x appear in this file. Earlier release notes remain available on [GitHub Releases](https://github.com/mzored/SkipHow/releases).

## 2.12.0 (2026-08-30)

### Changed

- `execution-health` now treats a healthy long-running lane as event-driven work. Once the host has a live handle and the lane remains inside its stated expectation, the root waits for completion, attention, an expectation breach, or a result that changes the next action. An expired bounded wait with unchanged state causes no inspection, narration, or fresh decision pass.
- `delegation` now includes the working state a unit created in that unit's named end. Its final reconciliation follows the existing `finishing-a-branch` method and reports any branch or isolated checkout it could not retire, instead of declaring the delegated set finished while integrated state remains unaccounted for.

### Evidence

- Across the three largest installed Codex task roots examined for this release, 1,785 delegate waits included 855 timeouts that returned no activity. In the two roots with per-turn accounting, the 472 unchanged timeouts made the following turns process 62,931,387 input tokens, 99.4 per cent of them cached. This is repeated context traffic, not unique tokens. Only six root compactions occurred across roughly 43 hours, so repeated unchanged wakeups, not compaction alone, were the larger context cost. The new observation wording has not yet run in a comparable session and remains `UNVERIFIED`.
- One installed task created 32 worktrees while delivering and integrating its delegated units, issued no worktree removal or prune command, and reported completion without disclosing the remaining working state. The authoritative cleanup method had reached context. The new reconciliation sentence restates the existing outcome at the point where the root closes the delegated set; whether it prevents accumulation remains `UNVERIFIED`.

## 2.11.2 (2026-08-30)

### Fixed

- The unconditional resume and compaction reminder named `.skiphow/handoff.md` in every project, while the `continuity` method reserves that fallback for a project with no tracked-work destination. A genuine installed 2.11.1 compaction delivered the reminder as a developer message; the agent repeated it and probed the path on its next live-state read even though the project kept the active work elsewhere. The reminder now reloads the kernel, request, repository instructions, and live state without selecting a continuation store. The conditional handoff fallback is unchanged.

### Evidence

- One installed Codex session running 2.11.1 reached a genuine compaction. The exact hook output reached the agent as a developer message, and the agent's next update and live-state read followed its unconditional handoff instruction. That proves the old wording caused the unnecessary probe. No genuine compaction has run on the corrected package, so its continuation behavior remains `UNVERIFIED`.

## 2.11.1 (2026-08-30)

### Changed

- The public skill description now says “product owner” rather than “nontechnical product owner,” states the outcome-first fit as ownership of the technical method so read-only work remains in scope, and excludes recommendations to adopt an owner-operated mandatory workflow or runtime orchestrator. It keeps requests to build those capabilities in the current project in scope. This corrects conflicts with the audience and read-only surface already stated in the README and makes adjacent negative categories explicit. The kernel body, authority boundary, and invoked runtime behavior are unchanged.
- The startup continuity reminder now defers to the skill description instead of requiring the kernel for every project request. A discovery receipt showed the old reminder overriding the description and selecting SkipHow for a mandatory owner-operated workflow. Resume and compaction reminders remain unconditional because they continue an already active request.
- README, FAQ, host manifests, marketplace copy, and Codex display metadata now use one category and promise: an outcome-first Agent Skill for Claude Code and Codex in which the owner owns outcomes, tradeoffs, and protected actions while the agent owns technical decisions, implementation, and proof. The product now answers directly when to use the base agent, a spec/workflow framework, or a runtime orchestrator.
- Popularity counts and volatile package-size counts have been removed from public positioning. Prior art now compares mechanisms and boundaries rather than stars.
- README and FAQ now state that reliable trigger-based method loading remains `UNVERIFIED`. The site gives keyboard users explicit focus for horizontally scrollable tables and command blocks, labels the tables, keeps the primary action closer on mobile screens, and exposes the GitHub repository as a homepage action.
- The public pages now describe their social preview for assistive clients, use semantic term-description lists for fit and claim boundaries, and pass the W3C HTML validator. Deterministic site checks now protect the responsive viewport, landmarks, direct GitHub links, homepage repository action, Open Graph image description, and the invalid generic ARIA pattern found in the launch audit.

### Added

- A static, JavaScript-free GitHub Pages site with product, comparison, and evidence pages; canonical metadata; `SoftwareSourceCode` JSON-LD; a sitemap; favicon; and a custom social preview asset. Publication remains a separate protected action.
- A standing discoverability protocol records twelve bilingual recommendation prompts covering the fitting case and all three rejection paths, scoring fields, target repository metadata, launch checklist, and 30/60/90-day measurement cadence. It accounts for GitHub's 14-day referral window, includes Google's Generative AI performance report, preserves the owner-supplied ChatGPT answer as the available pre-launch observation, and records official OpenAI directory submission as a later distribution phase.
- Deterministic site validation checks required routes, metadata, structured data, sitemap coverage, local links, and the absence of client-side scripts.

### Evidence

- In nine isolated Claude Code sessions on the exact candidate, direct, indirect outcome-owner, indirect read-only, incomplete, and two current-project capability requests selected SkipHow; unrelated, owner-operated mandatory-workflow, and runtime-orchestrator adoption requests did not. One run per cell is not a precision rate. Exact-candidate Codex selection remains `UNVERIFIED` because a fresh isolated home had no authentication and credentials were not moved.
- Package checks and visual inspection are recorded in the completion report for this change. The GitHub Pages site, repository description, homepage, and topics were published and verified after integration. The follow-up live-site audit found and corrected three invalid ARIA labels, added the missing prominent repository action, and aligned the measurement record with matched-cell comparisons and the data GitHub and Bing actually expose. The repository social preview and webmaster properties were not changed.

## 2.11.0 (2026-08-29)

### Fixed

- The kernel's method list opened with a permission and closed with an obligation, and the permission stood first. "Read only the guidance that materially helps the current request" asks a run to weigh what a method would add before opening it, which is a judgment nothing can make about a file it has not read. Version 2.5.0 had already added the obligation two paragraphs below it, on receipts showing methods going unread, and left the permission in place. The obligation is now the opening sentence and the permission is gone from both places it stood, the section itself and the skill description a host reads when it selects the skill: read the method that governs an act before that act, whether its trigger matches is the only question, and one whose trigger does not match stays unopened. No rule was added: one obligation replaced the permission and the restatement of that obligation below the list, and the section is sixteen words longer than it was.
- The rule sending a plan that spans several units to the project's tracker was conditioned on "an authorized change", which left out the other way a plan becomes a record: the owner asks for the plan itself, hands it to a later run, and authorizes no change at all. The destination now follows the plan — where the request authorizes recording it, as the record the owner asked for or as the state an authorized change needs to finish safely, it goes where the project keeps tracked work. [`decomposition`](plugins/skiphow/skills/skiphow/references/decomposition.md) carried the same rule for a split and the same looseness, conditioned on any authorized durable record, and it is corrected with it. The grant is unchanged: a request that authorizes no record still writes nothing, and a request whose record is something else is not permission to write a plan beside it.

### Evidence

- The scan that prompted this release covers every session on the maintainer's own projects that loaded an installed package, and searches each installed reference file's own opening sentence rather than its path. It splits by major version: under 1.x, twelve of nineteen sessions carried at least one method's text into context; under 2.x, none of eighteen did, and only one of those touched the package directory at all, to measure the size of the plugin cache. The two most consequential 2.x runs in the period — a triage that opened twenty-two tracker items, and a three-and-a-half-hour run with twenty-eight delegates — opened none of `tracked-work`, `continuity`, `decomposition`, or `delegation`.
- The paired isolated runs do not reproduce that failure, and the release does not claim the change repairs it. On a throwaway fixture with the host's own built-ins and nothing else, 2.10.1 opened the matching method in three of three sessions, before acting in each, and opened nothing for the request that matches no trigger. The release candidate did the same: `diagnosing-bugs` on the defect, `tracked-work` and `project-setup` on the request to record findings, `prioritization` on the request to order competing work, and nothing on the plain question. So the non-loading is real in long installed sessions and absent in a clean one, which points at what those sessions carry rather than at the sentence changed here. The cause stays `UNVERIFIED`.
- What the change rests on is the contradiction itself, which is readable in the shipped text and needs no receipt. Whether removing it changes what a long session does is unmeasured, and the release candidate opened somewhat more methods per session than 2.10.1 on the same prompts, which one run per cell cannot separate from noise.
- The plan-destination correction has one observation behind it. An installed 2.10.0 session asked to record a batch of findings and extend the plan for the next agent opened twenty-two items in the project's tracker and wrote the plan and the launch brief into two ignored local files, beside two more the same project had already accumulated, none of them visible to the tracker holding the items. The owner's launch prompt for the next run then had to name that file by hand.
- Package checks: `scripts/check.py` passed, `git diff --check` clean, Claude package validation and isolated install passed. Codex package validation and isolated install are `UNVERIFIED`: this machine has no Codex plugin validator installed.

## 2.10.1 (2026-08-29)

### Fixed

- The kernel already forbade asking the owner to choose engineering mechanics. It now restates that where a permitted ask is actually put. `Authority` allows an ask for a protected action, a material product choice, or a human-only step, which governs what an ask may concern and never how it is worded. `Autonomy` governs the wording, and its explanation was scoped to the product choice, so nothing repeated the ban at the moment a run decides how to phrase a protected ask it is entitled to make. The two sentences compose without conflict — choose the mechanism yourself, then ask only for the grant — and the receipt below is a run that failed to compose them. The kernel now states the composition: a protected or human-only ask is put the same way as a product choice, as what it changes for the owner, their account, or their exposure, with the technical decision already taken. No choice between technical options is put to them, and where the ask exists only because a step is theirs to perform, what is asked for is that step rather than approval of the way around it.

### Evidence

- An installed 2.10.0 session on a real project ended a two-hour run by asking its owner whether it might replace a named environment variable on staging with the currently authorized GitHub CLI token, offered against a properly scoped token the same sentence called better. The owner rejected it as a question that was never theirs, and named the boundary in their own words: they settle product questions and what no agent can reach, and nothing else.
- The run deviated from text that was plain and in context. "Do not ask them to choose libraries, branches, test commands, schemas, architecture, or other engineering mechanics" was in the kernel all session; the run's reasoning never reaches it, and reasons only from the credential clause it was obeying, which it quoted an hour earlier while making the staging configuration change beside it without asking, because the owner's request had named staging and had not named credentials. Told the decision was its own, it named the same defect the owner had — the phrasing, not the ask — and finished the delivery within the hour. The message's other item, a payment setting only the owner could reach, drew no objection.
- One session cannot show that agents in general need more than the sentence that was already there, and this release does not claim it does. The receipt meets the revisit condition recorded under "An unstated choice is an unfinished result" — an owner asked about engineering mechanics — and not the neighbouring condition of repeated such questions: a scan of every session on both hosts that loaded the package in a real project found this one instance, and the only other permission-shaped question was a legitimate product question about what a public ranking may reveal.
- So this is a clarification shipped against an unmet evidence bar, recorded as the owner's decision rather than as a demonstrated need, the same disposition 2.5.0, 2.8.0 and 2.10.0 took. Their ground is that the owner never handling engineering is the boundary the product exists to hold, so a single visible breach of it is worth restating the rule where the breach happened. What holds the cost down is that nothing here is a step or a gate: it constrains the wording of an ask the contract already permitted, in the section that already explains how an ask is put.
- Two narrower alternatives lost. Rescoping the existing sentence from "a product choice" to any input would have carried "recommend one option" with it, which is written for a menu and would license the very shape that failed. Narrowing the credential gate so that configuring a credential inside an already-granted destination needs no separate grant would have removed the question instead of fixing how it was put, and the receipt argues against it: what was moving was the owner's personal identity into a persistent deployed service, which is the case that clause protects, and the grant cost one turn rather than the work.
- The separation this states is the one [`mattpocock/skills` issue #962](https://github.com/mattpocock/skills/issues/962) proposes and its maintainers have left open: ask about the situation and the outcome in plain language, and map the answer to the technical term afterward. It also carries to a protected ask a boundary this project had already drawn three times against a menu of engineering options put to the owner, in `to-spec`, `to-tickets`, and `finishing-a-development-branch`.
- Whether the wording changes what a run writes is `UNVERIFIED`. No paired receipt was made, and the rule the run broke was already there.

## 2.10.0 (2026-08-29)

### Changed

- [`technical-design`](plugins/skiphow/skills/skiphow/references/technical-design.md) now opens on a technology, architecture, or system-shape choice that nothing already in the project answers, in place of a choice the agent judges material. Materiality is the agent's estimate of its own decision, which this repository has already found unusable in the same file: ten runs on the architecture fixture chose well and not one took the outside read that method requires, because each read its own decision as ordinary and cheap to reverse, and no Claude session in that pass opened the method at all. What the project holds is a fact about the repository, decidable before starting, which is the shape 1.9.0 gave decomposition and 2.8.0 gave tracked work.
- [`codebase-design`](plugins/skiphow/skills/skiphow/references/codebase-design.md) now also opens on an existing structure the owner has asked to improve. That request is neither an interface nor a module boundary, so it matched the old trigger only by accident, and no other method reached it: `prioritization` fires on candidates already recorded and `diagnosing-bugs` on defects.

### Added

- `technical-design` says what to do when constraint recovery comes back empty because the project is new. Every recovery instruction the package carries reads an existing project, so in an empty one they all return nothing, and the kernel's asking rule is scoped to what a person using the product gets, which expected load, who operates it, and what it is meant to become are not. The constraints are unstated rather than absent, they are the owner's to supply, and only the ones that would change the shape the run would otherwise choose are asked, once, inside the round [`product-decisions`](plugins/skiphow/skills/skiphow/references/product-decisions.md) already runs, kept to what the product has to do rather than how it would be built. Where the request already implies them, nothing is asked. No new round, and no reach into requests the project already settles.
- `codebase-design` gains the survey discipline the improve-an-existing-structure case needs: scope the look by what the project's history keeps returning to and what the outcome must touch, leave recorded decisions alone unless the friction is worth reopening them, and treat the survey itself as a read. Where the request authorizes changes, the run carries out what the owner's outcome names and leaves the rest as records, so the kernel's existing boundary — recording a problem is not permission to work on it — reaches the request most likely to ignore it without refusing the grant the kernel gives. The chain onward already exists through `prioritization` and `advancing-tracked-work`.

### Evidence

- `improve-codebase-architecture` from `mattpocock/skills` was read as its current text. Adapted: scope before you scan, weighting the areas the commit history keeps returning to, because a deepening pays off only where more change is coming; and following recorded decisions rather than re-arguing them. Rejected: its HTML report built on two content-delivery networks, a record format SkipHow would impose on somebody else's project, on the same ground that refused `triage`'s `.out-of-scope/` directory; and the menu asking the owner which candidate to explore, which is the engineering-shape gate already refused in `to-spec`, `to-tickets` and `finishing-a-development-branch`. The skill disables model invocation in its own frontmatter, so upstream also treats it as owner-initiated. No source text was taken; [`docs/prior-art.md`](docs/prior-art.md) records the disposition.
- Three narrower alternatives were considered and lost, recorded in [`docs/decisions.md`](docs/decisions.md): the greenfield paragraph without the trigger change, which would sit in the file that measurably never opened; widening the kernel's asking rule to cover the product's trajectory, against an over-asking risk that is already `UNVERIFIED` and sixteen negative controls; and a separate method for improving an existing codebase, which would split one paragraph of discipline from the vocabulary it uses.
- The change was reviewed on the other host before completion. Codex returned three findings against this repository's qualifying bar and all three are confirmed and fixed. The first trigger draft read "nothing already running to settle", which the architecture fixture refutes on its own receipt: that project runs Postgres, so a run applying the draft would read the choice as settled and never open the method, when having Postgres answers nothing about whether the partner call belongs inside the transaction. A stack is not an answer, and the trigger now asks what the project answers. The greenfield paragraph said to ask for the missing constraints without qualification, which is a mandatory question on every new project including one whose behavior is fully stated, so it now asks only for what would change the shape and takes what the request already implies. And saying the survey "does not authorize the refactor" was an authority error: a request to improve an existing structure is a request to change the project, and the kernel grants the edits its stated result needs, so the survey is a read while the authorized change is whatever the owner's outcome names.
- A second review round returned two more, both confirmed and fixed. `docs/decisions.md` and `docs/prior-art.md` still described the authority rule the first round had removed, which would have let a later contributor restore it; both now describe what ships. And the greenfield ask is an obligation to ask that the package did not carry before, which the conditional wording narrows without supplying the evidence `AGENTS.md` requires for a mandatory question. That is now recorded as the owner's decision against an unmet bar, the same disposition 2.8.0 and 2.5.0 took, rather than as a demonstrated need.
- Whether either new trigger changes what a run does is `UNVERIFIED`. The old trigger's failure is measured; the replacement is reasoning from the text, which is the same position 2.8.0 recorded for itself.

## 2.9.0 (2026-08-29)

### Added

- The kernel now says that work you do not own includes work another session is doing at the same moment: a checkout, branch, or running service the run did not create is shared, and uncommitted changes in it belong to somebody. Where the host can tell a session whether another one is working in the project, it asks before doing anything that would only be safe alone. Reading in parallel is safe; one writer at a time in a checkout is what its single branch and index allow, not a preference. Whether the host can name the other sessions is read as part of live state rather than asked as a precondition, so nothing here is a step. Until now the rule to preserve work you do not own read as a rule about state that was already there, and the isolation rule fired only for lanes a session creates itself, so a peer session nobody spawned matched no trigger at all.
- [`delegation`](plugins/skiphow/skills/skiphow/references/delegation.md) now asks each lane to confirm it is in a checkout of its own before it writes, by reporting the path it is working in and the commit it starts from. An isolation mechanism that reports success while handing back the shared checkout is the failure isolation exists to prevent, and it turns an instruction that would be harmless in a worktree — resetting to a base, cleaning the tree, switching branches — into one that destroys whatever else was there. The same paragraph now records that isolation is not total: separate worktrees share one stash stack.

### Evidence

- The defect is demonstrated rather than argued. A 2026-08-27 session on 2.1.2 dispatched two delegates through the host's own worktree isolation; the host placed both in the shared main checkout; the root read the wrong base commit as a mis-branched worktree and ordered a hard reset, reasoning in its own message that the delegate had changed no files and so nothing would be discarded. That is correct in a worktree. In the shared tree it destroyed thirteen files of uncommitted work belonging to a second session writing the same checkout, which recorded the loss independently. The work survived only because the repository's commit hook had stashed a patch minutes earlier. The outcome breached the kernel rule against resetting unrelated changes, which that version already carried, and the run did not know it was breaching anything. The incident is evidence of the failure mode rather than of the current sentence causing it: the version that ran carried no worktree guidance in `delegation` at all, and the sentence preferring the host's mechanism arrived the following day in 2.2.1, with the same silence about confirming what came back. Full account in [`docs/evidence.md`](docs/evidence.md).
- The ambient half rests on cost, not on damage. Eleven hand-written owner instructions between 2026-07-04 and 2026-08-29, across four repositories and at least three addressed to this package, tell a session that another agent is running and to avoid conflicting with it; in one repository, twenty-six pairs of sessions that both ran writing commands overlap in time across six weeks. Where sessions knew a peer was live they handled it well, one building its commit through a temporary index so it never touched the shared HEAD. The package cannot know when a peer is live, so it carries the consequence and the owner supplies the fact once.
- One fact in the new wording was tested here rather than taken from a source: two worktrees of one repository share a single stash stack, a stash pushed from either is listed by both, and a pop takes the top entry whichever tree created it. Git 2.50.1.
- Prior art was read as its current text and is mostly a negative result: no comparable project makes two agents writing one checkout safe, most avoid it with a worktree each, the few that arbitrate a shared tree use advisory locks and reservations their own documentation calls non-blocking, and Superpowers, `mattpocock/skills` and agent-os never mention a peer session in shipped instruction text. The read/write asymmetry is adapted from `claude-flow`. GSD and `mattpocock/skills` contribute evidence rather than mechanism, including worktrees silently degrading to the shared tree and session isolation disabled by one wrong environment variable name. Every coordination mechanism these projects carry — milestone and state locks, ticket and runtime leases, advisory claims, file reservations — was rejected as code SkipHow has no runtime to manage. [`docs/prior-art.md`](docs/prior-art.md) records what was adapted and what was not.
- A separate method for working alongside other sessions was rejected: its trigger cannot be decided without already knowing a peer exists. The reasoning, and the honest limit that prose may not reach this failure at all, are in [`docs/decisions.md`](docs/decisions.md).
- The change was reviewed on the other host before completion. Codex returned five findings against this repository's qualifying bar. Four are confirmed and fixed: the kernel draft turned the host question into a precondition on work while `docs/decisions.md` claimed the change added no step; "nothing in the package was violated" was wrong, because the kernel rule against resetting unrelated changes was already shipped in the version that ran, and the `delegation` sentence blamed for the gap postdates the incident by a day; the kernel said a checkout has a single stash, which the test above contradicts and which `delegation` states correctly; and the prior-art summary said every project avoids the problem with a worktree each while its own next paragraph listed the locks, leases and reservations some of them ship. The fifth, that `SOURCES.json` records no `claude-flow` entry, was refused: that file covers the one upstream whose text was adapted, and this page's own convention is that an idea taken without source text is credited in prose, which is how 2.8.0 credited Paperclip, Superpowers and GSD.
- Whether the new wording changes what a run does is `UNVERIFIED`. No paired run was made on it.

## 2.8.0 (2026-08-29)

### Added

- The kernel now says when work has to exist in the project's tracker. Work carried on its own branch to reach review has an item there before that branch does, and the change is linked to that item; a change carried out and verified inside one session, with no branch of its own to review, needs none. Nothing created an item for the work itself before this release. Every trigger the package carried was reactive — the owner asked for a record, pointed at records already there, the change left a problem unfixed, or the work was split — so the ordinary path of describing a result, branching, building and opening a review produced no tracked work at any point, and the tracker could not hold the project's current state.
- The kernel also now says when a tracked item is closed: on integration, not when the change is verified on the branch that carries it. Where the project integrates through review, what the work established is written into the item before the change reaches that review, because the run ends there. Closure then uses the tracker's own linked closure where the project supports it, and otherwise happens on integration. That is the half of this release that does not depend on any later session loading anything.
- [`tracked-work`](plugins/skiphow/skills/skiphow/references/tracked-work.md) replaces `intake` and carries the whole life of one item: the sizing that keeps a reviewable unit from becoming twelve records, claiming it before any investigation, linking it to the change as the branch is created, the difference between a sub-item and a real dependency, closing it with what the work established, and closing late what an earlier run left open. Everything `intake` carried about writing, reading, deduplicating and phrasing a record is unchanged and lives there now.

### Changed

- The claim rule moves out of [`advancing-tracked-work`](plugins/skiphow/skills/skiphow/references/advancing-tracked-work.md) into `tracked-work`, so a single named item reaches it too. Its trigger fires only when the owner asks to carry on with the backlog, which left one item worked without a claim at all. A claim that loses now means another session holds the item rather than that the claim is worth retrying.
- [`finishing-a-branch`](plugins/skiphow/skills/skiphow/references/finishing-a-branch.md) now closes the item the work was tracked under, confirming a tracker-performed closure rather than assuming it happened. It never mentioned the tracker before, so nothing connected an integrated change to the item that asked for it.
- `advancing-tracked-work` no longer closes an item once its outcome is demonstrated against live state. That contradicted `finishing-a-branch`, which holds that a branch is not integrated until it lands, and closed items before the change arrived. An item handed to a review is now set aside rather than closed, and items waiting on it stay blocked until that change arrives.
- [`project-setup`](plugins/skiphow/skills/skiphow/references/project-setup.md) records the calls a tracker needs for claiming, linking, recording a dependency, and closing, wherever they are not obvious from its own interface, and a recorded call that stops working joins the refresh conditions. Same note, same file, no new format.
- [`decomposition`](plugins/skiphow/skills/skiphow/references/decomposition.md), [`prioritization`](plugins/skiphow/skills/skiphow/references/prioritization.md) and [`continuity`](plugins/skiphow/skills/skiphow/references/continuity.md) point at `tracked-work` instead of `intake`.

### Evidence

- The defect is readable from the shipped text: `intake` opened with "Write when the owner's requested outcome is a durable record", which does not fire for a request to build or fix something, and the kernel's "agreed outcome" is what `product-spec` records the owner settling rather than a work item. It matches an observation already in [`docs/evidence.md`](docs/evidence.md): asked to build six member-facing capabilities, both hosts carried the whole thing in one pass in the root context, so nothing became an item.
- The loading argument this design opened with did not survive checking, and is recorded in [`docs/decisions.md`](docs/decisions.md) rather than dropped. Fourteen of twenty-eight Claude sessions opening no method was measured on packages before the 2.5.0 kernel fix that made an applicable method non-optional, and the evidence page states those counts are observations rather than a reliability rate. What stands is that `technical-design` opened in no Claude session in that pass including every one on its own fixture, and that three kernel wordings of the outside read were written, run and discarded without executing while the kernel's worktree rule was breached from inside the context. Neither placement is a guarantee, which is why closure is wired to the tracker instead.
- Whether this wording changes what a run does is `UNVERIFIED`. No paired fixture run was made for it, on the owner's instruction not to widen the work to demonstrate mechanics already understood.
- The kernel threshold is a mandatory step whose evidence bar is not met, and it is the owner's decision rather than a demonstrated need. No receipt shows capable agents failing to track work carried on a review branch; what the text shows is that nothing asked them to. This is recorded in [`docs/decisions.md`](docs/decisions.md) rather than smoothed over.
- The change was reviewed on the other host before completion. Codex returned five findings against the repository's own qualifying bar. Four were confirmed and are fixed: an unconditional claim that would have demanded a tracker write under a read-only request to diagnose one item; a late-closing rule that treated another run's open item as working state to clear away, when a tracker item is a durable record and the 2.7.0 ground for branches does not carry to it; "the run ends there" in `finishing-a-branch`, which collided with carrying several items in one session; and a new sentence claiming the tracker would not show a dependent blocked, which a recorded dependency does show. The fifth, that the kernel threshold exceeds the evidence bar, is correct on its own terms and was refused because the owner decided the rule, which is now stated in both records.
- Prior art was read as its current text: `wayfinder` for the claim primitive, `to-tickets` for its maintainers' own measurements of recording too finely, Paperclip for separating hierarchy from dependency and for a lost claim meaning another session holds the item, Superpowers for the contrast of a ledger deleted with the branch it served. No source text was taken. [`docs/prior-art.md`](docs/prior-art.md) records what was adapted and what was not.
- `python scripts/check.py` and `git diff --check` pass.

## 2.7.0 (2026-08-29)

### Added

- [`finishing-a-branch`](plugins/skiphow/skills/skiphow/references/finishing-a-branch.md) is a new method for work carried on its own branch or in an isolated checkout once it reaches its verified end. Finishing is two things: carrying the change to where the project itself calls it integrated, read off that project's own recent history rather than asked about, and clearing away what the work created. Checks are run against the merged state, because an earlier pass on the branch alone covers a state the merge replaced. Removal is limited to what your own work created and what is demonstrably integrated; an open review means it is not, and a squashed or rebased merge leaves no shared commit, so a missing shared commit is not evidence that work is unmerged. A refusal to remove a branch or checkout is a question to answer rather than an obstacle to force past: where it only reflects a merge that rewrote the work and the change is already established as integrated, removal proceeds, and where it reflects work or files that exist only there, it stops the removal.
- The same method makes the run that follows collect what the run before it could not. A branch usually becomes garbage after its session has ended, because review finishes later, so a rule that only fires at the end of a run can never retire it. When branch work next happens in a project whose request already authorizes changing it, the branches and isolated checkouts the agent's own earlier runs left there are retired under the same integration test. Late collection carries no authority of its own: it is working state the agent's own runs created, it reports rather than acts under a read-only request or where the project keeps integrated branches, and it authorizes no sweep of the repository.

### Changed

- The cleanup rule now lives in one place. `delegation` and `delivery` each carried a sentence about removing an owned branch or worktree once its work was integrated, and both now point at `finishing-a-branch` instead. The rules were never wrong; their triggers were unreachable for the case that produced the litter, since `delegation` only opens for delegated work and `delivery` only for a requested shared destination, and a branch created directly matched neither.

### Evidence

- The defect is measured, on a real project: 46 local branches, 43 of them already integrated, 15 of those left by host-created worktrees, one isolated checkout placed beside the repository against the kernel's own rule, and one orphaned directory under the ignored worktree location. What that inventory demonstrates is the accumulation, not its cause; the two explanations recorded in the decision history are reasoning from the shipped text. The corrective behavior carries no receipt and is `UNVERIFIED`.

## 2.6.0 (2026-08-29)

### Added

- [`advancing-tracked-work`](plugins/skiphow/skills/skiphow/references/advancing-tracked-work.md) is a new method for carrying recorded work forward across several items in one session, where `intake` owns one record at a time. It works the frontier — open items whose blockers are closed and that nothing else has claimed — in the order the project itself records, claims an item before investigating it so a second session cannot start the same work, closes each item at the point it is finished rather than at the end of the run, and recomputes the frontier as it does, because closing is what unblocks dependents. Independent frontier items may still run concurrently, one delegate each. It stops when the frontier is empty or everything left needs the owner, sets blockers aside rather than halting at the first, and reports the run as one reconciliation against what was asked.
- [`prioritization`](plugins/skiphow/skills/skiphow/references/prioritization.md) is a new method for the case where more competing candidates are on record than can be done soon: accumulated ideas, requests, and user feedback that no order settles on its own. What it produces is a short roadmap the owner can read and reorder, kept in the project's own tracker, and their order stands over any score. Reach and impact are theirs and are usually answered by the project's own records; effort is the agent's, read from the code, and is never asked; confidence measures the evidence behind reach and impact rather than whether the repair will work. A question reaches the owner only where sweeping the uncertain factor across its plausible range actually changes the order.

### Changed

- `prioritization` explicitly does not apply to units belonging to one outcome the owner already authorized. Those are sequenced by what blocks what — whichever is more valuable, the one that unblocks the other still goes first — so ranking siblings inside a decomposition produces an order that dependency then overrules. Which shape is in front of you is checked before anything is scored.
- `intake`, renamed to [`tracked-work`](plugins/skiphow/skills/skiphow/references/tracked-work.md) in 2.8.0, now requires a record written to survive the wait between being written and being acted on: the behavior the project should have rather than the edit that would produce it, and types, commands, and observable conditions rather than file paths and line numbers. This matters more now that a record can sit until `advancing-tracked-work` reaches it, by which time the paths have moved and a stale one sends the next session to the wrong place with confidence. The method already required a record a capable agent with no history could act on; it did not say this.
- `intake` now searches closed records as well as open ones. Something the project already built closes as already built, pointing at where it lives. Something the owner already turned down is reported to them with the reason rather than recorded again or reopened, because re-recording it spends their attention on an argument they have already had, and `prioritization` never scores a refused idea back onto the list.

### Evidence

- Nothing in this release carries a receipt. Both new methods and both `intake` amendments are `UNVERIFIED`.
- Three published skill collections were surveyed at their 2026-08-29 heads before any of this was written: [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills), [obra/superpowers](https://github.com/obra/superpowers), and [mattpocock/skills](https://github.com/mattpocock/skills). The frontier discipline in `advancing-tracked-work` is adapted from the second half of `wayfinder` and from `implement-spec`. The durability rule added to `intake` is adapted from `triage`'s agent-brief guidance. Nothing in any of the three covers prioritization, so that method is new rather than adapted. What was read and rejected, and why, is recorded in [`docs/prior-art.md`](docs/prior-art.md).
- The change was reviewed on the other host before completion. Codex, given the diff and this repository's contributor rules, returned four findings; three were confirmed and are fixed above. `advancing-tracked-work` had called an item's record "the authority for its scope", contradicting `intake`'s own sentence that records are evidence of intent rather than authority, and had required a record for discovered work "however small it looks", which exceeds the kernel's grant of one record for a material problem. The same method serialized the run in one paragraph and permitted concurrent lanes in the next. `prioritization` declared itself read-only and then instructed an unconditional tracker write. The fourth finding, that the two methods add mandatory steps without receipts, was weighed and not acted on: both live behind a method trigger rather than in the kernel, which is where `docs/decisions.md` places conditional technique and where it allows a method to carry the detail its discipline requires; the sensitivity sweep removes owner questions rather than adding a step, and the closed-record search is a clause inside a duplicate search `intake` already required.
- `SOURCES.json` and `THIRD_PARTY_NOTICES.md` now record `wayfinder` and `triage`'s agent-brief guidance as adapted source paths at the pinned upstream revision, and `advancing-tracked-work` as an adapted output. The same review found the provenance claim in `docs/prior-art.md` was true of neither file before this.
- A command surface for these entries was built and then removed before release. Two of the four commands restated policy the methods already carried, and the other two would have earned their place only by naming a method file to take its loading out of the model's hands, on evidence this repository does not have for these methods. Codex plugins support no command surface at all, so nothing was portable about the idea either. The package still ships exactly one skill and `scripts/check.py` is unchanged.
- `python scripts/check.py` and `git diff --check` pass. `python scripts/check_hosts.py` passes Claude package validation and Claude's isolated install; the Codex validator is not installed locally, so Codex package validation and isolated install are `UNVERIFIED` and run in CI.

## 2.5.0 (2026-08-29)

### Added

- [`model-routing`](plugins/skiphow/skills/skiphow/references/model-routing.md) returns as a focused method, on the owner's decision. It routes by what the work demands and never by what a provider calls it: bounded mechanical work at the cheapest sufficient level, work carrying a settled design at the ordinary one, deciding work at the strongest available, and anything that reviews or judges at no less than the session that dispatched it. Whether an unset delegate inherits the session is stated as something to check on the current host, not as a portable fact. Where a host offers only an effort control the levels collapse onto it; where it offers no per-delegate control they are unavailable. No model identifier, tier key, or cost table enters the package.
- [`product-spec`](plugins/skiphow/skills/skiphow/references/product-spec.md) is a new method for when the owner asks to settle what they want before work starts, so their result survives the conversation that produced it. It runs on their request, never on the agent's judgment that a result was broadly stated. It produces a document the owner can read back, in the place the project already tracks work, as the parent of the units carrying it out: a vocabulary in the owner's own terms settled before the outcomes, the outcome stated as what a person will be able to do and what would show it true, each decision with the option that was turned down, and what is deliberately out of scope. Engineering stays out of it, and the rounds end where `product-decisions` ends them rather than running until a design tree is exhausted.
- The kernel now treats an answer the owner gives as a decision the project carries: where the request authorizes a record, it is written where the work is tracked, with what it settled and the option they turned down, before anything depending on it is built. The kernel already required this for a reading the agent took on their behalf and said nothing about the answers they gave.
- The kernel now says that where the host lets you set the capability or effort a delegate runs at, you set it rather than leave it to the default, which is chosen for the session rather than for that lane. This duty is stated in both the kernel and the method: the kernel carries the instruction, the method carries how to choose.

### Changed

- The kernel now sizes a delegate: one outcome it can demonstrate on its own, verifiable alone and reviewable in one pass, and one delegate is not handed several. This constrains delegates, not decomposition — whether to delegate at all is unchanged.
- A lane that has stopped making measurable progress is stopped and diagnosed rather than waited on. Deciding a healthy duration before dispatching was considered and left in [`execution-health`](plugins/skiphow/skills/skiphow/references/execution-health.md): the receipts show no root ever set that expectation, but they do not show the durations were unhealthy, which is short of the bar this repository sets for a mandatory step.
- Where an authorized change runs across several units and needs a plan to finish safely, that plan now belongs where the project keeps tracked work rather than only in a local file or the conversation. It names a destination the earlier grant did not; when a checkpoint is created or refreshed at all is left to [`continuity`](plugins/skiphow/skills/skiphow/references/continuity.md) and is unchanged.
- The kernel now requires reading a method whose trigger plainly matches the work in front of it, before acting on that work rather than after. This is a new requirement, not a narrowing: the sentence it replaces only barred loading a method "merely because it exists", which left an applicable method optional. The anti-workflow half of that sentence stands, and a method whose trigger does not match still stays unopened.
- [`delegation`](plugins/skiphow/skills/skiphow/references/delegation.md) defers the capability question to `model-routing` instead of stating an effort floor of its own.

### Evidence

- The defect this release acts on was measured in the owner's own installed sessions, not in fixtures. Across four 2.x sessions on two repositories — two of them dispatching eighteen and eight delegates — `decomposition`, `delegation`, and `execution-health` reached context zero times, established by searching the transcripts for the files' own sentences rather than only for their paths. The longest delegates ran 235, 133, 111, 81, 81, 75, 58 and 47 minutes, and delegates took 67–68% of each session's output tokens and 92–94% of its cache writes.
- Twenty-five of the twenty-six delegates those two roots dispatched ran on the session's own model, including every implementation lane. The single explicit downgrade was applied to a delegate asked to verify a specification against code — the judging case the floor exists to protect.
- The product-spec method and the owner-decision rule carry no receipt. They answer a defect that is readable from the transcripts — a seventeen-kilobyte specification holding the owner's pricing and legal decisions stayed an untracked local file that its own executing session never reopened — but whether the wording produces the document is `UNVERIFIED`. The sessions did record owner decisions into the issues they opened without any rule requiring it, so the rule may be codifying behavior that already happens.
- This acts on the loading half of the standing revisit condition under "Critical rules stay in the kernel" in [`docs/decisions.md`](docs/decisions.md). The receipts show non-loading, not a wrong result traced to it, so the "needed for correct work" half stays inferred and is recorded that way. "Provider-independent policy" and "Authority follows the requested outcome" are amended with the evidence and the owner decision behind each change. The model-routing condition was not met when the owner decided it; that is now recorded plainly, and its replacement condition is stated as a replacement rather than presented as the original.
- Kernel placement is not yet shown to change behavior. The same sessions carried the kernel's existing rule against placing an isolated checkout beside the repository and one created three sibling worktrees anyway, so whether a moved rule is followed stays `UNVERIFIED` until receipts. That routing down is cheaper in total rather than merely per token is likewise `UNVERIFIED`.
- `AGENTS.md` now sets a bar for reviewing a change to the instructions, because the contract is prose and a reviewer can always propose a different wording. A finding qualifies when it names a factual error, a contradiction with a shipped sentence or a recorded decision, an undecidable trigger, a claim presented as demonstrated without a receipt, a mandatory step added below the evidence bar, or an authority or portability error; a rephrasing, a hedging preference, or "could be clearer" does not. Every finding is confirmed against the file before it is acted on, and a round returning only non-qualifying findings ends the review. This is a contributor rule and ships nothing.
- The change was reviewed on the other host before completion. Codex, given the diff and the repository's own contributor rules, returned seventeen findings. Fifteen were confirmed and are fixed above, including a pre-dispatch step that exceeded its evidence, a sizing rule that read as a mandate to delegate, an escalation rule that contradicted `execution-health`, a portability claim about model inheritance, a revisit condition rewritten rather than reported as unmet, and three sentences that asserted what this release records as `UNVERIFIED`. Two were not: the reviewer read the cache-write figures as unmeasured when they were measured from the same transcripts, and challenged a rationale about weak reviewers that this change moves between files rather than newly asserts.
- The receipts and their limits are recorded in [`docs/evidence.md`](docs/evidence.md) under "What delegation looked like in installed sessions", including that these are the maintainer's own uncontrolled sessions rather than paired runs.
- `python scripts/check.py` and `git diff --check` pass. `python scripts/check_hosts.py` passes Claude package validation and Claude's isolated install; the Codex validator is not installed locally, so Codex package validation and isolated install are `UNVERIFIED` and run in CI.

## 2.4.3 (2026-08-29)

### Changed

- `README.md` is rewritten for the reader who arrives from a search engine or an AI answer. It leads with what SkipHow is and which hosts run it, keeps install and a working request on the first screen, and states the boundary between what the owner decides and what the agent decides before any of the reasoning behind it.
- The README now says what real runs have shown, with the numbers: the size of the 2.4.2 pass, the negative controls, the flaky-test and false-fix cases, and the six-unit split over 2,725 lines. Behaviors with no receipt are named as unproven in the same section rather than left out.
- Plugin descriptions and keywords in both manifests, and the Claude marketplace description, now say what the skill does for the person installing it. The Codex `longDescription` states the same boundary as the README. The skill's own `description` frontmatter is unchanged, because it governs selection rather than presentation.

### Added

- [`docs/prior-art.md`](docs/prior-art.md) returns. It records the projects this one learned from, what each contributed, what was left out, and which of their ideas were read and rejected. The earlier version of this page was deleted along with the research tree it lived in, which lost the reasoning behind several standing rejections. Upstream issues and repository state were re-checked on 2026-08-29 before the page was restored.
- [`docs/faq.md`](docs/faq.md) answers what a reader asks before installing: which agents it runs on, whether it pushes or deploys without asking, where records go, what `UNVERIFIED` means in a report, and how to update or remove it. Every answer restates a rule that already exists in the guide, the kernel, or the evidence page.

### Evidence

- Documentation and package metadata only. The shipped instructions are unchanged, so no model behavior is claimed and no receipt is added. Every factual claim in the new pages traces to [`docs/evidence.md`](docs/evidence.md), [`docs/decisions.md`](docs/decisions.md), or a source link checked on 2026-08-29.
- The kernel and method word counts quoted in the README were measured on this package: 1,610 words in `SKILL.md` and 6,759 across 18 method files.
- `python scripts/check.py` and `git diff --check` pass. `python scripts/check_hosts.py` passes Claude package validation and Claude's isolated install; Codex package validation and Codex's isolated install are `UNVERIFIED` locally, because the validator is not installed on this machine and local policy restricts marketplace sources to the published repository. CI runs the Codex validator.

## 2.4.2 (2026-08-29)

### Changed

- A round of product questions now ends when nothing material is open, not when the owner has answered once. One round is the shape of a batch, not a budget: ask together everything that can be asked now, and when the owner's answer makes a further choice material, ask that one too. An answer is not permission to settle what it opened.
- A question that is with the owner is not answered by a default. Nothing whose product meaning depends on the answer is built, committed, or treated as settled while they decide, and the parts that do not depend on it carry on. Reversible technical choices are untouched by this and still need no confirmation.
- The kernel and `product-decisions` no longer read as permission to settle a material product choice and disclose it afterwards. What gets reported is a reading the project settled; having no answer yet is not an answer; and where such a choice has already been built, the work stays unfinished until the owner answers and the behavior agrees. This removes a contradiction with the rule above rather than demonstrating a new behavior, and its effect is `UNVERIFIED`.
- `product-decisions` states which questions are askable now — a question whose options only exist under a particular answer belongs to the round after that answer — and that anything the project, its records, or a source can settle is the agent's to settle rather than the owner's.

### Fixed

- The Codex isolation that `AGENTS.md` prescribes for receipts was insufficient. Codex reads a host-agnostic user skill directory that `CODEX_HOME` does not cover, and a control run under the old method carried three of the maintainer's own skills into the model's context. The method now isolates the operating-system home as well, and requires confirming isolation in the session transcript rather than by asking the model what it can see.
- `README.md` claimed a new feature stops to ask which product it should be, and that independent parts run concurrently. Receipts show the first on some runs and not others, and nothing shows the second. Both claims now state what was measured.
- `project-setup` did not say where the one-time record of a project's tracked work goes when the project keeps no agent instruction file of its own. A receipt shows Claude writing it into a file only Claude reads, which would make the other host ask the same question again. The method now says to put it where any agent working on the project would read it. Whether that changes the behavior is `UNVERIFIED`.

### Evidence

- Seventy-five owner turns across fifty-seven sessions on throwaway fixtures, on both hosts. The release's wording was built in steps, every claim says which wording produced it, and both shipped clauses were re-run on the exact release-candidate package. Method, isolation, and results are in [`docs/evidence.md`](docs/evidence.md); the transcripts are not retained.
- The round defect was demonstrated before the change on both hosts. In four 2.4.1 sessions across two fixtures, not one opened a second round after the owner's answer, and each settled the choices that answer had opened. With the frontier clause a second round appears on both hosts; on Codex it appears in one of three release-candidate sessions on the cancellation fixture, which the evidence records rather than smooths over.
- The second defect was the candidate's own. Having asked the two questions its new frontier had opened, Claude built both answers anyway, committed them, and reported one as "the failure case your answer opened, and I had to pick something to ship". Under the new clause the same fixture and prompts produce two questions, no dependent behavior, and one commit that is only a record — "No behaviour is coded yet, since either choice would otherwise be settled by whatever default was written". A second released-package session built the one piece both answers need and nothing else.
- Two cases built so that asking would be the failure produced no question on either host on the released package: a request with its acceptance criteria fully stated, and a purely technical fork. Sixteen negative-control sessions across all wordings produced no question and spawned nothing.
- The outside read that `technical-design` requires for a decision that is expensive to undo does not execute. Ten sessions on the same architecture fixture, five on each host, produced ten sound transactional-outbox designs and no outside read, with the method open in all five Codex runs. Three kernel wordings were written, tested, and discarded. Nothing was promoted, the method is unchanged, and the behavior stays `UNVERIFIED`. What the runs say points at the trigger — every one judged its own decision cheap to reverse.
- One reported defect plus several unrelated material problems in one code path produced one deduplicated record per problem, including one defect spanning two files that became a single record, and no record for the planted weak observations. "One carry-forward record" is not "one problem".
- Both hosts split a six-capability build over a 2,725-line codebase into six independently verifiable units with exactly one dependency edge, found the shared surface unprompted, and wrote nothing on a plan-only request. Asked to build the same six, both carried them in one pass. Delegation, concurrent lanes, worktrees, and delegate briefs remain `UNVERIFIED`; no run in the whole pass spawned a delegate, and no numeric trigger was added to force one.
- An intermittent test failure was diagnosed and fixed at its cause on both hosts, measured across hash seeds, with no retry, skip, or weakened assertion. A change that claimed to fix a double charge was rejected on both hosts after each reproduced the failure itself; Claude also showed the change's own test passing against unfixed code.
- `python scripts/check.py` and `git diff --check` pass. Both host package validators pass and Claude's isolated install passes. Codex's isolated install is `UNVERIFIED`: local machine policy restricts marketplace sources to the published repository.

## 2.4.1 (2026-08-28)

### Fixed

- `docs/evidence.md` claimed Claude behavior could not be isolated without exposing a token. That was wrong. `--setting-sources ''` with `--strict-mcp-config` and the package passed as a session plugin drops user settings, skills, plugins, hooks, and MCP servers while authentication stays in the system keychain untouched. A control run confirmed the owner skill loads and no `CLAUDE.md` reaches the context.
- The run count is now the number of counted cases, eleven on 2.3.0 and seventeen on the release, rather than the bench's total volume. The earlier figure counted runs against intermediate wording that the page never quoted.

### Evidence

- Claude behavior is no longer `UNVERIFIED`. The four cases 2.3.0 failed and the two it passed that mattered most behave the same on both hosts: the open product question comes back with a recommendation and nothing is written, a `Blocked` item stays blocked while the rest is fixed, a resumed epic closes items carrying what they established, and a reported bug is fixed with a regression test and a clean commit in about a minute with no questions.
- Three cases built so that asking would be the failure — a fully specified request, an ambiguity the project's own code settles, and a purely technical fork — produced no question and no assumption inventory. This is the counterweight the release previously lacked.
- A real repository of five hundred commits took a small feature in eight files and ninety-one lines, following its existing layout and commit convention, restructuring nothing, and leaving an unrelated dirty file and untracked directory untouched. A Russian request was answered in Russian with English commit, tests, and tracker entry.
- Method files load in proportion to the work on Codex and mostly do not load on Claude, where the kernel alone carried the same behavior across six runs. The rules this release turns on are in the kernel, which is why it held.
- Delegation, effort routing, and the delegate return shape remain `UNVERIFIED`: two runs built to provoke delegation did not, because the proportionality rule correctly judged three small features to be one pass. Continuity across compaction remains `UNVERIFIED`; the smallest auto-compaction window makes provoking a real one expensive, and simulating it would not be evidence.
- The shipped package is unchanged from 2.4.0. This release corrects documentation only.

## 2.4.0 (2026-08-28)

### Added

- A material choice the owner's request leaves open in what a person using the product gets, that available project evidence cannot settle, is now the owner's to make. The agent asks before building, in one round, each question carrying the option it recommends. What the project cannot do yet answers no such question; that is a cost for the owner to weigh, not a reading for the agent to take.
- A choice made instead of asking belongs in the report and in the record, named with the alternative that was not taken. Describing the behavior that was built is not naming the choice. A result that hides a choice is not finished.
- Closing a tracked item updates the record that work already owns, so it needs no separate grant. What the work established goes into the item before it closes, in proportion to what finding it cost: the cause, the evidence that the outcome holds, and any reading that had to be assumed. A report that could not be reproduced closes as not reproducible, naming what was checked and against what state. A one-line fix closes in a line.
- An item the project already marked as waiting on a decision belongs to whoever makes that decision. The block is the record's own instruction to ask, and answering it unilaterally while clearing the note is not progress.
- Effort is matched to the work, through whatever control the host exposes. A delegate that reviews, judges, or decides runs at no less effort than the session that dispatched it, because a weaker check reports agreement rather than finding what was missed. The floor is relative to the session, so no model name, tier, or host key enters the package.
- A technology, architecture, or system-shape decision that is expensive to undo gets one read from a context that did not produce it, given the problem and the evidence rather than the preferred answer, and asked what it would choose and what would make that choice wrong. A second host or model family is preferred; where neither exists, a fresh context given only the problem still beats rereading your own reasoning. The answer is evidence to weigh, not a vote.
- Where a delegate's output is long, it leaves the bulk in the host's own working area rather than the project and returns its verdict, its findings, and the path. Every finding still comes back; pulling whole reports into the dispatching context is what undoes the isolation.
- The decomposition check now looks for two units that would do the same work, not only for gaps. Delegates given adjacent briefs converge on the same choices and both write them.

### Changed

- Product questions go out in one round rather than one exchange at a time, so the owner answers once and the work carries on.
- The kernel's statement of what is not evidence now separates the three cases: the check ran and what it showed, the check did not run, or the search found nothing. A check that did not run is not a check that passed, and a thing not found is not a thing shown absent.
- `docs/evidence.md` reports observed behavior for the first time since 2.0, and its unverified list now names what the receipt method itself cannot reach.

### Evidence

- Forty-five one-off Codex runs against throwaway fixture repositories, in a host home holding the candidate skill tree and the host's own built-in skills. Claims below are quoted only from the eleven runs whose package matched 2.3.0 exactly and the six that matched this release. Method and results are in [`docs/evidence.md`](docs/evidence.md); the transcripts are not retained.
- Three failures on 2.3.0. An underspecified feature built to a silently chosen reading, three times. Closing tracked work stripping every item back to its title, twice. And, once, a tracker item marked `Blocked: needs a decision` answered unilaterally, shipped, closed, and its block deleted.
- On 2.4.0 the cart-sharing request returns the open question with a recommendation and writes nothing; the epic names the three product decisions it took in the result and the tracker; executing tracked work leaves the blocked item blocked and returns both decisions in one round; and a resumed session closes five items carrying what each established, against a baseline run of the same fixture that left five bare titles.
- Unchanged across the release: a reported bug fixed with a regression test and a clean commit in about a minute, opening two method files; a read-only comparison writing nothing; seven observations grouped into five items by cause.
- `python scripts/check.py` and `git diff --check` pass. Both host package validators pass, and Claude's isolated install passes. Codex's isolated install is `UNVERIFIED`: local machine policy restricts marketplace sources to the published repository, and CI skips installs by design.
- Claude behavior, delegation, concurrent lanes, effort routing, the outside read, continuity across compaction, and whether the asking rule over-asks all remain `UNVERIFIED`; no receipt reaches them.

## 2.3.0 (2026-08-28)

### Added

- `decomposition` is now its own method, with a trigger a run can evaluate before it starts: the parts of the work would land, be verified, or be reviewed separately. A unit is right-sized when one person can observe its behavior end to end, verify it alone, and review it in one pass. Units are cut through the layers, never along them, because a unit named for a schema, an endpoint, or a screen cannot be demonstrated alone and forces the whole result into one late review.
- Splitting is judgment, not a stage. Work whose parts land, get verified, and get reviewed together stays one unit, so small work keeps completing without ceremony.
- Mechanical changes with a wide blast radius are exempt from vertical slicing and sequenced expand, migrate, contract, so the project keeps working at every step.
- A unit states its outcome and what would show it true, and does not prescribe files, names, or steps. Only genuine blocking edges are recorded; order presented as dependency is what serializes work that could run concurrently.
- A decomposition is checked before it is acted on, against the original request and the records themselves, read back cold or by a delegate, because whoever drew the split is the worst judge of whether it holds.
- Delegate briefs carry the outcome, its completion condition, the boundary the delegate works inside, and the instruction to return a blocking unknown rather than settle it alone. A rule not written into the brief does not reach the delegate.
- A returned question is the orchestrator's to settle. It reaches the owner only under the kernel's existing bar, so many lanes do not become many interruptions.
- Lanes that write at the same time need separate working trees, or they run one at a time.

### Changed

- The kernel now requires reconciling split work against the request before reporting: what finished with evidence, what is blocked, and what is deliberately left and on what ground. Reporting success while a part was never started is a false completion. Leaving a unit for later needs a reason the owner would accept, and preferring not to do it is not one.
- `intake` reads the tracker as well as writing to it, and the kernel trigger now reaches work the project already has on record. Recorded work is reconciled against live project state; the agent settles what it can settle and raises only an unmade product decision or a part of the result no item covers.
- A batch of observations is grouped by cause before it becomes records. Several reports with one cause are one unit of work; one report with several causes is several. The owner's own description stays in the record.
- Deduplication is stated by repair rather than by wording: reports one fix resolves are merged, problems fixed separately stay separate even on the same screen.
- Recording a decomposition follows the same authority as any other record. A request only to plan, compare, or advise returns the split in the answer and writes nothing.
- `delegation` covers how units run; `decomposition` owns what they are and which edges genuinely block.

### Fixed

- `docs/evidence.md` stated that none of the 2.2.0 behavior was `UNVERIFIED`, which asserted the opposite of what it meant, and listed releases out of order.
- `docs/guide.md` named only review and diagnose as recording nothing, while the kernel's read-only list is wider.
- `THIRD_PARTY_NOTICES.md` omitted `delegation`, `project-setup`, and `technical-design` from the adapted references, and would have omitted the two added here.

### Evidence

- `python scripts/check.py` and `git diff --check` passed. Claude package validation and isolated install passed. Codex package validation is `UNVERIFIED` from a bare local invocation; CI runs it against the pinned validator on the pull request.
- Two independent reviews of the staged change found the first draft's method reachable only through triggers that excluded the scenarios it was written for, a write obligation with no authority gate, a self-contradicting deduplication rule, and an escape hatch that authorized the false completion it forbade. All were corrected before release.
- The runtime behavior is `UNVERIFIED`. No receipt yet shows large work split into independently verifiable units, concurrent lanes reconciling completely, or one cause producing one record.

## 2.2.1 (2026-08-28)

### Fixed

- Isolated checkouts land inside the project again. `delegation` now names where a worktree goes: the host's own mechanism first, then the location the repository already ignores, confirmed ignored before anything is created there, and a temporary directory only when the repository offers neither. A worktree beside the repository is never correct, because it escapes the project's ignore rules and cleanup and accumulates unnoticed.
- The kernel carries the boundary in one sentence, because the 1.8.0 audit measured that a reference which does not load governs nothing. Version 1.x kept this rule only in a reference, and 2.0.0 removed that reference without replacing it, leaving no placement rule at all.
- Removing an isolated checkout is never forced. A refusal is evidence that something still owns it.

### Evidence

- Deterministic checks and both host package validators passed.
- Reported from the owner's machine: twenty worktrees belonging to three repositories had accumulated beside them, while all three repositories keep an ignored `.worktrees/` directory of their own. Attribution to a specific package version is `UNVERIFIED`; the missing rule is not.

## 2.2.0 (2026-08-28)

### Added

- `execution-health`: give a long-running step an expected duration and a no-progress signal, treat a breach as information, classify the cause before correcting it, and stop after three genuine attempts against one hypothesis rather than trying a fourth.
- A reuse-first order in `technical-design`: search what the repository already has, then platform primitives, official SDKs, mature components, managed services, and a bounded spike before custom code. Building carries the burden of naming the requirement the alternatives fail.
- Recurring defect patterns in `diagnosing-bugs`, including work that is not idempotent on rerun, partial success reported as completion, a default branch absorbing what belongs elsewhere, and mocks that have drifted from the behavior they stand for.
- A statement in the kernel of what does not count as evidence: reasoning that a change should work, a path that looks equivalent, a suite that passed without knowing what each check covers, a screen that opened, or an absence of errors.

### Changed

- `testing` requires a regression test to close the bug class: observed failing against the unfixed code, asserting the violated invariant at the layer that owns it, covering each boundary a bad value crossed. Verification is staged by reach rather than rerun wholesale, and an intermittent pass is a defect until classified.
- `reviewing-changes` separates making a change from certifying it. Risky results are confirmed independently of the account that produced them, and an important defect is fixed before the work continues rather than carried forward as accepted.
- Never silence an unexplained failure by raising a timeout, adding a retry, disabling a check, weakening an assertion, or reaching for a bypass flag.
- `AGENTS.md` and `docs/decisions.md` record that method depth is limited by whether a method loads, not by its length.

### Evidence

- Deterministic checks and both host package validators passed.
- Every behavior in this release is `UNVERIFIED`, including whether the added depth changes an outcome. See the [current evidence](docs/evidence.md).

## 2.1.0 (2026-08-28)

### Added

- A project change now also grants the durable records the project keeps for that work: the agreed outcome, the state a later session needs to resume it, and one carry-forward record for a material problem the change leaves unfixed. A separable finding previously reached only the chat transcript, so the next session paid to rediscover it.
- `project-setup`: one owner question settles where tracked work lives and who may see it, recorded in the project's own agent instructions and not asked again.
- `technical-design`: recover the real constraints, check volatile facts against primary sources, compare options that genuinely differ, and decide without returning the choice to the owner.
- `delegation`: shape large work as a task graph rather than a list, serialize parts that touch the same shared surface, and point delegates at context instead of copying it.
- Versioning and release rules in `AGENTS.md`, including one release per coherent change set rather than one per package edit.

### Changed

- `product-decisions` now establishes the intended outcome and its acceptance criteria before substantial work, asking only where different readings would produce a materially different product.
- `continuity` treats the project's own record of tracked work as the continuation surface. `.skiphow/handoff.md` remains the fallback for a project with no such destination.
- `intake` records carry the impact, what surfaced the problem, the evidence already gathered, and the explanations already ruled out, using the tracker's own structure.
- Durable text the project keeps follows the language and conventions of its own history rather than the conversation's.

### Evidence

- Deterministic checks and both host package validators passed.
- The new runtime behavior is `UNVERIFIED`. No receipt yet covers recording a finding once, resuming from a record, or the absence of added ceremony on small work. See the [current evidence](docs/evidence.md).

## 2.0.2 (2026-08-28)

### Changed

- Cut the tracked repository from 108 files to 50 without changing the owner skill, internal methods, or continuity hook.
- Rewrote the README for a faster first read and moved installation, design, decisions, and evidence into four focused documents.
- Replaced the 1.x ADR and research tree with concise current summaries and immutable links to the complete 2.0.1 archive.
- Removed the contributor-only dogfood analyzer, its transcript-format tests, and the unused run-summary script.
- Grouped retained tests by package structure, deterministic checks, and host checks.

## 2.0.1 (2026-08-28)

### Changed

- Replaced the 1.x workflow contract with one owner-facing skill and a small set of focused internal methods.
- Kept authority, autonomy, preservation, and verified completion in the owner kernel.
- Removed magic phrases, fixed routes, model tiers, standing roles, and mandatory process that strong agents can choose for themselves.
- Kept shared policy independent of provider model IDs and host-specific routing.
- Required explicit owner authority for production, public releases, credentials, payments, access changes, and destructive actions.
- Updated deterministic checks for the one-skill package, continuity hook, source attribution, versions, links, and portability.

### Evidence

- Deterministic checks and both host package validators passed.
- Claude isolated installation passed. Codex isolated installation was `UNVERIFIED` because managed source policy rejected the local marketplace.
- Six retained Codex observations covered a small project change, read-only diagnosis and product choice, protected-action boundaries, and a visual interaction. See the [current evidence](docs/evidence.md) for limits and durable source links.
