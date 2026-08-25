---
name: codebase-design
description: Internal module and interface design capability for CTO-selected architecture or restructuring decisions.
---

# codebase-design

Use this capability when a CTO decision needs a clearer module, interface, seam, or dependency shape. It is internal. The CTO owns the technical decision and does not ask the Owner to choose an interface, adapter pattern, or design process.

Use these terms consistently:

- A module combines an interface and its hidden implementation.
- The interface includes types, invariants, ordering, errors, required configuration, and relevant performance behavior.
- A deep module gives callers substantial behavior through a small interface. A shallow module mostly passes its interface onward.
- A seam is where behavior can vary without changing its caller. An adapter is one implementation placed at that seam.

Prefer deep modules. Reduce methods and parameters, hide sequencing and policy inside the implementation, and keep knowledge near the code that owns it. Use the deletion test: if removing a module only moves the same complexity into every caller, the module has value; if the complexity disappears, it was likely a pass-through.

Put a seam only where behavior genuinely varies. One implementation does not justify an adapter by itself. A production implementation plus a real test substitute can justify one, but keep internal test seams out of the external interface.

Classify each dependency before choosing the design:

- In-process behavior can stay inside the module and be tested directly.
- A locally substitutable dependency should use the real local substitute in tests.
- A remote system the project owns can sit behind an injected port with production transport and in-memory adapters.
- A true external system can sit behind an injected port with a narrow mock when no practical substitute exists.

Callers and tests should use the same external interface. Accept varying dependencies rather than constructing them inside business logic, and return observable results where practical. When a new deep-module test replaces shallow implementation-coupled tests, remove the obsolete tests instead of layering both sets.

Compare alternatives when uncertainty warrants it, but choose the lightest analysis that resolves the decision. Do not require a three-agent design exercise or a user-facing checkpoint.

For each viable design, write the interface, usage example, hidden responsibilities, dependency strategy, and trade-offs in interface size and change locality. Compare alternatives only when the first reasonable design leaves material uncertainty. Recommend and implement the strongest option under CTO authority.
