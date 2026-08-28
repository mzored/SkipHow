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

Version 2.4.0 is the first release since 2.0 backed by receipts. Forty-five one-off Codex runs exercised the package while it changed: one throwaway fixture repository per run, a host home holding the candidate skill tree and the host's own built-in skills and nothing else, and the same prompt on both sides of each change. Fixtures were a small JavaScript storefront in three shapes: no contributor notes, notes naming a tracker that did not exist yet, and notes plus a tracker holding three open items and one done item. Neither the prompts nor the fixtures named SkipHow, and the skill was selected in all forty-five. The transcripts are not retained in this repository; the method in [`AGENTS.md`](../AGENTS.md) reproduces them.

The wording went through several revisions, so the two sets below are quoted only from runs whose package matched the release exactly: eleven on 2.3.0, six on 2.4.0.

On 2.3.0 the runs showed:

- a reported bug fixed with a regression test, a passing suite, and a clean local commit, opening two of the method files and finishing in about a minute;
- a comparison request that said not to change code changing nothing and recommending one option;
- seven scattered observations becoming five tracker items, with the three that shared one cause grouped into one and an existing item updated rather than duplicated;
- a bug fix in a project with no recorded tracker convention asking no setup question, because it produced no record;
- a large feature becoming a parent item and four units, each with an outcome someone can observe, and only the dependencies that genuinely block;
- a fresh session continuing that work from the tracker alone, without re-shaping it or repeating the investigation;
- a material defect found while building something unrelated recorded once, without derailing the task.

And three failures:

- the agent chose one reading of an underspecified feature and reported it as the request. Twice on "let someone share their cart with a friend", once more when shaping an accounts epic around merge and history rules nobody had asked for.
- closing tracked work stripped each item back to its title, discarding the cause, the evidence, and the acceptance criteria the tracker already carried. Twice, on different fixtures. One item whose reported bug did not exist was closed under its original wrong title.
- once, executing tracked work, it took an item marked `Blocked: needs a decision on how long notes can be`, invented a limit, shipped it, closed the item, and deleted the note. This is the first failure in its sharpest form: the decision had been written down and was still answered unilaterally.

On 2.4.0, against the same fixtures:

- "let someone share their cart with a friend, can you get that built" returns one question, a read-only snapshot or a cart both people edit, with a recommendation and the observation that the project settles neither. Nothing is written.
- shaping the accounts epic still writes the epic, and names the three product decisions it took in the result and in the tracker: guest checkout stays, earlier guest orders are not attached, and a password reset ends existing sessions. The kernel allows either branch, asking or naming, and this run took the second.
- executing tracked work fixes the item it can, leaves `Blocked: needs a decision` blocked, and returns both outstanding decisions in one round with a recommended option each. The item it closed carries the cause it found, the fix, and the number the regression test asserts.
- resuming the epic in a fresh session closes all five items carrying what each one established and what its tests cover, against a baseline run of the identical fixture that left five bare titles.
- the bug fix and the read-only comparison are unchanged, and the bug fix still opens two method files and asks nothing.

Method files load in proportion to the work across the set: two for a bug fix, three for a small feature, five for an epic or a resumed multi-unit build. These are observations, not a reliability rate.

## Still unverified

The receipts cover one host, one model, and one small fixture project. They do not prove:

- Claude model behavior. The runs are Codex only, because Claude's credentials live in the system keychain and could not be isolated into a throwaway host home without exposing a token.
- that the asking rule does not over-ask. A run scores a question as correct behavior, and no run can show a question that should not have been asked. One unchanged bug-fix fixture is the whole counterweight.
- what happens after the agent asks. A non-interactive run has nobody to answer.
- delegation, concurrent lanes, isolated worktrees, effort chosen per delegate, or a delegate returning a path instead of a report. Nothing in these runs spawned a delegate.
- the outside read of a consequential design decision.
- the execution disciplines 2.2.0 added: stopping after three attempts against one hypothesis, budgets and anomaly response, staged verification, and independent confirmation of a risky result.
- continuity across compaction or restart. Resuming from a tracker in a fresh session is covered; resuming a compacted session is not.
- real production or public-delivery actions.
- comparative cost or speed against any other approach.
- behavior in the owner's real application, or any general rate at which the skill is selected without being named.

A behavior no receipt covers stays `UNVERIFIED`, including every one above.
