from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

#创建会话表
class ChatSessionCreateSchema(BaseModel):
    title: str | None = Field(default=None, max_length=120)

#会话响应表
class ChatSessionResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    created_time: datetime
    updated_time: datetime

#创建消息表
class ChatMessageCreateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)

#消息响应表
class ChatMessageResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_time: datetime

