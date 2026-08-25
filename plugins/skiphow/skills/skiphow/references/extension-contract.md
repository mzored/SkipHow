# Extension contract

Domain and integration capabilities are internal and lazy. Add one only when a demonstrated request and a deterministic regression test justify its context and maintenance cost. Do not add a new public intent or adapter for speculative future use.

Each extension declares:

- its trigger and negative trigger;
- the authority that owns its decisions;
- required inputs;
- allowed local and remote mutations;
- protected actions that need explicit authority;
- its output and evidence contract;
- the fallback when it is unavailable;
- its runtime context budget;
- deterministic regression coverage;
- source and license when adapted from external work.

The controller loads an extension only after its trigger matches. The negative trigger prevents adjacent work from paying its cost. An unavailable extension must preserve the mutation boundary, use a smaller available mechanism when that still satisfies the request, and otherwise report the affected result as blocked or `UNVERIFIED`.
