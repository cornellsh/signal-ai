import logging
import re
from typing import Optional, Dict, Any

# Configure a basic logger for the Enclave.
# Logs from the Enclave must be anonymized and encrypted before being sent to the Host.
# This module enforces content restrictions.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO: Implement SecureLogHandler to handle anonymization, encryption,
# and forwarding logs to the Host-side logging mechanism (e.g., via IPC).
# For this task, we focus on content enforcement within the _log function.
# class SecureLogHandler(logging.Handler):
#     def emit(self, record):
#         # Implement anonymization and encryption here
#         anonymized_record = self._anonymize(record)
#         encrypted_record = self._encrypt(anonymized_record)
#         # Forward to Host-side logging mechanism (e.g., via IPC)
#         print(f"ENCLAVE_SECURE_LOG: {encrypted_record}")
# logger.addHandler(SecureLogHandler())


def _log(level: int, internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Internal secure logging function for the Enclave.
    Enforces schema and strict content restrictions:
    - Forbids SignalID, plaintext PII, and specific sensitive keywords in message or metadata.
    """
    log_entry = {
        "level": logging.getLevelName(level),
        "internal_user_id": internal_user_id,
        "message": message,
        "metadata": metadata if metadata is not None else {},
    }

    # Strict checks to prevent forbidden keywords and direct SignalID usage.
    forbidden_keywords = ["signalid", "signal_id", "prompt:", "response:", "message body:"]
    
    # PII pattern detection (similar to Host, but critical for Enclave)
    pii_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', # Email
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b' # Phone number (simple)
    ]

    for keyword in forbidden_keywords:
        if keyword in message.lower():
            raise ValueError(f"Attempted to log forbidden keyword '{keyword}' in message.")
    for pattern_str in pii_patterns:
        if re.search(pattern_str, message):
            raise ValueError(f"Attempted to log potential PII pattern '{pattern_str}' in message.")

    # Check metadata
    if metadata:
        metadata_str = str(metadata).lower()
        for keyword in forbidden_keywords:
            if keyword in metadata_str:
                raise ValueError(f"Attempted to log forbidden keyword '{keyword}' in metadata.")
        for pattern_str in pii_patterns:
            if re.search(pattern_str, metadata_str):
                raise ValueError(f"Attempted to log potential PII pattern '{pattern_str}' in metadata.")
    
    # Log to the internal Enclave logger. The SecureLogHandler (if implemented) would intercept this.
    logger.log(level, f"[Enclave Secure Log - UserID: {internal_user_id}] {message}", extra={"metadata": metadata})


def debug(internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None):
    """Logs a debug message securely, associating it with an internal_user_id if available."""
    _log(logging.DEBUG, internal_user_id, message, metadata)

def info(internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None):
    """Logs an informational message securely, associating it with an internal_user_id if available."""
    _log(logging.INFO, internal_user_id, message, metadata)

def warning(internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None):
    """Logs a warning message securely, associating it with an internal_user_id if available."""
    _log(logging.WARNING, internal_user_id, message, metadata)

def error(internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None):
    """Logs an error message securely, associating it with an internal_user_id if available."""
    _log(logging.ERROR, internal_user_id, message, metadata)

def critical(internal_user_id: Optional[str], message: str, metadata: Optional[Dict[str, Any]] = None):
    """Logs a critical message securely, associating it with an internal_user_id if available."""
    _log(logging.CRITICAL, internal_user_id, message, metadata)