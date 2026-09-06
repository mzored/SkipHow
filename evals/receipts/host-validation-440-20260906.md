Scope: this release runner. External candidate and model-session receipts are recorded separately.

| Capability | Status | Detail |
| --- | --- | --- |
| Deterministic package gate | UNVERIFIED | not run; pass --package-gate |
| Codex schema validation | UNVERIFIED | Codex plugin validator unavailable |
| Claude schema validation | PASS | claude plugin validate --strict |
| Clean Codex install | UNVERIFIED | managed source policy refused the local marketplace |
| Clean Claude install | PASS | receipt claude-clean-install-2026-09-06.json |
| Explicit invocation | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Implicit activation | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Continuity/bootstrap | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Behavioral contract suite | UNVERIFIED | never run or implied by CI; the versioned summary is docs/evidence.md |

## External candidate checks

The local deterministic gate passed on the 4.4.0 candidate at `6ebe0b4`. Claude Code
2.1.263 installed all seventeen regular files byte for byte in an empty configuration
directory (payload `5163a3c6…`) and uninstalled them; the receipt is in this
directory. The Codex row above records the refusal of a local marketplace by the
machine's managed source policy; the Codex receipt file in this directory retains
that refusal. No model session ran on 4.4.0; the ledger cells in
[`../host-smoke.json`](../host-smoke.json) record only the Claude install and
uninstall facts, and every Codex cell and every other Claude cell stays
`UNVERIFIED`. The Codex plugin validator was unavailable on this machine and runs
in CI.
