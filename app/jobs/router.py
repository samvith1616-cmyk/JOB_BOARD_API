from fastapi import APIRouter, HTTPException,status, Depends, Response
from sqlalchemy.orm import Session, joinedload
from app.jobs.schemas import JobCreate, JobResponse, JobUpdate
from typing import Annotated
from app.core.database import get_db
from app.auth.dependency import get_current_user
from app.users.models import User, UserRole
from app.jobs.models import Job
from app.companies.models import Company
import uuid
from sqlalchemy import func

router = APIRouter(tags=["jobs"])


@router.post("/job", response_model=JobResponse)
def create_job(job : JobCreate, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "Not authorized")
    company = db.query(Company).filter(Company.id == job.company_id, Company.owner_id==current_user.id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "Not authorized")
    job_data = Job(**job.model_dump())
    db.add(job_data)
    db.commit()
    db.refresh(job_data)
    return db.query(Job).options(joinedload(Job.company)).filter(Job.id == job_data.id).first()

@router.get("/job", response_model=list[JobResponse])
def get_all_jobs(db : Annotated[Session, Depends(get_db)]):
    jobs = db.query(Job).options(joinedload(Job.company)).all()
    return jobs

@router.get("/jobs/search", response_model=list[JobResponse])
def search_jobs(
    q: str,
    db: Annotated[Session, Depends(get_db)]
):
    if not q or len(q.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    search_query = func.plainto_tsquery('english', q)
    
    jobs = db.query(Job).options(
        joinedload(Job.company)
    ).filter(
        Job.search_vector.op('@@')(search_query)
    ).order_by(
        func.ts_rank(Job.search_vector, search_query).desc()
    ).all()
    
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No jobs found matching '{q}'"
        )
    
    return jobs

@router.get("/job/{id}",response_model=JobResponse)
def get_job(id : uuid.UUID, db : Annotated[Session, Depends(get_db)]):
    job = db.query(Job).filter(Job.id==id).options(joinedload(Job.company)).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No job with {id} found")
    return job

@router.delete("/job/{id}")
def delete_job(id : uuid.UUID, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    if current_user.role!=UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not permitted")
    job = db.query(Job).filter(Job.id == id)
    job_data= job.first()
    
    if not job_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No job as such")
    company = db.query(Company).filter(Company.id==job_data.company_id, Company.owner_id==current_user.id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted")
    job.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/job/{id}",response_model=JobResponse)
def update_job(id : uuid.UUID, job_update : JobUpdate, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    if current_user.role!=UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not permitted")
    job_data = db.query(Job).filter(Job.id == id).first()
    if not job_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No job found with id = {id}")
    company = db.query(Company).filter(Company.id==job_data.company_id, Company.owner_id==current_user.id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    job_update_data = job_update.model_dump(exclude_unset=True)
    for field, value in job_update_data.items():
        setattr(job_data,field,value)
    db.commit()
    db.refresh(job_data)
    return db.query(Job).options(joinedload(Job.company)).filter(Job.id == job_data.id).first()



    