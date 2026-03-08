from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid
from decimal import Decimal
from src.contributions.models import PaymentStatus
from datetime import datetime


class ContributionCreate(BaseModel):
    campaign_id: uuid.UUID
    amount: Decimal = Field(gt=0, description="Contribution amount in GHS")
    contributor_email: EmailStr
    contributor_name: str = Field(min_length=2, max_length=100)


class ContributionResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    user_id: uuid.UUID | None
    contributor_email: str
    contributor_name: str
    amount: Decimal
    payment_status: PaymentStatus
    paystack_reference: str | None
    created_at: datetime
    completed_at: datetime | None
    refunded_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PaymentInitResponse(BaseModel):
    """paystack payment initialization response"""

    authorization_url: str
    access_code: str
    reference: str
