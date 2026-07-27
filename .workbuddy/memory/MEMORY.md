# 项目长期记忆

## 配置管理约定
- 所有敏感配置（数据库连接串/密码、API Key、JWT 密钥）一律放 `.env`，**不写进源码**。
- `.env` 不入 git（已在 .gitignore），`.env.example` 作为占位符模板可提交。
- `backend/core/config.py` 用 `python-dotenv` 的 `dotenv_values()` 读取项目根的 `.env`；关键项（如 DATABASE_URL）源码默认值为空串，缺失配置应明确报错而非静默使用硬编码值。

## 环境与依赖
- 项目虚拟环境：`.venv`（Windows: `.venv/Scripts/python.exe`）
- 依赖清单：`requirements.txt`
