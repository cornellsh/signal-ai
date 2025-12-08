import json
import os
import logging
from typing import Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

class StateEncryptor:
    """
    Handles AES-256-GCM encryption of user state blobs.
    """
    def __init__(self, key: bytes):
        """
        key: 32-byte AES key.
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        self.aesgcm = AESGCM(key)

    def encrypt(self, state: Dict[str, Any]) -> bytes:
        """
        Serializes state to JSON and encrypts it.
        Returns: nonce + ciphertext + tag (handled by library)
        """
        try:
            data = json.dumps(state).encode('utf-8')
            nonce = os.urandom(12)
            ciphertext = self.aesgcm.encrypt(nonce, data, None)
            return nonce + ciphertext
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, blob: bytes) -> Dict[str, Any]:
        """
        Decrypts blob and returns state dict.
        """
        try:
            if not blob:
                return {}
            nonce = blob[:12]
            ciphertext = blob[12:]
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode('utf-8'))
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # If we cannot decrypt, it usually means the key changed or data is corrupted.
            raise
