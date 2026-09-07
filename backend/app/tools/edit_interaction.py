"""
Edit Interaction Tool

Allows Nova to update an existing interaction.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import select # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.models.interaction import Interaction


def edit_interaction(
    *,
    db: Session,
    interaction_id: int,
    updates: dict[str, Any],
) -> dict:
    """
    Update an existing interaction.

    Only fields present in `updates`
    will be modified.
    """

    interaction = db.execute(
        select(Interaction).where(
            Interaction.id == interaction_id
        )
    ).scalar_one_or_none()

    if interaction is None:
        return {
            "success": False,
            "message": "Interaction not found.",
        }

    editable_fields = {
        "interaction_type",
        "interaction_date",
        "duration_minutes",
        "subject",
        "notes",
        "attendees",
        "topics",
        "summary",
        "sentiment",
        "sentiment_reason",
        "follow_up",
    }

    for field, value in updates.items():

        if field not in editable_fields:
            continue

        if value is None:
            continue

        setattr(
            interaction,
            field,
            value,
        )

    interaction.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(interaction)

    return {
        "success": True,
        "interaction_id": interaction.id,
        "message": "Interaction updated successfully.",
    }