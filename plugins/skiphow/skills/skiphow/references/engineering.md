# Engineering methods

Load only the method needed by the changed work. These methods guide engineering choices. They do not create public commands, owner checkpoints, or mandatory ceremony.

- Read [testing](methods/testing.md) when the durable test seam, expected value, nondeterminism, or external boundary is unclear.
- Read [review](methods/review.md) when review is requested, required by repository policy, or warranted by risk, a public contract, or weak evidence.
- Read [design](methods/design.md) when adding or restructuring a module, interface, seam, or dependency boundary.
- Read [prototype](methods/prototype.md) when one unresolved interaction or state-model question could change desired behavior.
- Read [conflicts](methods/conflicts.md) only when Git is already in a conflicted merge or rebase.

Apply the smallest relevant method. Ordinary changes should not acquire a design exercise, prototype, or review panel.
