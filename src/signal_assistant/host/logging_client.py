import logging
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

    def _log(self, level: int, message: str, internal_user_id: Optional[str] = None, **kwargs):
        # Extract custom metadata if present in kwargs
        metadata = kwargs.pop('metadata', None)
        
        # Ensure internal_user_id is part of the message if provided.
        log_message = f"User({internal_user_id}) - {message}" if internal_user_id else message
        
        # If metadata exists, add it to the 'extra' dictionary for the standard logger
        if metadata:
            if 'extra' not in kwargs:
                kwargs['extra'] = {}
            kwargs['extra']['metadata'] = metadata

        self.logger.log(level, log_message, **kwargs)

    def debug(self, message: str, internal_user_id: Optional[str] = None, **kwargs):
        self._log(logging.DEBUG, message, internal_user_id, **kwargs)

    def info(self, message: str, internal_user_id: Optional[str] = None, **kwargs):
        self._log(logging.INFO, message, internal_user_id, **kwargs)

    def warning(self, message: str, internal_user_id: Optional[str] = None, **kwargs):
        self._log(logging.WARNING, message, internal_user_id, **kwargs)

    def error(self, message: str, internal_user_id: Optional[str] = None, **kwargs):
        self._log(logging.ERROR, message, internal_user_id, **kwargs)

    def critical(self, message: str, internal_user_id: Optional[str] = None, **kwargs):
        self._log(logging.CRITICAL, message, internal_user_id, **kwargs)
