from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.api_specification import ApiSpecification


class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    api_specification_id: Mapped[int] = mapped_column(
        ForeignKey("api_specifications.id"),
        nullable=False,
    )

    path: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    operation_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    api_specification: Mapped[ApiSpecification] = relationship(
        back_populates="endpoints",
    )
