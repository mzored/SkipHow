# Trust and operations

## Data, commands, and remote changes

SkipHow has no telemetry, hosted service, MCP server, background process, scheduler, or bundled runtime. The host may give it access to project files, commands, and connected services. Host sandboxing, approvals, repository instructions, and the request remain in force.

Read-only requests do not change files, trackers, branches, configuration, or campaign state. An authorized change may edit project files and run relevant builds, tests, formatters, previews, or inspection commands.

GitHub access is optional. SkipHow may write to GitHub for explicit persistence, delivery of existing tracked work, repository-required lifecycle operations, or requested setup. Creating an Issue, branch, comment, closing reference, or Project update is a remote mutation. A Project update requires an explicit `owner/number`; Project failure does not undo a completed canonical Issue or local delivery.

The default package installs no hooks. SkipHow does not build a replacement verifier, service, or integration merely because an optional check is unavailable.

## Configuration

The only project configuration path is `.skiphow/config.json`:

```json
{
  "tracker": "auto",
  "project": null,
  "campaign_root": ".skiphow/runs"
}
```

`tracker` accepts `auto`, `none`, `github`, or `local`. `project` is `null` or an explicit `owner/number`. `campaign_root` is a relative path that must remain inside the project. The shared parser rejects unknown keys, absolute paths, and traversal. A missing file is normal. Setup writes the file only after an explicit request.

To disable remote tracker writes, set `tracker` to `none`. To keep local persistence, use `local`. Revoking `gh` authentication also makes GitHub unavailable without affecting core local work.

## Diagnostics and package proof

Run:

```sh
python plugins/skiphow/scripts/doctor.py
```

Doctor is read-only. It reports host CLI availability separately from package proof. `codex --version` or `claude --version` can establish only `Host CLI: AVAILABLE`; it cannot establish package installation, skill activation, or outcome correctness.

Package proof is `VERIFIED`, `UNVERIFIED`, or `FAILED` and includes its receipt or reference when one exists. `UNVERIFIED` is an honest missing proof, not a pass. Doctor exits nonzero only when an explicit `--require` condition is unmet.

Doctor output does not include token or credential values. Before sharing output, review project names, paths, remote URLs, and error text for private information.

## Update and rollback

Use the host's plugin browser or marketplace commands to refresh the marketplace and reinstall the package. Start a new session so the host loads the updated skill. If Claude Code reports an on-disk plugin change, run `/reload-plugins`.

For rollback, install the previous tagged release from the same marketplace. A package rollback does not delete `.skiphow/config.json`, `.skiphow/inbox.md`, campaign directories, Issues, branches, comments, or Projects.

## Uninstall

In Codex CLI, open `/plugins`, select SkipHow, and choose uninstall. In Claude Code, run:

```text
/plugin uninstall skiphow@skiphow
```

Uninstall removes the plugin package, not project data or remote resources. Review and remove `.skiphow/config.json`, `.skiphow/inbox.md`, and completed campaign directories separately. Delete Issues, branches, comments, or Projects through GitHub only if you no longer need them.
