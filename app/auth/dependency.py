from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends
from typing import Annotated
import jwt
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.users.models import User


oAuth_scheme = OAuth2PasswordBearer(tokenUrl = "login")

def get_current_user(token : Annotated[str , Depends(oAuth_scheme)], db : Annotated[Session, Depends(get_db)]):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "Could not validate credentials", headers={"WWW-Authenticate" : "bearer"})
    try:
        payload = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
    except jwt.InvalidTokenError:
        raise credentials_exception
    if payload.get("type")!="access":
        raise credentials_exception
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    return user
    
    