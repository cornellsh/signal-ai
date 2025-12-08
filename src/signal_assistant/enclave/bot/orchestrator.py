from typing import List, Dict, Any, Tuple
from signal_assistant.enclave.bot.llm import LLMClient
from signal_assistant.enclave.privacy_core.core import DecryptedPayload
import logging

logger = logging.getLogger(__name__)

class BotOrchestrator:
    """
    Business logic for the bot.
    Operates purely on in-memory state (decrypted).
    Does NOT access database directly.
    """
    def __init__(self):
        self.llm = LLMClient()

    def process_message(self, payload: DecryptedPayload, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process message using in-memory state.
        Returns (response_text, updated_state).
        
        state structure:
        {
            "history": [{"role": "user", "content": "..."}, ...]
        }
        """
        # Extract history from state
        history = state.get("history", [])
        if not isinstance(history, list):
            history = []
        
        # Call LLM
        response_text = self.llm.generate_response(
            system_prompt="You are a helpful privacy-focused assistant.",
            chat_history=history,
            user_message=payload.content
        )

        # Update History
        history.append({"role": "user", "content": payload.content})
        history.append({"role": "assistant", "content": response_text})
        
        # Prune history (Last 10 messages)
        if len(history) > 20:
            history = history[-20:]

        state["history"] = history
        return response_text, state