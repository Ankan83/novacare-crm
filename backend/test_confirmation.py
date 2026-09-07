from app.database.session import SessionLocal
from app.services.chat_service import chat_service

db = SessionLocal()

state = None

print("=" * 60)
print("STEP 1")
print("=" * 60)

response = chat_service.process_message(
    db=db,
    message=(
        "I met Dr Rajesh Sharma yesterday "
        "for 30 minutes. "
        "It was a meeting. "
        "We discussed Ozempic."
    ),
    state=state,
)

print(response)

state = {
    "draft": response["draft"],
    "highlighted_fields": response["highlighted_fields"],
    "ready_for_confirmation": response["ready_for_confirmation"],
    "saved": response["saved"],
    "confirmed": response["confirmed"],
}

print()
print("=" * 60)
print("STEP 2")
print("=" * 60)

response = chat_service.process_message(
    db=db,
    message="yes",
    state=state,
)

print(response)

db.close()