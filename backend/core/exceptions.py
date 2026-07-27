from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.schemas.common import ErrorResponse


def register_exception_handlers(app: FastAPI) -> None:
    async def http_exception_handler(_: Request, exc: HTTPException):
        payload = ErrorResponse(
            code=exc.status_code,
            message=str(exc.detail) if exc.detail is not None else settings.response_default_error_message,
            detail=None,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        payload = ErrorResponse(
            code=422,
            message="validation error",
            detail=str(exc.errors()),
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    async def unexpected_exception_handler(_: Request, exc: Exception):
        payload = ErrorResponse(
            code=500,
            message="internal server error",
            detail=str(exc),
        )
        return JSONResponse(status_code=500, content=payload.model_dump())

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)