# AI对话应用开发文档

## 1. 项目概述

本项目是一个基于 `FastAPI + SQLAlchemy + JWT + 大模型流式输出` 的 AI 对话应用后端。当前代码结构已经完成了基础的用户认证、会话管理、消息流式回复等核心骨架，适合继续扩展为完整的聊天产品。

项目的主要目标：

- 提供用户注册、登录与鉴权能力
- 支持创建与管理聊天会话
- 支持发送消息并从大模型获取流式回复
- 支持 OpenAI / DeepSeek 两种大模型配置
- 通过环境变量实现部署与配置隔离

---

## 2. 技术栈

- **后端框架**：FastAPI
- **ORM**：SQLAlchemy
- **数据库**：MySQL（默认配置）
- **认证方式**：JWT
- **大模型调用**：OpenAI / DeepSeek 兼容接口
- **流式响应**：SSE / `text/event-stream`
- **数据校验**：Pydantic
- **HTTP 客户端**：httpx

---

## 3. 项目结构

当前后端目录主要如下：

- `main.py`：应用入口，负责创建 FastAPI 实例、注册路由、初始化数据库
- `backend/core/config.py`：统一配置管理
- `backend/core/database.py`：数据库连接、Session、建表初始化
- `backend/models/`：数据库模型
- `backend/schemas/`：请求与响应数据结构定义
- `backend/services/`：业务逻辑层
- `backend/routers/`：接口路由层
- `backend/crud/`：目前作为预留目录，暂未看到具体实现

---

## 4. 核心模块说明

### 4.1 应用入口

文件：`main.py`

主要职责：

- 创建 FastAPI 应用
- 启用全局 CORS
- 注册认证与聊天路由
- 在启动时执行数据库初始化
- 提供根路径与健康检查接口

关键接口：

- `GET /`：返回服务运行信息
- `GET /health`：健康检查

### 4.2 配置模块

文件：`backend/core/config.py`

配置通过环境变量读取，支持默认值兜底。

当前支持的配置项：

- `APP_NAME`：应用名称，默认 `AI对话应用`
- `DATABASE_URL`：数据库连接地址
- `JWT_SECRET`：JWT 签名密钥
- `JWT_ALGORITHM`：JWT 算法，默认 `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`：Token 过期时间
- `OPENAI_API_KEY`：OpenAI Key
- `OPENAI_BASE_URL`：OpenAI 接口地址
- `OPENAI_MODEL`：OpenAI 模型名
- `DEEPSEEK_API_KEY`：DeepSeek Key
- `DEEPSEEK_BASE_URL`：DeepSeek 接口地址
- `DEEPSEEK_MODEL`：DeepSeek 模型名

模型选择策略：

- 如果配置了 `DEEPSEEK_API_KEY`，优先使用 DeepSeek
- 否则使用 OpenAI
- 如果两者都没有配置，则走本地模拟回复

### 4.3 数据库模块

文件：`backend/core/database.py`

职责：

- 创建 SQLAlchemy 引擎
- 创建会话工厂 `SessionLocal`
- 提供依赖注入函数 `get_db()`
- 在启动时执行 `Base.metadata.create_all()` 自动建表

说明：

- 当前是“启动自动建表”模式，适合开发阶段
- 若进入生产环境，建议切换为数据库迁移方案，例如 Alembic

### 4.4 数据模型

当前可见模型包括：

- `User`
- `ChatSession`
- `ChatMessage`

这些模型分别对应用户、会话和聊天消息。

一般关系如下：

- 一个用户拥有多个会话
- 一个会话包含多条消息
- 一条消息属于一个会话

### 4.5 数据校验层

文件：`backend/schemas/`

当前 schema 主要包括：

#### 认证相关

- `RegisterSchema`
- `LoginSchema`
- `TokenSchema`

#### 聊天相关

- `ChatSessionCreateSchema`
- `ChatSessionResponseSchema`
- `ChatMessageCreateSchema`
- `ChatMessageResponseSchema`

作用：

- 接收前端请求参数
- 校验数据格式和长度
- 定义接口响应结构

