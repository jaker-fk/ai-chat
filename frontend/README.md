# 前端启动说明

## 1. 安装依赖

进入前端目录后执行：

```bash
npm install
```

## 2. 启动开发服务器

默认使用 Vite 启动：

```bash
npm run dev
```

启动后通常会访问：

```text
http://127.0.0.1:5173
```

## 3. 配置后端地址

如果后端不是运行在 `http://127.0.0.1:8000`，可以在前端目录创建 `.env` 文件并配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 4. 功能说明

当前前端包含以下功能：

- 登录
- 注册
- JWT 登录态保存
- 会话列表
- 创建会话
- 编辑会话标题
- 流式消息发送
- Enter 发送，Shift+Enter 换行
- 自动滚动到最新消息
- 侧边栏响应式收起
- 消息气泡头像与状态指示

## 5. 后端接口依赖

前端依赖以下后端接口：

- `POST /auth/register`
- `POST /auth/login`
- `GET /chat/sessions`
- `POST /chat/sessions`
- `GET /chat/sessions/{session_id}/messages`
- `POST /chat/sessions/{session_id}/stream`

## 6. 常见问题

### 6.1 登录后看不到会话

确认后端服务已启动，并且数据库中存在当前用户的会话数据。

### 6.2 聊天不流式输出

确认后端 `/chat/sessions/{session_id}/stream` 接口正常返回 `text/event-stream`。

### 6.3 接口请求失败

确认 `VITE_API_BASE_URL` 与后端地址一致，并且浏览器可直接访问该地址。
