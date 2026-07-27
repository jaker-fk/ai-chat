type AuthMode = 'login' | 'register';

type Props = {
  mode: AuthMode;
  username: string;
  password: string;
  nickname: string;
  loading: boolean;
  error: string | null;
  onModeChange: (mode: AuthMode) => void;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onNicknameChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function AuthPanel({
  mode,
  username,
  password,
  nickname,
  loading,
  error,
  onModeChange,
  onUsernameChange,
  onPasswordChange,
  onNicknameChange,
  onSubmit,
}: Props) {
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand-block">
          <div className="brand-badge">AI</div>
          <div>
            <h1>AI 对话应用</h1>
            <p>安全登录、会话管理、流式聊天，全部接入后端接口。</p>
          </div>
        </div>

        <div className="mode-switch">
          <button className={mode === 'login' ? 'active' : ''} onClick={() => onModeChange('login')} type="button">
            登录
          </button>
          <button className={mode === 'register' ? 'active' : ''} onClick={() => onModeChange('register')} type="button">
            注册
          </button>
        </div>

        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            用户名
            <input value={username} onChange={(e) => onUsernameChange(e.target.value)} placeholder="输入用户名" />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(e) => onPasswordChange(e.target.value)} placeholder="输入密码" />
          </label>
          {mode === 'register' && (
            <label>
              昵称
              <input value={nickname} onChange={(e) => onNicknameChange(e.target.value)} placeholder="输入昵称" />
            </label>
          )}
          {error && <div className="notice error">{error}</div>}
          <button className="primary-btn" type="submit" disabled={loading}>
            {loading ? '处理中...' : mode === 'login' ? '登录进入' : '注册并进入'}
          </button>
        </form>
      </div>
    </div>
  );
}

