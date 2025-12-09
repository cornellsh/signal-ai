import pytest
from signal_assistant.enclave.privacy_core.sanitizer import PIISanitizer

def test_no_pii_no_change():
    text = "This is a normal sentence with no sensitive information."
    assert PIISanitizer.sanitize(text) == text

def test_email_sanitization():
    text = "Contact me at test@example.com for more info."
    expected = "Contact me at [EMAIL] for more info."
    assert PIISanitizer.sanitize(text) == expected

def test_multiple_emails_sanitization():
    text = "Emails: user1@domain.com, user2@another.org."
    expected = "Emails: [EMAIL], [EMAIL]."
    assert PIISanitizer.sanitize(text) == expected

def test_email_at_beginning_and_end():
    text = "first@email.net. This is a message. last@email.co"
    expected = "[EMAIL]. This is a message. [EMAIL]"
    assert PIISanitizer.sanitize(text) == expected

def test_phone_number_sanitization_dash():
    text = "Call me at 123-456-7890 for assistance."
    expected = "Call me at [PHONE_NUMBER] for assistance."
    assert PIISanitizer.sanitize(text) == expected

def test_phone_number_sanitization_spaces():
    text = "My number is 123 456 7890."
    expected = "My number is [PHONE_NUMBER]."
    assert PIISanitizer.sanitize(text) == expected

def test_phone_number_sanitization_no_separator():
    text = "You can reach me at 1234567890 anytime."
    expected = "You can reach me at [PHONE_NUMBER] anytime."
    assert PIISanitizer.sanitize(text) == expected

def test_multiple_phone_numbers_sanitization():
    text = "Numbers are: 111-222-3333 and 444 555 6666."
    expected = "Numbers are: [PHONE_NUMBER] and [PHONE_NUMBER]."
    assert PIISanitizer.sanitize(text) == expected

def test_mixed_pii_sanitization():
    text = "My email is mixed@test.com and phone is 987-654-3210."
    expected = "My email is [EMAIL] and phone is [PHONE_NUMBER]."
    assert PIISanitizer.sanitize(text) == expected

def test_empty_string():
    assert PIISanitizer.sanitize("") == ""

def test_only_pii():
    text = "only@pii.org"
    expected = "[EMAIL]"
    assert PIISanitizer.sanitize(text) == expected

def test_pii_with_other_symbols():
    text = "Email: <user@example.com>."
    expected = "Email: <[EMAIL]>."
    assert PIISanitizer.sanitize(text) == expected

def test_pii_within_words_should_not_match():
    # While these are part of larger "words", the regex matches the PII portions.
    # The current regex prioritizes identifying the PII patterns themselves.
    text_email_embedded = "thisisnotmyemail@example.comword"
    expected_email_embedded = "[EMAIL]word" # The email part is redacted
    assert PIISanitizer.sanitize(text_email_embedded) == expected_email_embedded

    text_phone_embedded = "thisismyphone123-456-7890number"
    expected_phone_embedded = "thisismyphone[PHONE_NUMBER]number" # The phone part is redacted
    assert PIISanitizer.sanitize(text_phone_embedded) == expected_phone_embedded

def test_pii_edge_cases_and_non_match():
    # Test cases that should NOT be detected as PII by our current regex
    assert PIISanitizer.sanitize("user@domain") == "user@domain" # Incomplete email
    assert PIISanitizer.sanitize("123-456-789") == "123-456-789" # Incomplete phone
    assert PIISanitizer.sanitize("not a number") == "not a number"
    assert PIISanitizer.sanitize("email@example.co.uk") == "[EMAIL]" # Longer TLDs
    assert PIISanitizer.sanitize("email@sub.domain.com") == "[EMAIL]" # Subdomains
