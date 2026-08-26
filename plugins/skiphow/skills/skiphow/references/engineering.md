# Engineering methods

Load only the method the changed work needs. These guide engineering choices; they create no commands, checkpoints, or ceremony, and ordinary changes should not acquire a design exercise, prototype, or review panel.

- [testing](methods/testing.md) when the durable test seam, expected value, nondeterminism, or external boundary is unclear.
- [review](methods/review.md) when review is requested, required by repository policy, or warranted by risk, a public contract, or weak evidence.
- [design](methods/design.md) when adding or reshaping a module, interface, seam, or dependency boundary.
- [prototype](methods/prototype.md) when one unresolved interaction or state-model question could change the desired behavior.
- [conflicts](methods/conflicts.md) only when Git is already in a conflicted merge or rebase.
