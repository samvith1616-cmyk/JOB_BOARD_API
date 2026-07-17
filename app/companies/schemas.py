from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class CompanyCreate(BaseModel):
    name : str
    description : str
    location : str


class CompanyResponse(BaseModel):
    id : uuid.UUID
    name : str
    description : str
    location : str
    created_at : datetime
    updated_at : datetime

    class Config:
        from_attributes = True

class CompanyUpdate(BaseModel):
    name : str | None = None
    description : str | None = None
    location : str | None = None
