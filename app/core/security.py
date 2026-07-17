from pwdlib import PasswordHash
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

secret_key = settings.SECRET_KEY
algorithm = settings.ALGORITHM


pass_hash = PasswordHash.recommended()

def hash_password(password : str) -> str:
    return pass_hash.hash(password)

def verify_password(plain_password : str, hashed_password : str) -> bool:
    return pass_hash.verify(plain_password,hashed_password)



def create_token(data: dict, expires_delta: timedelta, token_type: str):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({
        "exp": expire,
        "type": token_type,
        "jti": str(uuid.uuid4())
    })

    encoded_jwt = jwt.encode(
        to_encode,
        secret_key,
        algorithm=algorithm
    )

    return encoded_jwt

def create_access_token(data : dict):
    exp = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY_MINUTES)
    return create_token(data,exp,"access")
def create_refresh_token(data:dict):
    exp = timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS)
    return create_token(data,exp,"refresh")

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.InvalidTokenError:
        return {}

def get_token_remaining_ttl(payload: dict) -> int:
    exp = payload.get("exp")
    if not exp:
        return 0
    remaining = int(exp - datetime.now(timezone.utc).timestamp())
    return max(remaining, 0)
