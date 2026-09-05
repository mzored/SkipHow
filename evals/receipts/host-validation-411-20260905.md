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

## External candidate checks

The local deterministic gate passed on the replacement candidate. A separate approved-Git-source Codex clean install and uninstall passed in empty host homes, comparing all 15 package files. The earlier local-source refusal above remains a result of that invocation. Exact receipts are in [host-smoke.json](../host-smoke.json) and [the approved-source capture](host-validation-411-20260905/codex-approved-git-install.json). Both host schema validators and both exact candidate installations pass. Model diagnostics concern the prior 4.1.0 payload and do not become 4.1.1 behavioral-suite observations.
