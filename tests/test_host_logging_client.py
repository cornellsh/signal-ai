import pytest
import re # Import re for re.escape
from signal_assistant.host import logging_client

# Define the PII patterns as they are in logging_client.py for consistent testing
PII_EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PII_PHONE_PATTERN = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'

def test_info_logs_successfully():
    # This test primarily ensures that non-forbidden messages can be logged without raising an error
    # The actual output to console is not captured by default pytest, but this checks for exceptions
    try:
        logging_client.info("test_user_id", "This is an informational message.")
    except ValueError as e:
        pytest.fail(f"Logging info message failed unexpectedly: {e}")

def test_warning_logs_successfully():
    try:
        logging_client.warning("test_user_id", "This is a warning message.", {"code": 101})
    except ValueError as e:
        pytest.fail(f"Logging warning message failed unexpectedly: {e}")

def test_error_logs_successfully():
    try:
        logging_client.error("test_user_id", "This is an error message.", {"component": "host"})
    except ValueError as e:
        pytest.fail(f"Logging error message failed unexpectedly: {e}")

def test_debug_logs_successfully():
    try:
        logging_client.debug("test_user_id", "This is a debug message.", {"data": [1, 2, 3]})
    except ValueError as e:
        pytest.fail(f"Logging debug message failed unexpectedly: {e}")

def test_rejects_signal_id_in_message():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'signal_id' in message.")):
        logging_client.info("user123", "User signal_id: 12345 received.")

def test_rejects_signal_id_in_metadata():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'signal_id' in metadata.")):
        logging_client.info("user123", "Some message", {"id_type": "signal_id"})

def test_rejects_pii_email_in_message():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_EMAIL_PATTERN}' in message.")):
        logging_client.info("user123", "User email: test@example.com")

def test_rejects_pii_email_in_metadata():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_EMAIL_PATTERN}' in metadata.")):
        logging_client.info("user123", "Some message", {"contact": "test@example.com"})

def test_rejects_pii_phone_in_message():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_PHONE_PATTERN}' in message.")):
        logging_client.info("user123", "User phone: 555-123-4567")

def test_rejects_pii_phone_in_metadata():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_PHONE_PATTERN}' in metadata.")):
        logging_client.info("user123", "Some message", {"phone_number": "555-123-4567"})

def test_rejects_forbidden_keyword_prompt_in_message():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'prompt:' in message.")):
        logging_client.error(None, "LLM prompt: 'Tell me about PII.' failed.")

def test_rejects_forbidden_keyword_response_in_message():

    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'response:' in message.")):

        logging_client.info("user123", "LLM response: '...'")

def test_rejects_forbidden_keyword_message_body_in_message():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'message body:' in message.")):
        logging_client.info("user123", "Message body: 'Hello, world!'")

def test_no_false_positives_for_safe_content():
    try:
        logging_client.info("user123", "This is a safe message without PII or forbidden keywords.")
        logging_client.info("user123", "Another safe message.", {"safe_key": "safe_value"})
    except ValueError as e:
        pytest.fail(f"False positive PII detection: {e}")
