# Repository instructions

## Source material

Use current primary documentation for host CLI behavior, supported plugin formats, and security guidance. Do not preserve stale commands because they appear in an old issue or summary.

## Claims and verification

Run the smallest relevant deterministic check before making a claim about a change. Run the repository test suite and `git diff --check` before completion. Record the command and result when a change needs host support evidence.

## Portable packaging

Do not add personal paths, home-directory assumptions, private helpers, credentials, telemetry, MCP servers, hooks, or bundled runtimes without an approved product decision. Keep one canonical workflow. Adapters may point to it but must not copy its policy.

Changes to packaging or `cto-run` require validation in both Codex and Claude Code. Support claims require fresh evidence for the exact candidate commit.
