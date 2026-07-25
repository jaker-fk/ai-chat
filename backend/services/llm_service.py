from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from backend.core.config import settings


async def stream_llm_reply(messages: list[dict[str, str]]) -> AsyncIterator[str]:
    base_url = settings.deepseek_base_url or settings.openai_base_url
    api_key = settings.deepseek_api_key or settings.openai_api_key
    model = settings.deepseek_model if settings.deepseek_api_key else settings.openai_model

    if not api_key:
        content = "未配置大模型 API Key，当前为本地模拟回复。"
        for chunk in _chunk_text(content):
            yield chunk
        return

    payload = {"model": model, "messages": messages, "stream": True}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{base_url.rstrip('/')}/chat/completions", json=payload, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line.removeprefix("data:").strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj["choices"][0]["delta"].get("content")
                except Exception:
                    delta = None
                if delta:
                    yield delta


def _chunk_text(text: str, size: int = 12):
    for index in range(0, len(text), size):
        yield text[index:index + size]

