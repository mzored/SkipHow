# Codebase design

Use this method when a change needs a new or reshaped module, interface, seam, or dependency boundary. The agent owns the technical choice unless it changes the product contract.

## Put complexity behind a small interface

A useful module gives callers meaningful behavior while hiding sequencing, policy, invariants, error handling, and dependency details. A shallow wrapper repeats those details without reducing them.

Use the deletion test. If removing the module merely pushes the same complexity into every caller, the module earns its place. If the complexity disappears, the wrapper probably does not.

Add a seam only where behavior truly varies. One implementation does not justify an adapter by itself. A production dependency plus a real local substitute can justify one when both use the same product interface.

Classify dependencies before designing the boundary:

- Keep in-process behavior inside the module and test it directly.
- Use a real local substitute for databases, filesystems, or services when practical.
- Put an owned remote system behind an injected narrow interface with a local adapter.
- Mock a third-party system only when no practical local substitute exists.

Compare alternatives only while material uncertainty remains. For each viable option, state its caller interface, hidden responsibilities, dependency strategy, failure behavior, and how many places a future change would touch. Choose the smallest design that keeps product behavior clear and tests stable.
