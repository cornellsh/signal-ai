import logging
import base64

logger = logging.getLogger(__name__)

class NitroKMS:
    """
    Mock implementation of AWS Nitro Enclaves KMS / Sealing.
    In production, this would use the Nitro Secure Module (NSM) API.
    """
    def __init__(self):
        self.mock_key = b"DEV_KEY_DO_NOT_USE_IN_PROD"

    def seal(self, plaintext: bytes) -> bytes:
        """
        Seals data to the Enclave's identity (PCRs).
        """
        logger.info("Sealing data (MOCKED)...")
        # In dev, we just return it, maybe base64 encoded to look 'encrypted'
        return base64.b64encode(plaintext)

    def unseal(self, ciphertext: bytes) -> bytes:
        """
        Unseals data if the Enclave's identity matches.
        """
        logger.info("Unsealing data (MOCKED)...")
        try:
            return base64.b64decode(ciphertext)
        except Exception:
            logger.error("Failed to unseal data")
            raise ValueError("Unseal failed")

    def get_attestation_doc(self) -> bytes:
        """
        Returns the signed attestation document from the hypervisor.
        """
        return b"MOCK_ATTESTATION_DOC"
