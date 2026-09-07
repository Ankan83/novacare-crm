"""
Conversation Questions

Defines the guided workflow for Nova.
This file contains no business logic.
"""

from typing import Final


# Workflow order
WORKFLOW: Final[list[str]] = [
    "hcp_name",
    "interaction_type",
    "interaction_date",
    "description",
]


# Questions shown to the user
QUESTIONS: Final[dict[str, str]] = {
    "hcp_name": (
        "Which Healthcare Professional did you interact with?"
    ),

    "interaction_type": (
        "What type of interaction was it? "
        "(Meeting, Call, Email, Conference, Webinar, etc.)"
    ),

    "interaction_date": (
        "When did the interaction happen?"
    ),

    "description": (
        "Please describe the interaction in a few sentences. "
        "Include products discussed, doctor feedback, objections, "
        "duration, attendees, follow-up actions, or anything important."
    ),
}


# Field labels for review UI
FIELD_LABELS: Final[dict[str, str]] = {
    "hcp_name": "Healthcare Professional",
    "interaction_type": "Interaction Type",
    "interaction_date": "Interaction Date",
    "description": "Discussion",
}


def get_question(field: str) -> str:
    """
    Return the question for a workflow field.
    """

    return QUESTIONS.get(field, f"Please provide {field}.")


def get_next_step(draft: dict) -> str | None:
    """
    Return the next missing workflow step.

    Returns None when all guided fields are complete.
    """

    for field in WORKFLOW:

        value = draft.get(field)

        if value is None:
            return field

        if isinstance(value, str) and value.strip() == "":
            return field

    return None