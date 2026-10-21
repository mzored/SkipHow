# Changelog

All notable changes to SkipHow 2.x and later appear in this file. Earlier release notes remain available on [GitHub Releases](https://github.com/mzored/SkipHow/releases).

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
