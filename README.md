# SkipHow

An adaptive virtual CTO for founders and product owners using Claude Code or Codex.

Describe the product outcome in ordinary language. You keep product decisions;
SkipHow owns research, architecture, planning, implementation, review, integration,
and verification. Work stays proportional to the request. The host supplies the
model, tools, permissions, sessions, and subagents.

[![CI status](https://github.com/mzored/SkipHow/actions/workflows/ci.yml/badge.svg)](https://github.com/mzored/SkipHow/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/mzored/SkipHow?label=release)](https://github.com/mzored/SkipHow/releases)
[![MIT license](https://img.shields.io/github/license/mzored/SkipHow)](LICENSE)

## Is it for you?

Use SkipHow when you want the agent to own engineering through a verified result
while you decide product behavior, scope, cost, risk, privacy, and rollout. Technical
fluency does not matter; ownership of the outcome does.

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

In Claude Code, use `/skiphow:skiphow` instead of `$skiphow`. The agent resolves
the trusted instruction file your host reads, previews one reversible block, and
writes it after confirmation. Configured, available, and loaded are separate facts;
loading is only visible in a fresh session. Installation and activation grant no
actions. The [activation guide](docs/guide.md#activate-it) explains the lifecycle
and manual fallback.

Explicit invocation remains available:

```text
$skiphow The totals overlap on small screens. Find the cause and fix it.
```

## Recurring workflows

Ordinary project requests need no mode. Optional workflows share the same CTO
kernel, authority boundaries, and internal references.

| Skill | Requested result |
| --- | --- |
| `skiphow-bug` | Find and repair the general cause, then verify at the authorized destination |
| `skiphow-plan` | Prepare the whole scope, resolve product questions, review executable tasks, and return a launch; no implementation |
| `skiphow-longrun` | Deliver agreed substantial work with coordinated implementation and independent review |
| `skiphow-deploy-ready` | Complete deferred checks, review, commits, and authorized integration |
| `skiphow-fast-fixes` | Show checked local fixes while you send feedback; delivery starts when requested |

Use `$skiphow-plan` in Codex or `/skiphow:skiphow-plan` in Claude Code, with the
same naming pattern for the other workflows. The [workflow guide](docs/guide.md#recurring-workflows)
covers examples, planning readiness, feedback, and delivery boundaries.

## Authority and evidence

Answering, research, diagnosis, review, and ordinary planning are read-only. A change
request permits editing and verification within its scope. Applicable authorization
can cover routine shared delivery; production, public releases, credentials, access,
material deletion, and wider disclosure need explicit owner authorization. The
[owner guide](docs/guide.md#know-what-your-request-allows) explains the boundaries.

SkipHow adds no intelligence and enforces no security boundary. Package checks
prove structure and declared invariants. Identified historical runs show bounded
loading, task, and delivery observations; current-package CTO behavior, reliable
multi-agent execution, general activation reliability, and comparative benefit
remain `UNVERIFIED`. See the [evidence ledger](docs/evidence.md) and the
[dated host-support matrix](SECURITY.md#host-support-as-of-2026-09-06).

## Documentation

Start with the [documentation index and repository map](docs/README.md).
It links the owner guide, FAQ, product contract, design, current decisions, prior
art, evaluation corpus, and historical archives.

For development, read [Contributing](.github/CONTRIBUTING.md). Report vulnerabilities
through the [private security process](SECURITY.md). Release notes are in the
[changelog](CHANGELOG.md).
