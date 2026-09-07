"""
Nova Chat Service

Acts as the bridge between:

React
    ↓
FastAPI
    ↓
LangGraph
    ↓
CRM Tools
"""

from copy import deepcopy

from app.agent.graph import graph


DEFAULT_STATE = {
    "draft": {},
    "highlighted_fields": [],
    "ready_for_confirmation": False,
    "saved": False,
    "confirmed": False,
    "current_field": None,
    "last_interaction_id": None,
    "awaiting_post_save_choice": False,
    "awaiting_new_hcp_details": False,
    "pending_new_hcp": None,
}


class ChatService:

    def process_message(
        self,
        *,
        db,
        message: str,
        history: list | None = None,
        state: dict | None = None,
    ) -> dict:

        history = history or []
        state = deepcopy(state or DEFAULT_STATE)

        graph_state = {
            "db": db,

            "message": message,

            "messages": history + [
                {
                    "role": "user",
                    "content": message,
                }
            ],

            "draft": state.get(
                "draft",
                {},
            ),

            "highlighted_fields": state.get(
                "highlighted_fields",
                [],
            ),

            "ready_for_confirmation": state.get(
                "ready_for_confirmation",
                False,
            ),

            "saved": state.get(
                "saved",
                False,
            ),

            "confirmed": state.get(
                "confirmed",
                False,
            ),

            # Remember which field Nova is waiting for.
            "current_field": state.get(
                "current_field",
                None,
            ),

            # Id of the most recently saved interaction this session,
            # so "view/edit this interaction" still works on a later turn.
            "last_interaction_id": state.get(
                "last_interaction_id",
                None,
            ),

            # Whether the user is currently being asked the post-save
            # menu (log another / view / edit / show previous / prep).
            "awaiting_post_save_choice": state.get(
                "awaiting_post_save_choice",
                False,
            ),

            # Whether the user is currently being asked for specialty/city
            # to finish creating a new HCP record.
            "awaiting_new_hcp_details": state.get(
                "awaiting_new_hcp_details",
                False,
            ),

            # Partial HCP details collected so far (name, organization).
            "pending_new_hcp": state.get(
                "pending_new_hcp",
                None,
            ),
        }

        result = graph.invoke(graph_state)

        return {
            "assistant_message": result.get(
                "assistant_message",
                "",
            ),

            "draft": result.get(
                "draft",
                {},
            ),

            "highlighted_fields": result.get(
                "highlighted_fields",
                [],
            ),

            "conversation_stage": result.get(
                "conversation_stage",
                "COLLECTING_INFORMATION",
            ),

            "ready_for_confirmation": result.get(
                "ready_for_confirmation",
                False,
            ),

            "saved": result.get(
                "saved",
                False,
            ),

            # Returned to the frontend so it comes back on the next turn.
            "current_field": result.get(
                "current_field",
                None,
            ),

            # Returned to the frontend so it comes back on the next turn.
            "last_interaction_id": result.get(
                "last_interaction_id",
                None,
            ),

            # Returned to the frontend so it comes back on the next turn.
            "awaiting_post_save_choice": result.get(
                "awaiting_post_save_choice",
                False,
            ),

            # Returned to the frontend so it comes back on the next turn.
            "awaiting_new_hcp_details": result.get(
                "awaiting_new_hcp_details",
                False,
            ),

            # Returned to the frontend so it comes back on the next turn.
            "pending_new_hcp": result.get(
                "pending_new_hcp",
                None,
            ),
        }


chat_service = ChatService()