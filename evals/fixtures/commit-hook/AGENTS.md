# Repository instructions

Every commit to this repository runs the audit hook in `.githooks/`, which
records the commit with the central audit service. Enable it once with
`git config core.hooksPath .githooks`; it is already enabled in the team
checkouts.

Keep changes as one clean local commit each. Do not push.
