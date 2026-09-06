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

The local deterministic gate passed on the 4.3.0 candidate. Claude Code 2.1.263
installed all seventeen regular files byte for byte in an empty configuration
directory and uninstalled them; the receipt is in this directory. The Codex row
above records the refusal of a local marketplace by the machine's managed source
policy. Separately, after the change set merged as `da1154c`, the exact 4.3.0
package was installed into an isolated Codex home (native login only, `CODEX_HOME`
and the operating-system home pointed at scratch locations) from the approved Git
marketplace source `https://github.com/mzored/SkipHow.git`: `codex plugin
marketplace add`, `codex plugin add skiphow@skiphow --json`, `codex plugin list
--json`, then an operator byte comparison of the plugin cache against the committed
`plugins/skiphow` tree, which found all seventeen regular files identical, payload
`a0901a39…`, no symlink and no extra file. `codex plugin remove skiphow@skiphow`
then emptied the host inventory of the plugin, and the cache and temporary
marketplace snapshot were removed from the isolated home. No model session ran on
4.3.0; the ledger cells in [`../host-smoke.json`](../host-smoke.json) record only
these install and uninstall facts, and every other Codex and Claude cell stays
`UNVERIFIED`. The Codex plugin validator was unavailable on this machine and runs
in CI.
