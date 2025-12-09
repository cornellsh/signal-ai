import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union, List
import uuid
import enum
from signal_assistant.enclave import secure_logging
from signal_assistant.enclave.state_encryption import StateEncryptor
from signal_assistant.enclave.privacy_core.sanitizer import SanitizedPrompt

# Type aliases for clarity
SignalID = str
InternalUserID = str

class LE_REQUEST_TYPE(enum.Enum):
    GET_EXTERNAL_ID = "GET_EXTERNAL_ID"
    GET_LOGS = "GET_LOGS"
    ACCESS_SENSITIVE_DATA = "ACCESS_SENSITIVE_DATA" # Restricted

@dataclass
class LE_RESPONSE:
    status: str # "GRANTED" or "DENIED"
    data: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None

@dataclass
class DecryptedPayload:
    sender: str
    content: Union[str, SanitizedPrompt]
    timestamp: int

class KeyStore:
    """
    Securely manages Signal private keys. 
    In the future, this will interface with TEE secure storage.
    """
    def __init__(self):
        self._keys_loaded = False

    def load_keys(self):
        # Stub for secure key loading
        self._keys_loaded = True
        
    def decrypt(self, encrypted_payload: bytes) -> str:
        if not self._keys_loaded:
            raise RuntimeError("Keys not loaded")
        # Stub decryption
        return encrypted_payload.decode("utf-8", errors="ignore")

