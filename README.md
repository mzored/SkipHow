# SkipHow

SkipHow is an open source plugin collection that carries work from an owner's idea to verified delivery. It keeps product decisions with a Product Director, technical decisions with a CTO, and asks the owner only for decisions that require owner authority.

SkipHow supports Codex and Claude Code as first-class hosts. The plugin has no MCP server, telemetry, remote service, or credential flow.

## Install with Codex

Use a current Codex installation with plugin marketplaces enabled:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

The marketplace name is `skiphow`, as declared in its marketplace manifest.

## Install with Claude Code

Use a current Claude Code installation with marketplace plugin commands:

```sh
claude plugin marketplace add mzored/SkipHow
claude plugin install skiphow@skiphow
```

## Skills

Most requests can use ordinary language. The plugin routes them through these skills:

| Skill | Purpose |
| --- | --- |
| `skiphow` | Route owner intent and enforce decision ownership. |
| `idea` | Capture a raw idea in the canonical tracker. |
| `shape` | Research and shape an idea into an approved Product Contract. |
| `develop` | Freeze approved work into a campaign and hand it to the CTO. |
| `fix` | Repair defects with rigor proportional to uncertainty and risk. |
| `diagnose` | Internal root-cause loop used when initial inspection is inconclusive. |
| `cto-run` | Execute or resume a durable technical campaign. |

The owner's normal interface is `idea`, `shape`, `develop`, and `fix`. `skiphow` can select them implicitly. `fix` handles defect reports, calls `diagnose` only for unclear causes, and starts `cto-run` only when the repair needs a durable campaign. Both `diagnose` and `cto-run` remain internal capabilities.

## Run cto-run

You can still invoke `cto-run` explicitly for a prepared technical campaign. Give it a repository runbook, a durable run directory, and an optional target.

In Codex:

```text
$cto-run docs/runbooks/release.md .skiphow/runs/release-0.1.0 main
```

In Claude Code, plugin skills use the plugin namespace:

```text
/skiphow:cto-run docs/runbooks/release.md .skiphow/runs/release-0.1.0 main
```

The run directory records `state.json`, `journal.jsonl`, `briefing.md`, decisions, evidence, receipts, and `FINAL.md`. Reuse that directory to resume the same campaign.

## Host requirements

The host must provide file access, command execution, task controls, and a way to preserve the run directory. The workflow reads repository instructions and the runbook before it changes a project. Host policy takes priority.

## Clean uninstall

Remove the installed plugin, then remove the marketplace if no other plugin uses it.

```sh
codex plugin remove skiphow@skiphow
codex plugin marketplace remove skiphow
```

```sh
claude plugin uninstall skiphow@skiphow
claude plugin marketplace remove skiphow
```

## Support policy

SkipHow supports the current Codex and Claude Code plugin workflows. A support claim needs a reproducible installation or validation check for that host. Report defects through the repository issue templates.

## Limitations

SkipHow coordinates work inside a host session. It does not ship hooks, a bundled command-line program, an MCP server, telemetry, or a remote control plane. It cannot bypass host policy, repository instructions, protected-action approval, or missing authority. Tracker-based skills require the host to have access to the project's canonical tracker.

## Architecture

Read [the architecture guide](docs/architecture.md) for the canonical skill, the Claude Code adapter, durable files, and release gates.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). The repository also follows its [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Read [SECURITY.md](SECURITY.md) before reporting a vulnerability.

## Changelog

Release notes are in [CHANGELOG.md](CHANGELOG.md).

## License

SkipHow is licensed under the [MIT License](LICENSE).
