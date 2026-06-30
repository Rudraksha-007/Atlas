import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
import os
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
