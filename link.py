import secrets
import string
from datetime import datetime, timedelta
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Request, status,Query)
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import func
from sqlalchemy.orm import Session
from core.cache import get_cached_link, cache_link, invalidate_link
from core.config import settings
from core.ratelimit import rate_limit
from database.models import savedb, ClickLog
from database.database import seesion_local
import qrcode, base64, io
from fastapi.responses import Response

router = APIRouter()
ALPHABET = string.ascii_letters + string.digits


# ───────── Schemas ─────────
class CreateUrlShortRequest(BaseModel):
    original_url: HttpUrl
    custom_code: str | None = None
    expires_at: datetime | None = None


class UrlShortResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class LinkStatsResponse(BaseModel):
    short_code: str
    total_clicks: int
    daily_clicks: list[dict]
    top_referers: list[dict]


# ───────── Helpers ─────────
def get_db():
    db = seesion_local()
    try:
        yield db
    finally:
        db.close()


def generate_short_code(length: int = 7) -> str:
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))


def log_click(link_id: int, ip: str, user_agent: str, referer: str):
    """بعد از ارسال جواب اجرا می‌شه — session مستقل داره"""
    db = seesion_local()
    try:
        db.add(ClickLog(link_id=link_id, ip=ip,
                        user_agent=user_agent[:512], referer=referer[:512]))
        db.query(savedb).filter(savedb.id == link_id).update(
            {savedb.clicks: savedb.clicks + 1}      # آپدیت اتمیک — race condition نداره
        )
        db.commit()
    finally:
        db.close()


def client_ip(request: Request) -> str:
    return request.headers.get("x-forwarded-for", "").split(",")[0].strip() \
        or (request.client.host if request.client else "unknown")


# ───────── Endpoints ─────────
@router.post("/url/short", status_code=status.HTTP_201_CREATED, response_model=UrlShortResponse)
async def short_url(req: CreateUrlShortRequest, db: Session = Depends(get_db)):
    code = req.custom_code or generate_short_code()

    exist = db.query(savedb).filter(savedb.short_code == code).first()
    if exist:
        raise HTTPException(status.HTTP_409_CONFLICT, "USED CODE")

    new_link = savedb(
        short_code=code,
        original_url=str(req.original_url),
        clicks=0,
        expires_at=req.expires_at,
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)

    
    cache_link(code, new_link.id, new_link.original_url,
               new_link.expires_at.isoformat() if new_link.expires_at else None)

    return UrlShortResponse(
        short_code=new_link.short_code,
        original_url=new_link.original_url,
        clicks=new_link.clicks,
        expires_at=new_link.expires_at,
    )


@router.get("/{code}", dependencies=[Depends(rate_limit)])   # 🛡️ rate limit اینجا
async def redirect_url(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    link_id = None
    original_url = None

   
    cached = get_cached_link(code)
    if cached:
        link_id = cached["id"]
        original_url = cached["url"]
        if cached["expires_at"] and datetime.fromisoformat(cached["expires_at"]) < datetime.utcnow():
            raise HTTPException(status.HTTP_410_GONE, "link is gone")
    else:
        link = db.query(savedb).filter(savedb.short_code == code).first()
        if not link:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "link not found")
        if link.expires_at and link.expires_at < datetime.utcnow():
            raise HTTPException(status.HTTP_410_GONE, "link is gone")

        link_id, original_url = link.id, link.original_url
        cache_link(code, link.id, link.original_url,
                   link.expires_at.isoformat() if link.expires_at else None)

    # ۳. ثبت کلیک در بک‌گراند — کاربر منتظر نمی‌مونه
    background_tasks.add_task(
        log_click, link_id, client_ip(request),
        request.headers.get("user-agent", ""),
        request.headers.get("referer", ""),
    )

    return RedirectResponse(url=original_url, status_code=status.HTTP_302_FOUND)


@router.get("/{code}/stats", response_model=LinkStatsResponse)
async def get_stats(code: str, db: Session = Depends(get_db)):
    link = db.query(savedb).filter(savedb.short_code == code).first()
    if not link:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "link not found")

    week_ago = datetime.utcnow() - timedelta(days=7)

    daily = (
        db.query(func.date(ClickLog.clicked_at).label("day"),
                 func.count(ClickLog.id).label("count"))
        .filter(ClickLog.link_id == link.id, ClickLog.clicked_at >= week_ago)
        .group_by(func.date(ClickLog.clicked_at))
        .order_by(func.date(ClickLog.clicked_at))
        .all()
    )
    top_referers = (
        db.query(ClickLog.referer, func.count(ClickLog.id).label("count"))
        .filter(ClickLog.link_id == link.id, ClickLog.referer.isnot(None))
        .group_by(ClickLog.referer)
        .order_by(func.count(ClickLog.id).desc())
        .limit(5)
        .all()
    )

    return LinkStatsResponse(
        short_code=link.short_code,
        total_clicks=link.clicks,
        daily_clicks=[{"date": str(d.day), "clicks": d.count} for d in daily],
        top_referers=[{"referer": t.referer, "count": t.count} for t in top_referers],
    )


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(code: str, db: Session = Depends(get_db)):
    link = db.query(savedb).filter(savedb.short_code == code).first()
    if not link:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "link not found")

    db.delete(link)
    db.commit()
    invalidate_link(code) # del from cache but its still working

@router.get("/url/all")
async def list_links(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    total = db.query(savedb).count()
    links = (db.query(savedb).order_by(savedb.id.desc())
             .offset(skip).limit(limit).all())
    return {
        "total": total,
        "items": [UrlShortResponse.model_validate(l) for l in links],
    }



@router.get("/{code}/qr")
async def get_qr(code: str, db: Session = Depends(get_db)):
    link = db.query(savedb).filter(savedb.short_code == code).first()
    if not link:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "link not found")

    img = qrcode.make(f"{settings.base_url}/{code}")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")