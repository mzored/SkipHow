# Campaign delivery runbook

Deliver the immutable campaign recorded by the technical controller.

- Freeze one outcome, included work, exclusions, source identity, and priority order already established by the Owner or canonical queue.
- Decompose only concrete frontier work into independently verifiable vertical slices. Keep unresolved later work unspecified until dependencies clarify it.
- Keep Product acceptance, reuse decisions, migrations, rollback, and specialist review sparse. Add each section only when the work triggers it.
- Bind completion evidence to the delivered state. Reconcile tracker state only for tracked items.
- Do not create all artifact directories in advance. Create a directory when its first artifact is written.
- Generate the final report from durable state at completion instead of maintaining a second hand-written source of truth.

The campaign ends when every included item has terminal evidence or a recorded authorized blocker, mutable state is reconciled, and no executable lane remains. A product acceptance receipt is required only when the governing extended decision or repository policy requires one.
