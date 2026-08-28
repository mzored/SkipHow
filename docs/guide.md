# Owner guide

Tell SkipHow what should change for someone using the product. You do not need to name a library, design a schema, write tickets, or choose an agent workflow.

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

Start a new session after installing or updating. If the owner skill does not load automatically, add `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code.

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

Rough requests are fine. Before substantial work it tells you back what it understood and what would count as done, so you can correct it early. SkipHow reads the project before it asks you for anything. It brings a question back only when the answer changes product behavior, scope, priority, cost, risk, privacy, or rollout. It also asks when an action needs your explicit grant or only a person can complete it.

Where your request leaves a genuine product choice open, you get the question before the work, with the option it recommends, and everything answerable at that point arrives together rather than one message at a time. Some choices only exist once you have answered another. Say yes to cancelling parcels that are already on their way and the question of who pays the carrier's fee appears, which nobody could have put to you before. Those come back in a second round, and only those. Once nothing material is open, the work starts. "Let someone share their cart with a friend" comes back asking whether the friend gets a snapshot or a live shared cart, not with one of the two silently built. Where it had to choose without asking, the report names the choice and the alternative it did not take, so correcting it costs one message. What the project cannot do yet is never treated as an answer to what the product should do; it is a cost, and the cost is yours to weigh.

You can correct or extend the request while work is running. The agent treats the new message as part of the current outcome unless you replace the request.

## Know what your request allows

| Request | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, review, research, plan, triage, or organize | Read and report |
| Create a record | Write that record only |
| Change the project | Edit, check, make a clean local commit, and keep the project's record of that work |
| Deliver the change | Use the repository's normal shared path |

A mixed request such as "review and fix" allows a project change. A request only to review does not.

Changing a project does not grant an unrelated push, pull request, or merge. Ask for shared delivery when you want it. Name production, staging, a public release, payments, repository settings, access changes, material deletion, wider disclosure, or credential work explicitly.

## Keep work in one place

The first time a project needs to record something, SkipHow asks once where your tasks and findings should live and who may see them, then writes that choice into the project's own instructions. After that it uses the same place without asking again.

Work with more than one result you could check separately is split into parts you can each see working, with only the genuine dependencies between them. Parts that do not block each other are free to run at the same time where your host supports it. The splitting is what the runs show; running the parts concurrently is the intent, and no receipt has demonstrated it yet. When your request allows a change, that split is recorded where your tasks live and the report names what continues it, so you can start it now or in a later session. When you only asked for a plan, you get the split in the answer and nothing is written.

That record is what lets a later session continue your work, and what stops a problem found along the way from disappearing when the conversation ends. Finishing a tracked item writes what the work established back into it, so nobody pays for the same investigation twice. Something reported that turns out not to happen is closed as not reproducible, with what was checked, rather than as fixed. A request only to answer, compare, diagnose, review, research, plan, triage, or organize still records nothing.

## Read the report

A finished report starts with what changed and the evidence that still applies. It names blockers and `UNVERIFIED` claims instead of turning them into success.

SkipHow preserves unrelated work. A dirty checkout prevents a commit only when the owned change cannot be separated safely. It weakens verification only when it makes the evidence unreliable.

## Remember the host boundary

Codex or Claude Code supplies the sandbox, permissions, tools, sessions, subagents, and credentials. SkipHow cannot exceed those controls. A plugin hook may remind the host to load the owner skill at session boundaries, but it cannot restore context or grant authority by itself.
