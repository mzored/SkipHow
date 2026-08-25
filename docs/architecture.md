# Accepted target architecture

This document describes the architecture accepted for Issue #15. It becomes the current product architecture when that issue removes the custom runner and legacy skill tree.

SkipHow will be one portable Agent Skill for product owners. It will translate a request into the smallest workflow that can finish the work and prove the result. It will not be a runner, scheduler, task database, or provider bridge.

Host manifests install the same canonical `SKILL.md`. They may adapt installation and capability names, but they must not copy policy. The public interface is ordinary language through the `skiphow` skill.

## Execution paths

Bounded work runs in the current host session. A direct request does not need an Issue, branch, review, subagent, or persistent artifact unless the result or repository policy requires one. Risk changes authority and evidence requirements. It does not make ceremony mandatory.

Long work uses the host's goals, background tasks, resume support, subagents, and worktrees. The root agent keeps the requested outcome, scope, authority, and integration responsibility. It may parallelize independent read-only work. Parallel mutations require separate host-managed worktrees with disjoint ownership.

SkipHow does not emulate missing host features. Without background or resume support, it completes the safe sequential portion, saves a handoff in the canonical work record, and reports unattended continuation as `UNVERIFIED`.

## State and recovery

Git is authoritative for code and history. When GitHub is connected, Issues define tracked work, pull requests record delivery, and checks record remote verification. Host task state coordinates the active run. SkipHow does not maintain a second task database.

Without GitHub, captured product signals use the append-only `.skiphow/inbox.md`. Long work that must stop uses `.skiphow/handoff.md`. These files are fallbacks, not mirrors of GitHub.

At an Issue boundary, the agent updates the Issue or pull request with completed evidence, open findings, and the next action. After compaction or resume, it reconstructs the run from Git, GitHub, the host task, and any local fallback file. It does not require the full transcript.

## Progressive policy

`SKILL.md` contains the owner contract, authority rules, routing, and completion standard. It stays short enough to load on every request. Detailed instructions live in references and load only when the request needs them.

References may cover intake, product decisions, delivery, diagnosis, long work, GitHub, and model routing. Each rule has one canonical owner. Host adapters translate capabilities and syntax only.

## Model roles

Core policy uses semantic roles instead of model IDs:

- `FAST` handles bounded read-only search, inventory, extraction, and fact checks.
- `STANDARD` handles implementation, debugging, tests, and documentation.
- `DEEP` handles product shaping, architecture, security, unknown causes, reuse research, integration, and independent review when the risk warrants it.

The host maps each role to a current available model. The root agent and integrator inherit the user's main model. A cheap subagent does not receive normal code mutation by default. SkipHow does not call a separate router model.

Model role and reasoning effort remain separate choices. A transient failure keeps the same route. Repeated reasoning failure may increase effort or model role at a checkpoint. A mutable lane does not downgrade midway through its work. If the host cannot select a model role, the task inherits the current model and any claimed cost saving stays `UNVERIFIED`.

## Authority and delivery

Discussion and research are read-only. Requests to save work authorize persistence. Requests to fix or implement authorize ordinary repository changes and verification. End-to-end or unattended requests also authorize merge and cleanup when repository rules, required checks, required reviews, and the exact pull request head permit them.

SkipHow never bypasses branch protection. It removes only clean worktrees and owned branches whose changes are merged. Product choices, production actions, credentials, payments, privacy changes, public release, and irreversible actions still require clear authority.

GitHub delivery must reconcile remote state before every protected action and confirm the resulting state afterward. A small untracked change may stay on the direct path when repository policy allows it.

## Evidence and findings

Completion follows the changed behavior, not a model's claim. The agent uses the strongest practical evidence available for the exact final state. Local deterministic checks, remote checks, review, package validation, and live evaluation are distinct evidence types. Missing evidence stays `UNVERIFIED`.

Material findings outside the current scope cannot disappear into the transcript. A blocking or inseparable defect joins the current work. An independent verified defect goes to the canonical tracker after a duplicate search. Uncertain findings become `NEEDS_RESEARCH`. Read-only work reports a ready work item but does not persist it without authority.

Package support and behavior support are separate claims. A manifest installation check proves packaging only. Long-run recovery, model routing savings, and end-to-end GitHub delivery require fresh outcome evidence on each claimed host.
