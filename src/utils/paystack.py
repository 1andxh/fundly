import httpx
from typing import Any
from decimal import Decimal, ROUND_HALF_UP
from src.config import config

PAYSTACK_SECRET_KEY = config.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = config.PAYSTACK_BASE_URL


class PaystackClientError(Exception):
    """Raised for Paystack API/network failures."""


class PaystackClient:
    def __init__(self):
        self.secret_key = PAYSTACK_SECRET_KEY
        self.base_url = PAYSTACK_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    async def intialize_transcation(
        self,
        email: str,
        amount: Decimal,
        reference: str,
        callback_url: str | None = None,
    ) -> dict[str, Any]:
        """initialize a transaction"""
        url = f"{self.base_url}/transaction/initialize"

        normalized_amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        amount_in_pesewas = int(normalized_amount * 100)

        payload = {
            "email": email,
            "amount": amount_in_pesewas,
            "reference": reference,
            "currency": "GHS",
        }
        if callback_url:
            payload["callback_url"] = callback_url

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url=url, json=payload, headers=self.headers)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise PaystackClientError("Paystack request failed") from exc

            data = response.json()

            if data.get("status"):
                return data["data"]
            raise PaystackClientError(f"Paystack error: {data.get('message')}")

    async def verify_transaction(self, reference: str) -> dict[str, Any]:
        "verify transaction from reference"

        url = f"{self.base_url}/transaction/verify/{reference}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url=url, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            if data.get("status"):
                return data["data"]
            else:
                raise Exception(f"Paystack error: {data.get('message')}")

    async def refund_transaction(self, reference: str) -> dict[str, Any]:
        url = f"{self.base_url}/refund"

        payload = {"transaction": reference}

        async with httpx.AsyncClient() as client:
            response = await client.post(url=url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            if data.get("status"):
                return data["data"]
            else:
                raise Exception(f"Paystack error: {data.get('message')}")


paystack_client = PaystackClient()
