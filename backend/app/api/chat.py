"""
Chat API
"""

import logging

from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.api.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Nova"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    state = {
        "draft": request.draft,
        "highlighted_fields": [],
        "conversation_stage": request.conversation_stage,
        "ready_for_confirmation": request.ready_for_confirmation,
        "saved": False,
        # These three were previously declared on ChatRequest but never
        # actually forwarded into `state` here, so they were silently
        # dropped on every request regardless of what the frontend sent.
        "current_field": request.current_field,
        "last_interaction_id": request.last_interaction_id,
        "awaiting_post_save_choice": request.awaiting_post_save_choice,
        "awaiting_new_hcp_details": request.awaiting_new_hcp_details,
        "pending_new_hcp": request.pending_new_hcp,
    }

    try:
        return chat_service.process_message(
            db=db,
            message=request.message,
            history=[
                message.model_dump()
                for message in request.history
            ],
            state=state,
        )

    except Exception:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process the chat request.",
        )