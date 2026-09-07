from app.schemas import ChatRequest

request = ChatRequest(
    message="I met Dr. Rajesh Sharma yesterday."
)

print(request.model_dump())