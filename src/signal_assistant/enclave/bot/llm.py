from typing import List, Dict, Any
from signal_assistant.config import enclave_settings
from signal_assistant.enclave.secure_config import SecureConfig, AttestationError
from signal_assistant.enclave.kms import KeyManager # Import KeyManager
from signal_assistant.enclave import secure_logging
from signal_assistant.enclave.privacy_core.sanitizer import SanitizedPrompt # Import SanitizedPrompt

class LLMClient:
    def __init__(self, key_manager: KeyManager): # Accept KeyManager instance
        self.secure_config = SecureConfig(key_manager) # Pass KeyManager to SecureConfig
        # In future: init OpenAI/Gemini client here using enclave_settings.openai_api_key
        pass


    def generate_response(self, system_prompt: SanitizedPrompt, chat_history: List[Dict[str, SanitizedPrompt]], user_message: SanitizedPrompt, attestation_verified: bool) -> str:
        """
        Generates a response from the LLM.
        Access to the LLM API key is gated by attestation_verified.
        Inputs MUST be SanitizedPrompt.
        """
        if not isinstance(system_prompt, SanitizedPrompt) or not isinstance(user_message, SanitizedPrompt):
             secure_logging.critical(None, "LLMClient: received non-sanitized prompt!")
             return "Error: Internal Security Violation (Unsanitized Input)"

        try:
            # Attempt to retrieve the LLM API key, which is gated by attestation_verified
            llm_api_key = self.secure_config.get_llm_api_key(attestation_verified)
            secure_logging.debug(None, "LLMClient: Successfully retrieved LLM API key.", metadata={"key_prefix": llm_api_key[:5]})
        except AttestationError:
            secure_logging.error(None, "LLMClient: Failed to retrieve LLM API key due to unverified attestation.")
            return "Error: LLM access denied due to attestation failure."
        except Exception as e:
            secure_logging.error(None, f"LLMClient: Failed to retrieve LLM API key: {e}")
            return f"Error: LLM access failed: {e}"

        # Mock response for now to allow end-to-end testing without API keys
        # In a real scenario, this would involve calling the actual LLM API using .content
        _ = llm_api_key # Use the key to avoid unused variable warning
        
        return f"This is a mock AI response to: {user_message.content}"
