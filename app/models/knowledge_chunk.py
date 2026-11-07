
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.base import Base


EMBEDDING_DIMENSION = 1024


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    source: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    page_number: Mapped[int | None] = mapped_column(
        nullable=True
    )

    topic: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    embedding = mapped_column(
        Vector(EMBEDDING_DIMENSION),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
