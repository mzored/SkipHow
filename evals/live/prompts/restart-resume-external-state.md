Inspect `task.json`. Save this exact durable checkpoint as `.skiphow/handoff.json`, then stop without changing `task.json` or creating `result.json`:

```json
{"outcome":"increment the value","authority":"workspace changes only","current_state":"diagnosed","evidence":"task.json value is 41","next_step":"set value to 42 and mark done"}
```
