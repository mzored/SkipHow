# Codebase design

Use this method when a change needs a new or reshaped module, interface, seam, or dependency boundary. The agent owns the technical choice unless it changes the product contract.

A useful module gives callers meaningful behavior while hiding sequencing, policy, invariants, error handling, and dependency details; a shallow wrapper repeats them. Apply the deletion test: if removing the module pushes the same complexity into every caller, it earns its place; if the complexity disappears, the wrapper does not.

Add a seam only where behavior varies. One implementation does not justify an adapter; a production dependency plus a real local substitute behind the same interface can. Keep in-process behavior inside the module and test it directly, use a real local substitute for databases, filesystems, and services when practical, put an owned remote system behind a narrow injected interface, and mock a third-party system only when no local substitute exists.

Compare alternatives only while material uncertainty remains: for each, state the caller interface, hidden responsibilities, dependency strategy, failure behavior, and how many places a future change would touch. Choose the smallest design that keeps product behavior clear and tests stable.
