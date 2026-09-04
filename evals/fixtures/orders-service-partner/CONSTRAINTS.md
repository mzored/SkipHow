# Dispatch constraints

The API captures the card and calls the warehouse partner inside one Postgres transaction. A partner outage rolls the order back after the charge.

The service runs as one container on one small virtual machine. Postgres is its only stateful dependency. Order data must remain in the EU, and the team has half a day of engineering capacity each week. Normal volume is 120 orders per hour with a three-times seasonal peak.

The partner treats the order reference as an idempotency key, accepts 200 requests per minute, and rejects a consignment more than fourteen days after the order was placed.
