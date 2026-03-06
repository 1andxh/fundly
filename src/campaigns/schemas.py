from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, timezone
import uuid
from .models import CampaignStatus

now = datetime.now(timezone.utc)


class CampaignCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=500)
    story: str | None = None
    goal_amount: float = Field(gt=0, description="Goal amount in GHS")
    deadline: datetime
    image_url: str | None = None

    @field_validator("deadline")
    @classmethod
    def deadline_validator(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        if v <= now:
            raise ValueError("Deadline must be in the future")
        return v


class CampaignResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    description: str
    story: str | None
    goal_amount: float
    current_amount: float
    image_url: str | None
    deadline: datetime
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime | None
    ended_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CampaignList(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    description: str
    goal_amount: float
    current_amount: float
    image_url: str | None
    deadline: datetime
    status: CampaignStatus

    model_config = ConfigDict(from_attributes=True)


class CampaignUpdate(BaseModel):

    title: str | None = Field(None, min_length=5, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=500)
    story: str | None = None
    goal_amount: float | None = Field(None, gt=0)
    deadline: datetime | None = None
    image_url: str | None = None

    @field_validator("deadline")
    @classmethod
    def deadline_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v is not None and v <= datetime.now(timezone.utc):
            raise ValueError("Deadline must be in the future")
        return v
