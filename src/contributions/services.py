from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import uuid
from decimal import Decimal, ROUND_HALF_UP
from src.campaigns.models import Campaign, CampaignStatus
from src.contributions.models import Contribution, PaymentStatus
from src.contributions.schemas import (
    ContributionCreate,
    PaymentInitResponse,
)
from src.utils.paystack import paystack_client, PaystackClientError
from sqlalchemy import select
from pydantic import EmailStr
import logging


logger = logging.getLogger("uvicorn.access")
MIN_CONTRIBUTION_AMOUNT = Decimal("1.00")
MAX_CONTRIBUTION_AMOUNT = Decimal("1000000.00")


class ContributionService:
    @staticmethod
    def _normalize_amount(amount: float) -> Decimal:
        return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

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
            if campaign.status == CampaignStatus.SUCCESSFUL:
                message = "This campaign has ended succesfully, goal reached"
            elif campaign.status == CampaignStatus.FAILED:
                message = "This campaign has ended without reaching its goal"
            else:
                message = f"This campaign is {campaign.status.value}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{message} Contributions are no longer accepted",
            )
        return campaign

    async def _validate_contribution_amount(self, amount: Decimal):
        if amount < MIN_CONTRIBUTION_AMOUNT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum contribution amount is {MIN_CONTRIBUTION_AMOUNT} GHS",
            )
        if amount > MAX_CONTRIBUTION_AMOUNT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum contribution amount is {MAX_CONTRIBUTION_AMOUNT} GHS",
            )

    async def _create_contribution_record(
        self,
        campaign_id: uuid.UUID,
        contributor_email: EmailStr,
        contributor_name: str,
        amount: Decimal,
        session: AsyncSession,
    ) -> Contribution:
        contribution = Contribution(
            campaign_id=campaign_id,
            contributor_email=contributor_email,
            contributor_name=contributor_name,
            amount=amount,
            payment_status=PaymentStatus.PENDING,
        )
        session.add(contribution)
        await session.commit()
        await session.refresh(contribution)

        return contribution

    async def initiate_contribution(
        self, contribution_data: ContributionCreate, session: AsyncSession
    ) -> PaymentInitResponse:

        await self._get_active_campaign(
            campaign_id=contribution_data.campaign_id, session=session
        )

        amount = self._normalize_amount(contribution_data.amount)
        await self._validate_contribution_amount(amount)
        contribution = await self._create_contribution_record(
            contribution_data.campaign_id,
            contribution_data.contributor_email,
            contribution_data.contributor_name,
            amount,
            session,
        )
        session.add(contribution)
        await session.flush()

        try:
            payment_response = await paystack_client.intialize_transcation(
                email=contribution_data.contributor_email,
                amount=amount,
                reference=str(contribution.id),
            )

        except PaystackClientError as e:
            logger.error(f"Paystack initialization failed:  {str(e)}", exc_info=True)
            await session.rollback()

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service unavailable. Please try again later.",
            )

        contribution.paystack_reference = payment_response["reference"]
        contribution.paystack_access_code = payment_response.get("access_code")  # type: ignore

        await session.commit()

        return PaymentInitResponse(
            authorization_url=payment_response["authorization_url"],
            access_code=payment_response["access_code"],
            reference=payment_response["reference"],
        )
