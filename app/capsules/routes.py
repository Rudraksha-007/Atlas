from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.db.database import getDb
from datetime import datetime, timedelta, timezone
from app.db.models import capsule
from app.schemas.capsule import CreateCapsule
from app.db.models import user
from app.auth.utils import hash_token, verify_user

router = APIRouter(
    prefix="/capsule",
    tags=["capsule"],
)

load_dotenv()


@router.get("/")
async def capsule_welcome():
    return {"Message": "Welcome to Capsule-Endpoint"}


@router.post("/create")
async def create(
    payload: CreateCapsule,
    db: Session = Depends(getDb),
    incoming_user: user = Depends(verify_user),
):
    email_list_dicts = [email.model_dump() for email in payload.email_list]

    new_capsule = capsule(
        user_id=incoming_user.id,
        subject=payload.subject,
        body=payload.body,
        del_time=payload.del_time,
        api_ver=payload.api_ver,
        client_ip=payload.client_ip,
        status=payload.status,
        email_list=email_list_dicts,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(new_capsule)
    db.commit()
    db.refresh(new_capsule)
    return {"id": new_capsule.id, "message": "Capsule created successfully"}
