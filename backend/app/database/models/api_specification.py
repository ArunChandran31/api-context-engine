from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.endpoint import Endpoint


class ApiSpecification(Base):
    __tablename__ = "api_specifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    base_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    source_file: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------
    #
    # This stores the Supabase Auth user UUID that owns the
    # specification.
    #
    # It is temporarily nullable because existing local database
    # records need to be assigned to the current user during the
    # one-time ownership migration.
    #

    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    endpoints: Mapped[list[Endpoint]] = relationship(
        back_populates="api_specification",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_api_specifications_user_id_created_at",
            "user_id",
            "created_at",
        ),
    )
