from fastapi import HTTPException, status
import hmac
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, update
from src.contributions.models import Contribution, PaymentStatus
from src.campaigns.models import Campaign
import logging
from .exceptions import WebhookError

logger = logging.getLogger("uvicorn.access")


async def verify_paystack_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    # compute has
    computed_hash = hmac.new(
        key=secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha512
    ).hexdigest()
    # compare signature from header
    return hmac.compare_digest(computed_hash, signature)


async def process_charge_success(
    event_data: dict,
    session: AsyncSession,
) -> dict:
    reference = event_data.get("reference")

    if not reference:
        logger.error("Webhook missing reference", extra={"event_data": event_data})
        # We return a dict instead of raising to send a 200 to Paystack
        return {"status": "error", "message": "Missing reference"}

    # 1. Lock contribution for update
    stmt = (
        select(Contribution)
        .where(Contribution.paystack_reference == reference)
        .with_for_update()
    )
    result = await session.execute(stmt)
    contribution = result.scalar_one_or_none()

    if not contribution:
        logger.warning(f"Contribution not found for reference: {reference}")
        return {"status": "error", "message": "Contribution not found"}

    # Idempotency check
    if contribution.payment_status == PaymentStatus.COMPLETED:
        return {"status": "already_processed", "contribution_id": str(contribution.id)}

    if contribution.payment_status == PaymentStatus.REFUNDED:
        return {"status": "error", "message": "Contribution was already refunded"}

    # status update
    contribution.payment_status = PaymentStatus.COMPLETED
    contribution.completed_at = datetime.now(timezone.utc)

    # atomic update
    goal_reached = False
    new_total = contribution.amount

    if contribution.campaign_id:
        update_stmt = (
            update(Campaign)
            .where(Campaign.id == contribution.campaign_id)
            .values(current_amount=Campaign.current_amount + contribution.amount)
            .returning(Campaign.current_amount, Campaign.goal_amount)
        )
        update_result = await session.execute(update_stmt)

        row = update_result.one()

        new_total, goal_amount = row
        goal_reached = new_total >= goal_amount

    await session.commit()

    # todo: background tasks (Emails, Push Notifications)

    if goal_reached:
        logger.info(f"Goal reached for campaign {contribution.campaign_id}!")

    # todo: bg_tasks (notify_creator_goal_reached)

    return {
        "status": "processed",
        "contribution_id": str(contribution.id),
        "campaign_id": str(contribution.campaign_id),
        "amount": float(contribution.amount),
        "new_campaign_total": float(new_total),
        "goal_reached": goal_reached,
    }
