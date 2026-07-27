from __future__ import annotations
from core.config import settings
TEST_PLAN = {
    "scope": "认证接口（/auth/register, /auth/login）",
    "goal": "验证注册、登录、重复注册、错误凭证、Token 返回格式与鉴权基础行为",
    "recommended_tooling": ["pytest", "TestClient", "SQLite test database", "monkeypatch"],
    "scenarios": [
        {
            "name": "注册成功",
            "request": {
                "method": "POST",
                "path": "/auth/register",
                "body": {"username": "alice", "password": "123456", "nickname": "Alice"},
            },
            "expected": ["200/201 成功", "返回 access_token", "token_type 为 bearer"],
        },
        {
            "name": "重复注册被拒绝",
            "request": {
                "method": "POST",
                "path": "/auth/register",
                "body": {"username": "alice", "password": "123456"},
            },
            "expected": ["400 错误", "detail 包含 username already exists"],
        },
        {
            "name": "登录成功",
            "request": {
                "method": "POST",
                "path": "/auth/login",
                "body": {"username": "alice", "password": "123456"},
            },
            "expected": ["200 成功", "返回 access_token", "token_type 为 bearer"],
        },
        {
            "name": "错误密码登录失败",
            "request": {
                "method": "POST",
                "path": "/auth/login",
                "body": {"username": "alice", "password": "wrong-password"},
            },
            "expected": ["401 错误", "detail 包含 invalid credentials"],
        },
        {
            "name": "缺少必填字段",
            "request": {
                "method": "POST",
                "path": "/auth/register",
                "body": {"username": "a"},
            },
            "expected": ["422 校验错误"],
        },
        {
            "name": "Token 格式校验",
            "request": {
                "method": "Header", 
                "path": "后续 chat 接口",
                "body": {"Authorization": "Bearer <token>"},
            },
            "expected": ["能被后续接口识别为当前用户"],
        },
    ],
    "implementation_notes": [
        "建议为测试单独配置 SQLite 内存库或测试库。",
        "建议 monkeypatch backend.core.database.SessionLocal 或 get_db 依赖。",
        "建议每个测试前清理用户表数据。",
        "建议对 JWT payload 做最小断言，只验证 sub 和过期时间字段。",
    ],
}


if __name__ == "__main__":
   print(settings.jwt_secret)

