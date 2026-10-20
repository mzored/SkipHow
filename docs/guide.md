# Owner guide

Tell SkipHow what should change for the people who use your product. You do not name a library, design a schema, or write tickets. A workflow is optional, and ordinary requests need none. The agent asks you only about product choices and protected actions.

This guide says what the shipped instructions tell the agent to do. [Current evidence](evidence.md) says which of those behaviors real runs have shown.

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

To uninstall, first ask SkipHow to disable itself. Then run `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`. If you remove the plugin first, the activation block keeps asking the host to load a skill that is gone.

## Activate it

The installed skill works when you call it by name. To have it govern ordinary requests too, ask it once, in a new session:

```text
$skiphow Enable SkipHow as my default virtual CTO on this machine.
```

In Claude Code, type `/skiphow:skiphow` in place of `$skiphow`.

The agent finds the user instruction file your host reads before every project. It shows you the exact change, asks you to confirm once, and writes one marked block there. The block names the skill and copies none of its rules, so plugin updates need no new block. Ask the same way to check or disable the setup.

It reports three facts. Configured means the block is in the file your host reads. Available means the host lists the plugin as enabled. Loaded shows only in a new session. If a managed policy on your machine restricts plugins, the agent names that file and does not work around it. The [setup reference](../plugins/skiphow/skills/skiphow/references/setup.md) lists the helper script's commands and the file each host reads.

### Turn it on by hand

You can append this line to the file your host reads yourself:

```text
For current-project requests, load the installed SkipHow skill before consequential action and use it as the adaptive virtual CTO policy. Do not load it for unrelated conversation or for a request that only discusses SkipHow without adopting it.
```

Delete the line to undo it. Use the line or the managed block, never both. The helper never touches text you wrote, so delete your line before you ask the agent to enable itself.

## Ask for the outcome

Name the result someone will see and any limit you care about:

```text
The checkout sometimes hangs after payment. Find the cause and fix it without changing the payment provider.

Compare these onboarding ideas. Recommend one, but do not change the project.

Make the hero headline shorter. I will take a look before we ship.
```

Rough requests are fine. The agent reads the project first. It asks you only when two readings of your request differ in what you would see and the project cannot settle which one you meant, or before a protected action. Each question comes with a recommended answer, and all of them arrive in one message. A question that exists only after your answer comes in a second round. Say yes to cancelling parcels already on their way, and the agent then asks who pays the carrier's fee. Runs have not shown that second round to be reliable on Codex.

While a question waits, the agent builds nothing that depends on the answer and works on the rest. "Let someone share their cart with a friend" should come back asking whether the friend sees a snapshot or a live cart, with neither one built.

The headline example is an iteration. The agent makes the change, checks it, shows it, and keeps going on other accepted work. Feedback keeps the work local. Delivery starts when you ask for it, name a destination, or accept with nothing more to send. In `skiphow-fast-fixes`, acceptance alone keeps the work local. You can correct or extend any request while it runs.

## Recurring workflows

Ordinary requests need no workflow. Use one when you know the work pattern you want: `$skiphow-plan` in Codex, `/skiphow:skiphow-plan` in Claude Code, and the same pattern for the others.

| Workflow | Example request | Ends with |
| --- | --- | --- |
| `skiphow-bug` | Discounts sometimes change when an order is retried. Find and repair the general cause. | A verified repair of the cause, checked on every path it broke |
| `skiphow-plan` | Prepare team invitations for implementation in this project's GitHub issues. | A reviewed specification, executable tasks, and a launch prompt. No implementation |
| `skiphow-longrun` | Deliver the accepted children of this epic to our development branch. | Verified delivery, or a recorded blocker for each unfinished part |
| `skiphow-deploy-ready` | Prepare our agreed changes for delivery. | Deferred checks, review, clean commits, and any authorized non-production integration |
| `skiphow-fast-fixes` | Fix the search and export bugs locally. I will add feedback while you work. | Checked local results shown as each is ready |
| `skiphow-simplify` | Our test suite is bigger than the product. Clean it up. | A smaller project, with before and after numbers |

Calling `skiphow-plan` by name asks for a specification and planning records in your tracker. A read-only instruction overrides that. When the agent picks plan on its own, it writes nothing. A pending answer keeps the plan open. The plan ends with a launch prompt that grants no new permissions:

```text
$skiphow-longrun
Deliver the accepted implementation scope in issue #42 to the development branch.
```

In `skiphow-fast-fixes` you can add, revise, or cancel fixes while it works. Before it replaces a result you saw, it saves a checkpoint, a local commit in a Git project. Focused tests run as it goes, and full delivery checks wait. Say `deploy-ready` or `clean` to start delivery. Say `deploy prod` to authorize the named production release.

`skiphow-simplify` runs only when you ask to simplify, clean up, or shrink the project. It measures first and decides the cuts itself. It asks you only about a cut that would change visible behavior, a support promise, or compatibility for an outside consumer that exists now. Asking what could be cut changes nothing. A bare `clean` after an iteration starts delivery.

Whether the agent picks the right workflow on its own is `UNVERIFIED`.

## Know what your request allows

