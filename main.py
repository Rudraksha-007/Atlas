# main.py
import os
from app.capsules.routes import router as capsule_router
from app.auth.routes import router as auth_router


from app.db.base import Base
from app.db.database import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router

app = FastAPI()

# frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
allow_origins=[
        "http://localhost:5173",
    ],    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Hello"}


Base.metadata.create_all(bind=engine)
app.include_router(capsule_router)
app.include_router(auth_router)
