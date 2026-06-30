from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    user_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
