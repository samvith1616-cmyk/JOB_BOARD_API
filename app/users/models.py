import uuid
from sqlalchemy import Boolean, Column, Integer, String, text, Enum
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.applications.models import Application


import enum

class UserRole(str, enum.Enum):
    JOB_SEEKER = "job_seeker"
    EMPLOYER = "employer"
    ADMIN = "admin"
 



class User(Base):
    __tablename__ = "users"

    id : Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4) 
    email : Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password : Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.now)
    role : Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.JOB_SEEKER)
    is_active : Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    applications : Mapped[list["Application"]] = relationship("Application", back_populates="user")
    

