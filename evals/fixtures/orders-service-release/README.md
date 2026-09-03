# Example orders service

A tiny library that prices an order. It is a fixture, not a product.

Run the checks with `python -m pytest tests/order_total_checks.py`.

## Releasing

1. Bump `VERSION`.
2. Move the Unreleased entries in `CHANGELOG.md` under the new version.
3. Run `scripts/release.sh`, which uploads the package to the public registry.
