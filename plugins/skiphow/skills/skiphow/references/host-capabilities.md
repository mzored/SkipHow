# Host capability contract

Choose mechanisms by what the current host can do, not by host or tool names. Use the simplest available capability that satisfies the request:

- `inspect_project`: read project files, instructions, and state;
- `mutate_project`: create or change project files and local state;
- `run_local_commands`: run local checks and project commands;
- `optional_external_verifier`: run a non-required host or service check when available;
- `research_external_sources`: inspect current authoritative external sources;
- `delegate_read_only`: assign bounded inspection without mutation;
- `delegate_mutable_lane`: assign one owned mutable scope;
- `fresh_independent_review`: obtain review from an agent that did not implement the candidate;
- `persist_external_work`: create or update a canonical remote record;
- `perform_protected_action`: perform an explicitly authorized protected or irreversible action.

Discover availability from the current session and repository policy. A missing convenience capability does not erase the underlying obligation. Complete bounded work sequentially when delegation is unavailable. Use local evidence when remote persistence is neither requested nor required.

Require a fresh reviewer only when repository policy or the changed surface requires independent review. If review is required but `fresh_independent_review` is unavailable, report the affected claim as `UNVERIFIED` or stop when repository policy makes it a blocker. Never substitute self-review and call it independent.

Do not emulate a missing capability by building an MCP server, App Server client, background daemon, universal controller, or new integration. Missing `perform_protected_action` stops only the protected step and requires a precise human handoff. Record limitations in campaign receipts or the final result only when they affect a material claim.

Host support claims require fresh receipts for the exact capabilities claimed. CLI discovery alone proves only that the CLI is available.
