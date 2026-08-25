# Host routing and continuity research

## Record

- Reviewed on 2026-08-26.
- Local hosts: Claude Code `2.1.246`, Codex CLI `0.149.1`.
- Sources: current vendor documentation fetched on the review date. URLs are listed at the end.
- Scope: how each host chooses a model per subagent, what a plugin may ship, how a session survives compaction, and how an owner starts an unattended run.

This note exists because the 1.0 policy says the root maps `FAST`, `STANDARD`, and `DEEP` "only from capability, cost, or latency metadata exposed by the host". Neither host exposes such metadata. The practical result is that every subagent inherits the root model and the tiers never do anything. The facts below show what the hosts do expose, so the next release can route for real without naming versioned model IDs.

## Claude Code

### Subagents

A subagent is a Markdown file with YAML frontmatter. Files live in the user agents directory, `.claude/agents/`, managed settings, the `--agents` flag, or a plugin's `agents/` directory.

Frontmatter fields the docs list: `name`, `description` (both required), `model`, `tools`, `disallowedTools`, `permissionMode`, `maxTurns`, `memory`, `skills`, `mcpServers`, `hooks`, `isolation`, `background`, `effort`, `color`, `initialPrompt`.

`model` accepts `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit` (the default). The model-config page calls the family aliases stable and recommends them over full IDs. Alias resolution is per provider (Anthropic API, Bedrock, Vertex, Foundry) and can be overridden with `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, and `ANTHROPIC_DEFAULT_HAIKU_MODEL`.

Resolution order for a subagent's model: `CLAUDE_CODE_SUBAGENT_MODEL` environment variable, then the per-invocation `model` parameter, then the definition's `model` field, then the main conversation's model.

`effort` accepts `low`, `medium`, `high`, `xhigh`, `max`. Models that do not support a level fall back to the highest they support. Capability and effort are separate controls, which is what ADR 0003 assumed.

Built-in `Explore` and `Plan` agents inherit the parent model, skip CLAUDE.md and git status, and are read-only. `isolation: worktree` gives a subagent a temporary worktree that the host removes when it made no changes. Background subagents keep Read, Grep, Glob, Bash, Edit, Write, WebFetch, WebSearch, Skill, and MCP tools but lose interactive tools. Nested delegation is allowed to 3 levels. Concurrency defaults to 20.

`permissionMode` in a subagent cannot widen the parent's mode. If the parent runs `bypassPermissions`, `acceptEdits`, or `auto`, that wins.

### Plugins and hooks

A plugin may ship `skills/`, `agents/`, `commands/`, `hooks/hooks.json`, and MCP servers. Plugin hooks merge with user and project hooks when the plugin is enabled. The docs describe no separate consent dialog for plugin hooks.

Hook events include `SessionStart` (matchers `startup`, `resume`, `clear`, `compact`, `fork`), `PreCompact` (matchers `manual`, `auto`), `PostCompact`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, and `UserPromptSubmit`. For `SessionStart` and `UserPromptSubmit`, plain-text stdout from a command hook is added as context the model can read. JSON output may use `additionalContext`. `PreCompact` can block compaction with exit code 2; the docs do not say that its stdout reaches the summary.

Hook types: `command`, `http`, `mcp_tool`, `prompt`, and `agent`. Prompt and agent hooks default to a fast model.

### Context and compaction

The model is not told how much context remains. `/context` is a user command. Auto-compaction triggers at the model window by default (1M for Fable 5, Sonnet 5, and Opus 5; 200K for Opus 4.6 and Sonnet 4.6) and can be changed with `/autocompact`, `--autocompact`, `autoCompactWindow` in settings, or `CLAUDE_CODE_AUTO_COMPACT_WINDOW`. Resume restores an active `/goal`. Subagent transcripts persist separately from the main conversation.

Conclusion for SkipHow: the skill cannot predict compaction. Continuity must come from writing state at natural boundaries and from a `SessionStart` hook with the `compact` and `resume` matchers that tells the resumed session where the handoff is.

### Unattended runs

`claude -p "<request>"` runs headless. Relevant flags: `--permission-mode` (`default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`), `--max-budget-usd`, `--max-turns`, `--allowedTools`, `--effort`, `--worktree`, `--continue`, `--resume`, `--autocompact`. `auto` mode uses a classifier and still prompts for risky actions. Goal mode (`/goal`) runs an evaluator after each turn until the stated condition holds. Background bash jobs are killed about five seconds after a `-p` result; subagents are waited for.

## Codex CLI

### Subagents

Custom agents are TOML files in the user agents directory or `.codex/agents/`. Required fields: `name`, `description`, `developer_instructions`. Optional: `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`. A value set in the agent file wins; otherwise the agent inherits the parent's model and effort.

Global settings under `[agents]`: `enabled`, `default_subagent_model`, `default_subagent_reasoning_effort`, `max_concurrent_threads_per_session`. The docs recommend a demanding model for ambiguous multi-step agents, a faster model for exploration and read-heavy scans, and a small model for narrow repeatable work. Those recommendations are written as current product names, not stable aliases, so they cannot appear in a portable skill.

The docs do not say that a plugin or skill can ship agent definitions. A plugin can ship skills, MCP servers, apps, and hooks.

### Hooks

Hooks are stable in this CLI version. Events: `SessionStart`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `PreToolUse`, `PostToolUse`, `PermissionRequest`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `Stop`. Locations: the user `hooks.json`, the user `config.toml`, `<repo>/.codex/hooks.json`, `<repo>/.codex/config.toml`, and a plugin's manifest or default `hooks/hooks.json`. For `SessionStart` and `UserPromptSubmit`, plain stdout is added as developer context. Users can disable all hooks with `[features] hooks = false`.

### Compaction and unattended runs

Auto-compaction uses `model_auto_compact_token_limit`. `codex resume` continues a session. `codex exec` runs non-interactively with `--sandbox <mode>`, `--approve-for-me`, `--ephemeral`, `--output-last-message`, and `--json`. The local feature registry lists `goals`, `multi_agent`, `plugins`, and `hooks` as stable.

## Machine-readable model metadata

Neither host documents a runtime API that returns model capability or price. Codex ships an internal `models.json` and caches a models cache in the user profile, but that is an implementation detail. Claude Code exposes aliases, not prices. Any design that waits for cost metadata will wait indefinitely.

## Published orchestration guidance

Anthropic's "Building effective agents" describes routing as a workflow pattern and gives the example of sending easy questions to a smaller model and hard ones to a stronger one. It describes orchestrator-workers as the pattern for work whose subtasks cannot be predicted in advance.

Anthropic's multi-agent research write-up used a stronger lead model with lighter subagents, reported a 90.2% improvement over a single agent on its internal evaluation, and warned that agents use roughly 4x the tokens of a chat and multi-agent systems roughly 15x. It recommends that each subagent brief state the objective, output format, tools, and boundaries.

Anthropic's context-engineering note names "context rot" (recall drops as context grows) and lists three remedies: compaction, structured notes outside the context, and subagents that return a short summary. It advises keeping decisions, unresolved bugs, and implementation details while discarding stale tool output.

OpenAI's Codex subagent guide says the same about cost: each subagent does its own model and tool work, so parallel agents consume more tokens than one agent. It recommends parallel agents first for read-heavy exploration, tests, triage, and summarization.

Superpowers' subagent-driven-development skill adds the practical caveat that matters most: the cheapest model often takes two to three times the turns and costs more in total. Turn count, not price per token, decides the bill. It also warns that omitting the model field silently inherits the parent's tier.

## What this means for SkipHow

1. Both hosts support per-subagent model and effort. Claude Code lets a plugin ship those definitions. Codex does not, so the Codex path is a documented one-time `[agents]` setting or project `.codex/agents/` files that SkipHow can write on request.
2. Family aliases (`haiku`, `sonnet`, `opus`) are the vendor-recommended stable names. Using them in a host adapter does not violate the "no model catalog" rule. Versioned IDs still must not appear anywhere in the package.
3. The skill cannot see compaction coming. Write the handoff at every item boundary and ship a `SessionStart` hook (`compact`, `resume`) on both hosts that points the resumed session at the handoff. That is the only reliable continuity mechanism the hosts offer.
4. Subagents cost more tokens, not fewer. Delegate for isolation and parallel reads, not as a habit. Route the cheap tier only to bounded read work with a direct check.

## Sources

- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/plugins.md
- https://code.claude.com/docs/en/hooks.md
- https://code.claude.com/docs/en/model-config.md
- https://code.claude.com/docs/en/context-window.md
- https://code.claude.com/docs/en/headless.md
- https://code.claude.com/docs/en/goal.md
- https://code.claude.com/docs/en/skills.md
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/plugins
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://www.anthropic.com/research/building-effective-agents
- https://www.anthropic.com/engineering/built-multi-agent-research-system
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md
