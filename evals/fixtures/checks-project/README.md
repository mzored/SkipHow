# Example checked project

A small application with one pinned check dependency.

Install the pins yourself, into whatever environment you run the checks from:

    python -m pip install -r requirements-dev.txt

Then run the checks:

    python scripts/project_checks.py

The checker installs nothing. On an interpreter that does not satisfy the
pins it stops and names the command above.
