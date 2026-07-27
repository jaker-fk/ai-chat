from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.chat_message import ChatMessage
from backend.models.chat_session import ChatSession
from backend.models.user import User
from backend.schemas.chat import ChatMessageCreateSchema, ChatSessionCreateSchema
from backend.services.knowledge_service import retrieve_context_for_question
from backend.services.llm_service import stream_llm_reply


def get_user_by_token(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return user


def create_chat_session(db: Session, user: User, payload: ChatSessionCreateSchema) -> ChatSession:
    session = ChatSession(user_id=user.id, title=payload.title or "新会话")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_chat_sessions(db: Session, user: User) -> list[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.updated_time.desc())
    return list(db.scalars(stmt).all())


def get_chat_session(db: Session, user: User, session_id: int) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return session


def list_messages(db: Session, session: ChatSession) -> list[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_time.asc())
    return list(db.scalars(stmt).all())


def delete_chat_session(db: Session, user: User, session_id: int) -> None:
    session = get_chat_session(db, user, session_id)
    for message in list_messages(db, session):
        db.delete(message)
    db.delete(session)
    db.commit()


def _build_chat_history_with_knowledge(db: Session, user: User, session: ChatSession, question: str) -> list[dict[str, str]]:
    history = [{"role": msg.role, "content": msg.content} for msg in list_messages(db, session)]
    context, _ = retrieve_context_for_question(db, user, question, limit=4)
    if not context:
        return history

    system_prompt = (
        "你是一个严谨的 AI 助手。当前用户可能在询问已上传知识库中的内容。"
        "请优先参考下面的知识库片段回答；如果片段不足以回答，请明确说明依据不足，"
        "然后再基于通用知识补充，并区分哪些内容来自知识库。\n\n"
        f"知识库片段：\n{context}"
    )
    return [{"role": "system", "content": system_prompt}, *history]


def send_message_and_stream(
    db: Session,
    user: User,
    session_id: int,
    payload: ChatMessageCreateSchema,
) -> Iterator[str]:
    session = get_chat_session(db, user, session_id)
    user_message = ChatMessage(session_id=session.id, role="user", content=payload.content)
    db.add(user_message)
    db.commit()

    history = _build_chat_history_with_knowledge(db, user, session, payload.content)
    assistant_text = ""
    for chunk in stream_llm_reply(history):
        assistant_text += chunk
        yield chunk

    assistant_message = ChatMessage(session_id=session.id, role="assistant", content=assistant_text)
    session.updated_time = datetime.now(timezone.utc)
    db.add(assistant_message)
    db.add(session)
    db.commit()
