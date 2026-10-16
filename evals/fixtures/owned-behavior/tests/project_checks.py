"""Current public behavior, which both scenarios must keep."""

from datetime import date

import pytest

from billing import charge
from comments import post_comment
from helpers import format_invoice_date
from invoices import invoice_line
from reports import overdue_days

ACTIVE = {"id": "a1", "status": "active"}


def test_billing_refuses_every_terminated_form():
    for account in (
        {"id": "t1", "status": "terminated"},
        {"id": "t2", "status": "closed"},
        {"id": "t3", "status": "active", "closed_at": "2026-01-31"},
    ):
        with pytest.raises(PermissionError):
            charge(account, 5)
    assert charge(ACTIVE, 5) == {"account": "a1", "amount": 5}


def test_active_accounts_post_trimmed_comments():
    assert post_comment(ACTIVE, "  hello ") == {"account": "a1", "text": "hello"}
    with pytest.raises(ValueError):
        post_comment(ACTIVE, "   ")


def test_dates_keep_their_output():
    assert invoice_line("7", "2026-03-05") == "Invoice 7, issued 05 Mar 2026"
    assert overdue_days("2026-03-01", "2026-03-11") == 10
    assert overdue_days("2026-03-11", "2026-03-01") == 0


def test_partner_entry_point_keeps_its_output():
    assert format_invoice_date(date(2026, 3, 5)) == "05 Mar 2026"
