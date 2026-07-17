from fastapi import APIRouter, Depends, HTTPException, status,Response
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.auth.schema import Token
from app.users.models import User
from typing import Annotated
import redis
from app.core.redis import get_redis, blacklist_token, is_token_blacklisted
from app.core.security import decode_token, get_token_remaining_ttl
from app.auth.dependency import get_current_user


router = APIRouter(tags = ["Auth"])


@router.post("/login", response_model=Token)
def login_user(user : Annotated[ OAuth2PasswordRequestForm , Depends()], db : Annotated[ Session, Depends(get_db)]):
    db_user = db.query(User).filter(User.email == user.username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")
    if not verify_password(user.password,db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "Invalid Credentials")
    access_token = create_access_token(data = {"sub" : str(db_user.id), "role" : db_user.role.value})
    refresh_token = create_refresh_token(data = {"sub" : str(db_user.id)})
    return Token(access_token = access_token, refresh_token= refresh_token, token_type= "bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    refresh_token: str,
    db: Annotated[Session, Depends(get_db)],
    redis: Annotated[redis.Redis, Depends(get_redis)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not a refresh token"
        )
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    ttl = get_token_remaining_ttl(payload)
    blacklist_token(redis, jti, ttl)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Annotated[Session, Depends(get_db)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
):
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not a refresh token"
        )
    jti = payload.get("jti")
    if jti is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    if is_token_blacklisted(redis_client, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    ttl = get_token_remaining_ttl(payload)
    blacklist_token(redis_client, jti, ttl)
    new_access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )