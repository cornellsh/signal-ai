import pytest
from src.ai_assistant_bot.signal_adapter.client import SignalPrivacyService

def test_strip_pii_no_pii():
    service = SignalPrivacyService()
    text = "This is a normal message."
    sanitized_text, is_stripped = service._strip_pii(text)
    assert sanitized_text == text
    assert is_stripped is False

def test_strip_pii_with_phone_number():
    service = SignalPrivacyService()
    text = "Please call PII_PHONE for details."
    sanitized_text, is_stripped = service._strip_pii(text)
    assert "PII_PHONE" not in sanitized_text
    assert "[REDACTED_PHONE]" in sanitized_text
    assert is_stripped is True

def test_strip_pii_with_email():
    service = SignalPrivacyService()
    text = "My email is PII_EMAIL, contact me."
    sanitized_text, is_stripped = service._strip_pii(text)
    assert "PII_EMAIL" not in sanitized_text
    assert "[REDACTED_EMAIL]" in sanitized_text
    assert is_stripped is True

def test_strip_pii_with_multiple_pii_types():
    service = SignalPrivacyService()
    text = "Call PII_PHONE or email PII_EMAIL ASAP."
    sanitized_text, is_stripped = service._strip_pii(text)
    assert "PII_PHONE" not in sanitized_text
    assert "PII_EMAIL" not in sanitized_text
    assert "[REDACTED_PHONE]" in sanitized_text
    assert "[REDACTED_EMAIL]" in sanitized_text
    assert is_stripped is True

def test_strip_pii_empty_string():
    service = SignalPrivacyService()
    text = ""
    sanitized_text, is_stripped = service._strip_pii(text)
    assert sanitized_text == ""
    assert is_stripped is False

def test_strip_pii_only_pii():
    service = SignalPrivacyService()
    text = "PII_PHONE PII_EMAIL"
    sanitized_text, is_stripped = service._strip_pii(text)
    assert sanitized_text == "[REDACTED_PHONE] [REDACTED_EMAIL]"
    assert is_stripped is True
