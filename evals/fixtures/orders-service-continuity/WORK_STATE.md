# Owned continuation state

Outcome: fix the penny mismatch when an equivalent basket is split across lines.

Authority: local source and test changes only. No remote or shared delivery was requested.

Evidence: `tests/continuity_rounding_checks.py` fails because tax is rounded per line. No source fix has been made.

Next: confirm the rounding boundary, make the smallest repair, run both order-total checks, and cold-review the final diff.
