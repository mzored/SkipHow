# SkipHow

Give SkipHow one ordinary-language request. It makes routine product and technical decisions, does the authorized work, and returns evidence for the result.

```text
Add a way to pause a subscription. Make the routine product and technical decisions and implement it.

Payments are sometimes charged twice. Find the cause, fix it, and verify the result.

Save this idea for later without expanding it: a monthly customer report.
```

No tracker, Project, Python, `gh`, setup command, or hook is required. SkipHow has no telemetry, hosted service, or background process. It uses the files, commands, and connected services already available in the host, subject to host and repository permissions.

## Install with Codex

Add this repository as a personal marketplace, then use the plugin browser:

```sh
codex plugin marketplace add mzored/SkipHow
codex
# Enter /plugins, select SkipHow, and install it.
```

Start a new session after installation. `/plugins` is the canonical install, update, enable, and removal interface. See the [OpenAI plugin guide](https://learn.chatgpt.com/docs/plugins).

Package discovery and activation still need a release receipt before this release can claim support. The Codex IDE extension is not claimed. The current marketplace policy limits the package to Codex, so ChatGPT Chat and Work are not claimed.

## Install with Claude Code

```text
/plugin marketplace add mzored/SkipHow
/plugin install skiphow@skiphow
```

Start a new session after installation. If Claude Code says that plugins changed on disk, run `/reload-plugins`. See the [Claude Code plugin guide](https://code.claude.com/docs/en/discover-plugins). Package discovery and activation still need a release receipt before this release can claim support.

## What SkipHow decides

SkipHow resolves routine reversible product details, architecture, dependencies, implementation, testing, review, sequencing, and integration. It asks a focused question only when the choice belongs to the Owner.

The Owner keeps authority over vision, audience, portfolio priority, material scope, commercial constraints, cost or risk commitments, protected actions, and irreversible external actions.

Analysis, research, review, diagnosis-only, and planning requests stay read-only unless you ask to save or change something.

## How work is handled

A clear software change goes straight to implementation and relevant evidence. A document, report, or other non-software project artifact uses artifact-appropriate checks without loading the engineering workflow.

A hard bug gets focused diagnosis before repair. Work gets durable campaign state only when coordination or recovery must survive a session, interruption, external wait, or dependency handoff. You do not select a mode or command.

## Optional configuration

`.skiphow/config.json` is optional. SkipHow writes it only when you explicitly request setup.

```json
{
  "tracker": "auto",
  "project": null,
  "campaign_root": ".skiphow/runs"
}
```

`tracker` accepts `auto`, `none`, `github`, or `local`. `project` is `null` or an explicit `owner/number`. `campaign_root` must be a relative path inside the project. Unknown keys, absolute paths, and path traversal are errors.

When you explicitly ask to save an idea or finding, SkipHow uses the configured tracker. With a GitHub origin and authenticated `gh`, `auto` can use a GitHub Issue. With no available tracker, it can use `.skiphow/inbox.md`. A GitHub Project is an optional view, never lifecycle authority.

## Support matrix

No host has package-validated support until release CI produces a fresh receipt for that exact package and host profile.

| Product | Discover/install | Skill activation | Inspect | Mutate | Commands | Subagents | Live outcomes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex CLI | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` |
| Codex desktop | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` |
| Claude Code | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` |
| Codex IDE | not claimed | not claimed | not claimed | not claimed | not claimed | not claimed | not claimed |
| ChatGPT Chat/Work | policy excluded | policy excluded | not claimed | not claimed | not claimed | not claimed | not claimed |

Core work needs project inspection. Change requests also need file mutation, and repository checks need command execution. Missing subagents do not block bounded work. Optional GitHub persistence needs authenticated `gh`; optional helper scripts support Python 3.10 through 3.13.

## Trust and removal

SkipHow may read or change local project files and run local commands only when the request authorizes that work. GitHub writes require explicit persistence, existing tracked work, repository-required lifecycle work, or requested setup. The default package installs no hooks.

See [trust and operations](docs/trust.md) for remote mutations, diagnostics, package proof, updates, rollback, and uninstall.

## Maintainer checks

```sh
python scripts/check.py
python scripts/check_hosts.py --output path/to/host-proof.json
```

The first command is deterministic and local. The second writes host proof as `VERIFIED`, `UNVERIFIED`, or `FAILED`; pass that receipt to doctor with `--package-proof-receipt`. Paid live evals are opt-in; release claims come from machine-readable receipts bound to the candidate commit, not an installed CLI version.

## Research and prior art

SkipHow adapts selected engineering practices from [mattpocock/skills](https://github.com/mattpocock/skills). Source-only copies retain their pinned commits and licenses; runtime policy does not load them. Exact vendored sources and pins live in the [source manifest](plugins/skiphow/skills/skiphow/references/third_party/sources.json).

Campaign and decision mechanics draw narrowly from [Paperclip](https://github.com/PaperclipAI/paperclip), [Mesa](https://github.com/msoedov/mesa), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [BMAD](https://docs.bmad-method.org/), and [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin). They are research inputs, not runtime dependencies or claims of superiority.

Project documents: [architecture](docs/architecture.md), [trust](docs/trust.md), [changelog](CHANGELOG.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md), [license](LICENSE).
