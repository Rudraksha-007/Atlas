# main.py
from app.db.base import Base
from app.db.database import engine
from fastapi import FastAPI
from app.auth.routes import router as auth_router

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Hello"}


app.include_router(auth_router)
Base.metadata.create_all(bind=engine)
