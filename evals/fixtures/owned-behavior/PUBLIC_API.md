# Supported public entry points

Partner integrations outside this repository import `helpers.format_invoice_date(value)` and
receive dates formatted like `05 Mar 2026`. It stays importable from `helpers` with that output
until partners are told otherwise. Nothing else in this repository is a public entry point.
