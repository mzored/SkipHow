# ADR 0007: Resolve model tiers and session continuity in host adapters

## Status

Accepted in 1.1.0. The adapters, the hook, and the deterministic checks below ship in that release.

## Date

2026-08-26

## Context

ADR 0003 defines `FAST`, `STANDARD`, and `DEEP` tiers and says the root maps them "only from capability, cost, or latency metadata exposed by the host". The [host research](../research/2026-08-26/host-routing-and-continuity.md) shows that neither Claude Code nor Codex exposes such metadata, and that the plugin ships no agent definitions. In practice every subagent inherits the owner's main model. The tiers never route anything.

Both hosts do support the controls the policy needs. Claude Code subagent definitions accept `model` with the family aliases `haiku`, `sonnet`, and `opus`, which the vendor documents as stable and recommends over versioned IDs, plus a separate `effort` field. A Claude plugin may ship those definitions under `agents/`. Codex custom agents accept `model` and `model_reasoning_effort` in `.codex/agents/*.toml`, and `[agents].default_subagent_model` sets a default. Codex plugins cannot ship agent files.

ADR 0002 and ADR 0006 forbid hooks because the retired runtime used them as part of a private execution engine. Meanwhile `long-work.md` asks the root to checkpoint "before compaction", which the model cannot foresee. Both hosts document a `SessionStart` hook with `compact` and `resume` matchers whose stdout is added to the resumed session's context. Both hosts allow a plugin to ship `hooks/hooks.json`.

The Superpowers project's measured caveat applies: the cheapest model often needs two to three times the turns and costs more in total. Routing saves money only for narrow work with a direct check.

## Decision

The shared skill keeps semantic tiers and says nothing about providers. Host adapters, and only host adapters, resolve tiers to host-native names.

### Roles

The skill defines three delegate roles. The root agent itself always inherits the owner's session model.

| Role | Tier | Work | Effort | Tools |
| --- | --- | --- | --- | --- |
| `scout` | `FAST` | Bounded read-only search, inventory, duplicate search, log and test-output extraction, fact checks with a direct answer | low | read-only |
| `builder` | `STANDARD` | Implementation, tests, and documentation for one owned scope in an isolated worktree | host default | edit and run, no remote writes |
| `reviewer` | `DEEP` | Planning an epic, unknown causes, architecture, security, build-versus-reuse judgment, independent review of a candidate | high | read-only plus running checks |

The root sends a task to a delegate only when isolation or parallelism pays for the transfer. A task that fits the current context runs in the current context. Every delegation names its role; nothing inherits by omission. After a second failure with the same cause, the root raises the role one tier or reviews the premise; after one more failure it stops and reports.

### Claude Code adapter

`plugins/skiphow/agents/scout.md`, `builder.md`, and `reviewer.md` set `model:` to `haiku`, `sonnet`, and `opus`, set `effort`, restrict `tools`, and set `isolation: worktree` for `builder`. Their bodies are short and point to the skill for policy. If an alias is unavailable in the owner's environment, the host falls back on its own; the skill treats a substituted route as `inherit` and reports it.

### Codex adapter

A Codex plugin cannot ship agents. The skill documents a one-time optional setting in the owner's `config.toml` (`[agents] default_subagent_model` and `default_subagent_reasoning_effort`) and can write `.codex/agents/scout.toml`, `builder.toml`, and `reviewer.toml` into a project when the owner asks for routing there. Those files set `model_reasoning_effort` per role and leave `model` unset unless the owner supplied one, because Codex has no stable family aliases. Without them, Codex delegates inherit the parent model and effort, which the skill reports.

### Continuity hooks

The plugin ships one `hooks/hooks.json`, read by both hosts from the default location, with `SessionStart` handlers for `startup`, `clear`, `compact`, and `resume`. Each handler is a portable shell one-liner that prints a fixed sentence and, when `.skiphow/handoff.md` exists, its last checkpoint. The startup sentence tells the session to invoke the skill for project requests, because the 1.1 receipts showed that a bare one-line bug report does not reliably trigger implicit skill selection on its own; the compact and resume sentence tells it to re-read the owner request and live state. The hook makes no network calls, reads no other files, writes nothing, and uses no plugin-specific runtime. No other hooks or events are permitted without a new ADR.

The skill's continuity rule changes from "checkpoint before compaction" to "update the handoff at every item boundary and before any long wait". The hook then re-reads it.

### Guardrails that stay

- No versioned model IDs anywhere in the package. The deterministic check keeps scanning for them and now covers `agents/` and `hooks/` too.
- No prices, no catalog, no router model.
- Model choice never widens authority. Delegates never hold GitHub credentials or perform remote writes.
- Savings claims stay `UNVERIFIED` until paired runs show them.

## Consequences

Routing becomes real on Claude Code out of the box and on Codex after one setting. The shared policy still transfers between hosts unchanged. `scripts/check.py` must allow `agents/` and `hooks/` in the plugin and verify their content. The test that forbids hooks changes to a test that permits exactly the continuity hook. ADR 0002 and ADR 0006 are amended by this ADR on those two points and otherwise stand. ADR 0003's "metadata only" mapping rule is replaced by the adapter rule.

## Rejected alternatives

### Keep waiting for host cost metadata

Neither vendor has announced it. The policy would stay inert.

### Put aliases in the shared skill

Aliases are one vendor's names. They belong in that vendor's adapter so the Codex path is not misled.

### A `PreCompact` hook that writes the handoff

The docs do not confirm that `PreCompact` output reaches the summary, and a hook cannot know the agent's current state. Writing at item boundaries is deterministic and host-independent.

### Route by turning `FAST` into the default for code

Superpowers' turn-count finding and ADR 0003's original reasoning both say no. Mutation starts at `STANDARD`.

## Evidence

- [Host routing and continuity research](../research/2026-08-26/host-routing-and-continuity.md)
- [Prior-art mechanics research](../research/2026-08-26/prior-art-mechanics.md)
- [System review](../research/2026-08-26/system-review.md)

## Revalidation triggers

Revisit when a host removes family aliases or per-agent effort, when Codex plugins can ship agent definitions, when either host exposes model cost metadata, or when paired runs show the cheap tier costs more in total on SkipHow's own scenarios.
