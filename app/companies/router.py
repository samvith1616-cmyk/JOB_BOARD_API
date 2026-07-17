from fastapi import Depends, HTTPException, status, APIRouter, Response
from typing import Annotated
from app.companies.models import Company
from app.companies.schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependency import get_current_user
from app.users.models import User
import uuid

router = APIRouter(tags=["Company"])


@router.post("/company", response_model=CompanyResponse)
def create_company(company : CompanyCreate, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    company_data = company.model_dump()
    company_data["owner_id"] = current_user.id
    new_company = Company(**company_data)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company
@router.get("/company", response_model=list[CompanyResponse])
def get_company(db : Annotated[Session, Depends(get_db)]):
    company_data = db.query(Company).all()
    if not company_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No comapnies found")
    return company_data
@router.get("/company/{id}",response_model=CompanyResponse)
def get_company_id(id : uuid.UUID , db : Annotated[Session, Depends(get_db)]):
    company_data = db.query(Company).filter(Company.id == id).first()
    if not company_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = "No such Company")
    return company_data
@router.delete("/company/{id}")
def delete_company(id : uuid.UUID, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    company_data = db.query(Company).filter(Company.id == id, Company.owner_id==current_user.id)
    if not company_data.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No company as such")
    company_data.delete(synchronize_session = False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.patch("/company/{id}",response_model=CompanyResponse)
def update_company(id : uuid.UUID, company_update : CompanyUpdate, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    company = db.query(Company).filter(Company.id == id,Company.owner_id==current_user.id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No such company found")
    update_data = company_update.model_dump(exclude_unset=True)
        
    for field , value in update_data.items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company



