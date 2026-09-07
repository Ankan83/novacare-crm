from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field # type: ignore


class InteractionCreate(BaseModel):
    hcp_id: int

    interaction_type: str

    interaction_date: datetime

    duration_minutes: int | None = None

    subject: str

    notes: str

    attendees: list[str] = Field(default_factory=list)

    topics: list[str] = Field(default_factory=list)

    sentiment: str = "neutral"

    sentiment_reason: str = ""

    summary: str = ""

    follow_up: str = ""


class InteractionResponse(InteractionCreate):
    id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )