# Owner guide

Tell SkipHow what should change for someone using the product. You do not need to name a library, design a schema, write tickets, or choose an agent workflow.

This guide describes what the shipped instructions require of the agent. That is not the same as what has been measured. [Current evidence](evidence.md) records which of these behaviors real runs have shown, which a run has shown failing, and which stay intended but unproven. Short answers to common questions are in the [FAQ](faq.md).

## Install

Codex:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Claude Code:

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Start a new session after installing or updating.

## Activate it

Name the skill in your request: `$skiphow` in Codex, `/skiphow:skiphow` in Claude Code. Explicit invocation is the reliable, portable mode and the one every documented behavior assumes. Both hosts can also select the skill on their own from its description; that path exists, but how reliably it fires for an ordinary request has not been measured, so it is `UNVERIFIED` and not something to lean on.

The package ships a session-start hook that prints a one-line reminder at startup, clear, compaction, and resume. It does not load the skill, restore context, grant authority, or guarantee activation. The two hosts treat it differently: Claude Code enables a plugin's hooks along with the plugin, while Codex asks you to review and trust each hook definition before it runs, so installing on Codex does not by itself make the reminder fire. The dated, per-capability host matrix is in the [security policy](../SECURITY.md#host-support-as-of-2026-09-04).

Update Codex:

```sh
codex plugin marketplace upgrade skiphow
codex plugin add skiphow@skiphow
```

Update Claude Code:

```sh
claude plugin marketplace update skiphow
claude plugin update skiphow@skiphow
```

Uninstall with `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`.

## Ask for the outcome

A useful request names the visible result and any limit you care about:

```text
The checkout sometimes hangs after payment. Find the cause and fix it without changing the payment provider.

Compare these onboarding ideas. Recommend one, but do not change the project.

Save these observations so we can prioritize them tomorrow.
```

Rough requests are fine. SkipHow reads the project before it asks you for anything. It brings a question back only when the answer changes product behavior, scope, priority, cost, risk, privacy, or rollout. It also asks when an action needs your explicit grant or only a person can complete it.

Where your request leaves a genuine product choice open, the instructions require the question to reach you before the work, with the option it recommends, and everything answerable at that point to arrive together rather than one message at a time. Some choices only exist once you have answered another. Say yes to cancelling parcels that are already on their way and the question of who pays the carrier's fee appears, which nobody could have put to you before. Those go back in a second round, and only those. Once nothing material is open, the work starts. A question that is with you is not answered by a default: nothing whose meaning depends on your answer is to be built while you decide, and the parts that do not depend on it carry on. "Let someone share their cart with a friend" should come back asking whether the friend gets a snapshot or a live shared cart, not with one of the two silently built. That second round is the part to check rather than assume: the runs on record show it holding on Claude Code and not reliably on Codex, and [current evidence](evidence.md) says what each one did. Where your project's own evidence settled a reading, the report names it and the alternative it did not take, so correcting it costs one message. Where nothing settles it, you get the question instead — not a choice made for you and mentioned afterwards. What the project cannot do yet is never treated as an answer to what the product should do; it is a cost, and the cost is yours to weigh.

You can correct or extend the request while work is running. The agent treats the new message as part of the current outcome unless you replace the request.

## Know what your request allows

| Request | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, review, research, plan, triage, or organize | Read and report |
| Create a record | Write that record only |
| Change the project | Edit, check, and commit the change locally where a commit fits the work |
| Deliver the change | Use the repository's normal shared path |

A mixed request such as "review and fix" allows a project change. A request only to review does not.

Changing a project does not grant an unrelated push, pull request, or merge. Ask for shared delivery when you want it. Name production, staging, a public release, payments, repository settings, access changes, material deletion, wider disclosure, or credential work explicitly.

## Records and tracked work

Installing SkipHow does not give your project a tracker and does not write a tracking convention into it. A project that keeps no record of its work has already answered that question. A record gets written when you ask for one or for tracker work, when you ask for work already on record to be carried forward, when your repository's own workflow makes that record part of the delivery you asked for, or when a change running over more than one session needs the little state it takes to resume and your project already has a private place allowed to hold it. A branch, a worktree or a review is an ordinary engineering mechanic and does not mean an item had to exist first, and a request only to answer, compare, diagnose, review, research, plan, triage, or organize records nothing at all.

Work with more than one result you could check separately is split into parts you can each see working, with only the genuine dependencies between them. Parts that do not block each other can run at the same time where your host can give each one a checkout of its own, and are done one after another where it cannot. The splitting is what the runs show; running the parts concurrently is the intent, and no receipt has demonstrated it yet. Where the split needs to outlive the session and a record is called for, it goes where your project already keeps that work, and the report names what continues it. When you only asked for a plan, you get the split in the answer and nothing is written.

Where work did go into your tracker, it closes as the change is integrated rather than when it looks finished on the branch, and what the work established is written back into it, so nobody pays for the same investigation twice. Something reported that turns out not to happen is closed as not reproducible, with what was checked, rather than as fixed. A material problem found along the way that does not block your result is reported to you rather than recorded, unless a record is one of the things your request allows.

## Read the report

A finished report starts with what changed and the evidence that still applies. It names blockers and `UNVERIFIED` claims instead of turning them into success.

The instructions require SkipHow to preserve unrelated work: a checkout, branch or running service it did not create is shared, and the uncommitted changes in it are somebody's. One run on record broke that and destroyed a peer session's uncommitted work, so if you keep two sessions on one checkout, read [current evidence](evidence.md) before you rely on it. A dirty checkout is a reason not to commit when the owned change cannot be separated safely, and it weakens verification only when it makes the evidence unreliable.

## Remember the host boundary

Codex or Claude Code supplies the sandbox, permissions, tools, sessions, subagents, and credentials. SkipHow cannot exceed those controls. A plugin hook may remind the host to load the owner skill at a session boundary where SkipHow already governs the request, but it cannot restore context or grant authority by itself.
