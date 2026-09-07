from app.agent.state import ConversationState

state: ConversationState = {
    "messages": [],
    "draft": {},
    "highlighted_fields": [],
    "conversation_stage": "SEARCHING_HCP",
    "ready_for_confirmation": False,
    "saved": False,
} # type: ignore

print(state)