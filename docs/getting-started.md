# Getting started

SkipHow installs as a plugin. It does not install a Python package or start a service.

## Prerequisites

Use a current Codex CLI or Claude Code release with plugin support. Git must be available because both hosts fetch this repository as a marketplace. GitHub delivery also needs repository access through the host or GitHub CLI.

## Codex

Install the marketplace and plugin:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Check the installed entry:

```sh
codex plugin list
```

Start a new session, then ask for an outcome. If implicit selection does not activate SkipHow, include `$skiphow` in the request.

Update the marketplace snapshot and reinstall the plugin:

```sh
codex plugin marketplace upgrade skiphow
codex plugin add skiphow@skiphow
```

Start a new session after the update.

Uninstall the plugin:

```sh
codex plugin remove skiphow@skiphow
```

Remove the marketplace only when no installed plugin still needs it:

```sh
codex plugin marketplace remove skiphow
```

## Claude Code

Use the HTTPS URL so installation does not depend on an SSH key:

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Check the installed entry:

```sh
claude plugin list
```

Start a new session. If implicit selection does not activate SkipHow, use `/skiphow:skiphow`.

Update both the marketplace and plugin:

```sh
claude plugin marketplace update skiphow
claude plugin update skiphow@skiphow
```

Claude Code requires a restart before the updated plugin becomes active.

Uninstall the plugin:

```sh
claude plugin uninstall skiphow@skiphow
```

Remove the marketplace only when no installed plugin still needs it:

```sh
claude plugin marketplace remove skiphow
```

## Troubleshooting

If the plugin does not appear, confirm the marketplace is listed, rerun the host's marketplace update command, and start a new session. An old session keeps the skills it loaded at startup.

If installation fails under managed policy, ask the workspace administrator whether the `mzored/SkipHow` marketplace is allowed. SkipHow does not bypass host policy.

If a command shown here is missing, update the host and check its current plugin documentation. Host commands and managed controls change independently of SkipHow.

An uninstall removes the plugin from the host. It does not delete Issues, pull requests, Git branches, `.skiphow/inbox.md`, `.skiphow/handoff.md`, or host transcripts. Remove retained records through the system that owns them.
