# SkipHow

An adaptive virtual CTO for founders and product owners using Claude Code or Codex.

Describe the product outcome in ordinary language. You keep product decisions;
SkipHow owns research, architecture, planning, implementation, review, integration,
and verification. Work stays proportional to the request. The host supplies the
model, tools, permissions, sessions, and subagents.

SkipHow also keeps the system you own small. Everything the agent adds stays, and
you pay for it in every later change. So it builds the least that delivers the
result, writes a test only for a break a user or caller would notice, moves every
caller in the repository instead of leaving a compatibility shim, and asks for independent review only
where a mistake is expensive. It removes what no longer pays for itself. Guards for
money, security, customer data, and the release path stay.

[![CI status](https://github.com/mzored/SkipHow/actions/workflows/ci.yml/badge.svg)](https://github.com/mzored/SkipHow/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/mzored/SkipHow?label=release)](https://github.com/mzored/SkipHow/releases)
[![MIT license](https://img.shields.io/github/license/mzored/SkipHow)](LICENSE)

## Is it for you?

Use SkipHow when you want the agent to own engineering through a verified result
while you decide product behavior, scope, cost, risk, privacy, and rollout. You do
not need to read code. You need to own the outcome.

If your base agent already does this reliably, another instruction layer adds little.
A specification framework fits an owner who wants to approve the development method.
A runtime orchestrator fits persistent teams, queues, scheduling, and budget enforcement.
SkipHow is an instruction layer and provides none of those runtime services.

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

Start a new session after installation. The [owner guide](docs/guide.md) covers
updates and uninstall.

## Activate it for ordinary language

Ask the installed skill to enable itself once:

```text
$skiphow Enable SkipHow as my default virtual CTO on this machine.
```

In Claude Code, use `/skiphow:skiphow` instead of `$skiphow`. The agent previews one reversible block and writes it after you confirm. Installation and activation grant no actions. The [activation guide](docs/guide.md#activate-it) covers the lifecycle and manual fallback.

Explicit invocation remains available:

```text
$skiphow The totals overlap on small screens. Find the cause and fix it.
```

## Recurring workflows

Ordinary requests need no mode. Six optional workflows share the same CTO kernel and authority boundaries.

| Skill | Requested result |
| --- | --- |
| `skiphow-bug` | Find and repair the general cause, then verify at the authorized destination |
| `skiphow-plan` | Prepare the whole scope, resolve product questions, and return a launch, with no implementation |
| `skiphow-longrun` | Deliver agreed substantial work with review scaled to consequence |
| `skiphow-deploy-ready` | Complete deferred checks, review, commits, and authorized integration |
| `skiphow-fast-fixes` | Show checked local fixes while you send feedback |
| `skiphow-simplify` | Measure the project and remove what does not pay, only when you ask |

The [workflow guide](docs/guide.md#recurring-workflows) has an example request for each.

## Authority and evidence

Answering, research, diagnosis, review, and ordinary planning are read-only. A change request permits editing and verification within its scope, and carries routine delivery through the project's established non-production workflow. Production, public releases, credentials, access, material deletion, and wider disclosure need explicit owner authorization. The [owner guide](docs/guide.md#know-what-your-request-allows) explains the boundaries.

SkipHow adds no intelligence and enforces no security boundary. Package checks prove structure and declared invariants. Current-package CTO behavior, reliable multi-agent execution, general activation reliability, and comparative benefit remain `UNVERIFIED`. See the [evidence ledger](docs/evidence.md) and the [host facts](docs/evidence.md#host-facts).

## Documentation

For owners:

- [Owner guide](docs/guide.md): install, activation, workflows, what a request allows, reports, and common questions.
- [Evidence](docs/evidence.md): which claims real runs have shown, which stay `UNVERIFIED`, and host facts.
- [Security](SECURITY.md): supported versions, the untrusted-repository profile, and private reporting.

For contributors:

- [Owner-outcome contract](docs/outcome-contract.md): what every implementation must deliver.
- [Decisions](docs/decisions.md): live decisions, why they stand, and what would reopen them.
- [Prior art](docs/prior-art.md): what SkipHow took from other projects and what it refused.
- [Contributing](.github/CONTRIBUTING.md) and [repository instructions](AGENTS.md).
- [Evaluation corpus](evals/README.md): cases, fixtures, and retained receipts.
- [Changelog](CHANGELOG.md): what changed in each release and why.

Earlier documentation lives in git history:

- [`90cfdbb`](https://github.com/mzored/SkipHow/tree/90cfdbbbf2a354973ede4d716853ce62886e2c6b) holds the documents as of 7.0.8, before they were cut to one governing copy per fact.
- [`2f72c7f`](https://github.com/mzored/SkipHow/tree/2f72c7f218f29db20421eddce6d280e0d6f52045/docs) holds the documentation as of 7.0.1.
- [`72aef45`](https://github.com/mzored/SkipHow/tree/72aef4540d30d3639a2f63af6663971345c6dc5a/docs) holds the longer ledgers through 6.3.3.
