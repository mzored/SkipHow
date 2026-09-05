# Owner guide

Tell SkipHow what should change for someone using the product. You do not need to name a library, design a schema, write tickets, or choose an agent workflow.

This guide describes what the shipped instructions require of the agent. That is not the same as what has been measured. [Current evidence](evidence.md) records which of these behaviors real runs have shown, which a run has shown failing, and which stay intended but unproven. Short answers to common questions are in the [FAQ](faq.md).

## Install

Codex:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Claude Code:

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Start a new session after installing or updating.

## Activate it

Plugin installation makes the skill available. For ordinary-language default governance, ask the installed skill to enable itself once, in a fresh session:

```text
$skiphow Enable SkipHow as my default virtual CTO on this machine.
```

Use `/skiphow:skiphow` instead of `$skiphow` in Claude Code. The agent resolves the trusted user instruction file your host reads, previews the exact change, asks for one confirmation, writes one owned block, and reports three separate facts: configured (the block is in the effective file), available (the host lists the plugin installed and enabled), and loaded (only a fresh session shows this). Ask it to check or disable itself the same way. It never presents a configuration check as loading evidence, and if a managed policy on your machine restricts plugins or instructions it reports the exact file rather than working around it.

The agent uses a helper shipped inside the plugin, `skills/skiphow/scripts/activation.py`, which you can also run yourself with any Python 3 interpreter. It resolves the file the way the host discovers it: Codex reads `AGENTS.override.md` in its home when that file exists and is not empty, and `AGENTS.md` otherwise, with `CODEX_HOME` relocating the home; Claude Code reads `CLAUDE.md` and unconditional `rules/*.md` files under its configuration directory, with `CLAUDE_CONFIG_DIR` relocating it. Preview first, then add `--apply` to make the displayed change:

```sh
python <installed plugin>/skills/skiphow/scripts/activation.py status --host codex
python <installed plugin>/skills/skiphow/scripts/activation.py install --host codex
python <installed plugin>/skills/skiphow/scripts/activation.py install --host codex --apply
python <installed plugin>/skills/skiphow/scripts/activation.py remove --host claude-code --apply
```

Installation is idempotent, including after a plugin update. The block references the installed skill by name, so it contains no copied policy or version-specific cache path. `install` also moves a block found in a file the host does not read, such as `AGENTS.md` beside a non-empty `AGENTS.override.md`, and consolidates a duplicate copy from a Claude rule; `remove` deletes every copy it may edit. Linked files are inspected and reported, never written through. Removal preserves unrelated content and restores the original trailing-newline state when no content follows the block. A file created solely for the block is removed when it has no other content. Updates stage the complete file beside the target before replacing it, preserving its permissions and leaving the original intact if staging fails. Edited or duplicate blocks require inspection rather than automatic replacement. If you previously added the README line manually, remove that exact line yourself before installing a managed block; the tool does not claim ownership of existing prose. `--target <file>` names another trusted file explicitly when you keep your instructions elsewhere.

