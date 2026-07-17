import redis
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

def get_redis():
    return redis_client


def blacklist_token(redis_client, jti: str, ttl: int):
    redis_client.setex(jti, ttl, "blacklisted")

def is_token_blacklisted(redis_client, jti: str) -> bool:
    return redis_client.exists(jti) == 1