from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from app.api.services import article_service
from app.core.config import root_path
from app.core.database import get_db
from app.schemas import ArticleQuery

router = APIRouter()


@router.post("/articles/")
def get_article_list(query: ArticleQuery, db: Session = Depends(get_db)):
    return article_service.get_article_list(db, query)


@router.get("/torrents/")
def get_torrent(keyword, db: Session = Depends(get_db)):
    return article_service.get_torrents(keyword, db)

templates = Jinja2Templates(directory=f"{root_path}/app/templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
