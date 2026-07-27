from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.auth import LoginSchema, RegisterSchema, TokenSchema
from backend.schemas.common import SuccessResponse
from backend.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["身份认证"])


@router.post("/register", response_model=SuccessResponse[TokenSchema],tags=["注册"])
def register(payload: RegisterSchema, db: Session = Depends(get_db)):
    token = register_user(db, payload)
    return SuccessResponse[TokenSchema](data=token)


@router.post("/login", response_model=SuccessResponse[TokenSchema],tags=["登录"])
def login(payload: LoginSchema, db: Session = Depends(get_db)):
    token = login_user(db, payload)
    return SuccessResponse[TokenSchema](data=token)
