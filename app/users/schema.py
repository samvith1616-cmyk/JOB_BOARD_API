from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid
from app.users.models import UserRole
import enum

class SignupRole(str,enum.Enum):
    JOB_SEEKER = "job_seeker"
    EMPLOYER = "employer"


class UserCreate(BaseModel):
    email : EmailStr
    password : str
    role : SignupRole = SignupRole.JOB_SEEKER

class UserResponse(BaseModel):
    id : uuid.UUID
    email : EmailStr
    created_at : datetime
    updated_at : datetime
    role : UserRole

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email : EmailStr | None = None
