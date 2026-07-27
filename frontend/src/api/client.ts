import type { ApiSuccess } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';
const TOKEN_KEY = 'ai_chat_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers as Record<string, string> | undefined),
    },
  });

  const text = await response.text();
  const raw = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const err = raw as { message?: string; detail?: string } | null;
    throw new Error(err?.message ?? err?.detail ?? `请求失败 (${response.status})`);
  }

  const payload = raw as ApiSuccess<T> | null;
  if (payload && typeof payload.code === 'number' && 'data' in payload) {
    return payload.data;
  }
  return raw as T;
}

export { API_BASE_URL, request };

export async function requestForm<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  const text = await response.text();
  const raw = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const err = raw as { message?: string; detail?: string } | null;
    throw new Error(err?.message ?? err?.detail ?? `请求失败 (${response.status})`);
  }

  const payload = raw as ApiSuccess<T> | null;
  if (payload && typeof payload.code === 'number' && 'data' in payload) {
    return payload.data;
  }
  return raw as T;
}

export async function streamChat(
  sessionId: number,
  content: string,
  onDelta: (delta: string) => void,
): Promise<string> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `流式请求失败 (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let full = '';

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data:')) continue;
      const json = trimmed.slice(5).trim();
      if (!json) continue;
      try {
        const evt = JSON.parse(json) as { delta?: string; done?: boolean; content?: string };
        if (evt.delta) {
          full += evt.delta;
          onDelta(evt.delta);
        }
        if (evt.done && typeof evt.content === 'string') {
          full = evt.content;
        }
      } catch {
        // 忽略无法解析的数据行
      }
    }
  }

  return full;
}
