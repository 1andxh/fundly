import hmac
import hashlib
from typing import Any
from fastapi import Request, HTTPException, status
from src.config import config
import json


async def verify_paystack_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    # compute has
    computed_hash = hmac.new(
        key=secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha512
    ).hexdigest()
    # compare signature from header
    return hmac.compare_digest(computed_hash, signature)


class PaystackSignatureGuard:
    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key

    async def __call__(self, request: Request) -> Any:
        signature = request.headers.get("x-paystack-signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Paystack signature header missing",
            )

        payload = await request.body()

        computed_hash = hmac.new(
            key=self.secret_key.encode("utf-8"), msg=payload, digestmod=hashlib.sha512
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        return json.loads(payload)


paystack_guard = PaystackSignatureGuard(secret_key=config.PAYSTACK_SECRET_KEY)
