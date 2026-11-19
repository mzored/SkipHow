# Changelog

All notable changes to SkipHow 2.x and later appear in this file. Earlier release notes remain available on [GitHub Releases](https://github.com/mzored/SkipHow/releases).

## 7.0.7 (2026-11-19)

### A finding off the request's path is still the lead's to fix

- Under a change request, the lead fixes every confirmed finding in the project in the same run, whether or not it relates to the request. The deferral reasons are unchanged: an owner decision, a protected action, a blocker, or a cost that would hurt the outcome, with the reason recorded. Before, the kernel said "within authority", and the Authority section granted "in-scope edits", so an agent could read a finding unrelated to the request as outside its grant and only list it.
- A finding is checked before it is reported, not only before it is acted on. The review playbook's copy of that rule is gone, because the kernel's Engineering standard reaches every review brief.
- The custody rule now says a part or a finding never goes to a session the owner must start. Before, it said "parts or findings of the outcome", which let an unrelated finding fall outside it.
- The kernel stays under its size limit. "Look past the diff" left the Engineering standard, because the finding rule now names the project as its scope, and a few phrases were shortened without changing what they ask. The tracked-work playbook drops two sentences the kernel already carries: separability is not a reason to defer, and plans and reports are deleted when the work lands.

### Why

A `skiphow-bug` session on 7.0.6 fixed a sign-in defect and ended with "found along the way, did not fix": production logs disappear at every deploy, and merge confirmation might return a server error, inferred from reading code and not checked. Its plan had labeled both "outside this change (report, don't fix here)" and called the logs "ops work of its own". It wrote no issue and named no deferral reason. When the owner objected, the same session found the logs' cause in under a minute, a nightly cleanup on the server, and refuted the server error in another minute. The kernel was in context throughout. The tracked-work playbook, which says separability is no reason to defer, was never opened, because the agent did not see itself as deferring.

The same shape recurs in at least ten of the owner's sessions on 7.0.0 to 7.0.6, found by a phrase search that undercounts. Confirmed findings ended listed as found and not fixed, filed as issues, or proposed as session cards for the owner to start, and the usual stated reason was that they lay outside the request. The same production-log loss was first listed this way on 20 October. The finding sentence has not changed since 7.0.0, so these sessions pool. The corpus already required the lead to fix a separable finding and forbade handing it to an owner-started session; the kernel's text did not say so.

Superpowers and Matt Pocock's skills, read as they stand today, both keep incidental findings out of the current task: Superpowers sends out-of-scope observations to a ledger as deferred minors, and Matt Pocock's skills keep explicit out-of-scope sections. SkipHow already rejected standing ledgers, and its owner asked for the opposite. Nothing was adopted.

### Checks and evidence

- This is a patch release. It restores what the owner-outcome contract and decisions already promised: supervision reaches past the request, and findings stay with the lead. Authority and protected-action boundaries are unchanged; production changes still need the owner's grant.
- No model sessions or clean-install runs were made, and whether the new wording changes behavior is `UNVERIFIED`.

## 7.0.6 (2026-11-17)

### A prepared plan always hands off

- `skiphow-plan` now says that a launch is due once preparation is complete: no product choice is open, the accepted sources can be read, and every task is written and sized. Access, credentials, data, or a human step that only execution needs no longer withholds the launch. It stays a blocker on the affected task, and the report tells the owner what to provide. When preparation is incomplete, the report says what withholds the launch.
- The launch is written in English. It points at where each added constraint was decided, and it restates no grant. Grants stay in the execution records, because a pasted launch becomes an owner message and would carry the grant without its conditions.
- The opening section no longer promises a launch unconditionally; it defers to the handoff section.
- `tracked-work` no longer pairs a launch line with "blocked work is not ready to execute". A launch line for blocked work names what resumes it.

### Contributing

- The development pin moves to markdown-it-py 4.3.0.

### Why

A user's report on 7.0.5 showed two sessions. In one, an explicitly invoked plan was prepared and reviewed, but it returned no launch, because its last task needed a spreadsheet connection the owner had to restore and no partial scope had been selected. The final report did not say the launch was withheld. The text supported that reading: the launch was due "when the scope is ready", and the sentence that followed listed known human prerequisites as blockers next to "readiness". In the other session, a requested launch came back in the owner's language, with first-person grants. "Write engineering artifacts in English" sat in the tracker sentence, while the kernel reports to the owner in their language, and the launch reaches the owner inside that report. Nothing forbade restating an existing grant.

Confirmed against the 7.0.5 text and kept out of the change:

- The long launch in the second session also copied requirements and model routing. "Requirements and dependencies stay in the task records; execution policy stays in SkipHow" was plain, so this is a run deviation that one session cannot show to be systematic.
- Both sessions kept the plan in repository files. The excerpts cannot show whether the project had an authorized local convention, so this stays `UNVERIFIED`. The question is already open in the evidence summary.

Prior art read for this shape: Superpowers' `writing-plans` always ends with a handoff after review and records no execution prerequisites. Nothing was adopted.

### Checks and evidence

- This is a patch release. It restores the promised "the plan ends with a launch prompt". Authority boundaries are unchanged except that the launch now restates no grant.
- An isolated read-only Codex review ran two rounds. Round 1 found that "the launch restates and grants no authority" contradicted the kernel: a pasted launch is an owner change request and grants ordinary in-scope execution. The wording now says that the launch restates no grant and adds no protected action. Round 2 found nothing that qualified. The isolated Codex home cached a SkipHow plugin at startup, and the transcripts show no read of it.
- The corpus gains `planning-execution-prerequisite-launch`, which is not run and remains `UNVERIFIED`. No model sessions or clean-install runs were made, so whether the new wording changes behavior is `UNVERIFIED`.

## 7.0.5 (2026-11-05)

### Attribution matches the shipped files

- The third-party notice said the kernel adapts the decision frontier from Matt Pocock's `grilling` skill. The frontier now lives in the `product` reference; the kernel keeps only a recommended answer for every owner question, all asked in one round. The notice now says so.
- `SOURCES.json` was checked against the upstream files at the pinned revision, one by one. It now credits the four workflows that carry adapted ideas: `skiphow-bug` from `diagnosing-bugs`, `skiphow-longrun` from `implement-spec`, `skiphow-plan` from `to-tickets` and `grilling`, and `skiphow-simplify` from `improve-codebase-architecture`. It drops `setup-matt-pocock-skills`, `wizard`, and the `writing-for-agents` skill-mechanics file, because no shipped text carries an idea from them any longer. The upstream licence, copyright, and inspected revision are unchanged.
- Runtime instructions are unchanged.

### Contributing

- Contributor tests that pinned shape instead of a contract are gone: `tests/test_package.py` and `tests/test_host_pilot_capture.py` whole, the unreferenced synthetic receipt `evals/receipts/capture-synthetic-pilot.json`, and duplicate, call-order, source-reading, and tooling-only tests elsewhere. The per-job workflow pins become one rule: no job holding a `write` permission checks out code, sets up Python, or runs installs or scripts. Site metadata checks are lint, as the decision on deterministic checks already said, and `site/.nojekyll` is no longer required.
- Development pins move to pytest 9.2.0 and pluggy 1.7.0, and both workflows use `actions/setup-python` 7.1.0.

### Why

Five pull requests from earlier sessions had passed CI and sat open for three days to nearly three weeks: the attribution fix, the test audit, and three dependency bumps. The attribution fix was prepared as 7.0.2, but 7.0.2 shipped other work, so its version stamps no longer applied. This release carries all five onto the current `main`.

### Checks and evidence

- This is a patch release. Authority and protected-action boundaries are unchanged.
- No model sessions or clean-install runs were made.

## 7.0.4 (2026-11-05)

### A run stops what it started running

- A run owns every process, server, simulator, and container it starts. It notes how to stop each one as it starts it and stops it before reporting completion, unless the owner asked to keep it. The report names a kept one with its address and branch. Previews shown during an iteration are not completion and stay up for inspection as before.
- A delegate stops what it set running before it returns, unless its brief keeps it, and names a kept one's address and how to stop it. The lead tracks those processes with the rest of the working state each unit created and reports any it could not retire.
- The kernel is 88 characters longer. The list of what the lead keeps when it delegates (owner questions, decisions, records, integration, final verification, and the completion claim) left it, because the delegation playbook carries the same list and the kernel makes reading it mandatory before any dispatch; the opening line and Done keep verification and the completion claim in the kernel. The delegation playbook drops a sentence repeating why the brief carries the Engineering standard, which the section's opening already gives.

### Contributing

- Every task that changes this repository now ends as a published release, unless the owner asks for analysis, a plan, or no release. Afterwards the task's worktrees and branches are removed, the main checkout is brought up to date, and pull requests, branches, and worktrees left by earlier sessions are released, closed with a reason, or named as waiting.

### Why

Dev servers, `log stream` sessions, booted simulators, and test containers repeatedly outlived the agents that started them, for hours to days. The custody section named every service as the lead's, and the integration playbook clears away what a run created, but no sentence said a run stops what it starts, when to learn how to stop it, or how to report one the owner wants kept. A delegate's brief carried no such rule at all.

### Checks and evidence

- This is a patch release. It carries out what custody already promised: a run's leftovers end retired or reported. Authority and protected-action boundaries are unchanged, and a live session's process stays untouched.
- No model sessions or clean-install runs were made, and the new behavior remains `UNVERIFIED`. No corpus case was added, because no recorded event observes a running process.

## 7.0.3 (2026-10-21)

### A correction reaches every place it applies

- A defect or an owner's correction now covers every place that shares its cause or role. The lead fixes them all where the cause lives, with no guard per place. Before, the kernel spoke only of a failure that repeats.
- In fast-fixes, feedback on one element, such as a selected component or a screenshot, is feedback on its role. The lead finds every element in that role, applies the change through the piece they share, and names the places it reached. It stays in one place only when the owner says so or the other places serve a different purpose.
- In fast-fixes, the lead inspects the rendered result on every screen that renders what it changed, against the state it replaces, not only the screen the owner pointed at.
- The kernel is 18 characters shorter. "Re-review only the fixes and stop when a round returns nothing that qualifies" left it, because the review playbook says the same and opens before any review or any work on findings.

### Why

One root session on 7.0.2 iterated on an interface for seven and a half hours. In about 24 of some 140 owner messages, the owner asked again for a change they had already asked for on another instance. Three times a shared piece changed for one screen broke another screen that had relied on it. The kernel and the workflow were in context throughout, because the host re-attached them after each of about twenty compactions, and the owner's wish for consistency survived in every summary. The wording was the gap. 6.3.4 said a second failure of one kind is a class whose other members get fixed, and its design playbook fixed the class with its sibling paths. 7.0.0 narrowed this to "when a failure repeats, fix the shared cause", which says nothing about the other instances that the decision record still promised and nothing about an owner's design correction. A comparable interface session on 6.3.4 drew one such complaint in 152 owner messages. The tasks differ, so that comparison proves no cause.

Matt Pocock's skills and Superpowers, read as they stand today, scope a fix to the reported defect and say nothing about a shared component's other consumers. Nothing in either was worth taking.

### Checks and evidence

- This is a patch release. It restores what the decision record already promised: a fix reaches the other instances. Authority and protected-action boundaries are unchanged.
- An isolated read-only Codex review ran one round, which also checked that the removed re-review clause keeps its path through the review playbook. It found nothing that qualified.
- The owner declined paid model sessions for this release. No model sessions or clean-install runs were made, and the new behavior remains `UNVERIFIED`.

## 7.0.2 (2026-10-21)

### Reports the owner can read, follow-ups the lead carries

- The final report reaches the owner in the language they write in and in product terms: what changed for users, where it runs and on which branch, decisions they would notice, and what is unverified, blocked, or waiting on them. Commit hashes, check names, and the account of every part, branch, worktree, finding, and blocker go in the commit, pull request, or issue the work may write and its audience may read, and otherwise stay in the report, so a read-only request still writes nothing. The kernel no longer orders the report to lead with how the work was checked or to use the `UNVERIFIED` label.
- Parts and findings of the requested outcome stay with the lead, done directly or through delegates. The lead never leaves them to sessions the owner has to start.
- When the host or sandbox refuses something the work needs, the lead asks the owner once, plainly, for a lasting permission instead of handing over a one-off command.
- The kernel is 83 characters and two words shorter. Three sentences that the delegation, tracked-work, testing, and integration playbooks already carry at the act left it, along with the delegation entry in References, which the dispatch rule already links.

### Why

An owner reported spending their time managing agents instead of the product and listed seven behaviors to fix. Each was checked against the 34 root sessions that ran 7.0.1 on that owner's project: 112 owner messages, 348 closing messages, and the merges in the same window. Three items already held on 7.0.1: finished change sessions ended merged into the non-production branch with their worktrees retired, the one exception following a project rule that reserves merges for a grant; the window's merges were mostly removals; and ordinary requests worked without naming a workflow. Three items traced to the kernel's own wording. 64% of closings to an owner writing in Russian were mostly English, and 64% carried hashes, branches, pull request numbers, or `UNVERIFIED`, which the Done section literally asked for. Six sessions ended with follow-up session cards for findings of their own work, which the owner then started, and the kernel never said those were the lead's. Three sessions handed the owner the same one-off command for a step the owner's own settings refused, where the kernel said only to name the blocker.

Superpowers and Matt Pocock's skills, read as they stand today, set no rule on the language or detail of the final report. Superpowers' parallel dispatch returns results to the lead, and nothing in either was worth taking.

### Checks and evidence

- This is a patch release. It restores what the owner-outcome contract already promised: one accountable lead and an honest report the owner can use. Authority and protected-action boundaries are unchanged.
- The corpus gains `owner-report-in-owner-language`, and `tracked-work-finding-reported-not-recorded` now forbids handing a confirmed finding to a session the owner must start. Neither has run.
- An isolated read-only Codex review ran two rounds. Round 1 found that the new accounting sentence told a read-only request, or a project with no tracker, to write a commit, pull request, or issue, against the Authority section and the tracked-work rule on audience. It now names only records the work may write and its audience may read, and otherwise the report; the decision and the contract match. Round 1 also found that the new corpus case claimed to check the commit message, which no event observes; the case and its README note now claim only what the report leaves out. Round 2 found nothing that qualified.
- The owner declined paid model sessions for this release. No model sessions or clean-install runs were made, and the new behavior remains `UNVERIFIED`.

## 7.0.1 (2026-10-18)

### Inherited rules and tooling are the CTO's to judge

- Rules, tools, and records that earlier sessions made are the CTO's own earlier decisions, including a technical option the owner picked from a list an agent offered; product choices stay the owner's however they were made. Only what the owner's own words require stays the owner's. Simplify no longer treats a rule as the owner's when its history is unclear, and commits under the owner's account do not make a rule theirs. Simplify keeps the intent the owner stated, such as small modules, and revises the mechanism an agent chose for it, such as a line limit with a baseline to maintain.
- A rule that forces needless work counts as a defect, and the kernel's reuse rule now applies before an agent repairs its own tooling as well as before it writes new tooling.
- Simplify judges the project's own tooling, gates, and limits by their cost per run and in fixes against what they catch and what the test runner, CI provider, linter, or a maintained library offers. The agents and CI jobs that run them do not count as the callers that justify them. A test cut that relies on other coverage holds only after that other test has been read.

### Findings and loading survive the run

- When a lead accepts a delegate's return, it settles each finding: fixes it, folds it into planned work, records it with the reason it waits, or says why it is not a finding. Returns list findings apart from status. The kernel opens `tracked-work` for deferred findings, which says where the record goes and what it carries.
- Every workflow now loads the kernel by invoking the `skiphow` skill where the host has a skill tool, and otherwise by reading the file. A host that re-attaches invoked skills after compaction then keeps the kernel in context.

### Why

A trace of 22 root sessions and their delegates that ran 7.0.0 on three owner projects found loading much improved, but also four failures. Three sessions lost a kernel they had read as a file at compaction. Leads never mentioned again 41% of the items their delegates raised. Agents kept an agent-chosen line limit and an agent-built test selector as owner decisions. Test deletions that claimed other coverage left holes that only review caught. See [evidence](docs/evidence.md) and [decisions](docs/decisions.md).

### Checks and evidence

- This is a patch release. It restores behavior 7.0.0 promised: revising agent-made rules, keeping the system small, and accounting for every finding. Authority and protected-action boundaries are unchanged, and product decisions stay the owner's.
- An isolated read-only Codex review ran three rounds. Round 1 found that the owner-pick clause in the kernel and simplify did not limit options to technical ones, so an agent could have revised a product choice the owner made from an agent's list. Both now say technical, and the docs match. Round 2 found that the new fixture claimed every direct fix changes the file's length, but a same-length fix exists. The fixture now says only a length-changing fix trips the budget, and the required revision does not depend on it. Round 3 found nothing that qualified.
- No paid model sessions or clean-install runs were made. The new behavior remains `UNVERIFIED`.

## 7.0.0 (2026-10-17)

### The CTO keeps the system small

- The kernel has a new Engineering standard section that loads on every request. Everything an agent adds stays and costs the owner, so it builds the least that delivers the outcome, and removing what no longer pays needs no more justification than adding it did. A replacement moves every in-repository caller and deletes the old path. Failures are fixed at their cause, never hidden behind fallbacks, retries, longer timeouts, or weaker assertions. Production code has nothing that exists only for tests. Test or tooling code growing faster than the product, repeated fixes to the project's own tooling, and long review loops count as defects.
- A test exists to catch a break a user or caller would notice. Before writing one, the agent names the production change that would make it fail. Tests go through the interface callers use and mock only what the project does not control. Tests that pin text, constants, configuration, styling, or layout, check call order or mocks, test the project's own tooling, or read source files are not written, and are removed in code the agent touches. A fixed bug gets one regression test only where a recurrence would otherwise go unseen.
- A finding, including a reviewer's, is a claim to check. It qualifies only when it names a broken behavior or requirement, a security or data risk, or a simpler design. "Add a test" or "cover more cases" with no named break is declined with a reason. Independent review runs only where a mistake is expensive, re-review covers only the fixes, and review stops after a round with nothing that qualifies.
- Project instructions that earlier agent sessions wrote on their own judgment now count as the CTO's own earlier decisions, revised when they cost more than they protect. Rules the owner asked for stay the owner's. Agents no longer write rules that make agents add artifacts, such as "every fix gets a test".
- Every implementation and review brief carries the Engineering standard, because delegates do not inherit skills.

### New workflow

- `skiphow-simplify`, invoked by the owner, measures an existing project, removes tests, tooling, shims, copied rules, and stale documents that do not pay through reviewed changes, keeps guards for money, security, customer data, and the release path, measures again, and revises the agent-written rules that produced the waste.

### Package layout

- New `testing` and `review` references replace `verification`. The `operations` reference is gone: release and CI moved to `integration`, verification cost to `testing`, learning from failures to `diagnosis`, and the technical roadmap to `tracked-work`. Every reference and workflow was rewritten in plain language.
- `skiphow-longrun` no longer requires a fresh reviewer for every slice; review scales to consequence. `skiphow-plan` reviews its plan once.
- Reversed: 6.3.5's preference for a failing check such as an import rule or exhaustiveness test over a comment, which produced source-reading tests in the field, and 6.3.3's sentence that age or cost alone justifies no deletion. A mechanical rule now goes into the project's existing linter or type checker.

### Why

A trace of two owner projects governed by 4.3.0 through 6.3.5 found test and tooling code larger than product code, tests of the projects' own deploy and CI scripts, custom test-selection and gate tooling, production branches written for mocks, and review loops of up to six rounds that mostly asked for more tests. The package text made every addition a gain and every removal a risk, and its test guidance reached about one in twenty test-writing delegates. See [evidence](docs/evidence.md) and [decisions](docs/decisions.md).

### Checks and evidence

- This is a major release because default side effects change: agents now delete tests and tooling that do not pay, revise agent-written project rules, and stop review rounds earlier. Authority and protected-action boundaries are unchanged.
- An isolated read-only Codex review ran three rounds. Round 1 found seven issues; six were fixed: credential handling regained "secure destination" and "command history", the kernel's reuse rule names the same command, tree, and environment, capability use and project-wide risk returned to the kernel, plan review re-reviews consequential fixes and lets small low-risk plans self-review, `review.md` no longer lets a small confirmed break drop, and `delegation.md` allows for hosts that fork the whole conversation. Refused: the argument that pasting the Engineering standard into a forked delegate duplicates context, because the pasted copy is the only channel known to reach delegates and costs about 2,500 characters. Round 2 found four, all fixed: deploy-ready's reuse rule, a fixed three-fix count and a three-to-five hypothesis quota in `diagnosis.md` that contradicted the 3.0.0 removal of fixed counts, and a missing trigger for long steps. Round 3 found nothing that qualified. The isolated Codex home received a cached SkipHow 6.3.5 plugin at startup; the transcripts show no read of it.
- No paid model sessions or clean-install runs were made. The new behavior and comparative benefit remain `UNVERIFIED`.

## Earlier releases

[Release notes for 6.x](https://github.com/mzored/SkipHow/blob/fb1aafadf982fd69b74fd1fde184ad062c32e7d7/CHANGELOG.md#635-2026-10-16) and [releases before 6.0.0](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/CHANGELOG.md#515-2026-09-26) remain in immutable source.
