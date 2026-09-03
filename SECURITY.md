# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 3.0.x | Yes |
| 2.16.x and earlier | No |

Security review covers the packaged owner skill, its linked methods, host manifests,
marketplace metadata, continuity hook, release checks, and documented authority
boundaries. Codex, Claude Code, GitHub, Git, operating systems, and third-party
services keep their own security policies.

## Host support, as of 2026-09-04

Host behavior changes. Each row below is only as current as its verification date, and
each row cites the first-party page it was read from. Check that page again before
relying on the row.

Only capabilities on which shipped rules depend are tracked: skill loading, persistent
instruction loading, hook trust, per-agent read-only controls, worktree isolation,
plugin validation, and clean installation. This is not a host feature database.

The rows are separate claims and must not be read as one. Schema validation shows that
a host accepts the package's shape; it never establishes that the host activates the
skill, that a hook runs, that a delegate is isolated, or how a model behaves once the
text reaches it. A `PASS` is a run that happened on the named host version; a
documentation-only row is `UNVERIFIED` however clearly the page describes the feature.

Tested host versions, where a run exists, are Claude Code 2.1.259 and Codex CLI 0.153.0,
the versions `claude --version` and `codex --version` reported on 2026-09-04. Those are
two observed versions and not a tested range.

Where a row cites `developers.openai.com`, that address redirected on 2026-09-04 to a
page under `learn.chatgpt.com`; the redirect target is the page actually read.

### Claude Code