### 4.6 认证服务

文件：`backend/services/auth_service.py`

当前实现了：

- 密码哈希与校验
- 用户注册后生成 JWT
- 用户登录后生成 JWT
- 通过 `Authorization: Bearer <token>` 解析当前用户

实现特点：

- 密码哈希目前是演示性质的简化实现，生产环境应替换为 `bcrypt` / `passlib`
- Token 中使用 `sub` 保存用户 ID
- Token 过期时间由配置控制

> 注意：`backend/routers/auth.py` 中的注册和登录接口当前返回 `501 Not Implemented`，说明路由层还未接入服务层实现。后续开发时应补齐该部分。

### 4.7 聊天服务

文件：`backend/services/chat_service.py`

当前实现的业务逻辑：

- 创建聊天会话
- 查询当前用户的会话列表
- 获取指定会话详情
- 获取会话消息列表
- 发送消息并流式获取大模型回复

消息流处理逻辑：

1. 保存用户消息到数据库
2. 组装历史消息上下文
3. 调用 `stream_llm_reply()` 获取流式响应
4. 将模型回复拼接为完整文本
5. 保存助手消息到数据库
6. 更新会话时间

### 4.8 大模型服务

文件：`backend/services/llm_service.py`

职责：

- 根据配置选择模型供应商
- 以流式方式请求大模型
- 将返回内容拆分成 chunk 输出
- 在未配置 API Key 时返回本地模拟文本

请求方式：

- 使用 OpenAI 风格的 `/chat/completions` 接口
- 请求体包含 `model`、`messages` 和 `stream=true`

输出方式：

- 通过异步生成器逐段返回内容
- 可被上层封装为 SSE 推送给前端

---

## 5. 接口说明

### 5.1 基础接口

#### `GET /`

返回：

```json
{"message":"AI 对话应用 running"}
```

#### `GET /health`

返回：

```json
{"status":"ok"}
```

### 5.2 认证接口

路由前缀：`/auth`

#### `POST /auth/register`

用途：注册用户并返回访问令牌。

请求体：

```json
{
  "username": "testuser",
  "password": "123456",
  "nickname": "用户A"
}
```

返回结构：

```json
{
  "access_token": "xxx",
  "token_type": "bearer"
}
```

#### `POST /auth/login`

用途：用户登录并返回访问令牌。

请求体：

```json
{
  "username": "testuser",
  "password": "123456"
}
```

### 5.3 聊天接口

路由前缀：`/chat`

鉴权方式：

- 请求头中需要携带 `Authorization: Bearer <token>`

#### `GET /chat/sessions`

用途：获取当前用户的会话列表。

#### `POST /chat/sessions`

用途：创建新会话。

请求体：

```json
{
  "title": "我的第一个会话"
}
```

#### `GET /chat/sessions/{session_id}/messages`

用途：获取指定会话的消息历史。

#### `POST /chat/sessions/{session_id}/stream`

用途：发送消息并以 SSE 方式接收大模型流式回复。

请求体：

```json
{
  "content": "你好，请介绍一下你自己"
}
```

SSE 返回示意：

```text
data: {"delta":"你好"}

data: {"delta":"，我是..."}

data: {"done":true,"content":"完整回复"}
```

---

## 6. 数据库设计建议

从现有模型推断，数据库至少包含以下三张表：

### 6.1 `user`

字段建议：

- `id`
- `username`
- `password_hash`
- `nickname`
- `role`
- `created_time`
- `updated_time`

### 6.2 `chat_session`

字段建议：

- `id`
- `user_id`
- `title`
- `created_time`
- `updated_time`

### 6.3 `chat_message`

字段建议：

- `id`
- `session_id`
- `role`
- `content`
- `created_time`

---

## 7. 开发环境配置

建议使用环境变量配置 `.env` 或系统环境变量。

示例：

