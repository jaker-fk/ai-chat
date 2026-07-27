from __future__ import annotations

import json
from typing import Iterator

import httpx

from backend.core.config import settings


def stream_llm_reply(messages: list[dict[str, str]]) -> Iterator[str]:
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

    try:
        with httpx.Client(timeout=None) as client:
            with client.stream("POST", f"{base_url.rstrip('/')}/chat/completions", json=payload, headers=headers) as response:
                if not response.is_success:
                    # 把 API 返回的错误信息友好地抛给前端，避免连接被静默关闭
                    try:
                        err_body = response.read()
                        err_json = json.loads(err_body)
                        err_msg = err_json.get("error", {}).get("message", f"API 错误 {response.status_code}")
                    except Exception:
                        err_msg = f"API 请求失败 ({response.status_code})"
                    yield f"[模型服务错误：{err_msg}]"
                    return

                for line in response.iter_lines():
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
    except httpx.RequestError as exc:
        yield f"[网络错误：无法连接到模型服务 ({type(exc).__name__})]"
    except Exception as exc:
        yield f"[模型服务异常：{exc}]"


def _chunk_text(text: str, size: int = 12):
    for index in range(0, len(text), size):
        yield text[index:index + size]
