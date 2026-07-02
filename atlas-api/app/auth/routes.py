import hashlib, os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import SignupRequest, LoginRequest, RefreshRequest, LogoutRequest
from app.auth.utils import oauth_signup_or_login, hash_token, verify_user
from sqlalchemy.orm import Session
from app.db.database import getDb
from app.db.models import user, refresh_token
from datetime import datetime, timedelta, timezone
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

load_dotenv()

expiry_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


@router.get("/")
async def auth_welcome():
    return {"Message": "Welcome to Auth-Endpoint"}


@router.post("/local/signup")
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


@router.post("/local/login")
async def login(request: LoginRequest, db: Session = Depends(getDb)):
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
    refresh_token_value = create_refresh_token({"sub": str(db_user.id)})
    # hashlib.sha256(refresh_token_value.encode()).hexdigest(),
    new_refresh_token = refresh_token(
        user_id=db_user.id,
        token_hash=hash_token(refresh_token_value),
        expiry=datetime.now(timezone.utc) + timedelta(days=expiry_days),
    )
    db.add(new_refresh_token)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer",
    }


@router.post("/{provider}/oauth")
async def start_oauth(provider: str):
    pass


@router.post("/{provider}/callback")
async def login_oauth():
    pass


@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: Session = Depends(getDb)):
    incoming_hash = hash_token(payload.refresh_token)
    stmt = select(refresh_token).where(refresh_token.token_hash == incoming_hash)
    db_token = db.execute(stmt).scalar_one_or_none()
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh token"
        )
    if db_token.expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token Expired"
        )
    # stmt=select()
    db_user = db.get(user, db_token.user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User doesn't exist"
        )
    db.delete(db_token)
    new_access_token = create_access_token({"sub": str(db_user.id)})
    new_refresh_token = create_refresh_token({"sub": str(db_user.id)})
    new_refresh_token_db_entry = refresh_token(
        user_id=db_user.id,
        token_hash=hash_token(new_refresh_token),
        expiry=datetime.now(timezone.utc) + timedelta(days=expiry_days),
    )
    db.add(new_refresh_token_db_entry)
    db.commit()
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(payload: LogoutRequest, db: Session = Depends(getDb)):
    incoming_hash = hash_token(payload.refresh_token)
    stmt = select(refresh_token).where(refresh_token.token_hash == incoming_hash)
    db_token = db.execute(stmt).scalar_one_or_none()
    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refresh token"
        )
    else:
        db.delete(db_token)
        db.commit()
    return {"message": "Successfully Logged out"}


@router.post("/my_capsules")
async def capsules(
    db: Session = Depends(getDb),
    user: user = Depends(verify_user),
):
    # this endponit is not paginated
    return {"message": "You are logged in and using a protected Endpoint"}
