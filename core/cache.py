import json
import redis
from core.config import settings

r = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_cached_link(code: str) -> dict | None:
    try:
        raw = r.get(f"link:{code}")
        return json.loads(raw) if raw else None
    except Exception:
        return None  


def cache_link(code: str, link_id: int, url: str, expires_at: str | None):
    try:
        data = json.dumps({"id": link_id, "url": url, "expires_at": expires_at})
        r.setex(f"link:{code}", settings.cache_ttl, data)
    except Exception:
        pass


def invalidate_link(code: str):
    try:
        r.delete(f"link:{code}")
    except Exception:
        pass