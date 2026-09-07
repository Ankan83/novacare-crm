from app.agent.agent import nova_agent

state = {
    "messages": [
        {
            "role": "user",
            "content": "Hello Nova",
        }
    ],
    "draft": {},
    "highlighted_fields": [],
    "conversation_stage": "SEARCHING_HCP",
    "ready_for_confirmation": False,
    "saved": False,
}

result = nova_agent.invoke(
    state=state,
)

print(result)