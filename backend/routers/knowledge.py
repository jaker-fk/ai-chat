from __future__ import annotations

from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.common import SuccessResponse
from backend.schemas.knowledge import KnowledgeAskSchema, KnowledgeDocumentResponseSchema
from backend.services.auth_service import get_current_user_from_token
from backend.services.knowledge_service import answer_question, list_documents, upload_document

router = APIRouter(prefix="/knowledge", tags=["知识库"])


@router.get("/documents", response_model=SuccessResponse[list[KnowledgeDocumentResponseSchema]], tags=["知识文档列表"])
def documents(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)
    docs = list_documents(db, user)
    return SuccessResponse[list[KnowledgeDocumentResponseSchema]](data=[KnowledgeDocumentResponseSchema.model_validate(doc) for doc in docs])


@router.post("/documents/upload", response_model=SuccessResponse[KnowledgeDocumentResponseSchema], tags=["上传文档"])
def upload(authorization: str | None = Header(default=None), db: Session = Depends(get_db), file: UploadFile = File(...)):
    user = get_current_user_from_token(db, authorization)
    doc = upload_document(db, user, file)
    return SuccessResponse[KnowledgeDocumentResponseSchema](data=KnowledgeDocumentResponseSchema.model_validate(doc))


@router.post("/ask", response_model=SuccessResponse[dict], tags=["知识库问答"])
def ask(payload: KnowledgeAskSchema, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = get_current_user_from_token(db, authorization)
    return SuccessResponse[dict](data=answer_question(db, user, payload.question))
