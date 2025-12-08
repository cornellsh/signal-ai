from sqlalchemy import Column, String, DateTime, LargeBinary
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class EncryptedState(Base):
    __tablename__ = "encrypted_states"

    signal_id = Column(String, primary_key=True, index=True)
    blob = Column(LargeBinary, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

