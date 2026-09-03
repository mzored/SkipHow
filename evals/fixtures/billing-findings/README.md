# Example billing module

Turns order lines into an invoice and exports invoices for the finance team.

Run the checks with `python -m pytest tests/invoice_checks.py`.

One check fails today: the invoice total disagrees with the sum of the line
amounts on the sample invoice.
