# SkipHow

Build software without having to play CTO.

SkipHow is an open-source workflow for Codex and Claude Code. It is for solo developers and small teams who know what they want to make but do not want to manage every technical decision.

Tell it what the product should do. A Product Director decides what to build. A CTO decides how to build it. SkipHow comes back to you only when the choice belongs to the Owner.

```text
You: "Customers should be able to pause their subscription. Shape this idea."

SkipHow studies the problem, defines the first useful version,
reviews the proposal in a fresh context, and asks for approval.

You: "Approved. Build it."

The CTO chooses the implementation, delegates the work,
checks the result, and reports the evidence.
```

## Why SkipHow exists

A coding agent can write the code. That does not mean you should have to choose its libraries, settle architecture questions, split the work into tasks, or work out how to test it.

SkipHow began with a search for an existing framework that could take an owner's idea all the way to a checked result. The search turned up useful pieces. Some projects coordinated large teams of agents. Others handled product research, task routing, or code review. It did not turn up one system that answered the whole question that mattered here:

> Can the owner stay the owner while the AI takes responsibility for product and technical decisions?

SkipHow is our answer. It uses two permanent decision-making roles and brings in specialists only when the work needs them.

```text
Owner
  │  vision, taste, priority, material trade-offs
  ▼
Product Director
  │  user behavior, scope, evidence, success criteria
  ▼
CTO
  │  architecture, reuse, implementation, tests, integration
  ▼
Focused workers

Important product and technical work gets a fresh reviewer.
```

## Why not a traditional agent framework?

Long scripted workflows decide the process before they inspect the problem. SkipHow inspects first. A clear, local bug gets a short repair. Risky or ambiguous work gets research, recorded decisions, stronger checks, and durable state.

Large fixed agent teams create coordination work even when the task needs only one specialist. SkipHow keeps the permanent team small. Research, design, security, and testing are capabilities to call on, not seats that must always be filled.

Product copilots can give advice and hand the decision back to the user. SkipHow gives the Product Director room to decide. It asks the Owner about vision, audience, priority, major cost or risk, and irreversible actions. It does not ask the Owner to pick a database or testing strategy.

Company control planes are useful for sessions, budgets, tasks, and audit trails. They do not define what a good Product Director or CTO should decide. SkipHow works at that decision layer.

One more rule matters. The agent that wrote an important proposal should not be its only critic. SkipHow sends product contracts and major technical changes to a fresh reviewer.

That is the bet behind the project. Keep the permanent team small. Add process only when the work justifies it.

## Who it is for

SkipHow fits people who own a product but do not have a full product and engineering organization behind them:

- a solo developer maintaining a real product;
- a founder or domain expert who knows the customer better than the codebase;
- a small team without dedicated product and engineering leadership.

You still own the vision. SkipHow takes the technical questions off your desk and records enough evidence for you to judge the result.

## How you use it

Speak normally. You do not need to memorize commands or skill names.

### Save an idea

```text
Save an idea: let customers export a monthly activity report.
```

SkipHow saves the wording in the project's existing tracker. It does not research or expand the idea yet. If the project has no accessible tracker, it says so instead of creating a second backlog.

### Decide what to build

```text
Shape the activity report idea. Decide what the first useful version should include.
```

The Product Director reads the product, prior decisions, and available evidence. It resolves ordinary product questions, compares small viable approaches, and writes a Product Contract. A fresh reviewer checks the contract before you see the recommendation.

### Build approved work

```text
Build the approved activity report feature.
```

The CTO owns the technical plan. It checks whether to reuse maintained software, delegates focused tasks, integrates the work, and runs the checks required by the repository. Long campaigns keep their state on disk, so a wait or context loss does not erase the decisions already made.

### Fix a defect

```text
The report download fails when the account has no activity. Fix it.
```

A clear, low-risk defect takes the short path. An unclear defect gets a focused diagnosis. SkipHow creates a tracked or durable campaign only when the repair is broad, risky, or hard to verify.

## Who decides what

| Role | Decisions |
| --- | --- |
| Owner | Vision, taste, audience, priority changes, major cost or risk, protected actions, and irreversible actions |
| Product Director | What to build, why it matters, user behavior, scope, priority, non-goals, and success criteria |
| CTO | Architecture, libraries, reuse, implementation, tests, sequencing, delegation, and integration |
| Specialists | Focused research or implementation assigned by the Product Director or CTO |
| Reviewers | Independent criticism of important product and technical work |

SkipHow sends a question to the lowest role that can answer it from the evidence. If the Product Director or CTO owns the choice, the Owner does not get a questionnaire.

## What is included

Most users interact with four skills. `idea` saves a thought, `shape` makes the product decision, `develop` builds approved work, and `fix` repairs broken behavior. The `skiphow` router chooses between them from an ordinary request.

Three internal skills handle the heavier work. `diagnose` proves unclear root causes. `cto-run` manages durable technical campaigns. `github-task` manages GitHub issue and Project v2 state after another workflow decides that the work needs tracking.

## Install with Codex

Use a current Codex installation with plugin marketplaces enabled:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

The marketplace name is `skiphow`.

## Install with Claude Code

Use a current Claude Code installation with marketplace plugin commands:

```sh
claude plugin marketplace add mzored/SkipHow
claude plugin install skiphow@skiphow
```

## Run cto-run

Most users should start with an idea, a product request, or approved work. You can invoke `cto-run` directly when you already have a technical runbook. Pass it the runbook, a directory for durable state, and an optional target.

In Codex:

```text
$cto-run docs/runbooks/release.md .skiphow/runs/release-0.1.0 main
```

In Claude Code:

```text
/skiphow:cto-run docs/runbooks/release.md .skiphow/runs/release-0.1.0 main
```

The run directory stores state, decisions, evidence, receipts, and the final report. Use the same directory to resume the campaign.

## Limitations

SkipHow cannot supply product vision, access tools or accounts it has not been given, bypass repository policy, or approve protected actions. Material business choices stay with the Owner.

SkipHow runs inside Codex or Claude Code. It has no model runtime, hosted service, agent dashboard, MCP server, telemetry, remote service, credential flow, or bundled runtime.

SkipHow needs file access, command execution, task controls, Python 3, and a place to preserve the run directory. Tracker workflows also need access to the project's tracker. GitHub lifecycle support needs `git` and authenticated `gh` 2.93.0 or newer. On native Windows, Claude Code hooks use the Git Bash installed by Git for Windows.

## Design and project documentation

- [Architecture](docs/architecture.md) explains the workflows, host adapters, durable state, and release gates.
- [Changelog](CHANGELOG.md) contains release notes.

## Support policy

The project targets current Codex and Claude Code plugin workflows. A release claims host support only after a reproducible check against that exact candidate. Report defects through the repository issue templates.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change. The repository follows its [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Read [SECURITY.md](SECURITY.md) before reporting a vulnerability.

## License

SkipHow is licensed under the [MIT License](LICENSE).
