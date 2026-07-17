import uuid, enum
from sqlalchemy import Column, Integer, String, text, ForeignKey, UniqueConstraint
from app.core.database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import TIMESTAMP, Enum
from datetime import datetime
from app.applications.schemas import statusEnum

from app.jobs.models import Job
from app.users.models import User





class Application(Base):
    __tablename__ = "applications"

    id : Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[statusEnum] = mapped_column(Enum(statusEnum), nullable=False, default=statusEnum.PENDING)
    created_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at : Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=datetime.now)
    resume : Mapped[str] = mapped_column(String, nullable=True)


    __table_args__ = (UniqueConstraint('user_id', 'job_id', name='unique_user_job'),)
    user : Mapped["User"] = relationship("User", back_populates="applications")
    job : Mapped["Job"] = relationship("Job", back_populates="applications")