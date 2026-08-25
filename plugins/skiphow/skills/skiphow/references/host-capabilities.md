# Host capability contract

Choose mechanisms by capability, not host or tool name. Discover availability from the current session and repository policy.

- `inspect_project`: read project files, instructions, and state;
- `mutate_project`: create or change project files and local state;
- `run_local_commands`: run local checks and project commands;
- `optional_external_verifier`: run a non-required host or service check when available;
- `research_external_sources`: inspect current authoritative sources;
- `delegate_read_only`: assign bounded inspection without mutation;
- `delegate_mutable_lane`: assign one owned mutable scope;
- `fresh_independent_review`: obtain review from an agent that did not implement the candidate;
- `persist_external_work`: create or update a canonical remote record;
- `perform_protected_action`: perform an explicitly authorized protected or irreversible action;
- `durable_execution`: run installed SkipHow coordination that can preserve state, resume, wait, reconcile, and stop outside one model session.

Use the simplest available capability that satisfies the request. A missing convenience capability does not erase the obligation; complete bounded work sequentially when safe. Require a fresh reviewer only when repository policy or the changed surface requires one. If required independent review is unavailable, mark the affected claim `UNVERIFIED` or stop when policy makes it a blocker. Never call self-review independent.

Do not build an ad hoc App Server client, daemon, controller, or integration inside an unrelated task. When durability is required, use the installed SkipHow runner and its provider adapters. If `durable_execution` is unavailable, bounded work may continue in-session; background, recovery, and resume claims remain `UNVERIFIED`.

Missing `perform_protected_action` stops only that step and requires a precise human handoff. Record host limits only when they affect a material claim. Host support claims require fresh evidence for the exact capabilities claimed; command discovery alone proves only that a command is available.
