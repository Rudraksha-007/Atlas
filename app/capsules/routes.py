import json, uuid
from os import getenv
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.capsules.utils import redis_connection
from app.db.database import getDb
from datetime import datetime, timezone
from app.db.models import capsule
from app.schemas.capsule import CreateCapsule
from app.db.models import user
from app.auth.utils import verify_user
from sqlalchemy import select
from app.schemas.capsule import UpdateCapsule, CapsuleResponse

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
    attach_dict = None
    if payload.attachments is not None:
        attach_dict = [att.model_dump(mode="json") for att in payload.attachments]

    new_capsule = capsule(
        user_id=incoming_user.id,
        subject=payload.subject,
        body=payload.body,
        del_time=payload.del_time,
        api_ver=payload.api_ver,
        client_ip=payload.client_ip,
        status="PENDING",
        email_list=email_list_dicts,
        attachments=attach_dict,
        updated_at=datetime.now(timezone.utc),
    )
    capsule_dict = {
        c.name: getattr(new_capsule, c.name) for c in new_capsule.__table__.columns
    }
    json_roll = json.dumps(capsule_dict, default=str)
    db.add(new_capsule)
    db.commit()
    db.refresh(new_capsule)
    r = redis_connection()
    r.set_truth(new_capsule.id, "PENDING", new_capsule.version)
    # r.add_to_queue(new_capsule.id, payload.del_time.timestamp())
    # r.add_to_JSONMap(new_capsule.id, json_roll)
    return new_capsule


@router.get("/status/{id}")
async def fetch_status(
    id: str,
    db: Session = Depends(getDb),
    incoming_user: user = Depends(verify_user),
):
    stmt = select(capsule).where(capsule.id == id)
    cap = db.execute(stmt).scalar_one_or_none()
    if cap is None:
        raise HTTPException(status_code=404, detail="Capsule not found")
    if cap.user_id != incoming_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User doesn't hold authority for this capsule",
        )
    return {"STATUS": cap.status}


@router.get("/cancel/{id}")
async def cancel(
    id: str,
    db: Session = Depends(getDb),
    incoming_user: user = Depends(verify_user),
):
    stmt = select(capsule).where(id == capsule.id)
    res = db.execute(stmt).scalar_one_or_none()
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Capsule not found"
        )
    if res.user_id != incoming_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "user doesn't hold authority of the entity requested"},
        )
    new_ver = res.version + 1
    r = redis_connection()
    r.set_truth(uuid.UUID(id), status="CANNED", version=new_ver)
    # r.del_queue(uuid.UUID(id))
    # r.del_from_JSONMap(uuid.UUID(id))
    res.status = "CANNED"
    res.version = new_ver
    db.commit()
    return {"message": "the capsule has been taken care of."}


@router.patch("/update/{id}", response_model=CapsuleResponse)
async def update(
    id: uuid.UUID,
    payload: UpdateCapsule,
    db: Session = Depends(getDb),
    incoming_user: user = Depends(verify_user),
):
    stmt = select(capsule).where(capsule.id == id, capsule.user_id == incoming_user.id)
    result = db.execute(stmt)
    capsule_inst = result.scalar_one_or_none()

    if not capsule_inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Capsule not found"
        )
    update_dict = payload.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(capsule_inst, key, value)
    capsule_inst.version += 1  # increment version
    db.commit()
    db.refresh(capsule_inst)
    r = redis_connection()
    if payload.status is None:
        r.set_truth(capsule_inst.id, capsule_inst.status, capsule_inst.version)
    else:
        r.set_truth(capsule_inst.id, payload.status, capsule_inst.version)
    return capsule_inst
