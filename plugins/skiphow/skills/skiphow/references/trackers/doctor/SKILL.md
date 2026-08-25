---
name: doctor
description: Internal read-only diagnostics for core readiness and optional repository, GitHub Issues, Project, and host capabilities.
---

# Doctor

Use this only when the user asks for readiness or integration diagnostics. Do not run it before ordinary work.

Run the bundled read-only doctor when Python is available, or perform the same checks with host tools when it is not:

```text
python <plugin-root>/scripts/doctor.py [owner/repository]
```

Report these independent states:

```text
Core: READY | LIMITED
Repository: READY | LIMITED
GitHub Issues: AVAILABLE | NOT AVAILABLE
GitHub Project: CONNECTED | NOT CONFIGURED | UNAVAILABLE
Configuration: VALID | INVALID
Host CLI: AVAILABLE | NOT AVAILABLE
Package proof: VERIFIED | UNVERIFIED | FAILED
```

CLI availability does not prove package installation or activation. Package proof needs a receipt or reference for the exact candidate. Missing Python, `gh`, authentication, Project, or another optional integration never makes core readiness fail. Return nonzero only for an explicit `--require` condition. Do not install tools, authenticate, create configuration, or mutate local or remote state.
