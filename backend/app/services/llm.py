"""
LLM Service

Initializes the Groq LLM used throughout Nova.
"""

from langchain_groq import ChatGroq # type: ignore

from app.core.config import settings


llm = ChatGroq(
    api_key=settings.GROQ_API_KEY, # type: ignore
    model=settings.MODEL_NAME,
    temperature=0.2,
)