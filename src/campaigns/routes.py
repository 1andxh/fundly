from fastapi import APIRouter, Depends, status, Query
from .schemas import CampaignCreate, CampaignList, CampaignResponse, CampaignUpdate
from src.db.main import get_session
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from .services import CampaignService
from .models import CampaignStatus
import uuid
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

campaign_service = CampaignService()
current_user = Annotated[User, Depends(get_current_active_user)]
session = Annotated[AsyncSession, Depends(get_session)]

campaign_router = APIRouter()


@campaign_router.post(
    "/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED
)
async def create_campaign(
    payload: CampaignCreate, current_user: current_user, session: session
):
    return await campaign_service.create_campaign(
        data=payload, session=session, user=current_user
    )


@campaign_router.get("/", response_model=list[CampaignList])
async def list_campaigns(
    session: session,
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status_filter: CampaignStatus | None = Query(None, description="Filter by status"),
    q: str | None = Query(None, description="search campaigns"),
):
    campaigns = await campaign_service.list_campaigns(
        session=session,
        status_filter=status_filter,
        search_query=q,
        limit=limit,
        offset=offset,
    )
    return campaigns


@campaign_router.get("/my-campaigns", response_model=list[CampaignList])
async def get_my_campaigns(current_user: current_user, session: session):
    return await campaign_service.get_my_campaigns(
        current_user=current_user, session=session
    )


@campaign_router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(session: session, campaign_id: uuid.UUID):
    return await campaign_service.get_campaign(campaign_id=campaign_id, session=session)


@campaign_router.patch(
    "/{campaign_id}", response_model=CampaignResponse, response_model_exclude_unset=True
)
async def update_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignUpdate,
    current_user: current_user,
    session: session,
):
    return await campaign_service.update_campaign(
        campaign_id=campaign_id,
        data=payload,
        current_user=current_user,
        session=session,
    )
