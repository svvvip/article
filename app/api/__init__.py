from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api.v1 import article
from app.core.config import root_path
from app.core.database import Base, engine
from app.scheduler import start_scheduler, scheduler
from app.utils.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    logger.info(f"Scheduler started.")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped.")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段先用 *
    allow_credentials=True,
    allow_methods=["*"],  # 必须包含 OPTIONS
    allow_headers=["*"],  # 必须包含 X-Token
)
app.mount("/assets", StaticFiles(directory=f"{root_path}/app/assets"), name="assets")

app.include_router(article.router, prefix='/api/v1', tags=["article"])


