from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocumentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    filename: str
    content_type: str | None
    source_type: str
    content: str
    created_time: datetime
    updated_time: datetime


class KnowledgeChunkResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_index: int
    content: str
    keywords: str
    created_time: datetime


class KnowledgeAskSchema(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


