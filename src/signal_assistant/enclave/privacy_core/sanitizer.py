import re

class PIISanitizer:
    """
    Responsible for stripping Personally Identifiable Information from text.
    """
    # Simple regex for phone numbers (international format)
    PHONE_REGEX = re.compile(r'\+?\d[\d -]{8,12}\d')
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Replaces PII with safe tokens.
        """
        text = cls.PHONE_REGEX.sub('[PHONE_NUMBER]', text)
        text = cls.EMAIL_REGEX.sub('[EMAIL]', text)
        return text
