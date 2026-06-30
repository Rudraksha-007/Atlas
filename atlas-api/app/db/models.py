import uuid
from .base import Base
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET, ARRAY, JSON
from sqlalchemy import String, DateTime, func, Time
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.ext.mutable import MutableDict

from datetime import datetime


class user(Base):
    __tablename__ = "user"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    capsule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )

    email_groups: Mapped[dict[str, list[str]]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class capsule(Base):
    __tablename__ = "capsule"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )
    del_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    api_ver: Mapped[str] = mapped_column(
        String, unique=True, default="v1.0", index=True
    )
    client_ip: Mapped[str] = mapped_column(
        INET,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        Time(timezone=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    email_list: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
    )