| Capability | What the source says | Source | Verified | Tested version | Status |
| --- | --- | --- | --- | --- | --- |
| Skill loading | Plugin skills are discovered at `<plugin>/skills/<name>/SKILL.md` and namespaced `/<plugin>:<skill>`. The description sits in context and the body loads on invocation; description plus `when_to_use` is truncated at 1,536 characters in the listing. Both explicit `/name` and automatic invocation are available unless `disable-model-invocation` or `user-invocable` restricts them. | [Skills](https://code.claude.com/docs/en/skills) | 2026-09-04 | none | `UNVERIFIED` (documented; no activation run on record) |
| Persistent instruction loading | `CLAUDE.md` from the working directory and every directory above it, plus user and managed-policy files, load at the start of every session; subdirectory files load on demand. Claude Code reads `CLAUDE.md`, not `AGENTS.md`. | [Memory](https://code.claude.com/docs/en/memory) | 2026-09-04 | none | `UNVERIFIED` (documented) |
| Hook trust | A plugin's `hooks/hooks.json` is enabled when the plugin is enabled. The page documents a workspace-trust dialog for project subagent frontmatter hooks; it documents no per-hook review step for plugin hooks. | [Hooks](https://code.claude.com/docs/en/hooks) | 2026-09-04 | none | `UNVERIFIED` (documented; trust state not inspected by a run) |
| Per-agent read-only controls | Subagent frontmatter takes a `tools` allowlist, `disallowedTools`, and `permissionMode`, whose values include `plan` for read-only exploration. | [Subagents](https://code.claude.com/docs/en/sub-agents) | 2026-09-04 | none | `UNVERIFIED` (documented) |
| Worktree isolation | `isolation: worktree` runs a subagent in a temporary git worktree. | [Subagents](https://code.claude.com/docs/en/sub-agents) | 2026-09-04 | none | `UNVERIFIED` (documented) |
| Plugin validation | Manifest `.claude-plugin/plugin.json`; `claude plugin validate <path>` validates it and `--strict` treats warnings as errors. | [Plugins](https://code.claude.com/docs/en/plugins) | 2026-09-04 | 2.1.259 | `PASS` (`scripts/check_hosts.py`, 2026-09-04) |
| Clean installation | `claude plugin marketplace add`, `claude plugin install --scope user`, `claude plugin uninstall --scope user`; `CLAUDE_CONFIG_DIR` points the host at a scratch home. | [Discover plugins](https://code.claude.com/docs/en/discover-plugins), [Skills](https://code.claude.com/docs/en/skills) | 2026-09-04 | 2.1.259 | `PASS` (`scripts/check_hosts.py --smoke`: clean home, install, 16 regular files matching the candidate, uninstall verified, 2026-09-04) |

### Codex CLI

| Capability | What the source says | Source | Verified | Tested version | Status |
| --- | --- | --- | --- | --- | --- |
| Skill loading | Skills are discovered from `.agents/skills` in the current, parent, and repository-root directories, the user-level `.agents/skills` directory in the home directory, `/etc/codex/skills`, and system skills. Progressive disclosure lists name and description within 2 per cent of the context window, or 8,000 characters where that is unknown; the full file loads on selection. Explicit `$skill` invocation and implicit invocation are both available; `allow_implicit_invocation` in `agents/openai.yaml` defaults to true. | [Skills](https://developers.openai.com/codex/skills) | 2026-09-04 | none | `UNVERIFIED` (documented; no activation run on record) |
| Persistent instruction loading | `AGENTS.override.md` or `AGENTS.md` in the Codex home, then `AGENTS.md` from the project root down to the current directory, concatenated once per session, up to `project_doc_max_bytes` (32 KiB by default). | [AGENTS.md](https://developers.openai.com/codex/guides/agents-md) | 2026-09-04 | none | `UNVERIFIED` (documented) |
| Hook trust | A non-managed hook runs only after the exact hook definition is reviewed and trusted; trust is recorded against the hook's hash, so any edit requires re-review. Installing or enabling a plugin does not trust its hooks; Codex skips plugin-bundled hooks until trusted. | [Hooks](https://developers.openai.com/codex/hooks) | 2026-09-04 | none | `UNVERIFIED` (documented; the package hook has not been shown to run on Codex) |
| Per-agent read-only controls | Custom agents are TOML files in the Codex home `agents/` directory or the project `.codex/agents/` and may set `sandbox_mode` per agent; the page names marking one agent read-only as the example. Absent an override, subagents inherit the parent's sandbox policy and permission mode. | [Subagents](https://developers.openai.com/codex/subagents) | 2026-09-04 | none | `UNVERIFIED` (documented; corrects the earlier claim that no declarable per-delegate profile exists) |
| Worktree isolation | The subagents page documents no worktree or separate-checkout option for a subagent. | [Subagents](https://developers.openai.com/codex/subagents) | 2026-09-04 | none | `UNVERIFIED` (not documented either way) |
| Plugin validation | Manifest `.codex-plugin/plugin.json`. There is no `codex plugin validate` subcommand; validation runs the `validate_plugin.py` script shipped with the plugin-creator system skill in the Codex repository, which CI checks out at a pinned commit. | [openai/codex plugin-creator scripts](https://github.com/openai/codex/tree/333beecd41281b1350688b417a2f20c66e2a743e/codex-rs/skills/src/assets/samples/plugin-creator/scripts) | 2026-09-04 | none locally | `UNVERIFIED` locally (validator not on this machine); required to `PASS` in CI |
| Clean installation | `codex plugin marketplace add`, `codex plugin add`, `codex plugin list --json`, `codex plugin remove` exist in `codex plugin --help`; `CODEX_HOME` relocates the host home. The plugins page documents the plugin browser and uninstall but none of these commands. | [Plugins](https://developers.openai.com/codex/plugins), `codex plugin --help` 0.153.0 | 2026-09-04 | 0.153.0 | `UNVERIFIED` (the local run was refused by a managed `/etc/codex/requirements.toml` source policy before install; nothing was installed) |

### Codex surfaces

Codex is more than one product surface, and only the CLI has rows above. On 2026-09-04
the first-party plugins page ([Plugins](https://developers.openai.com/codex/plugins),
redirecting to `learn.chatgpt.com/docs/plugins`) said that plugins work in Codex in the
ChatGPT desktop app and that Codex CLI has a plugin browser, and that the IDE extension
does not support plugins. No run on this project has been made on any surface other
than the CLI.

| Surface | What the source says | Verified | Status |
| --- | --- | --- | --- |
| Codex CLI | Plugin browser and `codex plugin` commands; rows above. | 2026-09-04 | `UNVERIFIED` activation; see rows above |
| ChatGPT desktop app (Codex) | Plugins supported. | 2026-09-04 | `UNVERIFIED` (documented only; no run) |
| IDE extension | Does not support plugins. Whether the same skill loads there as a standalone `.agents/skills` entry is not stated. | 2026-09-04 | `UNVERIFIED` (unsupported as a plugin per the page) |
| Cloud and web Codex | Not mentioned on the page read. | 2026-09-04 | `UNVERIFIED` |

Behavioral status is `UNVERIFIED` on both hosts, and it is a separate claim from every row
above. No host documents that identical instruction text produces equivalent behavior,
and the two loading models differ materially: one keeps every description in context,
the other lists a capped inventory and loads the file on selection. What runs have and
have not shown is in [current evidence](docs/evidence.md).

Each release publishes the compact matrix that `scripts/check_hosts.py` prints, with one
row per capability. A skipped or unavailable check stays `UNVERIFIED` there; it is never
folded into a passing aggregate. The session steps of the clean-install procedure,
starting a clean session and verifying explicit invocation, start a model and are
reported only from a receipt supplied to the script; without one they stay `UNVERIFIED`.

This repository's continuous integration is not dual-host behavioral support and does
not claim to be. It requires the pinned Codex validator, validates the Claude package
only where that executable is present, and skips isolated installation entirely.

## Report a vulnerability

Do not open a public Issue for a suspected vulnerability. Submit a [private GitHub security advisory](https://github.com/mzored/SkipHow/security/advisories/new). Include the affected SkipHow version, host and version, smallest safe reproduction, impact, and any proposed mitigation.

Use synthetic data. Remove credentials, tokens, private repository names, customer data, personal paths, and production payloads. Do not test against a system you do not own or lack permission to assess.

If private reporting is unavailable, contact the maintainer through the [GitHub profile](https://github.com/mzored) without sending vulnerability details over a public channel. Wait for a private route.

The maintainer will acknowledge a valid report, investigate it, and coordinate a fix before disclosure when practical.

Read the [design](docs/design.md) for the boundary between SkipHow policy and host enforcement.
