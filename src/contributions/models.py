import enum
import uuid
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from src.db.base import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.campaigns.models import Campaign


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    contributor_email: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    contributor_name: Mapped[str] = mapped_column(String(128), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum", native_enum=False),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    paystack_reference: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    paystack_access_code: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="contributions"
    )
    user: Mapped["User | None"] = relationship("User", back_populates="contributions")

    @validates("payment_status")
    def validate_status_transitions(self, key, new_status):
        current_status = self.payment_status

        if (
            current_status in [PaymentStatus.COMPLETED, PaymentStatus.REFUNDED]
            and new_status == PaymentStatus.PENDING
        ):
            raise ValueError(f"Cannot reset payment status to {new_status}")

        if (
            current_status == PaymentStatus.REFUNDED
            and new_status == PaymentStatus.COMPLETED
        ):
            raise ValueError(
                "State Conflict: Cannot mark a REFUNDED contribution as COMPLETED"
            )

        return new_status
