"""
Single source of truth for the AI-First CRM interaction schema.

Every component (LangGraph, Validator, Prompts, API, UI)
should rely on this file instead of hardcoding field names.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldDefinition:
    key: str
    label: str
    required: bool
    ai_generated: bool
    editable_by_user: bool
    default: Any = None


INTERACTION_SCHEMA = {
    "hcp_name": FieldDefinition(
        key="hcp_name",
        label="Healthcare Professional",
        required=True,
        ai_generated=False,
        editable_by_user=False,
    ),

    "interaction_type": FieldDefinition(
        key="interaction_type",
        label="Interaction Type",
        required=True,
        ai_generated=False,
        editable_by_user=False,
    ),

    "interaction_date": FieldDefinition(
        key="interaction_date",
        label="Interaction Date",
        required=True,
        ai_generated=False,
        editable_by_user=False,
    ),

    "attendees": FieldDefinition(
        key="attendees",
        label="Attendees",
        required=True,
        ai_generated=False,
        editable_by_user=False,
        default=[],
    ),

    "subject": FieldDefinition(
        key="subject",
        label="Subject",
        required=False,
        ai_generated=True,
        editable_by_user=False,
        default="",
    ),

    "topics": FieldDefinition(
        key="topics",
        label="Topics Discussed",
        required=False,
        ai_generated=True,
        editable_by_user=False,
        default="",
    ),

    "notes": FieldDefinition(
        key="notes",
        label="Interaction Notes",
        required=True,
        ai_generated=False,
        editable_by_user=False,
        default="",
    ),

    "summary": FieldDefinition(
        key="summary",
        label="AI Summary",
        required=False,
        ai_generated=True,
        editable_by_user=False,
        default="",
    ),

    "sentiment": FieldDefinition(
        key="sentiment",
        label="AI Sentiment",
        required=False,
        ai_generated=True,
        editable_by_user=False,
        default="neutral",
    ),

    "follow_up": FieldDefinition(
        key="follow_up",
        label="Follow-up Recommendation",
        required=False,
        ai_generated=True,
        editable_by_user=False,
        default="",
    ),
}


REQUIRED_FIELDS = [
    field.key
    for field in INTERACTION_SCHEMA.values()
    if field.required
]


AI_GENERATED_FIELDS = [
    field.key
    for field in INTERACTION_SCHEMA.values()
    if field.ai_generated
]


USER_PROVIDED_FIELDS = [
    field.key
    for field in INTERACTION_SCHEMA.values()
    if not field.ai_generated
]


DEFAULT_DRAFT = {
    key: field.default
    for key, field in INTERACTION_SCHEMA.items()
}


FIELD_LABELS = {
    key: field.label
    for key, field in INTERACTION_SCHEMA.items()
}