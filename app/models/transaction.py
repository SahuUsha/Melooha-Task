
from datetime import datetime, timezone

from sqlalchemy import (
    Integer, String, DateTime, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    amount: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    balance_after: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="transactions")
