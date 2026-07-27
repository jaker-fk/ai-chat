import type { ChatSession } from '../api/types';

type Props = {
  apiBaseUrl: string;
  sessions: ChatSession[];
  currentSessionId: number | null;
  collapsed: boolean;
  deletingSessionId: number | null;
  onLogout: () => void;
  onCreateSession: () => void;
  onSelectSession: (sessionId: number) => void;
  onDeleteSession: (session: ChatSession) => void;
  onToggleCollapse: () => void;
};

export function Sidebar({
  sessions,
  currentSessionId,
  collapsed,
  deletingSessionId,
  onLogout,
  onCreateSession,
  onSelectSession,
  onDeleteSession,
  onToggleCollapse,
}: Props) {
  if (collapsed) {
    return (
      <aside className="sidebar collapsed">
        <button className="ghost-btn" type="button" onClick={onToggleCollapse} title="展开会话">☰</button>
        <button className="primary-btn" type="button" onClick={onCreateSession} title="新建会话">+</button>
        <button className="secondary-btn" type="button" onClick={onLogout} title="退出登录">⏻</button>
      </aside>
    );
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div><h2>会话</h2></div>
        <button className="ghost-btn" type="button" onClick={onToggleCollapse} title="收起会话">◀</button>
      </div>
      <button className="primary-btn full-width" type="button" onClick={onCreateSession}>新建会话</button>
      <div className="session-list">
        {sessions.map((session) => (
          <div key={session.id} className={session.id === currentSessionId ? 'session-row active' : 'session-row'}>
            <button className="session-item" type="button" onClick={() => onSelectSession(session.id)}>
              <strong>{session.title}</strong>
              <span>{new Date(session.updated_time).toLocaleString()}</span>
            </button>
            <button
              className="session-delete-btn"
              type="button"
              onClick={() => onDeleteSession(session)}
              disabled={deletingSessionId === session.id}
              aria-label={`删除会话 ${session.title}`}
              title="删除会话"
            >
              {deletingSessionId === session.id ? '…' : '×'}
            </button>
          </div>
        ))}
        {sessions.length === 0 && <div className="empty-state">暂无会话，先创建一个开始聊天。</div>}
      </div>
      <button className="secondary-btn" type="button" onClick={onLogout}>退出登录</button>
    </aside>
  );
}