class IdentityMappingService:
    """
    Manages the mapping between SignalID and InternalUserID strictly within the Enclave.
    Enforces privacy by ensuring Host only sees InternalUserID.
    """
    def __init__(self, state_encryptor: StateEncryptor, storage_path: str = "/tmp/enclave_identity.enc"):
        self._state_encryptor = state_encryptor
        self._storage_path = storage_path
        self._signal_to_internal: Dict[SignalID, InternalUserID] = {}
        self._internal_to_signal: Dict[InternalUserID, SignalID] = {}
        
    def load_state(self):
        if not os.path.exists(self._storage_path):
             return
        
        try:
            with open(self._storage_path, "rb") as f:
                encrypted_blob = f.read()
            
            state = self._state_encryptor.decrypt(encrypted_blob)
            self._signal_to_internal = state.get("signal_to_internal", {})
            self._internal_to_signal = state.get("internal_to_signal", {})
            secure_logging.info(None, "Identity state loaded successfully.")
        except Exception as e:
            secure_logging.error(None, f"Failed to load identity state: {e}")

    def save_state(self):
        state = {
            "signal_to_internal": self._signal_to_internal,
            "internal_to_signal": self._internal_to_signal
        }
        try:
            encrypted_blob = self._state_encryptor.encrypt(state)
            # Atomic write
            temp_path = self._storage_path + ".tmp"
            with open(temp_path, "wb") as f:
                f.write(encrypted_blob)
            os.replace(temp_path, self._storage_path)
            secure_logging.info(None, "Identity state saved successfully.")
        except Exception as e:
            secure_logging.critical(None, f"Failed to save identity state: {e}")
            raise

    def map_signal_id_to_internal_id(self, signal_id: SignalID) -> InternalUserID:
        """
        Retrieves or creates an InternalUserID for a given SignalID.
        """
        if signal_id in self._signal_to_internal:
            internal_id = self._signal_to_internal[signal_id]
            secure_logging.debug(None, "Mapped existing external ID to InternalUserID.", {"internal_id": internal_id})
            return internal_id
        
        # Create new mapping
        internal_id = str(uuid.uuid4())
        self._signal_to_internal[signal_id] = internal_id
        self._internal_to_signal[internal_id] = signal_id
        secure_logging.info(None, "Created new InternalUserID for external ID.", {"internal_id": internal_id})
        self.save_state() # Persist
        return internal_id

    def delete_user_data(self, internal_user_id: InternalUserID) -> None:
        """
        Irrevocably deletes mapping and associated data for a user.
        """
        if internal_user_id in self._internal_to_signal:
            signal_id = self._internal_to_signal[internal_user_id]
            del self._internal_to_signal[internal_user_id]
            if signal_id in self._signal_to_internal:
                del self._signal_to_internal[signal_id]
            
            # TODO: Trigger deletion of LongTermMemory and Host metadata via IPC
            secure_logging.info(None, "Deleted user data and mapping.", {"internal_id": internal_user_id})
            self.save_state() # Persist
        else:
            secure_logging.warning(None, "Attempted to delete unknown InternalUserID.", {"internal_id": internal_user_id})

    def _check_le_policy(self, request_type: LE_REQUEST_TYPE, target_id: Union[SignalID, InternalUserID], auth_context: Dict) -> bool:
        """
        CHECK_LE_POLICY: Enforces multi-party authorization and default-deny.
        """
        # Default DENY
        decision = False
        
        # simulated multi-party authorization check
        # In reality, this would verify cryptographic signatures from multiple independent parties
        is_authorized = auth_context.get("is_authorized_multi_party", False)
        
        if not is_authorized:
            secure_logging.warning(None, "LE Policy: Request unauthorized.", {"request_type": request_type.value})
            return False

        if request_type == LE_REQUEST_TYPE.GET_EXTERNAL_ID:
            # Allowed if target is InternalUserID and authorized
            if isinstance(target_id, str): # weak check, strictly should validate format
                 decision = True
        elif request_type == LE_REQUEST_TYPE.GET_LOGS:
             # Allowed if authorized
             decision = True
        elif request_type == LE_REQUEST_TYPE.ACCESS_SENSITIVE_DATA:
             # Explicitly DENY plaintext access even if authorized (privacy invariant)
             secure_logging.critical(None, "LE Policy: Denied access to sensitive plaintext.")
             decision = False
        
        secure_logging.info(None, f"LE Policy decision: {decision}", {"request_type": request_type.value})
        return decision

    def handle_le_request(self, request_type: LE_REQUEST_TYPE, target_id: Union[SignalID, InternalUserID], auth_context: Dict) -> LE_RESPONSE:
        """
        Handles Law Enforcement requests with strict policy enforcement.
        """
        if not self._check_le_policy(request_type, target_id, auth_context):
            return LE_RESPONSE(status="DENIED", reason="Policy verification failed or unauthorized request type.")

        if request_type == LE_REQUEST_TYPE.GET_EXTERNAL_ID:
            # target_id is expected to be InternalUserID
            if target_id in self._internal_to_signal:
                return LE_RESPONSE(status="GRANTED", data={"external_id": self._internal_to_signal[target_id]})
            else:
                return LE_RESPONSE(status="DENIED", reason="User not found.")
                
        elif request_type == LE_REQUEST_TYPE.GET_LOGS:
            # Return limited logs (mocked)
            return LE_RESPONSE(status="GRANTED", data={"logs": ["log_entry_1", "log_entry_2"]})
            
        return LE_RESPONSE(status="DENIED", reason="Unsupported request type.")

class PrivacyCore:
    def __init__(self):
        self.keystore = KeyStore()
        self.keystore.load_keys()

    def process_envelope(self, envelope) -> Optional[DecryptedPayload]:
        """
        Decrypts and sanitizes a raw envelope. 
        Returns None if decryption fails or message is invalid.
        """
        try:
            # In real implementation: 
            # plaintext = self.keystore.decrypt(envelope.payload)
            # For now, we assume payload is mock bytes
            
            # MOCK LOGIC: assuming payload is just bytes of text for prototype
            raw_text = envelope.payload.decode("utf-8")
            
            # Sanitize IMMEDIATELY after decryption
            from .sanitizer import PIISanitizer
            sanitized_text = PIISanitizer.sanitize(raw_text)
            
            return DecryptedPayload(
                sender=envelope.source_identifier,
                content=sanitized_text,
                timestamp=envelope.timestamp
            )
        except Exception as e:
            # Log error securely (without revealing content)
            return None
