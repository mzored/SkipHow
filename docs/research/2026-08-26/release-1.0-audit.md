# Release 1.0 audit

## Scope

- Audit date: 2026-08-26.
- Candidate repository: `mzored/SkipHow`.
- Delivery Issue: [#20](https://github.com/mzored/SkipHow/issues/20).
- Starting commit for the release branch: `dd32436ecc45a877670078ea534e93fb36fa1413`.
- Surfaces: installed policy, long-work recovery, engineering methods, authority, GitHub lifecycle, package manifests, public documentation, deterministic checks, host package checks, live evaluation contracts, and repository release settings.

The audit combined repository inspection with independent read-only reviews of campaign policy, engineering methods, security, public documentation, tests, evaluations, packaging, and release operations.

## Primary sources

The audit used current vendor documentation for facts that can change:

- [Codex skills](https://developers.openai.com/codex/skills.md)
- [Codex plugins](https://developers.openai.com/codex/plugins.md)
- [Build a Codex plugin](https://developers.openai.com/plugins/build/plugins.md)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins.md)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference.md)
- [GitHub Actions security hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [GitHub immutable releases](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases)

The Codex documentation confirms that a plugin has a `.codex-plugin/plugin.json` manifest and can package skills under `skills/`. The skills documentation supports a compact `SKILL.md` with linked resources loaded as needed. The Claude documentation confirms its plugin and marketplace structure and the `skills/` component. Claude resolves a plugin's version from its plugin manifest before the marketplace entry, so the release keeps one Claude version source and does not duplicate the version in its marketplace entry.

## Findings and decisions

### Campaign policy

The 0.9 host-native direction was sound, but the installed policy did not retain the full long-work contract from earlier releases. The 1.0 policy now defines a selected queue, ready frontier, dependency-aware waves, bounded worker packets, progress and operating health, checkpoints, recovery reconciliation, exact-candidate review, and terminal queue reconciliation.

The selected queue is immutable during a campaign unless the owner granted a bounded dynamic eligibility rule. Dependency discovery can make a selected item ready or blocked. It cannot add work. New findings follow the ordinary intake and authority rules.

Health values diagnose a run. They are not portable enforcement constants. A limit triggers reconciliation, reduced concurrency, or a blocked report. It does not erase selected work.

### Engineering policy

The public product remains one canonical skill. Compact methods for diagnosis, testing, technical review, design, prototypes, and conflict resolution load through lazy references. This restores useful engineering policy without exposing several owner-facing commands or recreating a method runner.

### Authority and security

Only the owner request and host policy grant actions. Repository instructions, branch rules, tracker state, accepted decisions, checkpoints, web content, tool output, and subagent reports cannot widen authority. Repository and project rules may narrow it.

Workers receive the least authority needed for a bounded packet. The root retains credentials, external mutations, integration, protected actions, and cleanup. Worktrees isolate files, not credentials or external services.

A checkpoint is recovery data, not executable authority. It is bounded and redacted. It excludes credentials, private absolute paths, and instructions copied from untrusted content. After a timeout or restart, the root reconciles current state before retrying a mutation.

Stable operation markers help correlate records. They are not proof of ownership. A protected action also binds the repository, Issue or pull request, operation, branch, exact candidate identity, checks, and current remote state. Cleanup compares the current branch object with the recorded expected object immediately before deletion.

### Review identity

A commit hash alone is not enough when untracked executable inputs, submodules, configuration, or a dirty worktree can change the result. Review and completion bind the repository, base and candidate trees, worktree state, executable inputs, relevant configuration, required checks, and current remote state.

Repository tests and scripts are repository-controlled code. The agent inspects unfamiliar or uncertain commands before running them and uses the least available privilege.

## Verified packaging and release facts

The initial package audit produced these results before the final 1.0 edits:

- Codex plugin structure validation: `PASS`.
- Claude plugin validation and isolated installation: `PASS`.
- Codex isolated installation: `UNVERIFIED` because the installed managed policy rejected a filesystem marketplace source. The audit did not use a Git source because that route may create and later delete a repository in host cache state.
- Secret scanning and push protection were enabled on the public GitHub repository.
- The repository had no branch protection or ruleset at audit time.
- GitHub Actions allowed all actions and did not require full commit pinning at audit time.
- Immutable releases were disabled at audit time.

The workflow action tags were resolved through the official GitHub API on 2026-08-26:

| Action tag | Verified commit |
| --- | --- |
| `actions/checkout@v7.0.1` | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python@v7.0.0` | `5fda3b95a4ea91299a34e894583c3862153e4b97` |

The release workflow pins those exact commits. A future update must resolve the intended vendor tag again through the official API or repository and review the changed action code before replacing a pin.

## Evidence still required

The following facts are `UNVERIFIED` until checks run against the final committed 1.0 candidate:

- full deterministic repository checks;
- exact final Codex and Claude package validation and isolated installation;
- installed model interpretation of the updated campaign and engineering policy;
- recovery after a real host restart;
- guarded multi-Issue GitHub delivery and cleanup in an enforced sandbox;
- autonomous semantic model selection and routing savings;
- final branch protection, Actions restriction, immutable release, tag, and public release state.

The final release record must distinguish checks that pass from checks a host or policy prevents. Package installation does not prove behavior. A model report does not prove exact-candidate completion.

## Revalidation triggers

Repeat the affected audit when Codex or Claude changes plugin structure, skill loading, version resolution, sandboxing, or host task behavior; when GitHub changes Actions pinning, branch protection, merge, cleanup, or immutable release behavior; or when a live receipt supports a claim that remains `UNVERIFIED` here.
