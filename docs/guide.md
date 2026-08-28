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

Rough requests are fine. SkipHow reads the project before it asks you for anything. It brings a question back only when the answer changes product behavior, scope, priority, cost, risk, privacy, or rollout. It also asks when an action needs your explicit grant or only a person can complete it.

You can correct or extend the request while work is running. The agent treats the new message as part of the current outcome unless you replace the request.

## Know what your request allows

| Request | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, review, research, plan, triage, or organize | Read and report |
| Create a record | Write that record only |
| Change the project | Edit, check, and make a clean local commit |
| Deliver the change | Use the repository's normal shared path |

A mixed request such as "review and fix" allows a project change. A request only to review does not.

Changing a project does not grant an unrelated push, pull request, or merge. Ask for shared delivery when you want it. Name production, staging, a public release, payments, repository settings, access changes, material deletion, wider disclosure, or credential work explicitly.

## Read the report

A finished report starts with what changed and the evidence that still applies. It names blockers and `UNVERIFIED` claims instead of turning them into success.

SkipHow preserves unrelated work. A dirty checkout prevents a commit only when the owned change cannot be separated safely. It weakens verification only when it makes the evidence unreliable.

## Remember the host boundary

Codex or Claude Code supplies the sandbox, permissions, tools, sessions, subagents, and credentials. SkipHow cannot exceed those controls. A plugin hook may remind the host to load the owner skill at session boundaries, but it cannot restore context or grant authority by itself.
