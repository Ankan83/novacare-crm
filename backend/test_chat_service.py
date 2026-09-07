from app.database.session import SessionLocal
from app.services.chat_service import chat_service

db = SessionLocal()

response = chat_service.process_message(
    db=db,
    message="I met Dr Rajesh Sharma yesterday for 30 minutes. We discussed Ozempic.",
)

print(response)

db.close()