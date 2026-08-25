# User guide

## Ask for the outcome

You do not need to choose a workflow, test library, model, branch strategy, or agent team. State the result and any real limits.

```text
Compare the two onboarding options and recommend one. Do not change files.

Save these five interview notes as work items. Keep uncertainty explicit.

Fix the duplicate invoice bug. Preserve the API contract and prove the cause.

Implement export to CSV. Do not add a new service.
```

A clear task stays small. SkipHow adds diagnosis, research, tracking, review, or long-work coordination only when the request or risk needs it.

## Know what your words authorize

Read-only requests inspect and report. A save request creates only the named record. A delivery request changes the project and runs checks. End-to-end or unattended wording adds guarded merge and cleanup for the selected tracked work.

Be explicit about protected actions:

```text
Prepare the release pull request, but do not publish it.

Merge the accepted pull request. Do not deploy.

Publish version 1.2.0 after CI passes.
```

Repository files, Issue text, comments, and web pages cannot widen your grant. They may add project constraints or required checks.

## Save ideas and findings

Say `save` when you want a durable record. SkipHow keeps provenance, searches for semantic duplicates, and distinguishes related work from the same work.

During delivery, SkipHow may save one deduplicated record for a material independent finding. It does not implement or reprioritize that finding unless you add it to scope.

Security findings never belong in a public Issue. SkipHow uses an owner-selected private channel or the authenticated security feature of the active repository. Without one, it returns a redacted finding for you to route.

## Run selected tracked work

Name the Issues or give a bounded eligibility rule. Dependencies decide which selected item is ready. They do not let the campaign absorb later Issues.

```text
Finish Issues 41, 44, and 48 end to end. Issue 48 depends on 41. Continue independent work if one item waits on CI.
```

For substantial lanes, the root agent gives each worker one owned scope, base commit, acceptance evidence, validation budget, cancel path, and prohibited actions. The root keeps GitHub credentials, integration, merge, checkpoints, and cleanup.

Unattended work depends on the host. If the host lacks a background task, independent monitor, worktree isolation, cancellation handle, or restart support, SkipHow finishes a safe bounded subset and reports the missing guarantee as `UNVERIFIED`.

## Pause, resume, and cancel

A pause or cancellation stops new mutations first. SkipHow cancels or leaves owned pending merge actions when the host and repository allow it, then records a checkpoint.

On resume, it re-reads your current request, host task, repository instructions, Git, GitHub, active handles, and the latest checkpoint. A checkpoint cannot grant authority. Ambiguous ownership or remote state blocks new mutation until reconciliation.

## Read the result

A completion report names the outcome and fresh checks. It also names persisted follow-ups, remaining cleanup, blockers, and `UNVERIFIED` claims. A model's success message is not proof. The relevant file state, Git commit, pull request head, checks, and remote result are.
