import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.routes import router
from app.db.models import Base, HealthSnapshot
from app.db.seed import seed_assets
from app.db.session import SessionLocal, engine
from app.historian.factory import get_historian
from app.processing.runner import backfill, run_once

REFRESH_SECONDS = int(os.environ.get("REFRESH_SECONDS", "60"))  # 0 disables the background job


def _process(first: bool = False) -> None:
    with SessionLocal() as session:
        if first:
            seed_assets(session)
            if session.scalar(select(HealthSnapshot.id).limit(1)) is None:
                backfill(session, get_historian())
        run_once(session, get_historian())


async def _loop() -> None:
    while True:
        await asyncio.sleep(REFRESH_SECONDS)
        await asyncio.to_thread(_process)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    await asyncio.to_thread(_process, True)
    task = asyncio.create_task(_loop()) if REFRESH_SECONDS > 0 else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Asset Health API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
