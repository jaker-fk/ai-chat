import { useEffect, useMemo, useRef, useState } from 'react';

import type { ChatMessage, ChatSession, KnowledgeDocument, KnowledgeSource } from '../api/types';

type Props = {
  currentSession: ChatSession | null;
  messages: ChatMessage[];
  chatError: string | null;
  chatLoading: boolean;
  messageInput: string;
  onMessageInputChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onKeyDown: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onEditSessionTitle: () => void;
  onToggleSidebar: () => void;
  sidebarCollapsed: boolean;
  documents: KnowledgeDocument[];
  documentLoading: boolean;
  documentError: string | null;
  documentUploading: boolean;
  documentQuery: string;
  documentHistory: {
    id: number;
    question: string;
    answer: string;
    sources: KnowledgeSource[];
    createdAt: string;
  }[];
  documentQuestioning: boolean;
  onDocumentQueryChange: (value: string) => void;
  onAskDocument: (event: React.FormEvent<HTMLFormElement>) => void;
  onUploadDocument: (file: File | null) => void;
  supportedUploadExtensions: string[];
  maxUploadSizeMB: number;
  onClearDocumentAnswer: () => void;
};

function shorten(text: string, limit = 140) {
  return text.length > limit ? `${text.slice(0, limit)}...` : text;
}

