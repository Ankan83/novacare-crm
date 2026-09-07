from app.tools.build_review import build_review

review = build_review(
    draft={
        "hcp_name": "Dr Rajesh Sharma",
        "interaction_type": "Meeting",
        "interaction_date": "16 July 2026",
        "subject": "Ozempic Discussion",
        "attendees": ["Ankan"],
        "topics": ["Ozempic"],
        "summary": "Positive discussion.",
        "sentiment": "positive",
        "follow_up": "30 days",
    }
)

print(review)