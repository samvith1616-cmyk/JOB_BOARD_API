import redis
from app.core.config import settings
import json
from typing import Optional

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



def get_cached(redis_client, key: str) -> Optional[list]:
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

def set_cache(redis_client, key: str, data: list, ttl: int = 3600):
    redis_client.setex(key, ttl, json.dumps(data))

def invalidate_cache(redis_client, pattern: str):
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)