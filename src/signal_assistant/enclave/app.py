# src/signal_assistant/enclave/app.py

from signal_assistant.enclave.transport import SecureChannel
from signal_assistant.enclave.signal_lib import SignalLib
from signal_assistant.enclave.privacy_core.sanitizer import PIISanitizer

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

    def _process_command(self, message: bytes):
        """
        Processes a received command.
        """
        print(f"EnclaveApp processing command: {message}")
        command, payload_str = message.decode().split(":", 1)
        payload_bytes = payload_str.encode()

        response = b"Unknown Command"
        if command == "GET_STATUS":
            response = b"Enclave is Operational"
        elif command == "INBOUND_MESSAGE":
            # Simulate decryption
            sender, decrypted_message = self.signal_lib.decrypt_envelope(payload_bytes)
            if sender and decrypted_message:
                sanitized_message = PIISanitizer.sanitize(decrypted_message)
                print(f"Decrypted and Sanitized message from {sender}: {sanitized_message}")
                response = f"Message processed from {sender}".encode()
            else:
                response = b"Failed to decrypt or process message"
        elif command == "OUTBOUND_MESSAGE":
            # Payload format: "recipient_id:plaintext_message"
            try:
                recipient_id, plaintext = payload_str.split(":", 1)
                encrypted_envelope = self.signal_lib.encrypt_message(recipient_id, plaintext)
                print(f"Encrypted message for {recipient_id}: {encrypted_envelope}")
                response = f"Outbound message encrypted for {recipient_id}".encode()
            except ValueError:
                response = b"Invalid OUTBOUND_MESSAGE format"
        elif command == "CHECK_LE_POLICY":
            # Simulate a policy check based on payload
            policy_request = payload_str
            print(f"Enforcing LE policy for request: {policy_request}")
            if "access_sensitive_data" in policy_request:
                response = b"LE Policy: Access Denied"
            else:
                response = b"LE Policy: Access Granted"
        elif command == "STORE_ENCRYPTED_DATA":
            try:
                signal_id, encrypted_data_str = payload_str.split(":", 1)
                encrypted_data = encrypted_data_str.encode()
                print(f"Enclave sending encrypted data for {signal_id} to host storage.")
                # In a real scenario, this would involve sending this data through the secure channel
                # to the host, which would then use BlobStore to save it.
                response = f"Encrypted data for {signal_id} sent to host storage.".encode()
            except ValueError:
                response = b"Invalid STORE_ENCRYPTED_DATA format"
        
        self.secure_channel.send(response)
