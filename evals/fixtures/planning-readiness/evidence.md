# Synthetic planning evidence

These are invented repository audit results for planning decisions, not measurements of a real application.
The selected scenario is named in the owner request. No implementation is present or requested.

## Localization

The accepted scope is a new locale for checkout, account settings, and appointment booking. Old training content
has been removed from the product and is excluded. The source inventory contains 360 short labels, 90 validation
messages with parameters, and 12 policy passages of 600 words each. Policy passages need their surrounding
section for meaning. The three journeys share one locale JSON file and one message formatter. Account-language
persistence is absent; a generic locale selector and placeholder checker already exist.

The current proposed tracker groups are language support, all customer screens, and final verification.
Each journey crosses screen text, service errors, confirmations, and rendered layout. Translation and independent
meaning/editorial review can use separate outputs after terminology and the relevant source inventory are ready.
Writing those results back touches the shared locale file. No process enforces concurrent ownership of that file.
Rendered checks require working locale support; translation itself does not. The placeholder checker cannot judge
meaning or visual clipping. The final reviewer would otherwise receive every translated string and every screen
at once. The payment provider's new error format is still unavailable, so exact payment-error assignments depend
on that result. Existing public interface names, fee amounts, and user-authored content must stay unchanged.

## Mechanical migration

An internal logging field changes from request_id to correlation_id across 48 independent consumers. They all
write to one collector which can accept both fields during migration. Six consumers are library adapters whose
contract tests run separately. One schema and one generated type file are shared. The old field can be removed
only after all consumers and the rollback target accept the new form. This changes no user journey. A retained
schema validator and consumer contract checks establish compatibility. Consumer inventory and changed-field
search establish completeness. No fixed batch size is prescribed by those checks.

## Small change

One confirmation message has an incorrect noun in one locale. Its single source entry and rendered confirmation
snapshot are the entire affected scope. Existing snapshot tooling verifies the message. There are no parallel
consumers, schema changes, unresolved product decisions, or downstream assignments. The owner wants the noun
to match the existing button label. A plan can explain this cohesive change without multiple workers or tickets.
