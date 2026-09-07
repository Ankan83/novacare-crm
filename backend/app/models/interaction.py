"""
Interaction Model

Defines the CRM interaction entity persisted in the database.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ( # type: ignore
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
) 
from sqlalchemy.orm import ( # type: ignore
    Mapped,
    mapped_column,
    relationship,
)

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.hcp import HCP


class Interaction(Base):
    """
    Stores a single interaction between a representative and an HCP.
    """

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    hcp_id: Mapped[int] = mapped_column(
        ForeignKey("hcps.id"),
        nullable=False,
    )

    interaction_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    interaction_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    attendees: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
    )

    topics: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
    )

    sentiment: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="neutral",
    )

    sentiment_reason: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    # Reserved for future AI-generated executive summaries.
    summary: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    follow_up: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    hcp: Mapped["HCP"] = relationship()