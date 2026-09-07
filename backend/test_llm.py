from app.services.llm import llm

response = llm.invoke("Say only the word: Connected")

print(response.content)