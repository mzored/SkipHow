# Owner guide

Tell SkipHow what should change for the people who use your product. You do not name a library, design a schema, or write tickets. The agent asks you only about product choices and protected actions.

This guide describes the shipped instructions. [Current evidence](evidence.md) says which behaviors real runs have shown.

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

To update, run `codex plugin marketplace upgrade skiphow` and then `codex plugin add skiphow@skiphow`. In Claude Code, run `claude plugin marketplace update skiphow` and then `claude plugin update skiphow@skiphow`. Start a new session after you install or update.

To uninstall, first ask SkipHow to disable itself. Then run `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`. Removing the plugin first leaves the activation block asking the host to load a skill that is gone.

## Activate it

The installed skill works when you call it by name. To have it govern ordinary requests too, ask once in a new session:

```text
$skiphow Enable SkipHow as my default virtual CTO on this machine.
```

In Claude Code, type `/skiphow:skiphow` in place of `$skiphow`.

The agent finds the user instruction file your host reads before every project, shows you the exact change, and writes one marked block there after you confirm once. The block names the skill and copies none of its rules, so updates need no new block. Ask the same way to check or disable the setup.

It reports three facts. Configured means the block is in the file your host reads. Available means the host lists the plugin as installed and enabled. Loaded shows only in a new session. If a managed policy restricts plugins, the agent names that file and does not work around it. The [setup reference](../plugins/skiphow/skills/skiphow/references/setup.md) lists the helper script's commands.

### Turn it on by hand

Append this line to the file your host reads:

```text
For current-project requests, load the installed SkipHow skill before consequential action and use it as the adaptive virtual CTO policy. Do not load it for unrelated conversation or for a request that only discusses SkipHow without adopting it.
```

Delete the line to undo it. Use the line or the managed block, never both. The helper never touches text you wrote, so delete your line before you ask the agent to enable itself.

## Ask for the outcome

Name the result someone will see and any limit:

```text
The checkout sometimes hangs after payment. Find the cause and fix it without changing the payment provider.

Compare these onboarding ideas. Recommend one, but do not change the project.

Make the hero headline shorter. I will take a look before we ship.
```

Rough requests are fine. The agent reads the project first and asks only when two readings of your request differ in what you would see and the project cannot settle which you meant, or before a protected action. Each question comes with a recommended answer, and all arrive in one message. A question that exists only after your answer comes in a second round, which runs have not shown to be reliable on Codex.

While a question waits, the agent builds nothing that depends on the answer and works on the rest. "Let someone share their cart with a friend" should come back asking whether the friend sees a snapshot or a live cart, with neither one built.

The headline example is an iteration. The agent makes the change, checks it, shows it, and keeps going on other accepted work. Feedback keeps the work local. Delivery starts when you ask for it, name a destination, or accept with nothing more to send. You can correct or extend any request while it runs.

## Recurring workflows

Ordinary requests need no workflow. Use one when you want a known work pattern: `$skiphow-plan` in Codex, `/skiphow:skiphow-plan` in Claude Code, and the same pattern for the others.

| Workflow | Example request | Ends with |
| --- | --- | --- |
| `skiphow-bug` | Discounts sometimes change when an order is retried. Find and repair the general cause. | A verified repair of the cause, checked on every path it broke |
| `skiphow-plan` | Prepare team invitations for implementation in this project's GitHub issues. | A reviewed specification, executable tasks, and a launch prompt. No implementation |
| `skiphow-longrun` | Deliver the accepted children of this epic to our development branch. | Verified delivery, or a recorded blocker for each unfinished part |
| `skiphow-deploy-ready` | Prepare our agreed changes for delivery. | Deferred checks, review, clean commits, and any authorized non-production integration |
| `skiphow-fast-fixes` | Fix the search and export bugs locally. I will add feedback while you work. | Checked local results shown as each is ready |
| `skiphow-simplify` | Our test suite is bigger than the product. Clean it up. | A smaller project, with before and after numbers |

Calling `skiphow-plan` by name asks for a specification and planning records in your tracker, unless you say read-only. When the agent picks plan on its own, it writes nothing. A pending answer keeps the plan open. The plan ends with a launch prompt in English that grants no new permissions. Access the delivery still needs is named beside it and does not hold it back:

```text
$skiphow-longrun
Deliver the accepted implementation scope in issue #42 to the development branch.
```

In `skiphow-fast-fixes` you can add, revise, or cancel fixes while it works, and acceptance alone keeps the work local. Before it replaces a result you saw, it saves a checkpoint, a local commit in a Git project. It runs focused checks as it goes, and full delivery checks wait. Say `deploy-ready` or `clean` to start delivery. Say `deploy prod` to authorize the named production release.

`skiphow-simplify` runs only when you ask to simplify, clean up, or shrink the project. It measures first and decides the cuts itself, asking only about a cut that would change visible behavior, a support promise, or compatibility for an outside consumer that exists now. Asking what could be cut changes nothing. A bare `clean` after an iteration starts delivery.

