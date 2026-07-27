from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.user import User
from backend.schemas.auth import LoginSchema, RegisterSchema, TokenSchema

_PASSWORD_HASH_ITERATIONS = 200_000
_PASSWORD_HASH_ALGORITHM = "sha256"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac(
        _PASSWORD_HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        _PASSWORD_HASH_ITERATIONS,
    )
    return "pbkdf2_sha256${iterations}${salt}${hash}".format(
        iterations=_PASSWORD_HASH_ITERATIONS,
        salt=base64.urlsafe_b64encode(salt).decode("ascii"),
        hash=base64.urlsafe_b64encode(derived_key).decode("ascii"),
    )


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations_text, salt_text, hash_text = password_hash.split("$", 3)
            iterations = int(iterations_text)
            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected_hash = base64.urlsafe_b64decode(hash_text.encode("ascii"))
        except Exception:
            return False

        derived_key = hashlib.pbkdf2_hmac(
            _PASSWORD_HASH_ALGORITHM,
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(derived_key, expected_hash)

    return hash_password(password) == password_hash


def register_user(db: Session, payload: RegisterSchema) -> TokenSchema:
    exists = db.scalar(select(User).where(User.username == payload.username))
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        role="admin" if payload.username == "admin" else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenSchema(access_token=create_access_token(user.id))


def login_user(db: Session, payload: LoginSchema) -> TokenSchema:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return TokenSchema(access_token=create_access_token(user.id))


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user_from_token(db: Session, authorization: str | None) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authorization required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authorization header")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user
