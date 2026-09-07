from app.agent.graph import graph
from app.database.session import SessionLocal

db = SessionLocal()

state = {
    "db": db,
    "message": "I met Dr Rajesh Sharma yesterday for 30 minutes. We discussed Ozempic.",
    "draft": {},
    "highlighted_fields": [],
    "ready_for_confirmation": False,
    "saved": False,
}

result = graph.invoke(state)

print(result["assistant_message"])
print(result["draft"])

db.close()