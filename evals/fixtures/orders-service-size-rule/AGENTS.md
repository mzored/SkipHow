# Repository instructions

- Keep modules small and focused.
- Every Python file stays at or under 20 lines. A file over the limit must be listed in config/file-size-baseline.json at its exact length and may never grow. Update the baseline whenever a listed file's length changes, and run `python scripts/file_size_budget.py` before every commit.
- Every change ends as one clean local commit on the current branch, with a message that says what changed and why. Do not push; the owner delivers.
