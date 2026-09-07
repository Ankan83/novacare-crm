from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field  # type: ignore


class DuplicateHCPRequest(BaseModel):
    full_name: str
    specialty: str = ""
    organization: str = ""
    city: str = ""
    email: str = ""
    exclude_id: int | None = None
    threshold: float = Field(default=0.72, ge=0, le=1)


class ComplianceRequest(BaseModel):
    text: str = ""
    interaction_id: int | None = None


class FollowUpEmailRequest(BaseModel):
    recipient: str = ""
    send: bool = False


class CalendarEventRequest(BaseModel):
    title: str = "CRM follow-up"
    start_date: str
    duration_minutes: int = Field(default=30, ge=15, le=480)
    description: str = ""
    location: str = ""


class TimelineItem(BaseModel):
    id: int
    hcp_id: int
    interaction_type: str
    interaction_date: datetime
    subject: str
    notes: str
    topics: list[str] = Field(default_factory=list)
    sentiment: str
    summary: str = ""
    follow_up: str = ""
    action_item: str | None = None
    follow_up_date: str | None = None


class MeetingPrepResponse(BaseModel):
    hcp_id: int
    hcp: dict[str, Any] | None = None
    last_interaction: dict[str, Any] | None = None
    interaction_count: int
    key_topics: list[str]
    open_follow_ups: list[dict[str, Any]]
    suggested_questions: list[str]
