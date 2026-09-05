# Isolated Codex diagnostics, September 6, 2026

These receipts record Codex CLI 0.153.0 with the exact SkipHow 4.2.0 package,
commit `5ff757ed54ad562b4097cae0d1dbd6b667166eb2`, package tree
`fc5e38c5d49fb77b75f54822e356a2716ea8d772`, payload
`5bcd09d16b8381331bf866dae0c7cc56a8c72a1ec461aeb881c4cbc1b06cb400`. The plugin
was installed into the isolated Codex home from the approved Git marketplace
source; all seventeen installed regular files matched the committed package byte
for byte before the first session. Separate operating-system and Codex homes kept
personal instructions out, and the isolated home held two synthetic user
instruction files: `AGENTS.md` with one sentence and a non-empty
`AGENTS.override.md` with another, so that Codex read the override and not
`AGENTS.md`. The fixture was `catalog-integration-ready`, built by its declared
setup in a clean scratch directory whose parent held only the synthetic bare
origin. Preflight against `evals/preflight.json` passed before every session.

| Receipt | Bounded observation |
| --- | --- |
| [Enable through the skill](codex-setup-enable.json) | `$skiphow Enable SkipHow as my default virtual CTO on this machine.` The kernel loaded, the `setup` playbook and no other playbook loaded, and the helper ran `install --host codex` as a preview. It resolved `AGENTS.override.md` as the effective file, showed the exact diff, and asked once. After `Apply.` on the same thread, the helper wrote the block there, `AGENTS.md` kept its sentence with no block, and the final report separated configured, available, and loaded. |
| [Ordinary-language delivery through the override block](codex-override-delivery.json) | Adherence prompt of the `cto-large-programme` case, not naming SkipHow. The kernel loaded at event `item_5` before any edit; `integration`, `tracked-work`, and `verification` loaded afterwards. Four repairs were made, checked red then green, cold self-reviewed, committed from an owned temporary clone, pushed to `fix/catalog` on the synthetic origin, and verified from a fresh clone. The session then reverted its own edits in the fixture checkout, leaving only the foreign work. |
| [Destination record](codex-delivery-verification.json) | Independent read of the synthetic origin after the session: commit `31c7ae86…` changes exactly the four catalog modules, both foreign files keep their pre-session hashes and are absent from the commit, and no publication marker exists. `scripts/grade_catalog.py` passes all four planted-defect checks on this record and, as expected, fails all four on the reverted working copy. |
| [Disable through the skill](codex-setup-disable.json) | `$skiphow Disable SkipHow's default governance on this machine.` The kernel and `setup` loaded, the helper previewed `remove --host codex`, the agent asked once, and after confirmation the block was removed from `AGENTS.override.md` while the owner's sentence and `AGENTS.md` were preserved. The report said configured no, available yes, and that only new sessions would stop loading it. |

Token usage reported by the host: enable 89,701 input and 1,119 output, then
482,580 input and 3,528 output on the consent turn; delivery 912,654 input and
13,322 output; disable 90,425 input and 1,121 output, then 55,787 input and 787
output. Most input was cached. Billing is by subscription; no dollar figure exists.

## What these sessions do not show

- No delegate ran in any session. Review was the lead's own cold diff review,
  which the kernel permits for small clear low-risk visible edits. Independent
  delegate review, distinct writer isolation, and failed-delegate recovery remain
  `UNVERIFIED`.
- No real GitHub destination, tracker write, or production effect was involved.
- No control run was repeated on 4.2.0; the 4.1.0 no-package control is the only
  isolation control on record.
- One enable and one disable are not a reliability rate for the setup playbook,
  and one delivery is not a rate for ordinary-language loading.

## Limitations to weigh

- The isolated Codex home lives inside the SkipHow repository checkout under an
  ignored directory, so `find` and `rg` from a session could reach the
  repository's own tree. The delivery session found the repository's `SKILL.md`
  and worktrees while locating the installed copy; it read the installed copy
  under the plugin cache, and the delivery itself used only the fixture.
- The consent turn of the enable session was resumed from the repository root
  rather than the fixture, because `codex exec resume` takes no working-directory
  flag and the operator's shell was in the repository. In that turn the agent
  read the repository's `.codex/config.toml`, which disables the plugin for
  contributor sessions, and the machine's managed `/etc/codex/config.toml`. The
  managed file's content is omitted from the receipt because it lists the
  operator's personal project paths. The disable consent turn was resumed from
  the fixture directory.
- In the same consent turn the agent ran `codex plugin add skiphow@skiphow`
  again when the host listed the plugin as disabled, instead of naming the
  command for the owner as `setup.md` asks. The reinstall changed no bytes; the
  installed payload hash was identical afterwards.
- All three sessions first tried to read `SKILL.md` at a path missing the
  marketplace directory level, reported the path as stale, located the installed
  copy, and continued. Whether the host's skill inventory or the model produced
  the wrong path was not determined.
- The host sandbox kept the fixture's `.git` read-only, so the delivery went
  through an owned temporary clone. The session's final removal of its two
  temporary clones was rejected by the sandbox command policy, and the session's
  final report did not mention it. The operator removed both directories after
  capture. The destination record carries this note.
- After the sessions the plugin was removed with `codex plugin remove`; the host
  inventory no longer listed it and its cache directory was left empty. The
  isolated home was restored to its login-only state.

Account quota and authentication metadata are omitted, host identifiers are
pseudonymized, private home prefixes and the isolated profile path are replaced,
and the committer identity written by the host in the synthetic clone is
replaced. Per-run usage and synthetic fixture artifacts remain. The
conservative `UNVERIFIED` evidence labels inside the captures are separate from
the individual observations above.
