# Writing for agents

Start with the behavior the instruction must change and the evidence that the default behavior is insufficient. Write outcomes, authority boundaries, and hard invariants. Leave tools and implementation choices to the agent unless a specific mechanism is itself required.

For an automatically discovered skill, make the description a precise trigger. Name the situations that should load it and the nearby situations that should not. Keep universally needed rules in the main file. Move conditional material behind a clear pointer only when the branch saves attention without hiding a requirement.

Give each rule one authoritative home. Remove contradictions and obsolete text when behavior changes. Do not copy facts the agent can cheaply read from configuration, source, or command help. Avoid fixed counts, magic phrases, provider-specific commands, and mandatory process unless evidence proves the constraint is necessary.

Write completion conditions the agent can verify. Prefer positive, direct instructions in project language. Explain uncommon terms once and keep related rules together.

Check the final document as an instruction system: trigger, authority, action, stopping condition, and conflicts with higher-priority or nearby instructions. Validate syntax and links. When model behavior matters, treat real runs as evidence and deterministic lint as package evidence only.
