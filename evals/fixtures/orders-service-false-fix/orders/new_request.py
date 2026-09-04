from orders.payments import ChargeRequest


def from_button_press(order_id: str) -> ChargeRequest:
    return ChargeRequest(order_id)
