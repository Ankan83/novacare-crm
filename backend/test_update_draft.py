from app.tools.update_draft import update_draft

draft = {
    "hcp_name": "Dr Rajesh Sharma",
    "subject": "",
    "sentiment": "neutral",
}

updates = {
    "subject": "Ozempic Discussion",
    "sentiment": "positive",
}

result = update_draft(
    current_draft=draft,
    updates=updates,
)

print(result)