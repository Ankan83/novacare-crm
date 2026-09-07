from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text # type: ignore
from sqlalchemy.orm import Mapped, mapped_column # type: ignore

from app.database.session import Base


class HCP(Base):
    __tablename__ = "hcps"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    specialty: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    organization: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
    )