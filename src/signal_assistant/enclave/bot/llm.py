from signal_assistant.config import enclave_settings

class LLMClient:
    def __init__(self):
        # In future: init OpenAI/Gemini client here using enclave_settings.openai_api_key
        pass


    def generate_response(self, system_prompt: str, chat_history: list[dict], user_message: str) -> str:
        """
        Generates a response from the LLM.
        """
        # Mock response for now to allow end-to-end testing without API keys
        return f"This is a mock AI response to: {user_message}"
