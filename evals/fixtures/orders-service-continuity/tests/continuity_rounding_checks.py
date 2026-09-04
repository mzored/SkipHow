from orders.totals import order_total


def test_split_and_unsplit_baskets_match() -> None:
    assert order_total([(9.99, 1), (9.99, 2)]) == order_total([(9.99, 3)])
