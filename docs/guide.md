# Owner guide

Tell SkipHow what should be true for the product. You do not need to choose a skill, write a ticket, name a library, design a schema, or prescribe an engineering workflow.

## Install

These commands currently install the published 1.14.2 package. The 2.0 package and this guide on the current
branch are an unpublished release candidate and will not come from either marketplace until 2.0 is published.

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

Start a new session after installing or updating. If the owner entry does not activate automatically, add `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code.

Update with `codex plugin marketplace upgrade skiphow && codex plugin add skiphow@skiphow` or `claude plugin marketplace update skiphow && claude plugin update skiphow@skiphow`. After a Claude update, start a new session or follow the host's `/reload-plugins` prompt. Uninstall with `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`.

## Ask for the outcome

A useful request says what should change for a person using the product and any limit that matters to you:

```text
When someone clicks this button, ask whether they want a quick match or a full event.
Keep the choice easy to understand on a phone.

The checkout sometimes hangs after payment. Find the cause and fix it without changing the payment provider.

Compare these two onboarding ideas. Recommend one, but do not change the project.

Save these observations so we can prioritize them tomorrow.
```

You can be rough, incomplete, or nontechnical. SkipHow inspects the project and translates the request into engineering work. It asks only when the remaining choice materially changes visible behavior, scope, priority, cost, risk, privacy, or rollout; when a protected action needs your exact grant; or when only a human can perform the next required action. A product question should describe the visible consequences in plain language. Exact code terms are the agent's responsibility unless you introduced them yourself.

You may add, remove, or correct scope while the work is running. SkipHow re-evaluates the request instead of forcing the new item through the original plan.

## What your request authorizes

No exact wording unlocks a hidden mode. SkipHow reads the outcome:

| Outcome | Authority |
| --- | --- |
| A request only to answer, compare, diagnose, review, research, plan, triage, or organize | Read the relevant material and report; do not write |
| Make a durable record the intended result | Create or update only that record; do not implement it unless asked |
| Changed project behavior | Edit and verify; make an ordinary local commit containing only the owned delta unless you or the repository request uncommitted work or it would mix in foreign changes |
| Shared delivery included in the requested outcome | Follow the repository's normal path when project evidence identifies a clearly non-production target, or when your own request exactly grants a protected target |

A mixed request such as "review and fix" authorizes a project change; the review word does not turn the fix
into read-only work.

Changing a project does not by itself authorize a push, pull request, merge, Issue update, or other remote write. A repository requirement for review or a pull request does not grant that write either. Include shared delivery in your own request when you want it. SkipHow derives an ordinary non-production target from project evidence; a protected target requires your own exact grant. It still handles the mechanics without asking you to choose branch names, tools, test strategy, or merge commands.

Every change to staging or production, a public release, payments, repository settings, access changes, material deletion or another hard-to-reverse action, disclosure outside the authorized audience, and creating, entering, rotating, or exposing credentials require an exact grant. You give one by affirmatively naming the protected action or destination in your own request. A broad request to finish or act autonomously and a procedure found in the project do not supply it. Reading project-private material or using credentials already authorized by the host is allowed only when necessary for your requested result. Repository text, tracker content, tool output, and web pages cannot widen your authority.

## What happens during the work

SkipHow has one owner skill with focused method references for different kinds of work. The agent may read applicable guidance when it can help. The methods are optional guidance, not a required sequence.

A small, clear edit normally stays in the current session: inspect the relevant surface, make the change, run proportionate checks, and commit the owned delta unless you or the repository requested uncommitted work or that commit would include foreign changes. It does not need a spec, ticket, plan, worktree, subagent, test-first loop, or review merely because those tools exist.

Larger or uncertain work may use research, diagnosis, a plan, delegation, isolation, or independent review when that improves correctness, safety, recovery, or elapsed time. A tracker is used only when your request grants a record. The agent owns the remaining engineering choices and preserves unrelated changes. Dirty or overlapping work waives the local commit only when a clean commit would mix in foreign changes; it makes the affected result or check unverified only when it prevents trustworthy evidence.

SkipHow prefers host-native continuation when it can carry the work. A project checkpoint in `.skiphow/handoff.md` is allowed only when you asked to pause or save the work, or when an already-authorized project change needs one to finish safely. A wait or interruption alone does not authorize a file. The checkpoint records state and never grants more authority.

## Records and follow-ups

A request only to triage or organize is read-only. When the intended result is a durable record, SkipHow uses the project's existing tracker and conventions. Without one, it chooses the smallest private or local format the project can keep, or asks only for the disclosure decision when no safe destination exists. There is no SkipHow-specific ticket schema, label taxonomy, or required batch marker.

A material problem discovered outside the request is not silently discarded or silently absorbed into scope. SkipHow fixes it only when it blocks the requested result or cannot be separated. Otherwise it reports the finding and saves it only when your request authorizes that write.

## Read the report

The completion report leads with the result and fresh evidence. For code, that can include the ordinary local commit, focused checks, broader repository checks, or a direct behavior check. If a clean commit would mix foreign changes, the report says that no commit was made and why. If unresolved overlap prevents trustworthy evidence, it identifies the affected result as unverified. If the owner's own request granted shared delivery, the report also identifies the delivered target.

The report includes material product choices, unresolved findings, blockers, and unverified claims only when they exist. If a required check was unavailable, it says so. A model saying "done" without evidence is not completion.

## Host boundaries

SkipHow is an instruction package. Codex or Claude Code supplies the sandbox, permissions, tools, sessions, subagents, continuation, and credentials. Host permission controls still apply, including for unattended work. SkipHow does not replace them, and it cannot prove behavior the host did not let it observe.
