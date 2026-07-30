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
from app.core.redis import get_redis, get_cached, set_cache, invalidate_cache
import redis as redis_module
from app.core.schema import PaginatedResponse
import math

JOBS_CACHE_KEY = "jobs:all"
JOBS_SEARCH_CACHE_PREFIX = "jobs:search:"

router = APIRouter(tags=["jobs"])


@router.post("/job", response_model=JobResponse)
def create_job(job : JobCreate, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)],
               redis_client: Annotated[redis_module.Redis,Depends(get_redis)]):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "Not authorized")
    company = db.query(Company).filter(Company.id == job.company_id, Company.owner_id==current_user.id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "Not authorized")
    job_data = Job(**job.model_dump())
    db.add(job_data)
    db.commit()
    db.refresh(job_data)
    invalidate_cache(redis_client, "jobs:*")

    return db.query(Job).options(joinedload(Job.company)).filter(Job.id == job_data.id).first()

@router.get("/job", response_model=PaginatedResponse[JobResponse])
def get_all_jobs(db : Annotated[Session, Depends(get_db)],redis_client : Annotated[redis_module.Redis,Depends(get_redis)], page : int = 1, limit : int = 10):
    if page < 1:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Page number should be greater than 0")
    if limit < 0 or limit > 15:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Limit should be from 0 to 15")
    
    cache_key = f"jobs:all:page:{page}:limit:{limit}"
    cached = get_cached(redis_client,cache_key)
    if cached:
        return cached
    total = db.query(Job).count()

    offset = (page - 1)*limit
    total_pages = math.ceil(total/limit)
    jobs = db.query(Job).options(joinedload(Job.company)).offset(offset).limit(limit).all()

    jobs_data = [JobResponse.model_validate(job).model_dump(mode="json") for job in jobs]
    response = {
        "data": jobs_data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }
    set_cache(redis_client,cache_key,response) #type: ignore
    return response

@router.get("/jobs/search", response_model=PaginatedResponse[JobResponse])
def search_jobs(
    q: str,
    db: Annotated[Session, Depends(get_db)],
    redis_client : Annotated[redis_module.Redis,Depends(get_redis)],
    page : int = 1,
    limit : int = 10
):
    if not q or len(q.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    if page < 1:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Page number should be greater than 0")
    if limit < 0 or limit > 15:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Limit should be from 0 to 15")
    cache_key = f"jobs:search:{q.lower().strip()}:page:{page}:limit:{limit}"

    cached = get_cached(redis_client,cache_key)
    if cached:
        return cached
    
    search_query = func.plainto_tsquery('english', q)
    total = db.query(Job).filter(
        Job.search_vector.op('@@')(search_query)
    ).count()

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No jobs found matching '{q}'"
        )

    offset = (page - 1) * limit
    total_pages = math.ceil(total/limit)
    
    jobs = db.query(Job).options(
        joinedload(Job.company)
    ).filter(
        Job.search_vector.op('@@')(search_query)
    ).order_by(
        func.ts_rank(Job.search_vector, search_query).desc()
    ).offset(offset).limit(limit).all()
    
    if not jobs:
        raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No jobs found matching '{q}'"
        )
    
    jobs_data = [JobResponse.model_validate(job).model_dump(mode="json") for job in jobs]
    response = {
        "data": jobs_data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }
    set_cache(redis_client,cache_key,jobs_data)

    return response

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



    