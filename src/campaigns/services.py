from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends
from datetime import datetime, timezone
import uuid
from .models import Campaign, CampaignStatus
from src.auth.models import User
from .schemas import CampaignCreate, CampaignResponse
from typing import Annotated
from src.auth.dependencies import get_current_active_user
from sqlalchemy import select, desc

MAX_GOAL_AMOUNT = 10_000_000
MAX_CAMPAIGN_DURATION_DAYS = 365

user = Annotated[User, Depends(get_current_active_user)]


class CampaignService:
    async def _validate_goal_amount(self, amount: float) -> None:
        """validate goal amount"""
        if amount > MAX_GOAL_AMOUNT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Goal amount cannot exceed {MAX_GOAL_AMOUNT:,} GHS",
            )

    async def _validate_deadline(self, deadline: datetime) -> None:
        now = datetime.now(timezone.utc)
        deadline_delta = deadline - now

        if deadline_delta.days > MAX_CAMPAIGN_DURATION_DAYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign duration cannot exceed {MAX_CAMPAIGN_DURATION_DAYS} days",
            )

    async def _validate_campaign_ownership(
        self, campaign: Campaign, user: User
    ) -> None:
        if campaign.creator_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this campaign",
            )

    async def _get_campaign_or_404(
        self, campaign_id: uuid.UUID, session: AsyncSession
    ) -> Campaign:
        statement = await session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = statement.scalar_one_or_none()
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            )
        return campaign

    async def _validate_campaign_is_active(self, campaign: Campaign) -> None:
        if campaign.status != CampaignStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update {campaign.status.value.lower()} campaign",
            )

    async def create_campaign(
        self, data: CampaignCreate, session: AsyncSession, user: user
    ) -> CampaignResponse:

        await self._validate_goal_amount(data.goal_amount)
        await self._validate_deadline(data.deadline)
        new_campaign = Campaign(
            creator_id=user.id,
            title=data.title,
            description=data.description,
            story=data.story,
            goal_amount=data.goal_amount,
            image_url=data.image_url,
            deadline=data.deadline,
            status=CampaignStatus.ACTIVE,
            current_amount=0.00,
        )

        session.add(new_campaign)
        await session.commit()
        await session.refresh(new_campaign)

        return new_campaign

    async def get_campaign(
        self, campaign_id: uuid.UUID, session: AsyncSession
    ) -> Campaign:
        return await self._get_campaign_or_404(campaign_id=campaign_id, session=session)

    async def list_campaigns(
        self,
        session: AsyncSession,
        status_filter: CampaignStatus | None = None,
        search_query: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Campaign]:
        statement = select(Campaign)

        if search_query:
            statement = statement.where(Campaign.title.ilike(f"%{search_query}%"))
        if status_filter:
            statement = statement.where(Campaign.status == status_filter)

        statement = (
            statement.order_by(desc(Campaign.created_at)).limit(limit).offset(offset)
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_my_campaigns(
        self, current_user: User, session: AsyncSession
    ) -> list[Campaign]:
        statement = (
            select(Campaign)
            .where(Campaign.creator_id == current_user.id)
            .order_by(desc(Campaign.created_at))
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def update_campaign(
        self,
        campaign_id: uuid.UUID,
        data: CampaignCreate,
        current_user: User,
        session: AsyncSession,
    ) -> Campaign:

        campaign = await self._get_campaign_or_404(
            campaign_id=campaign_id, session=session
        )
        await self._validate_campaign_ownership(campaign=campaign, user=current_user)
        await self._validate_campaign_is_active(campaign=campaign)
        await self._validate_goal_amount(data.goal_amount)
        await self._validate_deadline(deadline=data.deadline)

        campaign.title = data.title
        campaign.description = data.description
        campaign.story = data.story
        campaign.goal_amount = data.goal_amount
        campaign.image_url = data.image_url
        campaign.deadline = data.deadline

        await session.commit()
        await session.refresh(campaign)
        return campaign
