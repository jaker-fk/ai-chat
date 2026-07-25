from pydantic import BaseModel, Field

#前端注册表
class RegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    nickname: str | None = Field(default=None, max_length=100)

#登录表
class LoginSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

#token表
class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
