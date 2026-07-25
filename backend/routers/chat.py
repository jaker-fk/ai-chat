from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.chat import ChatMessageCreateSchema, ChatMessageResponseSchema, ChatSessionCreateSchema, ChatSessionResponseSchema
from backend.services.auth_service import get_current_user_from_token
from backend.services.chat_service import create_chat_session, get_chat_session, list_chat_sessions, list_messages, send_message_and_stream

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/sessions", response_model=list[ChatSessionResponseSchema])
def sessions(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = get_current_user_from_token(db, authorization)
    return list_chat_sessions(db, user)


@router.post("/sessions", response_model=ChatSessionResponseSchema)
def create_session(
    payload: ChatSessionCreateSchema,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = get_current_user_from_token(db, authorization)
    return create_chat_session(db, user, payload)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponseSchema])
def session_messages(
    session_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = get_current_user_from_token(db, authorization)
    session = get_chat_session(db, user, session_id)
    return list_messages(db, session)


@router.post("/sessions/{session_id}/stream")
def stream_chat(
    session_id: int,
    payload: ChatMessageCreateSchema,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = get_current_user_from_token(db, authorization)

    async def event_generator():
        assistant = ""
        async for chunk in send_message_and_stream(db, user, session_id, payload):
            assistant += chunk
            yield f"data: {json.dumps({'delta': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'content': assistant}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
