# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.4.x | Yes |
| 1.3.x | No |
| 1.2.x | No |
| 1.1.x | No |
| 1.0.x | No |
| Earlier versions | No |

Security support covers the packaged SkipHow skill, its host manifests, marketplace metadata, release checks, and documented GitHub delivery policy. Codex, Claude Code, GitHub, Git, operating systems, and third-party services keep their own security policies.

## Report a vulnerability

Do not open a public Issue for a suspected vulnerability. Submit a [private GitHub security advisory](https://github.com/mzored/SkipHow/security/advisories/new). Include the affected SkipHow version, host and version, smallest safe reproduction, impact, and any proposed mitigation.

Use synthetic data. Remove credentials, tokens, private repository names, customer data, personal paths, and production payloads. Do not test against a system you do not own or lack permission to assess.

If private reporting is unavailable, contact the maintainer through the [GitHub profile](https://github.com/mzored) without sending vulnerability details over a public channel. Wait for a private route.

The maintainer will acknowledge a valid report, investigate it, and coordinate a fix before disclosure when practical.

Read [how it works](docs/how-it-works.md) for the boundary between SkipHow policy and host enforcement.
