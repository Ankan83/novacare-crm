from datetime import datetime

from app.database.session import SessionLocal
from app.tools.save_interaction import save_interaction

db = SessionLocal()

try:

    result = save_interaction(
        db=db,
        draft={
            "hcp_id": 3,
            "interaction_type": "Meeting",
            "interaction_date": datetime.now(),
            "duration_minutes": 25,
            "subject": "Ozempic Discussion",
            "notes": "Doctor was interested in efficacy data.",
            "attendees": [
                "Jason Smith",
            ],
            "topics": [
                "Ozempic",
                "Clinical Trial"
            ],
            "summary": "Positive discussion.",
            "sentiment": "positive",
            "sentiment_reason": "Doctor showed strong interest.",
            "follow_up": "Reconnect after 30 days.",
        },
    )

    print(result)

finally:
    db.close()