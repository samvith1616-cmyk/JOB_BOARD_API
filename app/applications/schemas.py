from pydantic import BaseModel
from datetime import datetime
import enum, uuid
from app.jobs.schemas import JobResponse

class statusEnum(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ApplicationCreate(BaseModel):
    job_id : uuid.UUID
    resume : str


class ApplicationResponse(BaseModel):
    id : uuid.UUID
    user_id : uuid.UUID
    created_at : datetime
    updated_at : datetime
    job : 'JobResponse'
    class Config:
        from_attributes = True

class ApplicationStatusUpdate(BaseModel):
    status : statusEnum 


