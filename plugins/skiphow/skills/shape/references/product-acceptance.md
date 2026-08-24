# Product acceptance

Product acceptance checks that the exact implementation candidate delivers the approved Product Contract. It is required for user-visible work governed by a Product Contract. It is not Owner QA and it does not reopen technical decisions.

Before delivery, the Product Director records the acceptance scenarios that matter to the contract. Include the main journey and any material alternative, empty, error, or recovery state. State the evidence that can show each scenario, such as a working runtime flow, rendered output, API response, or accessibility result.

After the CTO has verified an exact candidate commit, the Product Director compares that candidate and its evidence with the Product Contract. Record the contract revision, candidate commit, evidence location, reviewer, date, and either `accepted` or `returned`.

For `direct` or `tracked-direct` delivery, store the receipt at the repository's established evidence location. When the repository has no convention, use `.skiphow/evidence/product-acceptance/<candidate-commit>/<contract-id>.json`; this is an evidence artifact, not a durable campaign. For `cto-run`, use the campaign receipt location from the durable state contract.

Return only concrete mismatches between the candidate and the contract. The CTO corrects them and submits a new exact candidate. If the desired behavior itself must change, return to `shape` for a Product Contract decision. Ask the Owner only when that decision needs Owner authority.
