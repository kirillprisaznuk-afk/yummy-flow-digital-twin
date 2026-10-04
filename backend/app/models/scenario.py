"""Persist assumptions, not derived results, and retain the calculation version."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.version import MODEL_VERSION


class Base(DeclarativeBase):
    pass


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(2000), default="")
    assumptions: Mapped[dict[str, str | int]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(20), default=MODEL_VERSION)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
