"""
Save Interaction Tool

Persists a completed interaction into the CRM database.
"""

from datetime import datetime

import dateparser # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.models.interaction import Interaction


def save_interaction(
    *,
    db: Session,
    draft: dict,
) -> dict:
    """
    Save a completed interaction.

    Parameters
    ----------
    db
        SQLAlchemy session.

    draft
        Interaction draft collected during the conversation.

    Returns
    -------
    Dictionary describing the saved interaction.
    """

    interaction = Interaction(
        hcp_id=draft["hcp_id"],
        interaction_type=draft["interaction_type"],
        interaction_date=(
            dateparser.parse(draft["interaction_date"])
            or datetime.now()
        ),
        duration_minutes=draft.get("duration_minutes"),
        subject=draft["subject"],
        notes=draft["notes"],
        attendees=draft.get("attendees", []),
        topics=draft.get("topics", []),
        sentiment=draft.get("sentiment", "neutral"),
        sentiment_reason=draft.get("sentiment_reason", ""),
        summary=draft.get("summary", ""),
        follow_up=draft.get("follow_up", ""),
    )

    try:
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "interaction_id": interaction.id,
    }