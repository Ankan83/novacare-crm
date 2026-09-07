"""
Create HCP Tool

Creates a new Healthcare Professional record when a search for an
existing one fails and the user chooses to add them instead.
"""

from datetime import datetime

from sqlalchemy.orm import Session  # type: ignore

from app.models.hcp import HCP


def create_hcp(
    *,
    db: Session,
    full_name: str,
    specialty: str,
    organization: str,
    city: str,
    email: str = "",
    notes: str = "",
) -> dict:
    """
    Create and persist a new HCP record.

    NOTE: `email` is NOT NULL in the HCP model but isn't collected by
    the "create new HCP" conversation flow, so it defaults to an empty
    string here. New HCPs created this way will have a blank email
    until someone fills it in later — flagging this since it's a real
    data-completeness tradeoff, not something to silently paper over.
    """

    hcp = HCP(
        full_name=full_name,
        specialty=specialty,
        organization=organization,
        city=city,
        email=email,
        notes=notes,
        # The model's created_at column is NOT NULL with no default —
        # it must be set explicitly or the insert fails.
        created_at=datetime.utcnow(),
    )

    try:
        db.add(hcp)
        db.commit()
        db.refresh(hcp)

    except Exception:
        db.rollback()
        raise

    return {
        "id": hcp.id,
        "full_name": hcp.full_name,
        "organization": hcp.organization,
    }