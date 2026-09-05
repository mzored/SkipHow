Scope: this release runner. External candidate and model-session receipts are recorded separately.

| Capability | Status | Detail |
| --- | --- | --- |
| Deterministic package gate | UNVERIFIED | not run; pass --package-gate |
| Codex schema validation | PASS | validate_plugin.py |
| Claude schema validation | PASS | claude plugin validate --strict |
| Clean Codex install | UNVERIFIED | managed source policy refused the local marketplace |
| Clean Claude install | PASS | receipt claude-clean-install-2026-09-05.json |
| Explicit invocation | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Implicit activation | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Continuity/bootstrap | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Behavioral contract suite | UNVERIFIED | never run or implied by CI; the versioned summary is docs/evidence.md |
