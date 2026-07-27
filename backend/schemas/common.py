from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    code: int = Field(default=0, description="业务码，0 表示成功")
    message: str = Field(default="success", description="提示信息")
    data: T | None = Field(default=None, description="响应数据")


class ErrorResponse(BaseModel):
    code: int = Field(default=-1, description="业务码，非 0 表示失败")
    message: str = Field(default="error", description="错误信息")
    detail: str | None = Field(default=None, description="错误细节")
