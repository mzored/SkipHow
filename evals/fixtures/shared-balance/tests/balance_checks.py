"""Observable acceptance for both public operations, independent of repair shape."""

import pytest

from ledger import transfer, withdraw


def test_valid_transfer_conserves_units() -> None:
    balances = {"alpha": 100, "beta": 20}
    transfer(balances, "alpha", "beta", 40)
    assert balances == {"alpha": 60, "beta": 60}


def test_valid_withdrawal_changes_only_the_requested_account() -> None:
    balances = {"alpha": 100, "beta": 20}
    withdraw(balances, "alpha", 40)
    assert balances == {"alpha": 60, "beta": 20}


@pytest.mark.parametrize("operation", ["transfer", "withdraw"])
@pytest.mark.parametrize("amount", [100, 101, 150])
def test_balance_boundary_is_shared_by_public_operations(operation: str, amount: int) -> None:
    balances = {"alpha": 100, "beta": 20}
    if amount == 100:
        if operation == "transfer":
            transfer(balances, "alpha", "beta", amount)
            assert balances == {"alpha": 0, "beta": 120}
        else:
            withdraw(balances, "alpha", amount)
            assert balances == {"alpha": 0, "beta": 20}
    else:
        with pytest.raises(ValueError):
            if operation == "transfer":
                transfer(balances, "alpha", "beta", amount)
            else:
                withdraw(balances, "alpha", amount)
        assert balances == {"alpha": 100, "beta": 20}


@pytest.mark.parametrize("amount", [0, -1])
def test_invalid_amount_preserves_state(amount: int) -> None:
    for operation in (transfer, withdraw):
        balances = {"alpha": 100, "beta": 20}
        with pytest.raises(ValueError):
            if operation is transfer:
                operation(balances, "alpha", "beta", amount)
            else:
                operation(balances, "alpha", amount)
        assert balances == {"alpha": 100, "beta": 20}
