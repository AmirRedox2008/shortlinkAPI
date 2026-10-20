from fastapi import HTTPException, Request, status
from core.cache import r
from core.config import settings


def rate_limit(request: Request):
    try:
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() \
             or (request.client.host if request.client else "unknown")

        key = f"rl:{ip}"
        current = r.incr(key)
        if current == 1:
            r.expire(key, settings.rate_limit_window)
        if current > settings.rate_limit:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                                "Too many requests, slow down!")

    except HTTPException:
        raise       
    except Exception:
        pass        