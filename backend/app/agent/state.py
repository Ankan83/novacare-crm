"""
Conversation State

Defines the shared state flowing through the LangGraph workflow.
"""

from typing import Any, Literal

from typing_extensions import TypedDict # type: ignore


ConversationStage = Literal[
    "SEARCHING_HCP",
    "WAITING_FOR_HCP_SELECTION",
    "COLLECTING_INFORMATION",
    "REVIEWING",
    "WAITING_FOR_CONFIRMATION",
    "SAVING",
    "COMPLETED",
]


class ConversationState(TypedDict):
    """
    Shared state used by Nova.
    """

    # LangGraph messages
    messages: list[Any]

    # Current interaction draft
    draft: dict[str, Any]

    # Fields updated during the last turn
    highlighted_fields: list[str]

    # Current workflow stage
    conversation_stage: ConversationStage

    # Waiting for user to choose one HCP from multiple matches
    pending_hcp_selection: dict[str, Any] | None

    # Review generated?
    ready_for_confirmation: bool

    # Persisted?
    saved: bool