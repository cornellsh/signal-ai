from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class RawEnvelope:
    """
    Represents a raw, encrypted envelope received from the Signal network.
    """
    source_identifier: str
    timestamp: int
    payload: bytes  # Encrypted content
    type: int
