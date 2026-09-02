# Project setup

Use this for the first durable record in a project with no recorded convention for tracked work. Settle where this project keeps tracked work once, so later sessions never re-derive it.

Inspect before asking. Read the remote, any tracker already in use, how its recent items are classified, whether the work is private or public, and the instruction file the project already keeps for agents. A project that clearly tracks work in one place has already answered most of the question.

Ask the owner one plain-language question: where their tasks and findings should live, and who may see them. Recommend what the project already uses and explain the visible consequence of each option, including whether a record would become public. Do not ask about formats, labels, schemas, or tooling.

Record the answer in the project's own agent instruction file rather than a file of your own: the destination, who may see it, and the classification the tracker already uses. Record with it the calls this tracker needs for the operations [tracked work](tracked-work.md) performs, wherever those are not obvious from the tracker's own interface. Those operations are claiming an item, linking a change to it, recording a dependency, and closing it.

A tracker that reaches one of them only through a lower-level call, or that identifies an item differently there than it does everywhere else, is a detail every later session would otherwise rediscover or get wrong silently. Where the project keeps no such file, write the record where any agent working on this project would read it, not only the host you happen to be running on. Otherwise the next session on the other host asks the same question again.

Keep it short and in ordinary project text: a destination, an audience, a classification, and only the calls that are not obvious. Never introduce a separate configuration format, and never create a tracker the owner did not choose.

Later work follows that record without inspecting again. Refresh it only when a write is rejected, a recorded call stops working, the recorded destination no longer exists, or the tracker's own convention has visibly moved.
