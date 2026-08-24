---
name: codebase-design
description: Internal module and interface design capability for CTO-selected architecture or restructuring decisions.
---

# codebase-design

Use this capability when a CTO decision needs a clearer module, interface, seam, or dependency shape. It is internal. The CTO owns the technical decision and does not ask the Owner to choose an interface, adapter pattern, or design process.

Prefer deep modules that hide behavior behind a small, explicit interface. Describe the interface beyond types: invariants, ordering, errors, required configuration, and relevant performance behavior. Put a seam where behavior genuinely varies. Add an adapter only when at least two justified implementations need it. Keep internal test seams private and test through the external interface.

Classify dependencies before choosing a seam: in-process, locally substitutable, remote but owned, or true external. Preserve locality by concentrating behavior and verification in the module. Replace shallow, implementation-coupled tests with behavioral tests at the chosen interface when that is safe and useful.

Compare alternatives when uncertainty warrants it, but choose the lightest analysis that resolves the decision. Do not require a three-agent design exercise or a user-facing checkpoint.

Read `upstream/SKILL.md` and `upstream/DEEPENING.md` for the pinned vocabulary and dependency guidance. This wrapper, repository policy, and CTO decisions take precedence. `DESIGN-IT-TWICE.md` is deliberately not vendored because its mandatory multi-agent and user-facing procedure does not apply here.
