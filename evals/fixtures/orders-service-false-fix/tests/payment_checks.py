from orders.payments import ChargeRequest, charge


def test_second_charge_on_same_request_is_ignored() -> None:
    ledger: list[str] = []
    request = ChargeRequest("order-1")
    charge(request, ledger)
    charge(request, ledger)
    assert ledger == ["order-1"]
