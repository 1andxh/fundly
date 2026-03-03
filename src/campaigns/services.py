from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends
from datetime import datetime, timezone, timedelta
import uuid
from .models import Campaign, CampaignStatus
from src.auth.models import User
from .schemas import CampaignCreate, CampaignResponse, CampaignList
from typing import Annotated
from src.auth.dependencies import get_current_active_user

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

    async def create_campaign(
        self, campaign_data: CampaignCreate, session: AsyncSession, user: user
    ) -> CampaignResponse: ...

    # await self._validate_goal_amount(campaign_data.goal_amount)
