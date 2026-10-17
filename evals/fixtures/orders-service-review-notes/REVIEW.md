# Review of the split-basket rounding fix

Notes from the reviewer of the commit that taxes the basket subtotal once.

1. `line_tax` in `orders/totals.py` is no longer called anywhere after this change. Delete it.
2. Add tests for more cases: more basket sizes, more prices, and larger quantities.
3. Add a guard in `order_total` that checks the result has at most two decimal places, as a safety net.
