# State contract

The run directory is durable state, not a substitute for the repository, tracker, or CI. Write plain JSON, JSON Lines, and Markdown so a later session can inspect and reconcile it.

`state.json` is the root-owned machine-readable record. Write it atomically. It includes:

```json
{
  "current_target": "string or null",
  "repository_commit": "exact commit identifier",
  "active_lanes": [{"task": "id", "owner": "id", "scope": ["path"], "base_commit": "id", "status": "active"}],
  "blocked_lanes": [{"task": "id", "status": "blocked", "blocker": "reason", "next_action": "action"}],
  "decisions": [{"id": "ADR-1", "verdict": "ADOPT|INTEGRATE|BUILD|DEFER|SPIKE", "evidence": "path"}],
  "evidence": [{"task": "id", "commit": "id", "path": "evidence/task/commit/"}],
  "product_acceptance": [{"product_contract_revision": "exact revision", "candidate_commit": "exact commit identifier", "status": "accepted|returned", "receipt": "receipts/product-acceptance/item.json", "evidence": "path", "reviewer": "id", "at": "timestamp"}],
  "last_reconciliation": {"at": "timestamp", "summary": "result", "sources": ["repository", "tracker", "CI"]}
}
```

Keep the task DAG, leases, ownership, path reservations, attempts, command budgets, baseline durations, contract hashes, exact commits, and recovery notes in `state.json` or linked records. The root updates global state. Workers write only scoped receipts.

`journal.jsonl` is append-only. Each line is one JSON object with `at`, `task`, `event`, `status`, and `summary`. It may also carry `evidence`, `commit`, `next_action`, `duration`, `failure_signature`, and `handle`.

```json
{"at":"timestamp","task":"task-id","event":"lane-dispatched","status":"active","summary":"scope reserved","evidence":"receipts/task-id.json"}
```

`briefing.md` records the authority map, source hashes, decisions, exact source locations, open questions, and corrections discovered during the run. Keep it concise and queryable. Split it into indexed parts if it grows beyond a practical working size.

Use `decisions/` for ADRs, `evidence/<task>/<commit>/` for raw check output, and `receipts/<task>.json` for a worker result with status, base and head commits, evidence, blocker, next action, and `reuse_check` as the verdict or `n/a`. Store Product Director acceptance at `receipts/product-acceptance/<item>.json`. Each acceptance receipt records the Product Contract revision, exact candidate commit, `accepted` or `returned` status, evidence location, reviewer, timestamp, and a concrete mismatch when returned. Use `n/a` only when the build-versus-reuse gate did not apply. `FINAL.md` is the final reconciliation and handoff.
