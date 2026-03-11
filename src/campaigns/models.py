import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.base import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.contributions.models import Contribution
    from src.payouts.models import Payout


class CampaignStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    story: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status_enum", create_type=True),
        default=CampaignStatus.ACTIVE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    creator: Mapped["User"] = relationship("User", back_populates="campaigns")
    contributions: Mapped[list["Contribution"]] = relationship(
        "Contribution",
        back_populates="campaign",
        passive_deletes=True,
    )
    payout: Mapped["Payout"] = relationship(
        "Payout", back_populates="campaign", uselist=False
    )
