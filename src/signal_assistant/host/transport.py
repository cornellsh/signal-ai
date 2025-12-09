import json
from queue import Queue
from typing import Any, Dict, Optional
import time

from cryptography.fernet import Fernet

from signal_assistant.host.logging_client import LoggingClient

# Instantiate the logger once per module
host_logger = LoggingClient("HostApp")

class SecureChannel:
    """
    Simulates a secure communication channel between the Host and the Enclave.
    Messages are encrypted/decrypted using Fernet for confidentiality.
    """
    def __init__(self, inbound_queue: Queue, outbound_queue: Queue):
        self.inbound_queue = inbound_queue
        self.outbound_queue = outbound_queue
        self.fernet = self._generate_or_load_key()

    def _generate_or_load_key(self) -> Fernet:
        """
        Generates a new Fernet key or loads an existing one.
        In a real scenario, this key management would be much more secure
        and involve KMS/attestation.
        """
        # For simulation, we generate a new key each time.
        # In production, this would be loaded securely.
        return Fernet(Fernet.generate_key())

    def establish(self) -> bool:
        """
        Establishes a secure channel. Placeholder for actual implementation.
        """
        host_logger.info(None, "Host SecureChannel established.")
        return True

    def send(self, data: bytes):
        """
        Encrypts data and sends it to the outbound queue (towards Enclave).
        """
        encrypted_data = self.fernet.encrypt(data)
        host_logger.debug(None, "Host SecureChannel sending (encrypted data)", metadata={"data_len": len(encrypted_data)})
        if hasattr(self.outbound_queue, 'put'):
            self.outbound_queue.put(encrypted_data)
        else:
            self.outbound_queue.append(encrypted_data)

    def receive(self, timeout: int = 5) -> Optional[bytes]:
        """
        Receives encrypted data from the inbound queue (from Enclave) and decrypts it.
        """
        try:
            encrypted_data = None
            if hasattr(self.inbound_queue, 'get'):
                encrypted_data = self.inbound_queue.get(timeout=timeout)
            else:
                start_time = time.time()
                while not self.inbound_queue:
                    if time.time() - start_time > timeout:
                        host_logger.warning(None, "Host SecureChannel receive timed out (List).")
                        return None
                    time.sleep(0.01)
                encrypted_data = self.inbound_queue.pop(0)

            host_logger.debug(None, "Host SecureChannel received (encrypted data)", metadata={"data_len": len(encrypted_data)})
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return decrypted_data
        except Exception as e:
            host_logger.warning(None, "Host SecureChannel receive timed out.")
            host_logger.error(None, f"Host SecureChannel decryption failed: {e}", metadata={"exception": str(e)})
            return None
