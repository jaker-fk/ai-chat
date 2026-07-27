from __future__ import annotations

import io
import re
from collections import Counter
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Iterable
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.knowledge_base import KnowledgeChunk, KnowledgeDocument
from backend.models.user import User
from backend.services.llm_service import stream_llm_reply

_SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".log"}
_SUPPORTED_BINARY_EXTENSIONS = {".pdf", ".docx", ".doc"}
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: KnowledgeChunk
    score: float


def upload_document(db: Session, user: User, file: UploadFile) -> KnowledgeDocument:
    filename = file.filename or "untitled.txt"
    suffix = Path(filename).suffix.lower()
    raw = file.file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty file")
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file too large")

    content = _extract_text(raw, suffix)
    document = KnowledgeDocument(
        user_id=user.id,
        filename=filename,
        content_type=file.content_type,
        source_type="upload",
        content=content,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    for index, chunk_text in enumerate(split_text(content)):
        db.add(KnowledgeChunk(document_id=document.id, chunk_index=index, content=chunk_text, keywords=_extract_keywords(chunk_text)))
    db.commit()
    return document


def list_documents(db: Session, user: User) -> list[KnowledgeDocument]:
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.user_id == user.id).order_by(KnowledgeDocument.updated_time.desc())
    return list(db.scalars(stmt).all())


def answer_question(db: Session, user: User, question: str, limit: int = 4) -> dict[str, object]:
    chunks = list(_load_candidate_chunks(db, user))
    scored = sorted((RetrievedChunk(chunk=chunk, score=_similarity(question, chunk.content)) for chunk in chunks), key=lambda item: item.score, reverse=True)
    top_chunks = _select_relevant_chunks(scored, limit=limit)
    context = "\n\n".join(f"[{index + 1}] {item.chunk.content}" for index, item in enumerate(top_chunks))
    if not context:
        return {"answer": "当前知识库里没有找到足够相关的内容，请先上传文档或换个问法。", "sources": []}

    return {
        "answer": _build_answer(question, context),
        "sources": [{"document_id": item.chunk.document_id, "chunk_id": item.chunk.id, "score": round(item.score, 4), "content": item.chunk.content} for item in top_chunks],
    }


def _load_candidate_chunks(db: Session, user: User) -> Iterable[KnowledgeChunk]:
    stmt = select(KnowledgeChunk).join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id).where(KnowledgeDocument.user_id == user.id)
    return db.scalars(stmt).all()


def _select_relevant_chunks(scored: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
    positive = [item for item in scored if item.score > 0.1]
    if positive:
        return positive[:limit]
    return scored[:limit]


def split_text(content: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", content).strip()
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _extract_text(raw: bytes, suffix: str) -> str:
    if suffix in _SUPPORTED_TEXT_EXTENSIONS or not suffix:
        return raw.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        return _extract_pdf_text(raw)
    if suffix == ".docx":
        return _extract_docx_text(raw)
    if suffix == ".doc":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doc format is not supported yet")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"unsupported file type: {suffix}")


def _extract_pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - dependency guard
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="pdf parser not installed") from exc

    reader = PdfReader(io.BytesIO(raw))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    content = "\n".join(pages).strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="pdf has no extractable text")
    return content


def _extract_docx_text(raw: bytes) -> str:
    try:
        with ZipFile(io.BytesIO(raw)) as archive:
            document_xml = archive.read("word/document.xml")
    except (BadZipFile, KeyError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid docx file")

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    content = "\n".join(paragraphs).strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="docx has no extractable text")
    return content


def _extract_keywords(text: str, limit: int = 12) -> str:
    words = re.findall(r"[\w\u4e00-\u9fff]{2,}", text.lower())
    return ",".join(word for word, _ in Counter(words).most_common(limit))


def _similarity(query: str, text: str) -> float:
    query_tokens = _tokenize(query)
    text_tokens = _tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0
    query_vec = Counter(query_tokens)
    text_vec = Counter(text_tokens)
    overlap = set(query_vec) & set(text_vec)
    numerator = sum(query_vec[token] * text_vec[token] for token in overlap)
    denominator = sqrt(sum(v * v for v in query_vec.values())) * sqrt(sum(v * v for v in text_vec.values()))
    return numerator / denominator if denominator else 0.0


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\u4e00-\u9fff]{2,}", text.lower())


def _build_answer(question: str, context: str) -> str:
    prompt = (
        "你是一个严谨的知识库问答助手。请只依据给定的文档片段回答问题；"
        "如果片段中没有直接答案，请说明文档未提供明确依据，不要编造。\n\n"
        f"问题：{question}\n\n"
        f"文档片段：\n{context}\n\n"
        "请用中文给出清晰、简洁、有条理的回答，并在需要时提及对应片段编号。"
    )
    messages = [
        {"role": "system", "content": "你只能基于用户提供的文档片段回答问题。"},
        {"role": "user", "content": prompt},
    ]
    answer = "".join(stream_llm_reply(messages)).strip()
    if not answer:
        return f"根据已上传文档，问题‘{question}’的相关内容如下：\n\n{context}"
    return answer
