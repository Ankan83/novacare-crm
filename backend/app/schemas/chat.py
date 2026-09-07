from typing import Any

from pydantic import BaseModel, Field  # type: ignore


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str

    history: list[ChatMessage] = Field(default_factory=list)

    draft: dict[str, Any] = Field(default_factory=dict)

    conversation_stage: str = "COLLECTING_INFORMATION"

    ready_for_confirmation: bool = False

    # Field that tells the backend which value the user is currently answering.
    current_field: str | None = None

    # Id of the most recently saved interaction in this session, so the
    # user can ask to view/edit it on a later turn without it being lost.
    last_interaction_id: int | None = None

    # True right after a save, while the user is being asked
    # "log another / view / edit / show previous / prepare for next meeting".
    # Needed so a bare "yes"/"no"/number on the NEXT turn is interpreted
    # as an answer to that menu rather than as a save confirmation or
    # free-text extraction target.
    awaiting_post_save_choice: bool = False

    # True while the user has been offered to create a new HCP record
    # and is being asked for specialty/city.
    awaiting_new_hcp_details: bool = False

    # The partial HCP record (name, organization) collected so far,
    # while awaiting_new_hcp_details is True.
    pending_new_hcp: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    assistant_message: str

    draft: dict[str, Any]

    highlighted_fields: list[str]

    conversation_stage: str

    ready_for_confirmation: bool

    saved: bool

    # Returned to the frontend so it can send it back
    # with the user's next message.
    current_field: str | None = None

    # Returned to the frontend so it can send it back on the next turn.
    last_interaction_id: int | None = None

    # Returned to the frontend so it can send it back on the next turn.
    awaiting_post_save_choice: bool = False

    # Returned to the frontend so it can send it back on the next turn.
    awaiting_new_hcp_details: bool = False

    # Returned to the frontend so it can send it back on the next turn.
    pending_new_hcp: dict[str, Any] | None = None