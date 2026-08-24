# <Project> <campaign> runbook

This runbook defines what the campaign must accomplish. The cto-run policy defines how it operates.

## Mission

<Describe the product outcome, why it matters now, and the observable result.>

## Coordinates

- Repository: `<repository location>`
- Base branch: `<branch>`
- Task source: `<tracker, specification, or run sheet>`
- Scope: `<issue list or range>`
- Durable run directory: `<run directory>`
- Optional target: `<target or null>`

## Non-goals

<List work this campaign must not attempt.>

## Protected actions

<List production, deployment, data, credential, privacy, financial, owner-reserved, and external actions that require explicit authorization.>

## Terminal condition

<State the exact evidence that completes the run. Include a distinct local-complete condition when remote reconciliation remains.>

## Durable paths

- `state.json`
- `journal.jsonl`
- `briefing.md`
- `decisions/`
- `evidence/`
- `receipts/`
- `FINAL.md`

## Dependency edges

<List known hard dependencies. The orchestrator rebuilds the live DAG from evidence.>

## Recovery seed

<Dated hints such as commits, active workspaces, reserved paths, and lanes. Verify every item before use.>

## Outage fallback

<Name external systems, the local work that may continue, remote actions to queue, and work that must wait.>

## Final handoff fields

<List project-specific handoff fields beyond commits, evidence, blockers, residual risks, decisions, and next actions.>
