import uuid, enum
from sqlalchemy import Boolean, Column, Integer, String, text, Enum, ForeignKey
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from datetime import datetime
from app.jobs.schemas import JobStatusEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.companies.models import Company
    from app.applications.models import Application


class Job(Base):
    __tablename__ = "jobs"

    id : Mapped[uuid.UUID] = mapped_column(UUID, primary_key = True, default = uuid.uuid4)
    title : Mapped[str] = mapped_column(String, nullable = False)
    description : Mapped[str] = mapped_column(String, nullable = False)
    salary : Mapped[int] = mapped_column(Integer, nullable = False)
    company_id : Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable = False)
    location : Mapped[str] = mapped_column(String, nullable = True)
    status : Mapped[JobStatusEnum] = mapped_column(Enum(JobStatusEnum), nullable = False, default=JobStatusEnum.OPEN)
    created_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.now)
    search_vector: Mapped[str] = mapped_column(TSVECTOR, nullable=True)

    company : Mapped["Company"] = relationship("Company", back_populates="jobs")
    applications : Mapped[list["Application"]] = relationship("Application", back_populates="job")