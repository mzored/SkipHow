# Setup

Open this when the owner asks to enable, check, or disable SkipHow's default governance on this machine, or asks why SkipHow did not load. Nothing here grants project authority: configuring the host to load this skill changes what the model reads, not what the owner has allowed.

## What the host reads

Default governance is one owned block in the trusted user instruction file the host reads before project work. Codex reads `AGENTS.override.md` in its home when that file exists and is not empty, and `AGENTS.md` otherwise; `CODEX_HOME` relocates the home. Claude Code reads `CLAUDE.md` and every unconditional `rules/*.md` file in its configuration directory for every project, a rule with `paths:` frontmatter only for matching files; `CLAUDE_CONFIG_DIR` relocates that directory. A block in a file the host does not read configures nothing, and a second copy in another file is litter that may become active later.

The helper beside this skill, [`scripts/activation.py`](../scripts/activation.py), resolves that file the same way and writes only its own block. Run it with the interpreter available on the machine, giving the directory that holds this skill's `SKILL.md`:

```sh
python <skill directory>/scripts/activation.py status --host codex
python <skill directory>/scripts/activation.py install --host claude-code
python <skill directory>/scripts/activation.py install --host claude-code --apply
python <skill directory>/scripts/activation.py remove --host codex --apply
```

`install` adds the block to the effective file and moves a copy found in any other file it may edit; `remove` deletes every copy it may edit. It never writes through a symbolic link: a linked file is inspected and reported, and its target is left for the owner. Without `--apply` each command shows the exact diff and changes nothing. Use `--target <file>` only when the owner names another trusted file. Where no Python interpreter is available, append the block text shown by the preview yourself and remove exactly that text to disable.

## One confirmation, three facts

Changing the owner's user instructions changes their machine, so show the preview and get one explicit confirmation before `--apply`; do not ask again for the same file in the same session. Report three facts separately: configured, meaning the block is in the effective file; available, meaning the host lists the plugin as installed and enabled; and loaded, which only a fresh session shows. A status result is never loading evidence.

## When something blocks it

A managed policy file, such as a machine-wide requirements file or managed settings, loads before user instructions and may restrict plugin sources, marketplaces, or instructions. Report the exact file and what it blocks. Do not bypass it, copy the policy into another file, or ask the owner to inspect code or logs. If the plugin is not installed or is disabled, name the host command that installs or enables it rather than editing configuration the helper does not own.

Disable before uninstalling: remove the block first, then remove the plugin, so no instruction asks the host to load a skill that is no longer there.
