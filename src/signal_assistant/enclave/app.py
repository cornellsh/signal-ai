# src/signal_assistant/enclave/app.py

import os # Added os import
from signal_assistant.enclave.transport import SecureChannel
from signal_assistant.enclave.signal_lib import SignalLib
from signal_assistant.enclave.privacy_core.sanitizer import PIISanitizer
from signal_assistant.enclave.serialization import CommandSerializer
from signal_assistant.enclave.kms import KeyManager, AttestationError # Import KeyManager and AttestationError
from signal_assistant.enclave.bot.orchestrator import LLMPipeline # Import LLMPipeline
from signal_assistant.enclave import secure_logging
from signal_assistant.enclave.privacy_core.core import IdentityMappingService # Added import
from signal_assistant.enclave.state_encryption import StateEncryptor # Added import
from signal_assistant.config import enclave_settings # Import settings
import json # Import json for json.JSONDecodeError

class EnclaveApp:
    """
    The main application within the enclave, responsible for processing commands
    received from the host via the secure channel.
    """
    def __init__(self, host_to_enclave_queue, enclave_to_host_queue):
        self.secure_channel = SecureChannel(host_to_enclave_queue, enclave_to_host_queue)
        self.signal_lib = SignalLib()
        self.key_manager = KeyManager() # Instantiate KeyManager
        self.llm_pipeline = LLMPipeline(self.key_manager) # Instantiate LLMPipeline with KeyManager
        self._running = False
        self.attestation_is_verified: bool = False # Initialize attestation flag
        self.identity_service = None # Initialize to None

    def _perform_attestation_verification(self) -> bool:
        """
        Simulates internal attestation verification.
        In a real scenario, this would involve complex cryptographic checks.
        """
        if os.environ.get("MOCK_ATTESTATION_FOR_TESTS_ONLY") == "1":
             secure_logging.warning(None, "SECURITY WARNING: Using MOCK ATTESTATION. NOT FOR PRODUCTION.")
             return True

        secure_logging.info(None, "EnclaveApp: Performing internal attestation verification (simulated).")
        # Fail closed by default
        return False

    def start(self):
        """Starts the enclave app (for testing purposes, processes one message)."""
        self._running = True
        secure_logging.info(None, "EnclaveApp is starting...")
        
        # Operational Governance Self-Check
        if enclave_settings and enclave_settings.environment == "PROD":
            if os.environ.get("MOCK_ATTESTATION_FOR_TESTS_ONLY") == "1":
                secure_logging.critical(None, "SECURITY VIOLATION: PROD environment detected with MOCK_ATTESTATION enabled. Aborting.")
                raise RuntimeError("Security Violation: Mock Attestation in PROD")

        # Perform attestation verification during startup
        self.attestation_is_verified = self._perform_attestation_verification()
        if not self.attestation_is_verified:
            secure_logging.critical(None, "Enclave attestation failed during startup. Sensitive operations will be blocked.")
        else:
            secure_logging.info(None, "Enclave attestation successful.")
            # Initialize IdentityMappingService
            try:
                 key_id = "ESSK_IDENTITY_MAPPING"
                 try:
                     mapping_key = self.key_manager.get_key(key_id, True)
                 except KeyError:
                     mapping_key = self.key_manager.generate_key(key_id, True)
                 
                 encryptor = StateEncryptor(mapping_key)
                 self.identity_service = IdentityMappingService(encryptor)
                 self.identity_service.load_state()
            except Exception as e:
                 secure_logging.critical(None, f"Failed to init IdentityService: {e}")
                 self._running = False
                 return

        if self.secure_channel.establish():
            while self._running:
                received_message = self.secure_channel.receive(timeout=1) # Short timeout for continuous check
                if received_message:
                    self._process_command(received_message)
                else:
                    # If no message, yield control briefly to avoid busy-waiting
                    pass # Or a small sleep if not in a separate thread context
        secure_logging.info(None, "EnclaveApp stopped.")

    def stop(self):
        """Stops the enclave app."""
        self._running = False

    def _process_command(self, message_bytes: bytes):
        """
        Processes a received command.
        """
        secure_logging.debug(None, "EnclaveApp processing raw message.", {"message_len": len(message_bytes)})
        try:
            deserialized_message = CommandSerializer.deserialize(message_bytes)
            command = deserialized_message["command"]
            payload = deserialized_message["payload"]
            secure_logging.debug(None, f"EnclaveApp processing command: {command}", {"payload_len": len(str(payload))})
        except (json.JSONDecodeError, ValueError) as e:
            secure_logging.error(None, f"Error deserializing command: {e}", {"exception": str(e)})
            self.secure_channel.send(b"Error: Invalid command format")
            return

        response = b"Unknown Command"
        if command == "GET_STATUS":
            response = b"Enclave is Operational"
        elif command == "INBOUND_MESSAGE":
            # Payload expects 'encrypted_envelope': bytes
            plaintext_envelope_bytes = payload.get("encrypted_envelope")
            if plaintext_envelope_bytes:
                if isinstance(plaintext_envelope_bytes, str):
                    plaintext_envelope_bytes = plaintext_envelope_bytes.encode('utf-8')
                sender, decrypted_message = self.signal_lib.decrypt_envelope(plaintext_envelope_bytes)
                
                if sender and decrypted_message:
                    internal_user_id = "UNKNOWN"
                    if self.identity_service:
                        internal_user_id = self.identity_service.map_signal_id_to_internal_id(sender)
                    else:
                        secure_logging.error(None, "Identity Service unavailable. Dropping message.")
                        self.secure_channel.send(b"Error: Service Unavailable")
                        return

                    secure_logging.debug(internal_user_id, "SignalLib.decrypt_envelope returned message from sender.", {"message_len": len(decrypted_message)})
                    
                    # Use LLMPipeline for processing and sanitization
                    # Note: decrypted_message is str. process_user_request expects str.
                    response_text = self.llm_pipeline.process_user_request(
                        internal_user_id=internal_user_id, # Use internal_user_id
                        user_message=decrypted_message,
                        context_data={}, # Placeholder for actual context
                        attestation_verified=self.attestation_is_verified
                    )
                    secure_logging.info(internal_user_id, "LLMPipeline processed message.", {"response_len": len(response_text)})
                    response = f"Message processed from {internal_user_id}".encode() # Do not return sender (SignalID)
                else:
                    response = b"Failed to decrypt or process message"
            else:
                response = b"Error: Missing encrypted_envelope in payload"
        elif command == "OUTBOUND_MESSAGE":
            # Payload expects 'recipient_id': str and 'plaintext': str
            recipient_id = payload.get("recipient_id")
            plaintext = payload.get("plaintext")
            if recipient_id and plaintext:
                encrypted_envelope = self.signal_lib.encrypt_message(recipient_id, plaintext) # This now returns plaintext bytes
                secure_logging.info(None, "Encrypted message for recipient.", {"encrypted_envelope_len": len(encrypted_envelope)})
                response = f"Outbound message encrypted for {recipient_id}".encode()
            else:
                response = b"Error: Missing recipient_id or plaintext in payload"
        elif command == "CHECK_LE_POLICY":
            # Delegate to IdentityMappingService
            if not self.identity_service:
                response = b"Error: Service Unavailable"
            else:
                # Payload expects 'request_type', 'target_id', 'auth_context'
                # Mapping from raw payload to LE_REQUEST_TYPE/args might be needed if payload structure differs
                # Assuming simplified mapping for now or reconstructing from policy_request_str if legacy
                
                # Check for legacy structure
                policy_request_str = payload.get("policy_request")
                if policy_request_str:
                     # Simulate translating legacy request to new API
                     from signal_assistant.enclave.privacy_core.core import LE_REQUEST_TYPE
                     req_type = LE_REQUEST_TYPE.ACCESS_SENSITIVE_DATA if "access_sensitive_data" in policy_request_str else LE_REQUEST_TYPE.GET_LOGS
                     
                     # Using dummy values for target/auth since legacy request didn't specify
                     resp_obj = self.identity_service.handle_le_request(req_type, "unknown", {"is_authorized_multi_party": False})
                     if resp_obj.status == "GRANTED":
                         response = b"LE Policy: Access Granted"
                     else:
                         response = b"LE Policy: Access Denied"
                else:
                    response = b"Error: Missing policy_request in payload"
        elif command == "STORE_ENCRYPTED_DATA":
            # Payload expects 'signal_id': str and 'encrypted_data': bytes
            signal_id = payload.get("signal_id")
            encrypted_data_bytes = payload.get("encrypted_data") # This is now raw bytes
            if signal_id and encrypted_data_bytes:
                if isinstance(encrypted_data_bytes, str):
                    encrypted_data_bytes = encrypted_data_bytes.encode('utf-8')
                
                # Example of using KeyManager with attestation flag
                try:
                    # Assume we need a specific key for storage, or just store directly
                    # For now, we'll just log that data is being stored.
                    # A more complete implementation would use self.key_manager.get_key/generate_key
                    secure_logging.info(None, "Enclave sending encrypted data to host storage.", {"data_len": len(encrypted_data_bytes)})
                    response = f"Encrypted data for {signal_id} sent to host storage.".encode()
                except AttestationError:
                    secure_logging.error(None, "Attempted to store encrypted data with unverified attestation.", {"signal_id": signal_id})
                    response = b"Error: Attestation failed for storage operation."
            else:
                response = b"Error: Missing signal_id or encrypted_data in payload"
        
        self.secure_channel.send(response)