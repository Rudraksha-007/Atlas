import bcrypt
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.schemas.auth import SignupRequest, LoginRequest
from sqlalchemy.orm import Session
from app.db.database import getDb
from app.db.models import user
from app.schemas.auth import OAuthRequest
import os
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

load_dotenv()


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["type"] = "access"
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
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


async def local_login(request: LoginRequest, db: Session = Depends(getDb)):
    stmt = select(user).where(user.email == request.email)
    res = db.execute(stmt)
    db_user = res.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User Not Found"
        )
    if not verify_password(request.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials"
        )

    access_token = create_access_token({"sub": str(db_user.id)})
    refresh_token = create_refresh_token({"sub": str(db_user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def oauth_signup_or_login(provider: str, payload: OAuthRequest, db: Session):
    pass


async def local_signup(payload: SignupRequest, db: Session = Depends(getDb)):
    exist_already = db.query(user).filter(user.email == payload.email).first()
    user_name_taken = db.query(user).filter(user.user_name == payload.user_name).first()

    if exist_already:
        raise HTTPException(status_code=409, detail="Email already exist")
    elif user_name_taken:
        raise HTTPException(status_code=409, detail="UserName already exists")
    hash_pass = hash_password(payload.password)
    new_user = user(
        user_name=payload.user_name,
        email=payload.email,
        password_hash=hash_pass,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created"}
