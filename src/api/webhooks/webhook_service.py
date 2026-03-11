from fastapi import HTTPException, status
import hmac
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
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


async def process_charge_success(event_data: dict, session: AsyncSession) -> dict:
    reference = event_data.get("reference")

    if not reference:
        # raise HTTPException(
        #     status_code=status.HTTP_400_BAD_REQUEST,
        #     detail="Missing reference in webhook data",
        # )
        return {"status":"error", "message": "Missing reference"}

    stmt = await session.execute(
        select(Contribution).where(Contribution.paystack_reference == reference).with_for_update()
    )
    contribution = stmt.scalar_one_or_none()

    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contribution with reference {reference} not found",
        )

    # check idempotency
    if contribution.payment_status == PaymentStatus.COMPLETED:
        return {
            "status": "already_processed",
            "message": "Contribution already marked as completed",
            "contribution": str(contribution.id),
        }
    if contribution.payment_status == PaymentStatus.REFUNDED:
        return {
            "status": "refunded",
            "message": "Comtribution was refunded, cannot reprocess",
            "contribution_id": str(contribution.id),
        }
    # update contribution
    contribution.payment_status = PaymentStatus.COMPLETED
    contribution.completed_at = datetime.now(timezone.utc)

    # update current amount
    stmt = await session.execute(
        select(Campaign).where(Campaign.id == contribution.campaign_id)
    )
    campaign = stmt.scalar_one_or_none()
    if campaign :
        campaign.current_amount += contribution.amount

        # check if goal reached
        goal_reached = campaign.goal_amount - campaign.current_amount
        if goal_reached == campaign.current_amount >= campaign.goal_amount:
            


        await session.commit()

        # todo: bg task: send receipts to contributor, notify creator if goal reached

    return {
        "status": "processed",
        "message": "Payment processed successfully",
        "contribution_id": str(contribution.id),
        "campaign_id": str(campaign.id),
        "new_campaign_total": Decimal(campaign.current_amount),
        "goal_reached": goal_reached,
    }

async def process_webhook_event()