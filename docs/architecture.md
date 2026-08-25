# Current architecture

SkipHow is one portable Agent Skill for product and software work. The owner describes the outcome in ordinary language. SkipHow chooses the smallest workflow that can finish the authorized work and check the result.

The Codex and Claude manifests package the same canonical `plugins/skiphow/skills/skiphow/SKILL.md`. They adapt installation metadata, not policy. SkipHow has no custom runner, scheduler, provider bridge, verifier process, model catalog, daemon, task database, hook, MCP server, or telemetry.

The dated [research](research/2026-08-25/README.md) records the evidence behind this design. The [ADRs](decisions/README.md) record the accepted decisions.

## Request routing

The public interface is the `skiphow` skill. Four internal routes separate intent without making the owner choose a command:

- `RESPOND` handles discussion, inspection, research, review, and diagnosis-only work. It is read-only.
- `RECORD` turns ideas, bugs, questions, and feedback into persistent work records. It does not implement them.
- `DELIVER` changes the product, verifies the result, and completes authorized delivery.
- `CONTROL` reports status or applies pause, resume, narrower authority, and cancellation through the host.

Bug repair is part of `DELIVER`. Long work is an execution choice, not another route.

## Execution

A bounded task runs in the current host session. It does not need an Issue, plan artifact, subagent, branch, review, or persistent state unless the task or repository policy calls for one.

Long work uses the host's goals, background tasks, resume support, subagents, and worktrees when the installed host confirms them. The root agent owns the outcome, authority, work queue, integration, and final proof. It may parallelize independent read work. Parallel writes require separate worktrees and disjoint ownership.

SkipHow does not emulate a missing host capability. If the host cannot preserve or resume the work, the agent completes the safe bounded portion, saves the next action in GitHub or `.skiphow/handoff.md`, and reports the missing behavior as `UNVERIFIED`.

## State and recovery

Git is authoritative for code and history. GitHub Issues are authoritative for tracked work. Pull requests and checks record delivery state. The host task coordinates the active run.

Without GitHub, authorized intake appends to `.skiphow/inbox.md`. A stopped long task may use `.skiphow/handoff.md`. These files are fallbacks, not a second task system.

At a work-item boundary or before handoff, the agent appends a checkpoint with scope, current authority and later restrictions, accepted decisions, remaining queue and dependencies, tracker and exact Git state, owned resources, last external action and result, evidence, blockers, and the next safe action. After compaction or resume, it re-reads the trusted owner request and host task, repository instructions, checkpoint, Git, and GitHub before changing anything. Missing authority or ownership blocks merge and cleanup.

## Policy loading

The canonical skill contains the owner contract, mutation boundary, request routing, and completion rule. Its seven references cover intake, product decisions, delivery, diagnosis, long work, GitHub, and model routing. The host loads them only when the task needs them.

Each rule has one owner. Host manifests do not copy it. This keeps routine requests short and makes policy changes reviewable.

## Model selection

Shared policy uses `FAST`, `STANDARD`, and `DEEP` capability tiers. It contains no provider model IDs. The root chooses a concrete subagent route only from current host metadata; otherwise it inherits the current model and marks selection `UNVERIFIED`. Model capability and reasoning effort are separate decisions.

The root agent and integrator inherit the owner's main model. `FAST` is limited to bounded read-only work with direct checks. Normal code mutation starts at `STANDARD`. `DEEP` handles high-judgment work and independent review when the cost of an error warrants it. See [model routing](model-routing.md).

## Authority and completion

The owner's words and repository policy set the mutation boundary. Read-only work cannot create files, Issues, branches, or remote state. A request to save information permits the named record. A request to fix or implement permits project changes, checks, and one deduplicated record for each material independent finding. It does not permit implementing or reprioritizing that finding. An explicit end-to-end or unattended request also permits guarded merge and cleanup for that scope.

Goals and subagents do not widen permissions. SkipHow never bypasses branch protection. It removes only clean owned worktrees and branches whose exact changes GitHub confirms as merged.

Completion follows fresh evidence for the final state, not an agent's success claim. Missing evidence remains `UNVERIFIED`. A material finding outside the request is fixed when it blocks the task, saved after a duplicate search when independent, or reported without persistence during read-only work.
