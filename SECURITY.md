# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 2.9.x | Yes |
| 2.8.x and earlier | No |

Security review covers the packaged owner skill, its linked methods, host manifests,
marketplace metadata, continuity hook, release checks, and documented authority
boundaries. Codex, Claude Code, GitHub, Git, operating systems, and third-party
services keep their own security policies.

## Report a vulnerability

Do not open a public Issue for a suspected vulnerability. Submit a [private GitHub security advisory](https://github.com/mzored/SkipHow/security/advisories/new). Include the affected SkipHow version, host and version, smallest safe reproduction, impact, and any proposed mitigation.

Use synthetic data. Remove credentials, tokens, private repository names, customer data, personal paths, and production payloads. Do not test against a system you do not own or lack permission to assess.

If private reporting is unavailable, contact the maintainer through the [GitHub profile](https://github.com/mzored) without sending vulnerability details over a public channel. Wait for a private route.

The maintainer will acknowledge a valid report, investigate it, and coordinate a fix before disclosure when practical.

Read the [design](docs/design.md) for the boundary between SkipHow policy and host enforcement.
