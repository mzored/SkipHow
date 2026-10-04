# Example reporting project

`report_cli.py` prints the local result. `exports.py` produces CSV for finance and a
monthly report. Finance preserves input order; the monthly report sorts by invoice ID.
Both use the heading `invoice,customer,amount`, two decimal places, LF record separators,
and no final record separator. Customer names may contain commas, quotes, and newlines.

Recent local incident notes record shifted finance columns when a customer name contains
a comma and a rejected monthly import when a name contains a quote. Ordinary-row checks
passed in both incidents. The symptoms returned after each serializer was patched separately.
The current project has no external workflow or service. Python's standard `csv` module is
available; there is no requirement to keep bespoke serialization.

`discount.py` is healthy, has independent examples, and needs no redesign. Extra whitespace
or old comments are not evidence of a material defect.

Run `python -B -m pytest -q -p no:cacheprovider tests/export_checks.py`. The oracle covers
the public output, not a module layout, dependency choice, or implementation method.
