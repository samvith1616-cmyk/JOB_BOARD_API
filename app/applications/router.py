from fastapi import APIRouter, HTTPException, status, Response, Depends
from sqlalchemy.orm import Session, joinedload
from app.applications.schemas import ApplicationCreate,ApplicationResponse,ApplicationStatusUpdate
from app.applications.models import Application
from app.users.models import User, UserRole
from typing import Annotated
from app.core.database import get_db
from app.auth.dependency import get_current_user
from app.jobs.models import Job
from sqlalchemy.exc import IntegrityError
import uuid

router = APIRouter(tags = ["Applications"])

@router.post("/application",response_model=ApplicationResponse)
def create_application(application : ApplicationCreate, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.JOB_SEEKER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not Permitted")
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Not job found")
    app_data = application.model_dump()
    app = Application(**app_data, user_id = current_user.id)
    try:

        db.add(app)
        db.commit()
        db.refresh(app)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job already applied")
    return db.query(Application).options(joinedload(Application.job).joinedload(Job.company)).filter(Application.id == app.id).first()

@router.get("/application/me",response_model=list[ApplicationResponse])
def get_all_applications(db : Annotated[Session,Depends(get_db)],current_user : Annotated[User, Depends(get_current_user)]):
    applications = db.query(Application).options(joinedload(Application.job).joinedload(Job.company)).filter(Application.user_id == current_user.id).all()
    return applications

@router.get("/application/me/{id}/",response_model=ApplicationResponse)
def get_application(id : uuid.UUID, db : Annotated[Session,Depends(get_db)],current_user : Annotated[User, Depends(get_current_user)]):
    app = db.query(Application).options(joinedload(Application.job).joinedload(Job.company)).filter(Application.user_id==current_user.id, Application.id == id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No such job")
    return app

@router.get("/job/{id}/applications",response_model=list[ApplicationResponse])
def get_all_job_allications(id : uuid.UUID, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorized")
    job = db.query(Job).options(joinedload(Job.company)).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No job as such")
    if job.company.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not permitted")
    applications = db.query(Application).options(joinedload(Application.job).joinedload(Job.company)).filter(Application.job_id==id).all()
    return applications
@router.delete("/application/{id}")
def delete_application(id : uuid.UUID, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.JOB_SEEKER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Can't delete the application")
    application = db.query(Application).filter(Application.id == id, Application.user_id == current_user.id)
    app = application.first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No application to delete")
    application.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.patch("/application/{id}", response_model=ApplicationResponse)
def update_role(id : uuid.UUID,app : ApplicationStatusUpdate, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    if current_user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorized")
    
    application = db.query(Application).options(joinedload(Application.job).joinedload(Job.company)).filter(Application.id==id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No application as such found")
    job = db.query(Job).filter(Job.id==application.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No job asa such")
    if job.company.owner_id!=current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Can't update the job")
    updated_data = app.model_dump(exclude_unset=True)

    application.status = updated_data["status"]
    db.commit()
    db.refresh(application)
    return application
    

