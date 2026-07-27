import { useCallback, useEffect, useMemo, useState } from 'react';

import { AuthPanel } from './components/AuthPanel';
import { ChatPanel } from './components/ChatPanel';
import { Sidebar } from './components/Sidebar';
import { API_BASE_URL, clearToken, getToken, request, requestForm, setToken, streamChat } from './api/client';
import type { ChatMessage, ChatSession, KnowledgeAnswer, KnowledgeDocument, KnowledgeSource, TokenData } from './api/types';

type AuthMode = 'login' | 'register';

export default function App() {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [deletingSessionId, setDeletingSessionId] = useState<number | null>(null);
  const [sessionToDelete, setSessionToDelete] = useState<ChatSession | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [documentLoading, setDocumentLoading] = useState(false);
  const [documentError, setDocumentError] = useState<string | null>(null);
  const [documentUploading, setDocumentUploading] = useState(false);
  const [documentQuery, setDocumentQuery] = useState('');
  const [documentHistory, setDocumentHistory] = useState<
    { id: number; question: string; answer: string; sources: KnowledgeSource[]; createdAt: string }[]
  >([]);
  const [documentQuestioning, setDocumentQuestioning] = useState(false);

  const currentSession = sessions.find((s) => s.id === currentSessionId) ?? null;

  const loadSessions = useCallback(async () => {
    try {
      const data = await request<ChatSession[]>('/chat/sessions');
      setSessions(data);
    } catch (err) {
      setChatError((err as Error).message);
    }
  }, []);

  const loadMessages = useCallback(async (sessionId: number) => {
    setChatError(null);
    try {
      const data = await request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
      setMessages(data);
    } catch (err) {
      setChatError((err as Error).message);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setDocumentLoading(true);
    setDocumentError(null);
    try {
      const data = await request<KnowledgeDocument[]>('/knowledge/documents');
      setDocuments(data);
    } catch (err) {
      setDocumentError((err as Error).message);
    } finally {
      setDocumentLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!sessionToDelete) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSessionToDelete(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sessionToDelete]);
  useEffect(() => {
    if (token) {
      void loadSessions();
      void loadDocuments();
    } else {
      setSessions([]);
      setMessages([]);
      setCurrentSessionId(null);
      setDocuments([]);
      setDocumentHistory([]);
    }
  }, [token, loadSessions, loadDocuments]);

  const handleAuthSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    try {
      const path = authMode === 'login' ? '/auth/login' : '/auth/register';
      const payload = authMode === 'login' ? { username, password } : { username, password, nickname: nickname || null };
      const data = await request<TokenData>(path, { method: 'POST', body: JSON.stringify(payload) });
      setToken(data.access_token);
      setTokenState(data.access_token);
      setUsername('');
      setPassword('');
      setNickname('');
    } catch (err) {
      setAuthError((err as Error).message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    setTokenState(null);
  };

  const handleCreateSession = async () => {
    setChatError(null);
    try {
      const session = await request<ChatSession>('/chat/sessions', {
        method: 'POST',
        body: JSON.stringify({ title: `新会话 ${new Date().toLocaleString()}` }),
      });
      setSessions((prev) => [session, ...prev]);
      setCurrentSessionId(session.id);
      setMessages([]);
    } catch (err) {
      setChatError((err as Error).message);
    }
  };

  const handleSelectSession = (sessionId: number) => {
    setCurrentSessionId(sessionId);
    void loadMessages(sessionId);
  };

  const handleDeleteSession = async (session: ChatSession) => {
    setDeletingSessionId(session.id);
    setChatError(null);
    try {
      await request<boolean>(`/chat/sessions/${session.id}`, { method: 'DELETE' });
      setSessions((prev) => prev.filter((item) => item.id !== session.id));
      if (currentSessionId === session.id) {
        setCurrentSessionId(null);
        setMessages([]);
        setMessageInput('');
      }
    } catch (err) {
      setChatError((err as Error).message);
    } finally {
      setDeletingSessionId(null);
      setSessionToDelete(null);
    }
  };

  const handleEditSessionTitle = () => {
    if (!currentSession) return;
    const next = window.prompt('修改会话标题', currentSession.title);
    if (next && next.trim()) {
      setSessions((prev) => prev.map((s) => (s.id === currentSession.id ? { ...s, title: next.trim() } : s)));
    }
  };

  const handleSubmitMessage = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentSessionId || !messageInput.trim() || chatLoading) return;
    const content = messageInput.trim();
    setMessageInput('');
    setChatError(null);

    const now = new Date().toISOString();
    const userMsg: ChatMessage = { id: Date.now(), session_id: currentSessionId, role: 'user', content, created_time: now };
    const assistantId = Date.now() + 1;
    const assistantMsg: ChatMessage = { id: assistantId, session_id: currentSessionId, role: 'assistant', content: '', created_time: now };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setChatLoading(true);

    try {
      const full = await streamChat(currentSessionId, content, (delta) => {
        setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + delta } : m)));
      });
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: full || m.content } : m)));
      void loadSessions();
    } catch (err) {
      setChatError((err as Error).message);
      setMessages((prev) => prev.filter((m) => !(m.id === assistantId && m.content === '')));
    } finally {
      setChatLoading(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      const form = event.currentTarget.form;
      if (form) form.requestSubmit();
    }
  };

  const toggleSidebar = () => setSidebarCollapsed((v) => !v);

  const handleUploadDocument = async (file: File | null) => {
    if (!file) return;
    setDocumentUploading(true);
    setDocumentError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await requestForm<KnowledgeDocument>('/knowledge/documents/upload', formData);
      await loadDocuments();
    } catch (err) {
      setDocumentError((err as Error).message);
    } finally {
      setDocumentUploading(false);
    }
  };

  const handleAskDocument = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!documentQuery.trim()) return;
    setDocumentQuestioning(true);
    setDocumentError(null);
    try {
      const question = documentQuery.trim();
      const data = await request<KnowledgeAnswer>('/knowledge/ask', { method: 'POST', body: JSON.stringify({ question }) });
      setDocumentHistory((prev) => [{ id: Date.now(), question, answer: data.answer, sources: data.sources, createdAt: new Date().toISOString() }, ...prev]);
      setDocumentQuery('');
    } catch (err) {
      setDocumentError((err as Error).message);
    } finally {
      setDocumentQuestioning(false);
    }
  };

  const handleClearDocumentAnswer = () => {
    setDocumentHistory([]);
    setDocumentQuery('');
  };

  const canShowKnowledge = useMemo(() => Boolean(token), [token]);

  if (!token) {
    return (
      <AuthPanel
        mode={authMode}
        username={username}
        password={password}
        nickname={nickname}
        loading={authLoading}
        error={authError}
        onModeChange={setAuthMode}
        onUsernameChange={setUsername}
        onPasswordChange={setPassword}
        onNicknameChange={setNickname}
        onSubmit={handleAuthSubmit}
      />
    );
  }

  return (
    <div className={`app-shell${sidebarCollapsed ? ' sidebar-collapsed' : ''}`} data-knowledge={canShowKnowledge ? 'true' : 'false'}>
      <Sidebar
        apiBaseUrl={API_BASE_URL}
        sessions={sessions}
        currentSessionId={currentSessionId}
        collapsed={sidebarCollapsed}
        deletingSessionId={deletingSessionId}
        onLogout={handleLogout}
        onCreateSession={handleCreateSession}
        onSelectSession={handleSelectSession}
        onDeleteSession={setSessionToDelete}
        onToggleCollapse={toggleSidebar}
      />
      <ChatPanel
        currentSession={currentSession}
        messages={messages}
        chatError={chatError}
        chatLoading={chatLoading}
        messageInput={messageInput}
        onMessageInputChange={setMessageInput}
        onSubmit={handleSubmitMessage}
        onKeyDown={handleKeyDown}
        onEditSessionTitle={handleEditSessionTitle}
        onToggleSidebar={toggleSidebar}
        sidebarCollapsed={sidebarCollapsed}
        documents={documents}
        documentLoading={documentLoading}
        documentError={documentError}
        documentUploading={documentUploading}
        documentQuery={documentQuery}
        documentHistory={documentHistory}
        documentQuestioning={documentQuestioning}
        onDocumentQueryChange={setDocumentQuery}
        onAskDocument={handleAskDocument}
        onUploadDocument={handleUploadDocument}
        supportedUploadExtensions={['.txt', '.md', '.markdown', '.json', '.csv', '.log']}
        maxUploadSizeMB={10}
        onClearDocumentAnswer={handleClearDocumentAnswer}
      />
            {sessionToDelete && (
        <div className="modal-backdrop" onClick={() => setSessionToDelete(null)}>
          <div
            className="modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-session-title"
          >
            <div className="modal-header">
              <div>
                <p className="modal-kicker">删除会话</p>
                <h3 id="delete-session-title">确认删除这个会话？</h3>
              </div>
              <button className="ghost-btn modal-close" type="button" onClick={() => setSessionToDelete(null)}>
                ×
              </button>
            </div>

            <p className="modal-body">
              会话 <strong>“{sessionToDelete.title}”</strong> 以及其中的全部消息都会被永久删除，无法恢复。
            </p>

            <div className="modal-actions">
              <button className="secondary-btn" type="button" onClick={() => setSessionToDelete(null)}>
                取消
              </button>
              <button
                className="danger-btn"
                type="button"
                disabled={deletingSessionId === sessionToDelete.id}
                onClick={() => void handleDeleteSession(sessionToDelete)}
              >
                {deletingSessionId === sessionToDelete.id ? '删除中...' : '确认删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
