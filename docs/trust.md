# Trust and operations

## Data and commands

SkipHow has no telemetry, hosted service, MCP server, or background process. The host may give it access to project files, commands, and connected services. SkipHow uses those capabilities only within the request, repository instructions, and host permissions.

For authorized change requests, it may edit project files and run the project's build, test, formatter, or inspection commands. Read-only requests do not change files, trackers, branches, or campaign state.

GitHub access is optional. SkipHow reads or changes GitHub only for explicit persistence, existing tracked work, repository-required lifecycle operations, or requested setup. A Project is changed only when an explicit configuration identifies it. The default package installs no hooks.

## Disable an integration

Set `tracker: none` and `project: disabled` in `.skiphow/config.yml`, or remove the file to return to automatic safe defaults. Revoking `gh` authentication also makes the GitHub adapter unavailable without affecting core local work.

## Diagnostics without secrets

Run:

```sh
python plugins/skiphow/scripts/doctor.py
```

The report contains capability states, not tokens or credential values. Before sharing any command output, review repository names, paths, remote URLs, and error text for private information.

## Update

Update the marketplace source, then reinstall the plugin through the host's plugin command. Start a new task or session so the host loads the new package. Read the changelog for migration notes before updating a repository with an active campaign.

## Roll back

Install the previous tagged release from the marketplace source. Existing `.skiphow/inbox.md`, optional configuration, Issues, Projects, and campaign directories are user data and are not removed by a package rollback.

## Uninstall

Run:

```sh
codex plugin remove skiphow@skiphow
claude plugin uninstall skiphow@skiphow
```

Uninstalling does not delete project files or remote resources. Remove `.skiphow/config.yml`, `.skiphow/inbox.md`, or completed campaign directories only after reviewing them. Delete or disconnect a GitHub Project separately if you created it and no longer want it.
