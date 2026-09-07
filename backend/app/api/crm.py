"""Read-only CRM timeline, copilot, quality and analytics APIs."""

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query  # type: ignore
from fastapi.responses import Response  # type: ignore
from sqlalchemy import select  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.api.deps import get_db
from app.models.hcp import HCP
from app.models.interaction import Interaction
from app.schemas.crm import (
    CalendarEventRequest,
    ComplianceRequest,
    DuplicateHCPRequest,
    FollowUpEmailRequest,
)
from app.services.crm_insights import (
    build_analytics,
    duplicate_score,
    extract_follow_up,
    build_calendar_event,
    build_follow_up_email,
    run_compliance_checks,
    send_follow_up_email,
)

router = APIRouter(tags=["CRM insights"])


def _interactions(db: Session, hcp_id: int | None = None) -> list[Interaction]:
    stmt = select(Interaction).order_by(Interaction.interaction_date.desc())
    if hcp_id is not None:
        stmt = stmt.where(Interaction.hcp_id == hcp_id)
    return list(db.execute(stmt).scalars().all())


def _timeline_item(item: Interaction) -> dict:
    return {
        "id": item.id, "hcp_id": item.hcp_id,
        "interaction_type": item.interaction_type,
        "interaction_date": item.interaction_date,
        "subject": item.subject, "notes": item.notes,
        "topics": item.topics or [], "sentiment": item.sentiment,
        "summary": item.summary or "", **extract_follow_up(item),
    }


@router.get("/interactions/timeline")
def interaction_timeline(
    hcp_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return {"items": [_timeline_item(i) for i in _interactions(db, hcp_id)[:limit]]}


@router.get("/interactions/{interaction_id}/follow-up")
def interaction_follow_up(interaction_id: int, db: Session = Depends(get_db)):
    item = db.get(Interaction, interaction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return {"interaction_id": interaction_id, **extract_follow_up(item)}


@router.get("/copilot/follow-ups")
def follow_up_copilot(
    hcp_id: int | None = Query(default=None), db: Session = Depends(get_db)
):
    return {
        "items": [
            {"interaction_id": i.id, "hcp_id": i.hcp_id, **extract_follow_up(i)}
            for i in _interactions(db, hcp_id)
            if (i.follow_up or "").strip()
        ]
    }


@router.post("/copilot/follow-ups/{interaction_id}/email")
def follow_up_email(
    interaction_id: int,
    request: FollowUpEmailRequest,
    db: Session = Depends(get_db),
):
    item = db.get(Interaction, interaction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interaction not found")
    hcp = db.get(HCP, item.hcp_id)
    follow_up = extract_follow_up(item)
    draft = build_follow_up_email(hcp.full_name if hcp else "there", follow_up["action_item"] or follow_up["follow_up"])
    if request.send:
        if not request.recipient:
            raise HTTPException(status_code=400, detail="Recipient email is required to send.")
        send_follow_up_email(request.recipient, draft["subject"], draft["body"])
    return {**draft, "sent": request.send}


@router.post("/copilot/calendar")
def calendar_event(request: CalendarEventRequest):
    content = build_calendar_event(
        request.title,
        request.start_date,
        request.duration_minutes,
        request.description,
        request.location,
    )
    return Response(
        content=content,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="nova-follow-up.ics"'},
    )


@router.get("/meeting-prep/{hcp_id}")
@router.get("/hcps/{hcp_id}/meeting-prep")
def meeting_preparation(hcp_id: int, db: Session = Depends(get_db)):
    hcp = db.get(HCP, hcp_id)
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    history = _interactions(db, hcp_id)
    topics = Counter(topic for i in history for topic in (i.topics or []))
    open_followups = [
        {"interaction_id": i.id, **extract_follow_up(i)}
        for i in history if (i.follow_up or "").strip()
    ]
    last = _timeline_item(history[0]) if history else None
    return {
        "hcp_id": hcp_id,
        "hcp": {"id": hcp.id, "full_name": hcp.full_name, "specialty": hcp.specialty,
                "organization": hcp.organization, "city": hcp.city},
        "last_interaction": last, "interaction_count": len(history),
        "key_topics": [topic for topic, _ in topics.most_common(10)],
        "open_follow_ups": open_followups,
        "suggested_questions": [
            "What has changed since our last conversation?",
            *[f"Can we follow up on {x['action_item']}?" for x in open_followups if x["action_item"]],
        ],
    }


@router.post("/hcps/duplicates")
def detect_duplicate_hcps(request: DuplicateHCPRequest, db: Session = Depends(get_db)):
    existing = db.execute(select(HCP)).scalars().all()
    candidate = request
    matches = [
        {"id": h.id, "full_name": h.full_name, "specialty": h.specialty,
         "organization": h.organization, "city": h.city, "email": h.email,
         "score": round(duplicate_score(candidate, h), 3)}
        for h in existing
        if h.id != request.exclude_id and duplicate_score(candidate, h) >= request.threshold
    ]
    return {"is_duplicate": bool(matches), "matches": sorted(matches, key=lambda x: x["score"], reverse=True)}


@router.post("/compliance/check")
def compliance_check(request: ComplianceRequest, db: Session = Depends(get_db)):
    text = request.text
    if request.interaction_id is not None:
        item = db.get(Interaction, request.interaction_id)
        if not item:
            raise HTTPException(status_code=404, detail="Interaction not found")
        text = " ".join([item.subject, item.notes, item.follow_up or ""])
    return run_compliance_checks(text)


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    return build_analytics(_interactions(db))
