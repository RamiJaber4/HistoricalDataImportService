import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from logging_config import setup_logging
from routers import router
from worker import process_queue

setup_logging()

logger = logging.getLogger(__name__)

logger.info("Application started")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start worker in background
    worker_task = asyncio.create_task(process_queue())
    yield
    # Cancel worker on shutdown
    worker_task.cancel()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
