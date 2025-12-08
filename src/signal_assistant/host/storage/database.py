from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from signal_assistant.config import host_settings
from .models import Base

engine = create_engine(host_settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in host_settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
