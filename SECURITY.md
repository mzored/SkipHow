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

## Host support, as of 2026-09-03

Host behavior changes. This matrix states what each host supported on the date in its
heading, and it is only as current as that date. Check the hosts' own documentation
again before relying on any row.

The rows are separate claims and must not be read as one. A host that validates the
package schema is not thereby shown to activate the skill; a host that activates the
skill is not thereby shown to isolate a delegate; and none of these rows says anything
about how a model behaves once the text reaches it.

| Category | Claude Code | Codex CLI |
| --- | --- | --- |
| Package schema validation | Manifest `.claude-plugin/plugin.json`. `claude plugin validate <path>` validates it, with `--strict` treating warnings as errors. | Manifest `.codex-plugin/plugin.json`. Validation is by the `validate_plugin.py` script shipped with the plugin-creator system skill. There is no `codex plugin validate` subcommand. |
| Isolated installation | Supported. Install scopes select where plugin configuration is stored, and pointing `CLAUDE_CONFIG_DIR` at a scratch directory installs into a host home of its own. | Supported, by pointing `CODEX_HOME` at a scratch directory. |
| Skill discoverability | Skills are discovered at `skills/<name>/SKILL.md` and namespaced `/<plugin>:<skill>`. The description sits in context and the body loads on invocation. Description and `when_to_use` are truncated at 1,536 characters. | Progressive disclosure. Name, description, and path are listed, capped at 2 per cent of the context window or at 8,000 characters where that window is unknown. The full file loads only when the skill is chosen. |
| Skill activation | Implicit and explicit invocation, both available by default. | Implicit invocation and explicit `$skill` invocation, governed by `policy.allow_implicit_invocation`, which defaults to true. |
| Hook enablement and trust | Plugin hooks are enabled with the plugin. No per-hook trust step is documented; the documented trust decision is taken once, when the plugin is installed. | Materially different. The exact hook definition must be reviewed and trusted before it runs, trust is recorded against the hook's hash so any edit requires re-review, and installing or enabling a plugin does not trust its hooks. |
| Reference loading | On demand. A reference file loads when the skill's own text leads the agent to it, never automatically with the skill. | On demand, the same way. |
| Delegate isolation capability | Host-enforced controls exist: a subagent `tools` allowlist, `disallowedTools`, `permissionMode: plan` for read-only exploration, and `isolation: worktree`. | No declarable per-delegate isolation profile of that kind. What exists is per-process: `--sandbox read-only`. The absence of an equivalent is `UNVERIFIED`; the documentation states it neither way. |
| Behavioral status | `UNVERIFIED`. | `UNVERIFIED`. |

Behavioral status is unverified on both hosts, and it is a separate claim from every row
above it. No host documents that identical instruction text produces equivalent
behavior, and the two loading models differ materially: one keeps every description in
context, the other lists a capped inventory and loads the file on selection. What runs
have and have not shown is in [current evidence](docs/evidence.md).

This repository's continuous integration is not dual-host behavioral support and does
not claim to be. It requires the pinned Codex validator, validates the Claude package
only where that executable is present, and skips isolated installation entirely.

## Report a vulnerability

Do not open a public Issue for a suspected vulnerability. Submit a [private GitHub security advisory](https://github.com/mzored/SkipHow/security/advisories/new). Include the affected SkipHow version, host and version, smallest safe reproduction, impact, and any proposed mitigation.

Use synthetic data. Remove credentials, tokens, private repository names, customer data, personal paths, and production payloads. Do not test against a system you do not own or lack permission to assess.

If private reporting is unavailable, contact the maintainer through the [GitHub profile](https://github.com/mzored) without sending vulnerability details over a public channel. Wait for a private route.

The maintainer will acknowledge a valid report, investigate it, and coordinate a fix before disclosure when practical.

Read the [design](docs/design.md) for the boundary between SkipHow policy and host enforcement.
