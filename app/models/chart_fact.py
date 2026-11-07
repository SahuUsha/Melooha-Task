
from datetime import datetime, timezone

from sqlalchemy import (
    Integer, String, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChartFact(Base):
    __tablename__ = "chart_facts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    fact_key: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    fact_value: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    source: Mapped[str] = mapped_column(
        String(100), default="chart_calculation"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="chart_facts")
