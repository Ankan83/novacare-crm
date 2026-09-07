"""
Get Interaction Tool

Fetches a previously saved interaction by id and returns it shaped as
a "draft" dict, matching the format used everywhere else in the
conversation flow (build_review, update_draft), so it can be passed
straight into build_review() to display or re-enter editing.
"""

from sqlalchemy import select  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.interaction import Interaction


def get_interaction(*, db: Session, interaction_id: int) -> dict:
    """
    Fetch a saved interaction by id and shape it as a draft dict.

    Raises ValueError if no interaction with that id exists.
    """

    interaction = db.execute(
        select(Interaction).where(Interaction.id == interaction_id)
    ).scalar_one_or_none()

    if not interaction:
        raise ValueError(
            f"No interaction found with id {interaction_id}"
        )

    # Interaction.hcp is a relationship() on the model — use it
    # directly rather than a second manual query.
    hcp = interaction.hcp
    hcp_name = hcp.full_name if hcp else "Unknown HCP"

    return {
        "hcp_id": interaction.hcp_id,
        "hcp_name": hcp_name,
        "hcp_specialty": hcp.specialty if hcp else None,
        "hcp_city": hcp.city if hcp else None,
        "interaction_type": interaction.interaction_type,
        "interaction_date": (
            interaction.interaction_date.strftime("%Y-%m-%d")
            if interaction.interaction_date
            else None
        ),
        "duration_minutes": interaction.duration_minutes,
        "subject": interaction.subject,
        "notes": interaction.notes,
        "attendees": interaction.attendees or [],
        "topics": interaction.topics or [],
        "sentiment": interaction.sentiment,
        "sentiment_reason": interaction.sentiment_reason,
        "follow_up": interaction.follow_up,
    }