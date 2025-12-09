import logging
import re # Added re
from typing import Optional, Dict, Any

class LoggingClient:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO) # Default level

        # Basic console handler for now
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log(self, level: int, message: str, internal_user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        # Strict checks to prevent forbidden keywords and direct SignalID usage.
        # These patterns must match what is expected by tests.
        forbidden_keywords = ["signalid", "signal_id", "prompt:", "response:", "message body:"]
        
        # PII pattern detection
        pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', # Email
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b' # Phone number (simple)
        ]

        # Check message content
        for keyword in forbidden_keywords:
            if keyword in message.lower():
                raise ValueError(f"Attempted to log forbidden keyword '{keyword}' in message.")
        for pattern_str in pii_patterns:
            if re.search(pattern_str, message):
                raise ValueError(f"Attempted to log potential PII pattern '{pattern_str}' in message.")

        # Extract custom metadata if present in kwargs (backwards compatibility) or use explicit arg
        if metadata is None:
            metadata = kwargs.pop('metadata', None)
        
        # Check metadata content
        if metadata:
            metadata_str = str(metadata).lower()
            for keyword in forbidden_keywords:
                if keyword in metadata_str:
                    raise ValueError(f"Attempted to log forbidden keyword '{keyword}' in metadata.")
            for pattern_str in pii_patterns:
                if re.search(pattern_str, metadata_str):
                    raise ValueError(f"Attempted to log potential PII pattern '{pattern_str}' in metadata.")

        # Ensure internal_user_id is part of the message if provided.
        log_message = f"User({internal_user_id}) - {message}" if internal_user_id else message
        
        # If metadata exists, add it to the 'extra' dictionary for the standard logger
        if metadata:
            if 'extra' not in kwargs:
                kwargs['extra'] = {}
            kwargs['extra']['metadata'] = metadata

        self.logger.log(level, log_message, **kwargs)

    def debug(self, internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.DEBUG, message, internal_user_id, metadata, **kwargs)

    def info(self, internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.INFO, message, internal_user_id, metadata, **kwargs)

    def warning(self, internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.WARNING, message, internal_user_id, metadata, **kwargs)

    def error(self, internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.ERROR, message, internal_user_id, metadata, **kwargs)

    def critical(self, internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None, **kwargs):
        self._log(logging.CRITICAL, message, internal_user_id, metadata, **kwargs)
