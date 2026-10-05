import json
import urllib.request


class CardGateway:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def charge(self, order_id: str, amount_cents: int) -> str:
        body = json.dumps({"order": order_id, "amount": amount_cents}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/charges",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)["charge_id"]
