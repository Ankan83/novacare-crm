from app.database.session import SessionLocal
from app.tools.edit_interaction import edit_interaction

db = SessionLocal()

result = edit_interaction(
    db=db,
    interaction_id=23,
    updates={
        "sentiment": "neutral",
        "summary": "Doctor requested more clinical evidence.",
    },
)

print(result)

db.close()