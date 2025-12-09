import pytest
import logging
from unittest.mock import MagicMock
from signal_assistant.enclave import secure_logging

def test_secure_logging_rejects_pii_in_message():
    """Verify that the secure logger raises ValueError when PII is detected in the message."""
    
    # Email
    with pytest.raises(ValueError, match="Attempted to log potential PII pattern"):
        secure_logging.info("user123", "User email is test@example.com")
        
    # Phone
    with pytest.raises(ValueError, match="Attempted to log potential PII pattern"):
        secure_logging.info("user123", "User phone is 555-123-4567")

def test_secure_logging_rejects_forbidden_keywords_in_message():
    """Verify that forbidden keywords (like SignalID) are rejected."""
    
    with pytest.raises(ValueError, match="Attempted to log forbidden keyword"):
        secure_logging.info("user123", "Processing SignalID: +15551234567")

def test_secure_logging_rejects_pii_in_metadata():
    """Verify that PII in metadata is also caught."""
    
    with pytest.raises(ValueError, match="Attempted to log potential PII pattern"):
        secure_logging.info("user123", "Processing message", metadata={"email": "test@example.com"})

def test_secure_logging_allows_safe_messages():
    """Verify that safe messages pass through."""
    
    # Mock the internal logger to verify calls
    with pytest.MonkeyPatch.context() as m:
        mock_logger = MagicMock()
        m.setattr(secure_logging, "logger", mock_logger)
        
        secure_logging.info("user123", "System started successfully.")
        
        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        assert args[0] == logging.INFO
        assert "System started successfully" in args[1]
        assert "[Enclave Secure Log - UserID: user123]" in args[1]