export function ChatPanel({
  currentSession,
  messages,
  chatError,
  chatLoading,
  messageInput,
  onMessageInputChange,
  onSubmit,
  onKeyDown,
  onEditSessionTitle,
  onToggleSidebar,
  sidebarCollapsed,
  documents,
  documentLoading,
  documentError,
  documentUploading,
  documentQuery,
  documentHistory,
  documentQuestioning,
  onDocumentQueryChange,
  onAskDocument,
  onUploadDocument,
  onClearDocumentAnswer,
  supportedUploadExtensions,
  maxUploadSizeMB,
}: Props) {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [previewDocumentId, setPreviewDocumentId] = useState<number | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatError, chatLoading]);

  const latestDocument = useMemo(() => documents[0] ?? null, [documents]);
  const latestQuestion = documentHistory[0] ?? null;
  const uploadTips = useMemo(() => supportedUploadExtensions.map((ext) => ext.replace(/^\./, '').toUpperCase()).join(' / '), [supportedUploadExtensions]);
  const uploadProgressText = documentUploading ? `正在上传${selectedFileName ? `：${selectedFileName}` : '...'}` : '选择文件';

  return (
    <main className="chat-panel">
      <header className="chat-header">
        <div className="chat-header-top">
          <button className="ghost-btn mobile-only" onClick={onToggleSidebar} type="button">
            {sidebarCollapsed ? '展开会话' : '收起会话'}
          </button>
          <div className="hero-copy">
            <span className="pill">知识库问答 + 流式聊天</span>
            <h1>{currentSession?.title ?? '先创建一个会话开始'}</h1>
            <p>上传文档后即可基于你的资料提问，支持文档检索、来源引用和连续对话。</p>
          </div>
          <div className="session-actions">
            {currentSession && (
              <button className="secondary-btn" type="button" onClick={onEditSessionTitle}>
                编辑标题
              </button>
            )}
            <span className="session-status">在线</span>
          </div>
        </div>
      </header>

      <section className="workspace-grid">
        <section className="chat-column">
          <div className="section-head">
            <div>
              <h2>对话</h2>
              <p>和 AI 继续对话，适合追问、总结和澄清问题。</p>
            </div>
            {latestDocument && <span className="hint-chip">最近文档：{latestDocument.filename}</span>}
          </div>

          <div className="message-list">
            {messages.map((message, index) => {
              const isUser = message.role === 'user';
              const isLast = index === messages.length - 1;
              const isStreaming = isLast && chatLoading && !isUser;

              return (
                <article key={message.id} className={isUser ? 'message user' : 'message assistant'}>
                  <div className="message-avatar">{isUser ? '你' : 'AI'}</div>
                  <div className="message-body">
                    <div className="message-meta">
                      <span>{isUser ? '你' : 'AI 助手'}</span>
                      <span className={isStreaming ? 'message-status streaming' : 'message-status'}>
                        {isUser ? '已发送' : isStreaming ? '生成中' : '已完成'}
                      </span>
                    </div>
                    <div className="message-content">{message.content}</div>
                  </div>
                </article>
              );
            })}
            {chatError && <div className="notice error">{chatError}</div>}
            {!currentSession && <div className="empty-state center">请先创建或选择一个会话。</div>}
            <div ref={bottomRef} />
          </div>

          <form className="chat-input-bar" onSubmit={onSubmit}>
            <textarea
              value={messageInput}
              onChange={(e) => onMessageInputChange(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={currentSession ? 'Enter 发送，Shift+Enter 换行' : '先创建会话再发送'}
              rows={3}
              disabled={!currentSession || chatLoading}
            />
            <button className="primary-btn" type="submit" disabled={!currentSession || chatLoading || !messageInput.trim()}>
              {chatLoading ? '发送中...' : '发送'}
            </button>
          </form>
        </section>

        <aside className="knowledge-panel">
          <div className="section-head">
            <div>
              <h2>知识库</h2>
              <p>上传文档，系统会自动切分内容并支持问答检索。</p>
            </div>
            <button className="ghost-btn" type="button" onClick={onClearDocumentAnswer}>
              清空回答
            </button>
          </div>

          <div
            className={dragActive ? 'upload-card drag-active' : 'upload-card'}
            onDragOver={(e) => {
              e.preventDefault();
              if (!documentUploading) setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              if (documentUploading) return;
              const file = e.dataTransfer.files?.[0] ?? null;
              if (file) {
                setSelectedFileName(file.name);
                onUploadDocument(file);
                setFileInputKey((v) => v + 1);
              }
            }}
          >
            <div>
              <h3>上传文档</h3>
              <p>支持拖拽上传，也可以点击选择文件。建议上传 {uploadTips} 文档，单个文件不超过 {maxUploadSizeMB}MB。</p>
            </div>
            <label className="file-picker">
              <input
                key={fileInputKey}
                type="file"
                accept={supportedUploadExtensions.join(',')}
                disabled={documentUploading}
                onChange={(e) => {
                  const file = e.target.files?.[0] ?? null;
                  setSelectedFileName(file?.name ?? null);
                  onUploadDocument(file);
                  setFileInputKey((v) => v + 1);
                }}
              />
              <span>{uploadProgressText}</span>
            </label>
            <div className="upload-meta">
              <span>{selectedFileName ?? '尚未选择文件'}</span>
              <span>{dragActive ? '松开即可上传' : '拖拽到此处更快捷'}</span>
            </div>
            <div className="upload-footnote">支持文档会自动切分索引，上传后可直接提问。</div>
            {documentError && <div className="notice error">{documentError}</div>}
          </div>

          <div className="docs-card">
            <div className="section-head compact">
              <div>
                <h3>已上传文档</h3>
                <p>{documentLoading ? '正在加载...' : `共 ${documents.length} 个文档`}</p>
              </div>
            </div>
            <div className="doc-list">
              {documents.map((doc) => (
                <article key={doc.id} className={previewDocumentId === doc.id ? 'doc-item active' : 'doc-item'} onClick={() => setPreviewDocumentId(doc.id)}>
                  <div className="doc-icon">DOC</div>
                  <div className="doc-body">
                    <strong>{doc.filename}</strong>
                    <p>{shorten(doc.content)}</p>
                    <span>{new Date(doc.updated_time).toLocaleString()}</span>
                  </div>
                </article>
              ))}
              {documents.length === 0 && <div className="empty-state">还没有上传文档，先传一份资料试试。</div>}
            </div>
          </div>

          <div className="qa-card">
            <div className="section-head compact">
              <div>
                <h3>知识库提问</h3>
                <p>直接问文档内容，系统会返回答案和引用来源。</p>
              </div>
            </div>
            <form className="qa-form" onSubmit={onAskDocument}>
              <textarea
                rows={4}
                value={documentQuery}
                onChange={(e) => onDocumentQueryChange(e.target.value)}
                placeholder="例如：这份文档的核心流程是什么？"
              />
              <button className="primary-btn" type="submit" disabled={documentQuestioning || !documentQuery.trim()}>
                {documentQuestioning ? '思考中...' : '基于文档回答'}
              </button>
            </form>
            <div className="knowledge-chat-history">
              {documentHistory.map((item) => (
                <div key={item.id} className="knowledge-thread">
                  <article className="knowledge-bubble question">
                    <div className="knowledge-bubble-meta">
                      <span>你的问题</span>
                      <span>{new Date(item.createdAt).toLocaleString()}</span>
                    </div>
                    <div className="knowledge-bubble-content">{item.question}</div>
                  </article>
                  <article className="knowledge-bubble answer">
                    <div className="knowledge-bubble-meta">
                      <span>知识库回答</span>
                      <span>{item.sources.length} 条来源</span>
                    </div>
                    <div className="knowledge-bubble-content">{item.answer}</div>
                    {item.sources.length > 0 && (
                      <div className="sources-list">
                        <div className="qa-result-title">引用来源</div>
                        {item.sources.map((source) => (
                          <article key={`${source.document_id}-${source.chunk_id}`} className="source-item">
                            <span className="source-score">{Math.round(source.score * 100)}%</span>
                            <p>{source.content}</p>
                          </article>
                        ))}
                      </div>
                    )}
                  </article>
                </div>
              ))}
              {!latestQuestion && !documentQuestioning && (
                <div className="empty-state">提一个关于文档的问题，这里会以聊天记录的形式保留历史问答。</div>
              )}
              {documentQuestioning && <div className="notice">知识库正在分析文档内容，请稍候...</div>}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
