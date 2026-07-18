# database/session.py
import os
from typing import Generator
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, SQLModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables.")

# echo=True prints raw SQL to the terminal for easier troubleshooting
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Helper to create tables directly when the app starts"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency provider for database sessions"""
    with Session(engine) as session:
        yield session