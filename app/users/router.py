from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import app.users.schema
from app.users.service import create_user
from app.core.database import get_db
from typing import Annotated
from app.auth.dependency import get_current_user
from app.users.models import User
import uuid


user_router = APIRouter(
    tags = ["users"]
)


@user_router.post("/users",response_model = app.users.schema.UserResponse)
def register_use(user : app.users.schema.UserCreate, db : Session = Depends(get_db)):
    user_id = db.query(User).filter(User.email==user.email).first()
    if user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Can't create user")
    return create_user(user,db)

@user_router.get("/users/{id}", response_model=app.users.schema.UserResponse)
def get_user(id : uuid.UUID, db : Annotated[Session, Depends(get_db)], current_user : Annotated[User, Depends(get_current_user)]):
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user