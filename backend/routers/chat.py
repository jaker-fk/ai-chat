from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.chat import ChatMessageCreateSchema, ChatMessageResponseSchema, ChatSessionCreateSchema, ChatSessionResponseSchema
from backend.schemas.common import SuccessResponse
from backend.services.auth_service import get_current_user_from_token
from backend.services.chat_service import (
    create_chat_session,
    delete_chat_session,
    get_chat_session,
    list_chat_sessions,
    list_messages,
    send_message_and_stream,
)

router = APIRouter(prefix="/chat", tags=["AI会话"])


@router.get("/sessions", response_model=SuccessResponse[list[ChatSessionResponseSchema]], tags=["会话列表"])
def sessions(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)
    sessions = list_chat_sessions(db, user)
    return SuccessResponse[list[ChatSessionResponseSchema]](data=[ChatSessionResponseSchema.model_validate(session) for session in sessions])


@router.post("/sessions", response_model=SuccessResponse[ChatSessionResponseSchema], tags=["创建会话"])
def create_session(payload: ChatSessionCreateSchema, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)
    session = create_chat_session(db, user, payload)
    return SuccessResponse[ChatSessionResponseSchema](data=ChatSessionResponseSchema.model_validate(session))


@router.delete("/sessions/{session_id}", response_model=SuccessResponse[bool], tags=["删除会话"])
def delete_session(session_id: int, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)
    delete_chat_session(db, user, session_id)
    return SuccessResponse[bool](data=True)


@router.delete("/sessions/{session_id}", response_model=SuccessResponse[bool], tags=["删除会话"])
def delete_session(session_id: int, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)
    delete_chat_session(db, user, session_id)
    return SuccessResponse[bool](data=True)


@router.get("/sessions/{session_id}/messages", response_model=SuccessResponse[list[ChatMessageResponseSchema]], tags=["会话消息列表"])
def session_messages(session_id: int, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)
    session = get_chat_session(db, user, session_id)
    messages = list_messages(db, session)
    return SuccessResponse[list[ChatMessageResponseSchema]](data=[ChatMessageResponseSchema.model_validate(message) for message in messages])


@router.post("/sessions/{session_id}/stream", tags=["流式会话"])
def stream_chat(session_id: int, payload: ChatMessageCreateSchema, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)

    async def event_generator():
        assistant = ""
        for chunk in send_message_and_stream(db, user, session_id, payload):
            assistant += chunk
            yield f"data: {json.dumps({'delta': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'content': assistant}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
