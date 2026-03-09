from fastapi import HTTPException, status
import hmac
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from decimal import Decimal

from src.contributions.models import Contribution, PaymentStatus
from src.campaigns.models import Campaign


async def verify_paystack_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    # compute has
    computed_hash = hmac.new(
        key=secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha512
    ).hexdigest()
    # compare signature from header
    return hmac.compare_digest(computed_hash, signature)
