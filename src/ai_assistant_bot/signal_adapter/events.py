from dataclasses import dataclass
from typing import Literal

@dataclass
class SignalEvent:
    """Base class for all Signal events."""
    timestamp: int
    source: str

@dataclass
class MessageReceivedEvent(SignalEvent):
    """Represents a received message event."""
    message_id: str
    sender_id: str
    conversation_id: str
    content_type: Literal["text", "attachment", "reaction"]
    # Encrypted content data will be processed by the Privacy Core
    encrypted_content_data: bytes

@dataclass
class GroupUpdateEvent(SignalEvent):
    """Represents a group update event."""
    group_id: str
    change_type: Literal["member_added", "member_removed", "name_changed"]
    # Additional fields as needed for group updates

# More event types will be added as required
