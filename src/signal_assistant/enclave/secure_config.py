# src/signal_assistant/enclave/secure_config.py
from cryptography.fernet import Fernet
from signal_assistant.enclave import secure_logging
from signal_assistant.enclave.exceptions import AttestationError # Import AttestationError
# We will pass KeyManager instance, not import it directly to break circular dependency

# In a real scenario, this key would be securely generated and exchanged, NOT hardcoded.
# This is for simulation/demonstration purposes only.
# Fernet keys must be 32 url-safe base64-encoded bytes.
SHARED_SYMMETRIC_KEY = Fernet.generate_key()

# KMS Master Key for encrypting/decrypting other keys within the KMS
# This key itself would need to be very securely managed (e.g., hardware-backed)
KMS_MASTER_KEY = Fernet.generate_key()

# Key for simulating Signal message encryption/decryption
SIGNAL_MESSAGE_KEY = Fernet.generate_key()

class SecureConfig:
    """
    Manages access to sensitive configuration values, especially external service API keys (EAKs).
    Ensures attestation verification is applied before releasing sensitive keys.
    """
    def __init__(self, key_manager): # Accept KeyManager instance
        self.key_manager = key_manager
        # Simulate provisioning of an LLM API key if it doesn't exist
        # In a real system, this would come from a secure provisioning process,
        # often involving the Host after attestation.
        try:
            # Try to get the key without attestation check first to see if it's there
            _ = self.key_manager.get_key("LLM_API_KEY_", attestation_verified=True)
        except KeyError:
            # If not found, simulate generating and sealing it (for testing purposes)
            # This generation itself should ideally be attestation-gated, but for testing
            # the _initial_ setup, we allow it to be sealed.
            # The *retrieval* will enforce attestation.
            self.key_manager.generate_key("LLM_API_KEY_", attestation_verified=True) # Generate as if attested

    def get_llm_api_key(self, attestation_verified: bool) -> str:
        """
        Retrieves the LLM API key, subject to attestation verification.
        """
        try:
            # Get the key using the attestation_verified flag
            api_key_bytes = self.key_manager.get_key("LLM_API_KEY_", attestation_verified)
            return api_key_bytes.decode('utf-8')
        except AttestationError as e:
            secure_logging.error(None, f"Attempted to retrieve LLM API key without verified attestation: {e}")
            raise
        except KeyError as e:
            secure_logging.error(None, f"LLM API key not found in KMS: {e}")
            raise
