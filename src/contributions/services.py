from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING
from src.contributions.models import Contribution, PaymentStatus
from src.contributions.schemas import (
    ContributionCreate,
    ContributionResponse,
    PaymentInitResponse,
)
from src.utils.paystack import paystack_client
from src.db.main import get_session
from sqlalchemy import select

if TYPE_CHECKING:
    from src.campaigns.models import Campaign, CampaignStatus

MIN_CONTRIBUTION_AMOUNT = 1.00
MAX_CONTRIBUTION_AMOUNT = 1_000_000


class CampaignService:

    async def _get_active_campaign(
        self, campaign_id: uuid.UUID, session: AsyncSession
    ) -> Campaign:
        stmt = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = stmt.scalar_one_or_none()

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            )

        if campaign.status != CampaignStatus.ACTIVE:
            pass

        return campaign

    async def initiate_contribution(
        self, contribution_data: ContributionCreate, session: AsyncSession
    ) -> PaymentInitResponse: ...

    # campaign =
