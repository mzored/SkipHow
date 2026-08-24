# State contract

The run directory is durable state, not a substitute for the repository, tracker, or CI. Write plain JSON, JSON Lines, and Markdown so a later session can inspect and reconcile it.

`state.json` is the root-owned machine-readable record. Write it atomically. It includes:

```json
{
  "current_target": "string or null",
  "current_state": {"kind": "git-commit|working-tree|deployment|artifact|other", "identity": "exact identifier"},
  "active_lanes": [{"task": "id", "owner": "id", "scope": ["path"], "base_identity": "id", "status": "active"}],
  "blocked_lanes": [{"task": "id", "status": "blocked", "blocker": "reason", "next_action": "action"}],
  "not_yet_specified": [{"area": "in-scope uncertainty", "revisit_after": ["task-id"]}],
  "decisions": [{"id": "ADR-1", "verdict": "ADOPT|INTEGRATE|BUILD|DEFER|SPIKE", "evidence": "path"}],
  "evidence": [{"task": "id", "state_identity": "id", "path": "evidence/task/state-identity/"}],
  "findings": [{"id": "finding-id", "summary": "material finding", "disposition": "RESOLVED|PERSISTED|DUPLICATE|DISMISSED", "canonical_reference": "tracker reference or null", "evidence": "path", "reason": "disposition reason"}],
  "last_reconciliation": {"at": "timestamp", "summary": "result", "sources": ["repository", "tracker", "CI"]}
}
```

Keep only fields used by the campaign. Add the concrete task DAG, native dependency edges, leases, path reservations, attempts, command budgets, contract hashes, exact state identities, product acceptance, or recovery notes when the run needs them. Keep ambiguity that cannot yet be phrased as executable work in `not_yet_specified`, not speculative lanes or tracker items. For Git delivery these identities are commits. The root updates global state. Workers write only scoped receipts.

When resuming state written before the final-state identity contract, interpret `repository_commit`, `base_commit`, `commit`, and `candidate_commit` fields as Git identities. Preserve the append-only journal and normalize those fields to `current_state`, `base_identity`, or `state_identity` on the next root-owned atomic write. Record the migration in `journal.jsonl`.

`journal.jsonl` is append-only. Each line is one JSON object with `at`, `task`, `event`, `status`, and `summary`. It may also carry `evidence`, `state_identity`, `next_action`, `duration`, `failure_signature`, and `handle`.

```json
{"at":"timestamp","task":"task-id","event":"lane-dispatched","status":"active","summary":"scope reserved","evidence":"receipts/task-id.json"}
```

`briefing.md` records the authority map, source hashes, decisions, exact source locations, open questions, and corrections discovered during the run. Keep it concise and queryable. Split it into indexed parts if it grows beyond a practical working size.

Create `decisions/`, `evidence/`, and `receipts/` only when the first corresponding artifact exists. A worker receipt contains status, base and final identities, evidence, blocker, and next action. Add `reuse_check` only when the task made a dependency or subsystem decision. Keep each material finding in `state.json` until it has a terminal disposition. Persisted and duplicate findings include their canonical tracker reference; resolved and dismissed findings include their evidence or reason.

Store product acceptance only when an extended decision or repository policy requires it. Its receipt records the decision revision, delivered-state identity, status, evidence, reviewer, timestamp, and a concrete mismatch when returned. A carried-forward receipt also records its basis and reviewed delta. Generate `FINAL.md` from the reconciled state when the campaign ends.
