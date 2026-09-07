from pydantic import BaseModel, Field # type: ignore


class InteractionExtraction(BaseModel):
    """
    Structured interaction extracted from
    a conversational message.
    """

    hcp_name: str | None = None

    interaction_date: str | None = None

    interaction_type: str | None = None

    subject: str | None = None

    notes: str | None = None

    duration_minutes: int | None = None

    attendees: list[str] = Field(default_factory=list)

    topics: list[str] = Field(default_factory=list)

    sentiment: str | None = None

    sentiment_reason: str | None = None

    follow_up: str | None = None