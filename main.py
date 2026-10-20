from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from database.session import init_db
from link import router as link_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          
    yield

app = FastAPI(title="URL Shortener", lifespan=lifespan)
app.include_router(link_router)

templates = Jinja2Templates(directory="template")   

@app.get("/", include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"base_url": "http://localhost:8000"}
    )