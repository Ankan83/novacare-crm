"""Small, deterministic helpers used by CRM insight endpoints."""

from __future__ import annotations

import re
import smtplib
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from email.message import EmailMessage
from typing import Any

import dateparser  # type: ignore
import dateparser.search  # type: ignore

from app.core.config import settings


def extract_follow_up(interaction: Any) -> dict[str, Any]:
    """Expose the saved follow-up as actionable, API-friendly fields."""
    text = (getattr(interaction, "follow_up", None) or "").strip()
    due_date = None
    if text:
        parsed = _resolve_follow_up_date(text) or dateparser.parse(
            text,
            settings={
                "PREFER_DATES_FROM": "future",
                "RETURN_AS_TIMEZONE_AWARE": False,
            },
        )
        if parsed:
            due_date = parsed.date().isoformat()
    action = re.sub(
        r"\b(by|on|before|within|in)\s+\d+\s+\w+\b", "", text, flags=re.I
    ).strip(" .")
    return {
        "follow_up": text,
        "action_item": action or None,
        "follow_up_date": due_date,
    }


def _resolve_follow_up_date(text: str) -> datetime | None:
    match = re.search(
        r"\b(next|last|this)\s+"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        text.lower(),
    )
    if not match:
        return None

    modifiers = {"last": -1, "this": 0, "next": 1}
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    today = datetime.now()
    target = weekdays[match.group(2)]
    delta = (target - today.weekday()) % 7
    if match.group(1) == "last":
        delta = delta or 7
        return today - timedelta(days=7 - delta)
    if match.group(1) == "next":
        delta = delta or 7
        return today + timedelta(days=delta)
    return today + timedelta(days=delta)


def normalize_identity(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def duplicate_score(candidate: Any, existing: Any) -> float:
    """Return a score in [0, 1] using strong email/name and org signals."""
    email_a = normalize_identity(getattr(candidate, "email", None))
    email_b = normalize_identity(getattr(existing, "email", None))
    name = SequenceMatcher(
        None,
        normalize_identity(getattr(candidate, "full_name", None)),
        normalize_identity(getattr(existing, "full_name", None)),
    ).ratio()
    org = SequenceMatcher(
        None,
        normalize_identity(getattr(candidate, "organization", None)),
        normalize_identity(getattr(existing, "organization", None)),
    ).ratio()
    if email_a and email_b and email_a == email_b:
        return 1.0
    return min(1.0, name * 0.7 + org * 0.2 + (
        0.1 if email_a and email_b and email_a == email_b else 0
    ))


_COMPLIANCE_RULES = (
    ("patient_identifier", re.compile(r"\b(mrn|patient\s+name|date\s+of\s+birth)\b", re.I)),
    ("adverse_event", re.compile(r"\b(adverse event|side effect|serious event)\b", re.I)),
    ("off_label", re.compile(r"\b(off[- ]label|unapproved indication)\b", re.I)),
    ("inducement", re.compile(r"\b(kickback|bribe|cash|gift|inducement)\b", re.I)),
)


def run_compliance_checks(text: str) -> dict[str, Any]:
    findings = [
        {"rule": rule, "message": f"Review possible {rule.replace('_', ' ')}."}
        for rule, pattern in _COMPLIANCE_RULES
        if pattern.search(text or "")
    ]
    return {"compliant": not findings, "findings": findings}


def build_analytics(interactions: list[Any]) -> dict[str, Any]:
    by_type = Counter(i.interaction_type for i in interactions)
    by_sentiment = Counter(i.sentiment for i in interactions)
    return {
        "total_interactions": len(interactions),
        "interaction_types": dict(by_type),
        "sentiment": dict(by_sentiment),
        "hcp_count": len({i.hcp_id for i in interactions}),
        "follow_ups": sum(bool((i.follow_up or "").strip()) for i in interactions),
        "generated_at": datetime.utcnow().isoformat(),
    }


def build_follow_up_email(hcp_name: str, action_item: str) -> dict[str, str]:
    subject = f"Follow-up: {action_item}"
    body = (
        f"Hello {hcp_name},\n\n"
        "Thank you for your time. As discussed, I will follow up on "
        f"{action_item.lower()}.\n\n"
        "Please let me know if there is anything else you need in the meantime.\n\n"
        "Best regards,"
    )
    return {"subject": subject, "body": body}


def send_follow_up_email(recipient: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise RuntimeError("SMTP is not configured; use the generated email draft instead.")

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def build_calendar_event(title: str, start_date: str, duration_minutes: int, description: str, location: str) -> str:
    start = dateparser.parse(start_date)
    if not start:
        raise ValueError("Invalid calendar start date.")
    end = start + timedelta(minutes=duration_minutes)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    def ics_escape(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Nova AI CRM//EN",
        "BEGIN:VEVENT", f"UID:nova-{stamp}@crm", f"DTSTAMP:{stamp}",
        f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{ics_escape(title)}", f"DESCRIPTION:{ics_escape(description)}",
        f"LOCATION:{ics_escape(location)}", "END:VEVENT", "END:VCALENDAR", "",
    ])
