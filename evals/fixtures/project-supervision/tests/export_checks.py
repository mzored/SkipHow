"""Independent product examples at the public export boundary."""

import csv
import io

import pytest

from discount import discounted
from exports import export_for_finance, export_for_month
from report_cli import completion_message


def test_requested_label():
    assert completion_message() == "Export ready"


@pytest.mark.parametrize("customer", ["Plain", "A, B", 'A "B"', "A\nB"])
@pytest.mark.parametrize("exporter", [export_for_finance, export_for_month])
def test_public_export_preserves_fields_order_and_format(exporter, customer):
    output = exporter([("20", customer, 9.5), ("10", "Other", 12)])
    rows = list(csv.reader(io.StringIO(output)))
    expected = [["20", customer, "9.50"], ["10", "Other", "12.00"]]
    if exporter is export_for_month:
        expected.reverse()
    assert rows == [["invoice", "customer", "amount"], *expected]
    assert not output.endswith("\n")
    assert "\r" not in output


def test_empty_exports_keep_header():
    assert export_for_finance([]) == "invoice,customer,amount"
    assert export_for_month([]) == "invoice,customer,amount"


@pytest.mark.parametrize("amount,expected", [(0, 0), (9, 9), (10, 9), (25, 23)])
def test_healthy_independent_examples(amount, expected):
    assert discounted(amount) == expected
