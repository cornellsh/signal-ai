from typing import List, Dict, Any, Tuple, Optional # Import Optional
from signal_assistant.enclave.bot.llm import LLMClient
from signal_assistant.enclave.privacy_core.core import DecryptedPayload
from signal_assistant.enclave import secure_logging
from signal_assistant.enclave.privacy_core.sanitizer import PIISanitizer # Import PIISanitizer
from signal_assistant.enclave.kms import KeyManager # Import KeyManager

class LLMPipeline: # Renamed from BotOrchestrator
    """
    Orchestrates all LLM interactions within the Enclave.
    Ensures mandatory PII sanitization of the assembled prompt before calling the external LLM.
    Operates purely on in-memory state (decrypted).
    Does NOT access database directly.
    """
    def __init__(self, key_manager: KeyManager): # Accept KeyManager instance
        self.llm = LLMClient(key_manager) # Pass KeyManager to LLMClient

    def process_user_request(self, internal_user_id: str, user_message: str, context_data: Optional[Dict[str, Any]] = None, attestation_verified: bool = False) -> str:
        """
        Processes a user request, including prompt assembly, PII sanitization,
        and interaction with the external LLM.
        """
        # Placeholder for context retrieval/tool calls. For now, context_data is directly used.
        # This function will encapsulate user message input, context retrieval, tool calls,
        # and final prompt assembly.
        
        # 1. Context Retrieval and Tool Outputs (Simplified for this task)
        # For this task, we'll assume context_data is already sanitized if it comes from long-term memory.
        # user_message is the raw input directly from the Signal Protocol Stack.
        
        # 2. Final Prompt Assembly (simplified for this task)
        # We'll assemble a simple prompt incorporating the user_message and context.
        # The full history (chat_history) from state.get("history", []) will be part of the assembled prompt.
        
        # Note: The original `process_message` method took `DecryptedPayload` and `state`.
        # This refactored method takes `internal_user_id` and `user_message` directly,
        # with `context_data` serving as a placeholder for conversational state or other context.
        # The history management will be simplified for this refactoring task.

        # For the purpose of demonstration and to integrate the sanitizer:
        # We need to construct the full prompt string that would be sent to the LLM.
        # This includes system prompt, chat history (from context_data), and the new user message.

        system_prompt = "You are a helpful privacy-focused assistant."
        chat_history = context_data.get("history", []) if context_data else []
        
        # Assemble the full prompt string
        # For LLMClient.generate_response, this assembly happens internally based on its arguments.
        # The critical part is that *all* text content flowing into generate_response is sanitized.
        
        # The LLMClient.generate_response will internally assemble the prompt.
        # We ensure its arguments are sanitized.
        
        # 3. Mandatory PII Sanitization (This is the critical step for the pipeline)
        # The combined "final prompt" concept applies to the effective prompt that LLMClient sees.
        # Since LLMClient takes separate args (system_prompt, chat_history, user_message),
        # we ensure each of these is sanitized before passing.
        
        # Call LLM with sanitized inputs and attestation status
        # Note: We sanitize system_prompt and user_message explicitly.
        # chat_history elements should also be sanitized.
        
        sanitized_system_prompt_obj = PIISanitizer.sanitize(system_prompt)
        sanitized_user_message_obj = PIISanitizer.sanitize(user_message)
        
        sanitized_chat_history_objs = []
        for entry in chat_history:
            sanitized_chat_history_objs.append({
                "role": entry["role"],
                "content": PIISanitizer.sanitize(entry["content"])
            })

        response_text = self.llm.generate_response(
            system_prompt=sanitized_system_prompt_obj,
            chat_history=sanitized_chat_history_objs,
            user_message=sanitized_user_message_obj,
            attestation_verified=attestation_verified # Pass the attestation flag
        )

        secure_logging.info(internal_user_id, "LLM Pipeline processed user request.", 
                            metadata={"user_message_len": len(user_message), "response_len": len(response_text)})

        return response_text