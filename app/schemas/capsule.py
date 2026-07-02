from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from enum import Enum
import re

# DeepSeek generated Code :


class CapsuleStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    DELETED = "deleted"


class EmailRecipient(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class CreateCapsule(BaseModel):
    # user_id: UUID = Field(default_factory=uuid4, description="User ID")
    subject: str = Field(..., max_length=255, description="Capsule subject")
    body: Optional[str] = Field(None, description="Capsule body content")
    del_time: datetime = Field(..., description="Deletion time (must be in the future)")
    client_ip: str = Field(..., description="Client IP address")
    status: CapsuleStatus = Field(CapsuleStatus.ACTIVE, description="Capsule status")
    email_list: List[EmailRecipient] = Field(
        ..., description="List of email recipients"
    )
    api_ver: str = Field("v1.0", description="API version")

    @field_validator("client_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate IPv4 or IPv6 address format"""
        # IPv4 pattern
        ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        # IPv6 pattern (basic)
        ipv6_pattern = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
        # Localhost patterns
        if v in ["127.0.0.1", "::1", "localhost"]:
            return v

        if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
            raise ValueError("Invalid IP address format. Expected IPv4 or IPv6.")

        # Additional IPv4 validation
        if re.match(ipv4_pattern, v):
            parts = v.split(".")
            for part in parts:
                if not 0 <= int(part) <= 255:
                    raise ValueError("Invalid IPv4 address: octet out of range")

        return v

    @field_validator("del_time")
    @classmethod
    def validate_del_time(cls, v: datetime) -> datetime:
        """Ensure delivery time is in the future"""
        if v <= datetime.now(v.tzinfo):
            raise ValueError("Delivery time must be in the future")
        return v

    @field_validator("email_list")
    @classmethod
    def validate_email_list(cls, v: List[EmailRecipient]) -> List[EmailRecipient]:
        """Ensure email list is not empty"""
        if not v:
            raise ValueError("Email list cannot be empty")
        return v

    model_config = {
        "json_encoders": {UUID: str, datetime: lambda v: v.isoformat()},
        "populate_by_name": True,
        "str_strip_whitespace": True,
        "use_enum_values": True,
    }


# # For updating capsule (partial update)
# class UpdateCapsule(BaseModel):
#     subject: Optional[str] = Field(None, max_length=255)
#     body: Optional[str] = None
#     del_time: Optional[datetime] = None
#     status: Optional[CapsuleStatus] = None
#     email_list: Optional[List[EmailRecipient]] = None
#     api_ver: Optional[str] = None

#     @field_validator("del_time")
#     @classmethod
#     def validate_del_time(cls, v: Optional[datetime]) -> Optional[datetime]:
#         if v and v <= datetime.now(v.tzinfo):
#             raise ValueError("Deletion time must be in the future")
#         return v

#     model_config = {
#         "json_encoders": {UUID: str, datetime: lambda v: v.isoformat()},
#         "populate_by_name": True,
#         "str_strip_whitespace": True,
#         "use_enum_values": True,
#     }


# For response/serialization (includes all fields)
class CapsuleResponse(BaseModel):
    id: UUID
    user_id: UUID
    subject: str
    body: Optional[str] = None
    del_time: datetime
    api_ver: str
    client_ip: str
    created_at: datetime
    updated_at: datetime
    status: str
    email_list: List[Dict[str, Any]]

    model_config = {
        "from_attributes": True,  # For SQLAlchemy/Pydantic V2 compatibility
        "json_encoders": {UUID: str, datetime: lambda v: v.isoformat()},
        "use_enum_values": True,
    }
