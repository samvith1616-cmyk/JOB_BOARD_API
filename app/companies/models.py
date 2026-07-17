from sqlalchemy import Column, Integer, String, text, ForeignKey
from app.core.database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import TIMESTAMP
from datetime import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.jobs.models import Job  # only in companies/models.py


class Company(Base):
    __tablename__ = "companies"

    id : Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name : Mapped[str] = mapped_column(String, nullable=False)
    description : Mapped[str] = mapped_column(String, nullable=True)
    location : Mapped[str] = mapped_column(String, nullable=True)
    owner_id : Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.now)

    jobs : Mapped[list["Job"]] = relationship("Job", back_populates="company")
    