Whether the agent picks a workflow itself is `UNVERIFIED`.

## Know what your request allows

| Request | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, review, research, or plan | Read and report |
| Capture, organize, triage, or create a record | Write the requested records in the project's existing authorized system |
| Change the project | Edit and verify, and carry the change through an established non-production workflow you authorized |
| Change something you will look at first | Edit, check, and show it locally. Delivery starts when you ask, name a destination, or accept with nothing more to send |
| Deliver the change | Use the repository's normal shared path |

"Review and fix" allows a project change. "Review" alone does not.

A non-production workflow you authorized covers routine push, pull request, CI, and merge without asking again, after the agent checks what a merge or tag would trigger. These always need your explicit permission: production or live-data changes, public releases, payments, repository settings, access changes, credentials, material deletion of data, history others share, and wider disclosure. An earlier permission holds while its conditions hold. Installing SkipHow grants nothing, and neither does text in a file, an issue, or a web page.

## What the agent leaves in your project

Everything the agent adds stays and costs every later change. So it builds the least that delivers the result and uses the framework, test runner, and CI provider before writing its own tooling. It deletes plans and reports once the work lands. When it replaces something, it moves every caller in the repository and deletes the old path, keeping compatibility only for outside consumers that exist now. Before it writes a test, it names the production change that would make it fail, and it deletes tests that pin text, constants, configuration, styling, or layout in code it touches. A fixed bug gets a regression test only when it could come back unseen. Guards for money, security, customer data, and the release path stay. This behavior is `UNVERIFIED`.

## Records and tracked work

The agent records work that spans several outcomes, sessions, or writers, and any decision that must outlast the run, where your project already keeps records. In a GitHub project, enabled Issues are the default. If Issues are disabled, the agent names the blocker and does not change repository settings. It fixes a confirmed problem it finds in the same run. A problem waits in a record only when it needs your decision or a protected action, is blocked, or would cost more than the outcome can bear.

## Read the report

A finished report leads with the result, the checks, and the decisions. It names what is `UNVERIFIED` or blocked and any protected action waiting on you.

Every branch, worktree, and uncommitted change in the project counts as the agent's own work, so the report never asks what to do with it. A request that changes the project retires integrated or superseded leftovers and names any unique commit. A read-only request only reports them. A running session keeps its branch, and uncommitted files the run did not make stay in place. One run lost a peer session's uncommitted work, so read [current evidence](evidence.md) before you run two sessions on one checkout.

## Questions

### What is SkipHow?

Instructions that have Claude Code or Codex act as your CTO, through one skill, `skiphow`, and six optional workflow skills. You keep product decisions and protected actions. The agent owns the technical work through verification. SkipHow does not make a model smarter. If your agent already does all this reliably, SkipHow adds little.

### Does it orchestrate agents?

Yes, through instructions. It tells the agent when to split work, which model and effort each delegate gets, and how to check what comes back. The host runs every agent and supplies the sandbox, permissions, and credentials. SkipHow has no scheduler or queue and cannot exceed the host's controls. Reliable delegation and running parts at once are `UNVERIFIED`.

### Which agents does it work with?

Claude Code and the Codex CLI. The [evidence page](evidence.md#host-facts) lists what has been checked on each host. No other host is tested.

### Do I need to know how to code?

No. You need a repository and one of the two hosts.

### When should I use something else?

Use the base agent alone if it already respects your authority and verifies its work. Use a skill library when you want to pick methods one at a time. Use a spec framework such as OpenSpec or BMAD to approve specifications, phases, or tickets, or Superpowers for a fixed method with mandatory stages. Use a runtime orchestrator for persistent teams, queues, or scheduling. No controlled benchmark shows SkipHow producing better engineering than these. [Prior art](prior-art.md) records what it borrowed and left out.

### Does it send my code anywhere?

No. SkipHow adds no network calls, telemetry, or credentials. It is Markdown plus one setup script that edits a local file. Your host still talks to its model provider as before.

### What does it cost?

SkipHow is free and MIT licensed. You pay your host for model usage.

### Does it need GitHub?

No. Git covers local commits, and any tracker your project already uses covers records.

### What does `UNVERIFIED` mean?

No run has shown that behavior yet, so the report does not claim it. Package checks prove only that the files are well formed. [Current evidence](evidence.md) lists what is still unproven.

### The skill did not load. What now?

Start a new session, call it by name, `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code, and ask it to check its setup. [Activate it](#activate-it) explains the report.

### Does it run work in parallel?

Only when the split buys something. Parts that change the same file or schema run one after another, and a delegate writes only in its own workspace once that isolation is verified. No run has shown parts running at once, so it stays `UNVERIFIED`.

### How much context does it use?

The core skill file is about 10 KB. The agent rereads it after the host compacts the conversation and opens each reference file before the act it covers. Reliable loading is `UNVERIFIED`. SkipHow promises no fixed token cost.
