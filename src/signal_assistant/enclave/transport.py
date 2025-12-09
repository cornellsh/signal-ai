# src/signal_assistant/enclave/transport.py
import time
from cryptography.fernet import Fernet
from signal_assistant.enclave.secure_config import SHARED_SYMMETRIC_KEY

class SecureChannel:
    """
    A basic secure channel for communication within the enclave.
    This is a placeholder and will be expanded with actual cryptographic operations.
    """
    def __init__(self, message_queue_in, message_queue_out):
        self.message_queue_in = message_queue_in
        self.message_queue_out = message_queue_out
        self.cipher_suite = Fernet(SHARED_SYMMETRIC_KEY)

    def send(self, plaintext_data: bytes) -> None:
        """
        Encrypts and sends data securely.
        """
        encrypted_data = self.cipher_suite.encrypt(plaintext_data)
        print(f"Enclave SecureChannel sending (encrypted): {encrypted_data}")
        self.message_queue_out.append(encrypted_data)

    def receive(self, timeout=5) -> bytes | None:
        """
        Receives and decrypts data securely.
        Includes a timeout to prevent indefinite blocking.
        """
        start_time = time.time()
        while not self.message_queue_in:
            if time.time() - start_time > timeout:
                print("Enclave SecureChannel receive timed out.")
                return None
            time.sleep(0.01) # Small delay to prevent busy-waiting
        
        encrypted_data = self.message_queue_in.pop(0)
        print(f"Enclave SecureChannel received (encrypted): {encrypted_data}")
        
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data
        except Exception as e:
            print(f"Enclave SecureChannel decryption failed: {e}")
            return None

    def establish(self) -> bool:
        """
        Establishes a secure channel. Placeholder for actual implementation.
        """
        print("Enclave SecureChannel established.")
        return True