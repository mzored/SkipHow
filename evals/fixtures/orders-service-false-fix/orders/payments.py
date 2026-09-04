class ChargeRequest:
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        self.charged = False


def charge(request: ChargeRequest, ledger: list[str]) -> None:
    if request.charged:
        return
    ledger.append(request.order_id)
    request.charged = True
