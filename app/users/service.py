import app.users.schema as schema
from sqlalchemy.orm import Session
from app.users.models import UserRole, User
from app.core.security import hash_password


def create_user(user : schema.UserCreate, db : Session):
    hashe_password = hash_password(user.password)
    new_user = User(
        email = user.email,
        hashed_password = hashe_password,
        role = UserRole(user.role.value)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user