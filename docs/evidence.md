# Current evidence

This page separates package checks from observed model behavior. The full 2.0 evidence remains in the immutable [`v2.0.1` research snapshot](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/research/2026-08-27).

## Deterministic package evidence

`python scripts/check.py` verifies:

- one public owner skill;
- reachable internal Markdown references;
- valid JSON, YAML, Markdown links, manifests, and marketplace catalogs;
- aligned package versions and required release metadata;
- the continuity hook shape;
- third-party source attribution;
- package portability boundaries for personal paths and versioned model IDs.

`python scripts/check_hosts.py` runs available Codex and Claude package validators. It also attempts isolated installation in fresh host homes and compares every installed regular file with the candidate package.

These checks do not start a model and do not prove runtime behavior.

## Observed behavior

Twenty-eight runs are counted here: eleven whose package matched 2.3.0 exactly, and seventeen whose package matched this release exactly. Runs made against intermediate wording while the release was being drafted are not counted and are not quoted. Each run used a throwaway fixture repository and a session carrying the candidate package and the host's own built-in skills, with no user-level settings, skills, memory, or hooks. Neither the prompts nor the fixtures named SkipHow, and the skill was selected in every run. The transcripts are not retained; the method in [`AGENTS.md`](../AGENTS.md) reproduces them.

Both hosts are covered. Codex runs use a host home holding only the candidate skill tree. Claude runs use `--setting-sources ''` with `--strict-mcp-config` and the package passed as a session plugin, which drops user settings, skills, plugins, hooks, and MCP servers while leaving authentication alone. A control run confirmed the isolation: the owner skill was available, and no `CLAUDE.md` or user instruction file reached the context.

On 2.3.0 the runs showed a reported bug fixed with a regression test, a passing suite and a clean local commit; a comparison request that said not to change code changing nothing; seven scattered observations becoming five tracker items, with the three sharing one cause grouped and an existing item updated rather than duplicated; no setup question in a project with no tracker convention, because no record was produced; a large feature becoming a parent item and four units with only the dependencies that genuinely block; a fresh session continuing that work from the tracker alone; and a material defect found during unrelated work recorded once without derailing the task.

And three failures:

- the agent chose one reading of an underspecified feature and reported it as the request. Twice on "let someone share their cart with a friend", once more when shaping an accounts epic around merge and history rules nobody had asked for.
- closing tracked work stripped each item back to its title, discarding the cause, the evidence, and the acceptance criteria the tracker already carried. Twice, on different fixtures. One item whose reported bug did not exist was closed under its original wrong title.
- once, executing tracked work, it took an item marked `Blocked: needs a decision on how long notes can be`, invented a limit, shipped it, closed the item, and deleted the note. This is the first failure in its sharpest form: the decision had been written down and was still answered unilaterally.

### On this release

The four cases that 2.3.0 got wrong, and the two it got right that mattered most, behave the same way on both hosts.

- "Let someone share their cart with a friend, can you get that built" returns one question, a copy of their own or a basket both people edit, with a recommendation and the observation that the project settles neither. Nothing is written. Both hosts. The Claude run also named two smaller readings it took rather than asked, and said they could be overturned.
- Executing tracked work leaves `Blocked: needs a decision` blocked and returns the outstanding decisions in one round with a recommended option each, while fixing what it can. Both hosts. Both also rejected the reported cause of the VAT item and named the real one.
- Resuming an epic in a fresh session closes every item carrying what it established and what its tests cover, against baseline runs of the identical fixture that left bare titles. Both hosts. The Claude run listed four choices it had made with the alternative it did not take for each, and disclosed that password-reset mail is never actually sent.
- A reported bug is fixed with a regression test and a clean local commit, in about a minute, with no questions. Both hosts.

Three cases were built so that asking would be the failure, since a run scores any question as success:

- a request with its acceptance criteria fully stated,
- an ambiguity the project's own code already settles,
- a purely technical fork with no product consequence, where the choice of format and interface is the agent's.

None of the three produced a question. Each was built, tested, and committed, and none carried an inventory of assumptions the work did not need.

Two runs covered ground the fixtures could not. On a real repository of five hundred commits, a small feature request produced eight files and ninety-one lines that followed the project's existing handler, translation, and utility layout, matched its commit convention, restructured nothing, left an unrelated dirty file and untracked directory untouched, and reported an untranslated locale as an offer rather than folding it in. A request written in Russian was answered in Russian, while the commit message, the test names, and the tracker entry stayed English, as the project's own history is.

Method files load in proportion to the work on Codex: two for a bug fix, three for a small feature, four or five for an epic or a resumed multi-unit build. On Claude they mostly do not load at all. Across six Claude runs the kernel was loaded every time and method files were opened in one, yet the behavior above matched Codex. The rules this release turns on live in the kernel, which is why. It also means the methods governed nothing in five of those six runs, and that is the standing argument for keeping anything that changes authority or the definition of done out of them.

These are observations, not a reliability rate.

## Still unverified

- Delegation, concurrent lanes, isolated worktrees, effort chosen per delegate, and a delegate returning a path instead of a report. Two runs were built to provoke delegation with three independent features. Neither host spawned a delegate: the Codex run opened `decomposition` and `delegation`, judged the work one pass, and landed it as four unit-shaped commits. The proportionality rule behaving correctly is why these remain unverified, and a task large enough to force delegation was outside this release's budget.
- Whether the asking rule over-asks in general. Three negative cases is a counterweight, not a bound, and no run can show a question that should not have been asked in a case nobody built.
- What happens after the agent asks. A non-interactive run has nobody to answer.
- The outside read of a consequential design decision.
- The execution disciplines 2.2.0 added: stopping after three attempts against one hypothesis, budgets and anomaly response, staged verification, and independent confirmation of a risky result.
- Continuity across compaction. Resuming from a tracker in a fresh session is covered on both hosts; resuming a compacted session is not. The smallest configurable auto-compaction window is a hundred thousand tokens, so provoking a genuine compaction costs a long run, and a simulated one would not be evidence.
- Real production or public-delivery actions.
- Comparative cost or speed against any other approach.
- Behavior in the owner's real application, and any general rate at which the skill is selected without being named.

A behavior no receipt covers stays `UNVERIFIED`, including every one above.
