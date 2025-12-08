from sqlalchemy.orm import Session
from typing import Optional
from .models import EncryptedState

class BlobStore:
    """
    Interface for the Blind Blob Store.
    Manages encrypted state blobs for users.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_state(self, signal_id: str) -> Optional[bytes]:
        """Retrieves the encrypted state blob for a given Signal ID."""
        record = self.db.query(EncryptedState).filter(EncryptedState.signal_id == signal_id).first()
        if record:
            return record.blob
        return None

    def save_state(self, signal_id: str, blob: bytes):
        """Upserts the encrypted state blob."""
        record = self.db.query(EncryptedState).filter(EncryptedState.signal_id == signal_id).first()
        if record:
            record.blob = blob
        else:
            record = EncryptedState(signal_id=signal_id, blob=blob)
            self.db.add(record)
        self.db.commit()