The package ships no session hook. Persistent user instructions are the smallest host-native setup that is present before the first project action without silently editing configuration or adding an executable surface. Their loading is documented on both hosts. What has been observed on each host is in the [dated support summary](evidence.md#support-summary-as-of-2026-09-06); the per-capability host matrix is in the [security policy](../SECURITY.md#host-support-as-of-2026-09-06). Use `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code as the explicit fallback and diagnostic path.

Update Codex:

```sh
codex plugin marketplace upgrade skiphow
codex plugin add skiphow@skiphow
```

Update Claude Code:

```sh
claude plugin marketplace update skiphow
claude plugin update skiphow@skiphow
```

Before uninstalling, ask SkipHow to disable itself, or run the helper's `remove --host <host> --apply` yourself. If you added the README line manually, remove that exact line instead. Then uninstall with `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`. Plugin removal alone does not edit your trusted instructions and would leave a request to load an unavailable skill.

## Ask for the outcome

A useful request names the visible result and any limit you care about:

```text
The checkout sometimes hangs after payment. Find the cause and fix it without changing the payment provider.

Compare these onboarding ideas. Recommend one, but do not change the project.

Save these observations so we can prioritize them tomorrow.
```

Rough requests are fine. SkipHow reads the project before it asks you for anything. It brings a question back only when the answer changes product behavior, scope, priority, cost, risk, privacy, or rollout. It also asks when an action needs your explicit grant or only a person can complete it.

Where your request leaves a genuine product choice open, the instructions require the question to reach you before the work, with the option it recommends, and everything answerable at that point to arrive together rather than one message at a time. Some choices only exist once you have answered another. Say yes to cancelling parcels that are already on their way and the question of who pays the carrier's fee appears, which nobody could have put to you before. Those go back in a second round, and only those. Once nothing material is open, the work starts. A question that is with you is not answered by a default: nothing whose meaning depends on your answer is to be built while you decide, and the parts that do not depend on it carry on. "Let someone share their cart with a friend" should come back asking whether the friend gets a snapshot or a live shared cart, not with one of the two silently built. That second round is the part to check rather than assume: the runs on record show it holding on Claude Code and not reliably on Codex, and [current evidence](evidence.md) says what each one did. Where your project's own evidence settled a reading, the report names it and the alternative it did not take, so correcting it costs one message. Where nothing settles it, you get the question instead — not a choice made for you and mentioned afterwards. What the project cannot do yet is never treated as an answer to what the product should do; it is a cost, and the cost is yours to weigh.

You can correct or extend the request while work is running. The agent treats the new message as part of the current outcome unless you replace the request.

## Know what your request allows

| Request | What SkipHow may do |
| --- | --- |
| Answer, compare, diagnose, review, research, or plan | Read and report |
| Capture, organize, triage, or create a record | Write the requested records in the project's existing authorized system |
| Change the project | Edit and verify; carry through an established owner-authorized non-production workflow |
| Deliver the change | Use the repository's normal shared path |

A mixed request such as "review and fix" allows a project change. A request only to review does not.

An established owner-authorized workflow can cover routine push, pull request, CI, and merge without another permission question. The agent checks that the destination, audience, and actual effects remain covered, including deployment triggered by a merge or tag. Production, live-data changes, public releases, payments, repository settings, access changes, material deletion, wider disclosure, and new credential work need applicable explicit owner authorization. A prior grant remains valid only while its scope and conditions hold. Installing or upgrading SkipHow creates no grant. Local previews and isolated test environments remain ordinary engineering.

## Records and tracked work

Installing SkipHow does not grant tracker writes. When authorized work needs shared durable records, the lead discovers the repository's issue availability, permissions, audience, and conventions. Enabled GitHub Issues are the default for an authorized GitHub workflow even with no tracking history; an existing authorized alternative remains usable. Several deliverable outcomes, multiple sessions or writers, durable decisions, and material separable findings warrant records. Disabled Issues or missing access leave a recoverable pending obligation through an authorized private channel and a specific blocker, without changing repository settings. Tiny same-session work and read-only requests record nothing. A branch, worktree, or review does not by itself create an item.

Work with more than one result you could check separately is split into parts you can each see working, with only the genuine dependencies between them. Parts that do not block each other can run at the same time where your host can give each one a checkout of its own, and are done one after another where it cannot. The splitting is what the runs show; running the parts concurrently is the intent, and no receipt has demonstrated it yet. Where the split needs to outlive the session and a record is called for, it goes where your project already keeps that work, and the report names what continues it. When you only asked for a plan, you get the split in the answer and nothing is written.

Where work did go into your tracker, it closes as the change is integrated rather than when it looks finished on the branch, and what the work established is written back into it, so nobody pays for the same investigation twice. Something reported that turns out not to happen is closed as not reproducible, with what was checked, rather than as fixed. A material problem found along the way ends fixed, safely recorded when it is separable, blocked with evidence and a next action, or rejected with a reason; it never silently disappears.

## Read the report

A finished report starts with what changed and the evidence that still applies. It names blockers and `UNVERIFIED` claims instead of turning them into success.

The instructions require SkipHow to preserve unrelated work: a checkout, branch or running service it did not create is shared, and the uncommitted changes in it are somebody's. One run on record broke that and destroyed a peer session's uncommitted work, so if you keep two sessions on one checkout, read [current evidence](evidence.md) before you rely on it. A dirty checkout is a reason not to commit when the owned change cannot be separated safely, and it weakens verification only when it makes the evidence unreliable.

## Remember the host boundary

Codex or Claude Code supplies the sandbox, permissions, tools, sessions, subagents, and credentials. SkipHow cannot exceed those controls. Persistent user instructions can ask the host to load the skill, but they do not enforce behavior or grant authority. Continuity comes from the owner request, Git, the project's tracker, CI, host state, and any authorized checkpoint.
