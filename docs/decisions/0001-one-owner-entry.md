# ADR 0001: Use one owner-facing SkipHow skill

## Status

Accepted

## Date

2026-08-25

## Context

SkipHow is for product owners who can describe the outcome they want but should not have to choose an engineering process. Separate commands for bugs, ideas, technical direction, and unattended work make the owner learn SkipHow's internal categories. They also invite each command to acquire its own policy and documentation.

The hosts do not share one command syntax. Codex and Claude can both install Agent Skills, but their explicit invocation syntax differs. A product interface built around slash commands would expose that difference and make the common path harder to explain.

The system still needs to distinguish discussion from persistence and code changes. That distinction determines authority. It does not need to become a menu shown to the owner.

## Decision

SkipHow has one public skill named `skiphow`. The owner describes work in ordinary language. Hosts may select the skill implicitly. Explicit host syntax remains a documented fallback, not a set of product commands.

The skill maps each request to one internal route:

- `RESPOND` answers, discusses, evaluates, or researches without changing project or external state.
- `RECORD` saves ideas, bugs, questions, and other product signals. It does not start implementation unless the owner also asks for delivery.
- `DELIVER` implements a change or fixes a problem, verifies the result, and completes the authorized delivery steps.
- `CONTROL` reports status or handles pause, resume, cancellation, and changed limits for host-managed long work.

Bug repair is a form of `DELIVER`. Long-running work is an execution choice within a route. Neither needs a separate public command.

SkipHow does not add public `/fix`, `/cto`, `/idea`, or `/automode` commands. It does not ask the owner to chain an intake command, a planning command, and an execution command.

Mutation authority comes from the owner's words and repository policy. Requests such as "discuss" and "research" stay read-only. Requests such as "save" permit persistence. Requests such as "fix", "implement", and "complete these issues end-to-end" permit the corresponding delivery work. The agent owns technical choices unless a decision changes product behavior, scope, cost, risk, rollout, privacy, or requires a protected action.

## Consequences

- The README can teach one interaction pattern with concrete examples.
- The canonical `SKILL.md` carries the routing and authority rules. Detailed methods load from references only when needed.
- Codex and Claude manifests must point to the same skill payload. Host wrappers must not copy policy.
- Internal route names may appear in technical documentation and tests, but they are not user-facing modes.
- When a request does not grant mutation clearly, SkipHow uses the read-only route and states what would require authority.
- Hosts that cannot select the skill implicitly require their own explicit invocation syntax. SkipHow documents this as a host difference rather than inventing a portable command that does not exist.

## Rejected alternatives

### Separate commands by task type

Commands such as `/fix`, `/idea`, `/cto`, and `/automode` would make owners classify work before SkipHow has inspected it. They would also duplicate shared rules across several entry points.

### One skill with visible workflow modes

Asking the owner to choose direct, tracked, or campaign mode exposes an execution choice that the agent can derive from task size, dependencies, and host capabilities.

### Runner commands as the main interface

A sequence based on setup, run IDs, verification files, and execute commands is an operator interface. It does not fit the product-owner workflow SkipHow is meant to support.

## Evidence

- [Product and UX research](../research/2026-08-25/product-and-ux.md)
- [Host capability research](../research/2026-08-25/host-capabilities.md)
- [Prior-art research](../research/2026-08-25/prior-art.md)

## Revalidation triggers

Revisit this decision if any of the following occurs:

- repeated evaluations show that ordinary-language routing causes material unauthorized actions or missed outcomes;
- a supported host cannot load one canonical skill without copied policy;
- owners repeatedly need a distinct command because natural language cannot express a protected authority boundary;
- a new portable Agent Skills standard defines one explicit invocation syntax across supported hosts.
