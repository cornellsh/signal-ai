# src/signal_assistant/enclave/app.py

from signal_assistant.enclave.transport import SecureChannel
from signal_assistant.enclave.signal_lib import SignalLib
from signal_assistant.enclave.privacy_core.sanitizer import PIISanitizer
from signal_assistant.enclave.serialization import CommandSerializer
import json # Import json for json.JSONDecodeError

class EnclaveApp:
    """
    The main application within the enclave, responsible for processing commands
    received from the host via the secure channel.
    """
    def __init__(self, host_to_enclave_queue, enclave_to_host_queue):
        self.secure_channel = SecureChannel(host_to_enclave_queue, enclave_to_host_queue)
        self.signal_lib = SignalLib()
        self._running = False

    def start(self):
        """Starts the enclave app (for testing purposes, processes one message)."""
        self._running = True
        print("EnclaveApp is starting...")
        if self.secure_channel.establish():
            while self._running:
                received_message = self.secure_channel.receive(timeout=1) # Short timeout for continuous check
                if received_message:
                    self._process_command(received_message)
                else:
                    # If no message, yield control briefly to avoid busy-waiting
                    pass # Or a small sleep if not in a separate thread context
        print("EnclaveApp stopped.")

    def stop(self):
        """Stops the enclave app."""
        self._running = False

    def _process_command(self, message_bytes: bytes):
        """
        Processes a received command.
        """
        print(f"EnclaveApp processing raw message: {message_bytes}")
        try:
            deserialized_message = CommandSerializer.deserialize(message_bytes)
            command = deserialized_message["command"]
            payload = deserialized_message["payload"]
            print(f"EnclaveApp processing command: {command} with payload: {payload}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error deserializing command: {e}")
            self.secure_channel.send(b"Error: Invalid command format")
            return

        response = b"Unknown Command"
        if command == "GET_STATUS":
            response = b"Enclave is Operational"
        elif command == "INBOUND_MESSAGE":
            # Payload expects 'encrypted_envelope': bytes as the key, which is now plaintext from SignalLib
            plaintext_envelope_bytes = payload.get("encrypted_envelope")
            if plaintext_envelope_bytes:
                # Ensure it's bytes for decrypt_envelope which expects bytes
                if isinstance(plaintext_envelope_bytes, str):
                    # This case should ideally not happen with correct CommandSerializer, but added for robustness
                    plaintext_envelope_bytes = plaintext_envelope_bytes.encode('utf-8')
                sender, decrypted_message = self.signal_lib.decrypt_envelope(plaintext_envelope_bytes)
                print(f"DEBUG: SignalLib.decrypt_envelope returned sender: {sender}, message: {decrypted_message}") # DEBUG PRINT
                if sender and decrypted_message:
                    sanitized_message = PIISanitizer.sanitize(decrypted_message)
                    print(f"Decrypted and Sanitized message from {sender}: {sanitized_message}")
                    response = f"Message processed from {sender}".encode()
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
                print(f"Encrypted message for {recipient_id}: {encrypted_envelope}")
                response = f"Outbound message encrypted for {recipient_id}".encode()
            else:
                response = b"Error: Missing recipient_id or plaintext in payload"
        elif command == "CHECK_LE_POLICY":
            # Payload expects 'policy_request': str
            policy_request_str = payload.get("policy_request")
            if policy_request_str:
                print(f"Enforcing LE policy for request: {policy_request_str}")
                if "access_sensitive_data" in policy_request_str:
                    response = b"LE Policy: Access Denied"
                else:
                    response = b"LE Policy: Access Granted"
            else:
                response = b"Error: Missing policy_request in payload"
        elif command == "STORE_ENCRYPTED_DATA":
            # Payload expects 'signal_id': str and 'encrypted_data': bytes
            signal_id = payload.get("signal_id")
            encrypted_data_bytes = payload.get("encrypted_data") # This is now raw bytes
            if signal_id and encrypted_data_bytes:
                # Ensure it's bytes for internal use
                if isinstance(encrypted_data_bytes, str):
                    # This case should ideally not happen with correct CommandSerializer, but added for robustness
                    encrypted_data_bytes = encrypted_data_bytes.encode('utf-8')
                print(f"Enclave sending encrypted data for {signal_id} to host storage.")
                response = f"Encrypted data for {signal_id} sent to host storage.".encode()
            else:
                response = b"Error: Missing signal_id or encrypted_data in payload"
        
        self.secure_channel.send(response)