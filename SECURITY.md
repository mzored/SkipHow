# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 7.0.x | Yes |
| 4.0.x through 6.3.x | No. Upgrade to 7.0.x. When coming from 5.x or earlier, review the 7.0 engineering standard and the 6.0 iteration defaults. Existing authorization stays unchanged. |
| 3.0.x and earlier | No |

Security review covers the packaged owner skill, its linked playbooks, host manifests, marketplace metadata, release checks, and documented authority boundaries. Codex, Claude Code, GitHub, Git, operating systems, and third-party services keep their own security policies.

A request that changes the project also repairs the engineering problems the run finds, within the grants that request already carries. It adds no grant. Read-only requests, protected actions, owner decisions, audience boundaries, and a trusted project's own narrower procedure keep their limits. [The kernel](plugins/skiphow/skills/skiphow/SKILL.md) is the governing text.

## Enforcement and host support

SkipHow is policy and enforces nothing. A declared field is not an enforced read-only boundary. Claude Code ignores `permissionMode` for plugin subagents. The Codex CLI 0.153.0 source did not apply a custom agent's `sandbox_mode`, so a subagent inherited the parent's sandbox.

This repository's continuous integration is not dual-host behavioral support. It requires the pinned Codex validator, validates the Claude package only where that executable is present, and skips isolated installation entirely.

The host capability table is in [the evidence ledger](docs/evidence.md#host-facts). The full dated validation and host-support tables and their receipts remain in the [7.0.8 security policy](https://github.com/mzored/SkipHow/blob/90cfdbbbf2a354973ede4d716853ce62886e2c6b/SECURITY.md).

## Untrusted repository profile

When a repository, branch, pull request, download, or incident snapshot is not yet trusted, use the host's controls before reading its instructions as procedure or running its code:

- Start from a disposable checkout.
- Use synthetic or redacted data.
- Inherit no unrelated credentials.
- Deny network access unless the task requires named destinations.
- Keep writing delegates disabled.
- Do not run project hooks, build scripts, tests, or project-supplied skills until their effects fit the request's authority and the repository's provenance is established.

On Codex, start the root session under a read-only sandbox and approval policy. Subagents inherit it. Current documentation describes a custom-agent `sandbox_mode` field, and the historical CLI 0.153.0 source did not apply it. That finding guarantees nothing about another version, so verify the active host's effective controls before relying on them. The `AGENTS.md` chain is behavioral context, not an enforcement boundary.

On Claude Code, use plan or equivalent read-only permissions plus the OS-enforced filesystem and network sandbox. Set sandbox unavailability to fail closed when the review depends on it, and disable the unsandboxed-command escape.

On either host, move a requested repair to a fresh bounded write environment only after the source and effects are understood.

## Report a vulnerability

Do not open a public Issue for a suspected vulnerability. Submit a [private GitHub security advisory](https://github.com/mzored/SkipHow/security/advisories/new). Include the affected SkipHow version, host and version, smallest safe reproduction, impact, and any proposed mitigation.

Use synthetic data. Remove credentials, tokens, private repository names, customer data, personal paths, and production payloads. Do not test against a system you do not own or lack permission to assess.

If private reporting is unavailable, contact the maintainer through the [GitHub profile](https://github.com/mzored) without sending vulnerability details over a public channel. Wait for a private route.

The maintainer will acknowledge a valid report, investigate it, and coordinate a fix before disclosure when practical.

Read the [owner-outcome contract](docs/outcome-contract.md) for the boundary between SkipHow policy and host enforcement.
