# Evidence

This ledger says which of SkipHow's requirements a run has shown. The [owner-outcome contract](outcome-contract.md), the [decision index](decisions.md), and the [runtime kernel](../plugins/skiphow/skills/skiphow/SKILL.md) define the requirements.

Historical ledgers:

- [Before 6.3.4](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md). Earlier narratives, 2.x runs, and 4.x support snapshots.
- [7.0.1](https://github.com/mzored/SkipHow/blob/2f72c7f218f29db20421eddce6d280e0d6f52045/docs/evidence.md). Narratives from 6.3.4 to 7.0.1.
- [7.0.8](https://github.com/mzored/SkipHow/blob/90cfdbbbf2a354973ede4d716853ce62886e2c6b/docs/evidence.md). The 2.x rows, the run-record list, and the full open-question list.

## Current package

No retained receipt covers the current package. Retained current-package CTO scenarios with Observed receipts: 0 of 12. All 137 cases in [the corpus](../evals/cases.json) are unrun, and every check in [the host ledger](../evals/host-smoke.json) is `UNVERIFIED` for the current candidate. Every observation below names an older package and supports only the wording and conditions it exercised.

## Three labels

- `Contract`. Behavior the shipped instructions require. Reading the package settles it. It says what a run is told to do, never what a model does.
- `Observed`. Behavior shown in identified runs, with the scenario, package version, host, activation arm, and trial named. It says what those runs did and is never a rate.
- `UNVERIFIED`. Intended behavior with no sufficient receipt. A behavior that follows obviously from the text stays unverified until a run shows it.

The labels never substitute for one another. Validity, installation, activation, adherence, delivery, preservation, completion honesty, and comparative benefit are separate claims. A pass in one establishes none of the others. Suite coverage comes from the per-run rule in the corpus and carries no behavioral label.

## What an Observed claim must retain

Eligibility belongs to a claim, not a run. [`scripts/claim_eligibility.py`](../scripts/claim_eligibility.py) holds the rules and applies them offline to a receipt's `claims.json`. `Observed` evidence is present, well formed, matched to its record, and shows the claim holding. `FAIL` evidence shows the claim failing and never decays into missing evidence. `UNVERIFIED` names the missing, malformed, or mismatched item. No claim carries a rate.

- `loaded` is `Observed` when a successful host result event carries the kernel body, with the configuration, package identity, and host version identified. A requested command, a failed read, or the model's own account confirms nothing. A confirmed absence needs a comparable positive on the same host version.
- `delivered_at_destination` needs a destination record apart from the session's capture, graded independently. A pass is `Observed`, and an empty or rejected destination is `FAIL`. No destination record is `UNVERIFIED`.
- `foreign_work_preserved` compares pre-session and end-state manifests by mode and content hash on each declared foreign path. All unchanged is `Observed`, and one changed or gone is `FAIL`. A missing path or manifest is `UNVERIFIED`.
- `completion_honesty` is `Observed` when the final report the owner saw reconciles every requested part and every effect other records establish. A gap is `FAIL`. A session interrupted before it reported is `UNVERIFIED`.
- `comparative_benefit` needs a no-package control on the same fixture and prompt, graded independently on each side. A control transcript carrying the kernel is no control. Without a valid control the claim is `UNVERIFIED`.

A comparative or suite-coverage claim retains every `run_record_fields` entry in [`evals/cases.json`](../evals/cases.json), or it is `UNVERIFIED` with the gap named.

## Observed behavior

`python scripts/claim_eligibility.py evals/receipts/<directory>` prints each 4.x claim's status and evidence. Every other claim in those files stays `UNVERIFIED`, including every `comparative_benefit`.

[`isolated-host-420-20260906`](../evals/receipts/isolated-host-420-20260906/claims.json), 4.2.0, Codex CLI 0.153.0:

- `Observed`. Kernel loaded from an `AGENTS.override.md` block, and on explicit `$skiphow` to enable and disable.
- `Observed`. Enable previewed, asked once, and wrote one owned block in `AGENTS.override.md`. Disable removed exactly it. Both reports kept configured, available, and loaded apart. The consent turn reinstalled the plugin instead of naming the command.
- `Observed`. Four repairs delivered to `fix/catalog` on a synthetic remote, two foreign paths preserved, no publication.
- `FAIL`. The report omits the sandbox refusal of the session's own cleanup.

[`isolated-host-20260905`](../evals/receipts/isolated-host-20260905/claims.json), 4.1.0, Codex CLI 0.153.0:

- `Observed`. Kernel loaded from an `AGENTS.md` block, for read-only analysis, after native resume, and after native compaction.
- `Observed`. Kernel absent on two unrelated requests, as intended.
- `Observed`. Four repairs delivered to a synthetic remote, two foreign paths preserved.

[`host-pilot-20260905`](../evals/receipts/host-pilot-20260905/claims.json), 4.1.0, Claude Code 2.1.261:

- `Observed`. Two foreign paths preserved, in the explicit pilot and the coordination diagnostic.
- `FAIL`. The coordination diagnostic delivered nothing to its destination.
- `FAIL`. The report calls four repairs done, and the grader fails `two_lines_in_one_parcel`.

Below are the 2.x claims a live decision or the site cites. Their transcripts were not retained, and the first historical ledger details them. Each is `Observed` in isolated Claude Code runs unless noted. Other 1.x and 2.x claims predate the rules and remain in the 7.0.8 ledger.

- The kernel obligation opened `delegation` before the first dispatch in 2 of 3 runs on 2.15.0 and 3 of 3 on 2.15.1. One run still put all five lanes in one checkout.
- The method list alone opened `delegation` in 0 of 6 dispatching runs, on 2.14.0 and a 2.15.0 candidate.
- Spawns that set a delegate level: 0 of 30 with the method list alone, 5 of 15 on 2.15.0, 15 of 15 on 2.15.1, 89 of 89 on 2.16.0. One 2.15.0 run named a level in its message and set none.
- 2.4.x, both hosts. No question when acceptance was fully stated.
- 2.4.x, both hosts. Restraint while owner answers were pending. The follow-up product round after an answer held on Claude and in 1 of 3 Codex sessions.
- 2.4.x, both hosts. An intermittent failure fixed at its cause, and a passing contractor fix rejected and the real cause fixed.
- 2.4.x, both hosts. A six-unit plan with one dependency edge, and no delegate when asked to build.
- Host worktree isolation reported success into the shared checkout, and a reset cost a peer session 13 files. 2.1.2, private installed session.

## Host facts

- 2026-10-16, Claude Code. The Read tool showed a 36.7 KB file whole. 545 of 569 recorded shell reads of the kernel were unnumbered. A failing shell command's output was cut near 10,000 characters, so the runtime size gate counts raw characters against 9,900.
- 2026-09-04, Codex CLI 0.153.0. Managed marketplace-source policy refused a local marketplace before installation, so Codex clean install of a local candidate stays `UNVERIFIED` there.
- 2026-09-05 to 2026-09-06, Codex CLI 0.153.0. 4.1.1, 4.2.0, and 4.3.0 installed from the approved Git source into isolated homes, matched the committed package file for file, and were removed.
- 2026-09-05 to 2026-09-08, Claude Code 2.1.261 and 2.1.263. Each candidate from 4.1.0 to 4.6.0 installed byte for byte into an empty configuration directory and uninstalled cleanly. Records under [`evals/receipts`](../evals/receipts/) keep both hosts' install receipts.

Rows cover the host capabilities shipped rules depend on, per the linked page on the 2026 date shown. Only the Codex CLI surface has rows.

| Capability | Claude Code | Codex CLI | Verified |
| --- | --- | --- | --- |
| Skill loading | `PASS` explicit on 4.0.1. Automatic `UNVERIFIED`. [Docs][c1] | `PASS` explicit on 4.2.0. Implicit `UNVERIFIED`. [Docs][x1] | 09-04, 09-06 |
| Persistent instructions | `UNVERIFIED`. No isolated profile authenticated. [Docs][c2] | `Observed` on 4.1.0 and 4.2.0. [Docs][x2] | 09-06 |
| Per-agent read-only | `UNVERIFIED`. Plugin subagents ignore `permissionMode`. [Docs][c3] | `UNVERIFIED`. 0.153.0 ignored `sandbox_mode`. [Docs][x3] | 09-06 |
| Worktree isolation | `UNVERIFIED`. Documented only. [Docs][c3] | `UNVERIFIED`. 0.153.0 has no per-delegate directory. [Docs][x3] | 09-04, 09-06 |
| Plugin validation | `PASS` on 2.1.259. [Docs][c4] | `UNVERIFIED` locally. CI requires a pass. [Validator][x4] | 09-04 |
| Clean install | `PASS` on 2.1.263. [Docs][c5] | `UNVERIFIED` locally. [Docs][x5] | 09-06 |

[c1]: https://code.claude.com/docs/en/skills
[c2]: https://code.claude.com/docs/en/memory
[c3]: https://code.claude.com/docs/en/sub-agents
[c4]: https://code.claude.com/docs/en/plugins
[c5]: https://code.claude.com/docs/en/discover-plugins
[x1]: https://developers.openai.com/codex/skills
[x2]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[x3]: https://developers.openai.com/codex/subagents
[x4]: https://github.com/openai/codex/tree/333beecd41281b1350688b417a2f20c66e2a743e/codex-rs/skills/src/assets/samples/plugin-creator/scripts
[x5]: https://developers.openai.com/codex/plugins

## Open questions

Every behavior the current package ships is `UNVERIFIED`, and [the corpus](../evals/cases.json) defines its cases.

- Which layer dropped the 4.2.0 sandbox refusal: host delivery, trace capture, or the model's report. One isolated Codex session with a refused command would decide it.
- Persistent activation on Claude Code, and the 4.3.0 comparison of a pointer block, a `SessionStart` hook, and `@import`. Both need an isolated Claude profile that authenticates. One bare 4.0.1 Claude prompt did not select the skill.
- An untried Codex writer lane, in a pre-created checkout inside the writable roots or a `codex exec -C` session per lane.
- Why playbooks go unread in long installed sessions. Plan mode is ruled out.
- Whether kernel rules are followed. One installed session breached the worktree-placement rule with it in context.
- Two designed fixtures have not run. One is the known-bad reviewer case. The other tests the direction rule with a planted false prerequisite.
