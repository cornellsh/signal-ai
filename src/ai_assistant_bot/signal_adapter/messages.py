from dataclasses import dataclass
from typing import Literal, Any

@dataclass
class SignalMessage:
    """Base class for all Signal messages."""
    recipient_id: str
    message_type: Literal["text", "attachment", "reaction", "command"]

@dataclass
class TextMessage(SignalMessage):
    """Represents a text message."""
    text: str
    message_type: Literal["text"] = "text"

@dataclass
class AttachmentMessage(SignalMessage):
    """Represents a message with an attachment."""
    attachment_id: str # ID or path to the attachment
    file_name: str
    content_type: str
    message_type: Literal["attachment"] = "attachment"

@dataclass
class ReactionMessage(SignalMessage):
    """Represents a reaction to a message."""
    target_message_id: str
    emoji: str
    message_type: Literal["reaction"] = "reaction"

@dataclass
class CommandMessage(SignalMessage):
    """Represents a command sent to the bot."""
    command: str
    args: dict[str, Any]
    message_type: Literal["command"] = "command"

# More message types will be added as required
