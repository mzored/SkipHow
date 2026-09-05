Scope: this release runner. External candidate and model-session receipts are recorded separately.

| Capability | Status | Detail |
| --- | --- | --- |
| Deterministic package gate | UNVERIFIED | not run; pass --package-gate |
| Codex schema validation | UNVERIFIED | Codex plugin validator unavailable |
| Claude schema validation | PASS | claude plugin validate --strict |
| Clean Codex install | UNVERIFIED | managed source policy refused the local marketplace |
| Clean Claude install | PASS | receipt claude-clean-install-2026-09-05.json |
| Explicit invocation | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Implicit activation | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Continuity/bootstrap | UNVERIFIED | not run by the release runner; external model-session evidence is recorded separately |
| Behavioral contract suite | UNVERIFIED | never run or implied by CI; the versioned summary is docs/evidence.md |

## External candidate checks

The local deterministic gate passed on the 4.2.0 candidate. Claude Code 2.1.261
installed all seventeen regular files byte for byte in an empty configuration
directory and uninstalled them; the receipt is in this directory. The Codex row
above records the refusal of a local marketplace by the machine's managed source
policy. Separately, the exact 4.2.0 package was installed into an isolated Codex
home from the approved Git marketplace source, compared byte for byte against the
committed package, exercised in three bounded sessions, and removed; those
receipts are in [`isolated-host-420-20260906/`](isolated-host-420-20260906/README.md)
and the ledger cells in [`../host-smoke.json`](../host-smoke.json) cite them. The
Codex plugin validator was unavailable on this machine and runs in CI.
