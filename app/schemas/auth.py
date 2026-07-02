from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    user_name: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LogoutRequest(BaseModel):
    refresh_token: str


class OAuthRequest(BaseModel):
    id_token: str


class RefreshRequest(BaseModel):
    refresh_token: str
    access_token: str


# FUCK PYTHON WHY DID THEY MAKE IT LIKE THIS !??FUCK PYTHON FUCK YOU PYTHON
class capsule_response(BaseModel):
    id: UUID
    user_id: UUID
    subject: str
    body: str
    del_time: datetime
    api_ver: str
    client_ip: str
    created_at: datetime
    updated_at: datetime
    status: str
    email_list: List[Dict[str, Any]]
