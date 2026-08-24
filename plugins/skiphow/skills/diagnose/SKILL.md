---
name: diagnose
description: Diagnose hard bugs and performance regressions with a deterministic red-green loop while keeping technical investigation inside the CTO boundary.
---

# diagnose

Read `upstream/SKILL.md` and use its diagnostic procedure. It is pinned from `mattpocock/skills` at commit `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`.

Apply these organization rules:

1. Treat the human as the Owner, not the debugging partner. Keep ranked hypotheses and technical checkpoints with the owning CTO or as internal working notes. Show them to the Owner only when their domain evidence or a product decision could change the investigation.
2. Exhaust repository evidence, available environments, tools, and bounded specialist work before requesting an artifact or action from the Owner.
3. Escalate only when missing evidence requires a human or protected action. State what was tried, the exact missing artifact or access, and why diagnosis cannot continue without it.
4. Respect the request boundary. A diagnosis request ends with the verified root cause and evidence. A request that includes a fix continues through regression coverage and the repository's technical execution workflow.
5. Repository and CTO policy own architecture, integration, review, whole-repository verification, tracker lifecycle, and completion claims. Do not duplicate them here.

Always redact secrets and sensitive captured data before sharing output or storing evidence.
