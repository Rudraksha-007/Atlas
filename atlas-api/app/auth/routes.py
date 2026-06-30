from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import SignupRequest, LoginRequest
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


@router.post("/signup", status_code=201)
async def signup(payload: SignupRequest, db: Session = Depends(getDb)):
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


@router.post("/login")
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
    refresh_token = create_refresh_token({"sub": str(db_user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def login():
    pass


@router.post("/logout")
async def logout():
    pass


@router.post("/capsules")
async def login():
    pass