```env
APP_NAME=AI对话应用
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/ai_chat?charset=utf8mb4
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

---

## 8. 本地启动建议

由于当前仓库未展示完整依赖文件，建议按如下思路启动：

1. 创建虚拟环境
2. 安装依赖：
   - `fastapi`
   - `uvicorn`
   - `sqlalchemy`
   - `pymysql`
   - `pyjwt`
   - `httpx`
   - `pydantic`
3. 配置数据库连接
4. 设置大模型 Key（可选）
5. 启动服务入口 `main.py`

示例启动命令通常为：

```bash
uvicorn main:app --reload
```

---

## 9. 当前已实现与待完善内容

### 已实现

- FastAPI 服务入口
- CORS 配置
- 数据库连接与自动建表
- 用户 JWT 认证基础能力
- 会话与消息数据结构
- 聊天消息流式输出
- OpenAI / DeepSeek 兼容接入

### 待完善

- 完善认证接口的测试验证方案
- 完整的错误处理与统一响应格式
- 数据库迁移工具
- 前端联调文档
- 管理员权限控制与更多用户角色能力

---

## 10. 开发规范建议

1. 路由只负责参数接收与响应返回，核心逻辑放在 `services/`
2. 所有数据库访问通过 `Session` 完成，避免在路由层直接写复杂 SQL
3. 请求与响应结构统一使用 `schemas/` 定义
4. 大模型接入保持供应商解耦，后续可继续扩展更多模型提供方
5. 鉴权统一走 JWT，接口层不要自行解析用户身份
6. 生产环境不要使用默认密钥与演示密码哈希实现

---

## 11. 后续扩展方向

- 增加前端页面与对话 UI
- 增加消息编辑、删除、重新生成
- 支持多轮上下文管理
- 支持文件上传与知识库问答
- 增加管理员后台
- 引入数据库迁移和测试体系
- 支持更多 LLM 供应商

---

## 12. 后端启动手册

### 12.1 环境准备

建议使用 Python 3.10+，并创建独立虚拟环境。

```bash
python -m venv .venv
```

激活虚拟环境：

- Windows PowerShell：

```bash
.\.venv\Scripts\Activate.ps1
```

- Windows CMD：

```bash
.\.venv\Scripts\activate.bat
```

- macOS / Linux：

```bash
source .venv/bin/activate
```

### 12.2 安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

如果你想同时安装前端依赖，可以进入 `frontend/` 执行：

```bash
cd frontend
npm install
```

### 12.3 配置环境变量

在项目根目录创建 `.env` 文件，至少配置数据库和 JWT 密钥：

```env
APP_NAME=AI对话应用
DATABASE_URL=sqlite:///./test_auth.db
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

如果需要接入模型服务，也可以继续配置：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 12.4 启动后端

在项目根目录执行：

```bash
uvicorn main:app --reload
```

服务启动后默认地址通常是：

```text
http://127.0.0.1:8000
```

### 12.5 验证接口

可以直接访问：

- `GET /health`：健康检查
- `POST /auth/register`：注册
- `POST /auth/login`：登录
- `GET /chat/sessions`：会话列表
- `POST /chat/sessions`：创建会话
- `GET /chat/sessions/{session_id}/messages`：消息列表
- `POST /chat/sessions/{session_id}/stream`：流式聊天

### 12.6 后端测试

执行认证测试：

```bash
pytest tests/test_auth.py
```

如果想运行全部测试：

```bash
pytest
```

### 12.7 常见问题

#### 数据库为空或没有表

确认 `.env` 中的 `DATABASE_URL` 已正确配置，并且服务启动时调用了 `init_db()`。

#### 导入报错

确认 `backend/core/exceptions.py` 已存在，且 `main.py` 中导入的是：

```python
from backend.core.exceptions import register_exception_handlers
```

#### 登录后无法进入聊天页

确认前端保存的 Token 有效，并且请求头包含：

```http
Authorization: Bearer <token>
```

---

## 13. 总结

当前项目已经具备一个 AI 对话应用后端的基础骨架：

- 有清晰的分层结构
- 有认证、会话、消息、流式输出的主流程
- 有环境变量驱动的配置体系
- 已经具备继续向完整产品演进的条件

如果继续开发，建议优先补齐认证路由、完善模型与数据库定义，并为前端联调提供更稳定的接口契约。
