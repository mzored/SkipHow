---
name: diagnose
description: Internal diagnosis capability for hard bugs and performance regressions whose cause remains unclear after initial inspection.
---

# diagnose

Read `upstream/SKILL.md` and use Phases 1 through 4 of its diagnostic procedure. It is pinned from `mattpocock/skills` at commit `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`.

Stop after the probes prove the root cause. Do not execute Phase 5. Remove tagged diagnostic instrumentation and throwaway prototypes using the relevant Phase 6 cleanup steps, then return the root cause and evidence to `fix` for risk classification and repair.

Apply these organization rules:

1. Treat the human as the Owner, not the debugging partner. Keep ranked hypotheses and technical checkpoints with the owning CTO or as internal working notes. Show them to the Owner only when their domain evidence or a product decision could change the investigation.
2. Exhaust repository evidence, available environments, tools, and bounded specialist work before requesting an artifact or action from the Owner.
3. Escalate only when missing evidence requires a human or protected action. State what was tried, the exact missing artifact or access, and why diagnosis cannot continue without it.
4. Return the verified root cause and evidence to the calling workflow. Let `fix` reassess risk and choose the repair path; do not start `cto-run` merely because diagnosis was required.
5. Repository and CTO policy own architecture, integration, review, whole-repository verification, tracker lifecycle, and completion claims. Do not duplicate them here.

Always redact secrets and sensitive captured data before sharing output or storing evidence.
