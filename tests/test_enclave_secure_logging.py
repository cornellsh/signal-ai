import pytest
import re
from signal_assistant.enclave import secure_logging

# Define the PII patterns as they are in secure_logging.py for consistent testing
PII_EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PII_PHONE_PATTERN = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'

def test_info_logs_successfully_with_user_id():
    try:
        secure_logging.info("test_user_id", "This is an informational message from Enclave.")
    except ValueError as e:
        pytest.fail(f"Logging info message failed unexpectedly: {e}")

def test_info_logs_successfully_without_user_id():
    try:
        secure_logging.info(None, "This is a system-level informational message from Enclave.")
    except ValueError as e:
        pytest.fail(f"Logging info message failed unexpectedly: {e}")

def test_warning_logs_successfully():
    try:
        secure_logging.warning("test_user_id", "Enclave process experienced a minor issue.", {"severity": "low"})
    except ValueError as e:
        pytest.fail(f"Logging warning message failed unexpectedly: {e}")

def test_error_logs_successfully():
    try:
        secure_logging.error("test_user_id", "Critical error within Enclave.", {"error_code": 500})
    except ValueError as e:
        pytest.fail(f"Logging error message failed unexpectedly: {e}")

def test_debug_logs_successfully():
    try:
        secure_logging.debug("test_user_id", "Detailed step-by-step execution in Enclave.", {"step": 1, "data_len": 200})
    except ValueError as e:
        pytest.fail(f"Logging debug message failed unexpectedly: {e}")

def test_rejects_signal_id_in_message():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'signalid' in message.")):
        secure_logging.info("enclave_user_delta", "Processing SignalID: 98765.")

def test_rejects_signal_id_in_metadata():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'signal_id' in metadata.")):
        secure_logging.info("enclave_user_delta", "Some enclave message", {"id_type": "signal_id"})

def test_rejects_pii_email_in_message():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_EMAIL_PATTERN}' in message.")):
        secure_logging.info("enclave_user_epsilon", "User email is test@enclave.com.")

def test_rejects_pii_email_in_metadata():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_EMAIL_PATTERN}' in metadata.")):
        secure_logging.info("enclave_user_epsilon", "Some enclave message", {"contact": "test@enclave.com"})

def test_rejects_pii_phone_in_message():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_PHONE_PATTERN}' in message.")):
        secure_logging.info("enclave_user_zeta", "User phone is 555-987-6543.")

def test_rejects_pii_phone_in_metadata():
    with pytest.raises(ValueError, match=re.escape(f"Attempted to log potential PII pattern '{PII_PHONE_PATTERN}' in metadata.")):
        secure_logging.info("enclave_user_zeta", "Some enclave message", {"phone_number": "555-987-6543"})

def test_rejects_forbidden_keyword_prompt_in_message():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'prompt:' in message.")):
        secure_logging.error("enclave_user_gamma", "LLM prompt: 'Analyze this sensitive data.' failed.")

def test_rejects_forbidden_keyword_response_in_message():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'response:' in message.")):
        secure_logging.info("enclave_user_alpha", "LLM response: 'Sensitive response content.'")

def test_rejects_forbidden_keyword_message_body_in_message():
    with pytest.raises(ValueError, match=re.escape("Attempted to log forbidden keyword 'message body:' in message.")):
        secure_logging.info("enclave_user_beta", "Message body: 'Confidential user chat.'")

def test_no_false_positives_for_safe_content():
    try:
        secure_logging.info("enclave_user_safe", "This is a safe message from Enclave without PII or forbidden keywords.")
        secure_logging.info(None, "Another safe system message.", {"safe_key": "safe_value"})
    except ValueError as e:
        pytest.fail(f"False positive PII detection: {e}")