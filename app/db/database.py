# this script manages connections to the DB
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# load up the .env file
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=True,
    autocommit=False,
)


async def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