| Request | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, review, research, or plan | Read and report |
| Capture, organize, triage, or create a record | Write the requested records in the project's existing authorized system |
| Change the project | Edit and verify, and carry the change through an established non-production workflow you authorized |
| Change something you will look at first | Edit, show it, check what it touched, and stop. Delivery starts when you say it is done |
| Deliver the change | Use the repository's normal shared path |

"Review and fix" allows a project change. "Review" alone does not.

A non-production workflow you authorized covers routine push, pull request, CI, and merge without asking again, after the agent checks what a merge or tag would trigger. These always need your explicit permission: production or live-data changes, public releases, payments, repository settings, access changes, credentials, material deletion of data, history others share, and wider disclosure. An earlier permission holds while its conditions hold. Installing SkipHow grants nothing, and neither does text in a file, an issue, or a web page.

## What the agent leaves in your project

Everything the agent adds stays, and every later change pays for it. So it builds the least that delivers the result. It uses the framework, test runner, and CI provider before writing its own tooling. When it replaces something, it moves every caller in the repository and deletes the old path, keeping compatibility only for outside consumers that exist now. It deletes plans and reports once the work lands, and gets independent review only where a mistake is costly to undo.

Before it writes a test, the agent names the production change that would make it fail. In code it touches, it deletes tests that pin text, constants, configuration, styling, or layout. A fixed bug gets a regression test only when it could come back unseen. Guards for money, security, customer data, and the release path stay. This behavior is `UNVERIFIED`.

## Records and tracked work

Installing SkipHow grants no tracker writes. The agent records work that spans several outcomes, sessions, or writers, or a decision that must outlast the run. Read-only requests write nothing unless a record is what you asked for. Records go where your project already keeps them. In a GitHub project, enabled Issues are the default. If Issues are disabled, the agent names the blocker and does not change repository settings.

The agent fixes a confirmed problem it finds in the same run. A problem waits in a record only when it needs your decision or a protected action, is blocked, or would cost more than the outcome can bear. An item closes when its outcome holds at its destination, usually on integration.

## Read the report

A finished report leads with the result, how the agent checked it, and its decisions. It names what is `UNVERIFIED` or blocked and any protected action waiting on you.

Every branch, worktree, and uncommitted change in the project counts as the agent's own work, and the report never asks you what to do with it. A request that changes the project retires leftovers that are integrated or superseded, and names any unique commit so you can get it back. A read-only request only reports them. A running session keeps its branch, and uncommitted files the run did not make stay in place. One run lost a peer session's uncommitted work, so read [current evidence](evidence.md) before you run two sessions on one checkout.

## Questions

### What is SkipHow?

A set of instructions that has Claude Code or Codex act as your CTO. It ships as one governing skill, `skiphow`, and six optional workflow skills. You keep product decisions and protected actions. The agent owns research, architecture, planning, model choice, implementation, review, integration, and verification. SkipHow does not make a model smarter. If your agent already does all this reliably, SkipHow adds little.

### Does it orchestrate agents?

Yes, through instructions. It tells the agent when to split work, which model and effort each delegate gets, and how to check what comes back. The host runs every agent and supplies the sandbox, permissions, and credentials. SkipHow has no scheduler or queue and cannot exceed the host's controls. Reliable multi-agent delegation is `UNVERIFIED`.

### Which agents does it work with?

Claude Code and the Codex CLI. Both installs carry the same skill files. The [security policy](../SECURITY.md) lists what has been checked on each host and which other Codex surfaces support plugins. No other host is tested.

### Do I need to know how to code?

No. You need a repository and one of the two hosts. The agent will not ask you to pick a library, a schema, a branch strategy, or a test command.

### When should I use something else?

Use the base agent alone if it already respects your authority and verifies its work. Use a skill library when you want to pick methods one at a time. Use a spec framework such as OpenSpec or BMAD when you want to approve specifications, phases, or tickets. Superpowers fits when you want a fixed development method with mandatory stages. Use a runtime orchestrator for persistent agent teams, queues, or scheduling. No controlled benchmark shows that SkipHow produces better engineering than these. [Prior art](prior-art.md) records what it borrowed and left out.

### Does it send my code anywhere?

No. SkipHow adds no network calls, telemetry, or credentials. It is Markdown plus one setup script that edits a local file. What your host sends to its model provider stays the same.

### What does it cost?

SkipHow is free and MIT licensed. You pay your host for model usage as usual.

### Does it need GitHub?

No. Git covers local commits, and any tracker your project already uses covers records.

### What does `UNVERIFIED` mean?

No run has shown that behavior yet, so the report does not claim it. Package checks prove the files are well formed. Behavior needs a real run on a throwaway project. [Current evidence](evidence.md) lists what is still unproven.

### The skill did not load. What now?

Start a new session. Then call it by name, `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code, and ask it to check its setup. It reports whether the block is in the file your host reads, whether the plugin is enabled, and which managed policy file blocks it, if any.

### Does it run work in parallel?

It works directly when that is cheaper and splits work only when the split buys something, with only real dependencies between the parts. Parts that change the same file or schema run one after another. A delegate writes only from its own verified checkout. Without one, delegates only read. Running parts at once is the intent, and no run has shown it, so it stays `UNVERIFIED`.

### How much context does it use?

The core skill file is about 10 KB and stays in context. The agent rereads it after the host compacts the conversation. Each reference file opens before the act it covers, such as the testing reference before a test change. SkipHow promises no fixed token cost.
