import os
import bcrypt
import hashlib
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.schemas.auth import SignupRequest, LoginRequest
from sqlalchemy.orm import Session
from app.db.database import getDb
from app.db.models import user
from app.schemas.auth import OAuthRequest
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError

load_dotenv()
security = HTTPBearer()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_user(
    request: Request,
    cred: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(getDb),
):
    """
    This function is responsible for verifying the login.
    It raises HTTP 401 if anything is wrong.
    """
    token = cred.credentials
    try:
        payload = jwt.decode(
            token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not Validate cred.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_obj = db.query(user).filter(user.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_obj


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["type"] = "access"
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    )
    return jwt.encode(
        payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["type"] = "refresh"
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    )
    return jwt.encode(
        payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )


def hash_password(password: str) -> str:
    """Hash a plain text password as soon as it arrives"""
    pass_bytes = password.encode(encoding="utf-8")
    hashed = bcrypt.hashpw(pass_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode(encoding="utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain text password"""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


async def oauth_signup_or_login(provider: str, payload: OAuthRequest, db: Session):
    pass
