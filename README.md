# SkipHow

SkipHow is an open source plugin collection for agent skills. Version 0.1.0 contains `cto-run`, a skill for running a software campaign from a runbook while keeping durable state that can be checked after a restart.

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

## Run cto-run

Invoke `cto-run` explicitly. It does not run from an incidental mention or automatic skill selection. Give it a repository runbook, a durable run directory, and an optional target:

```text
cto-run docs/runbooks/release.md .skiphow/runs/release-0.1.0 main
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

`cto-run` coordinates work inside a host session. It does not ship hooks, a bundled command-line program, an MCP server, telemetry, or a remote control plane. It cannot bypass host policy, repository instructions, protected-action approval, or missing authority.

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
