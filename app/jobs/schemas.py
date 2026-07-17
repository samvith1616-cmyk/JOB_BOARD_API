from datetime import datetime
from pydantic import BaseModel
import enum, uuid
from app.companies.schemas import CompanyResponse


class JobStatusEnum(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"



class JobCreate(BaseModel):
    title : str
    description : str
    salary : int
    location : str
    status : JobStatusEnum | None = JobStatusEnum.OPEN
    company_id : uuid.UUID

class JobResponse(BaseModel):
    id : uuid.UUID
    title : str
    description : str
    salary : int
    location : str
    status : JobStatusEnum
    company : 'CompanyResponse'

    class Config:
        from_attributes = True

class JobUpdate(BaseModel):
    title : str | None = None
    description : str | None = None
    salary : int | None = None
    location : str | None = None