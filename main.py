import os
import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.capsules.routes import router as capsule_router
from app.auth.routes import router as auth_router
from app.db.base import Base
from app.db.database import engine

load_dotenv()

ENABLE_KEEPALIVE = os.getenv("ENABLE_KEEPALIVE", "false").lower() == "true"
allow_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")


async def heartbeat():
    while True:
        # do your periodic work here
        print("hello dad i am alive")
        await asyncio.sleep(15 * 60)  # 15 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    Base.metadata.create_all(bind=engine)

    task = None
    if ENABLE_KEEPALIVE:
        task = asyncio.create_task(heartbeat())

    yield

    # shutdown
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allow_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Hello there, welcome to atlas!!"}


app.include_router(capsule_router)
app.include_router(auth_router)
