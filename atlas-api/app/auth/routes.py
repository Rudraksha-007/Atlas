from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import SignupRequest, LoginRequest
from app.auth.utils import local_login, oauth_signup_or_login, local_signup
from sqlalchemy.orm import Session
from app.db.database import getDb
from app.db.models import user
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from sqlalchemy import select

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.get("/")
async def auth_welcome():
    return {"Message": "Welcome to Auth-Endpoint"}


@router.post("/{provider}/signup")
async def signup(provider: str, payload: SignupRequest, db: Session = Depends(getDb)):
    if provider == "local":
        return await local_signup(payload, db)
    elif provider in ("google", "microsoft", "apple"):
        return await oauth_signup_or_login(provider, payload, db)
    raise HTTPException(400, "Unsupported provider")


@router.post("/{provider}/login")
async def login(provider: str, request: LoginRequest, db: Session = Depends(getDb)):
    if provider == "local":
        return await local_login(request, db)
    elif provider in ("google", "microsoft", "apple"):
        return await oauth_signup_or_login(provider, payload, db)
    raise HTTPException(400, "Unsupported provider")


@router.post("/refresh")
async def login():
    pass


@router.post("/logout")
async def logout():
    pass


@router.post("/capsules")
async def login():
    pass
