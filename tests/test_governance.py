import pytest
import os
from unittest.mock import patch, MagicMock
from signal_assistant_enclave.app import EnclaveApp
from signal_assistant.config import EnclaveSettings

@pytest.fixture
def mock_queues():
    return MagicMock(), MagicMock()

    @patch("signal_assistant_enclave.app.EnclaveRegistryVerifier")
    def test_prod_env_rejects_mock_attestation(self, mock_verifier, mock_queues):
        """
        Verifies that EnclaveApp refuses to start if ENVIRONMENT=PROD
        and MOCK_ATTESTATION_FOR_TESTS_ONLY is set.
        """
        # Mock Registry Verification to succeed
        mock_verifier.return_value.verify.return_value = "active"
        
        with patch.dict(os.environ, {"MOCK_ATTESTATION_FOR_TESTS_ONLY": "1", "ENCLAVE_ENVIRONMENT": "PROD"}):
            with self.assertRaisesRegex(RuntimeError, "Security Violation: DangerousCapabilities in PROD"):
                app = EnclaveApp(*mock_queues)
                app.start()

    @patch("signal_assistant_enclave.app.SecureChannel")
    @patch("signal_assistant_enclave.app.EnclaveRegistryVerifier")
    def test_dev_env_allows_mock_attestation(self, mock_verifier, mock_secure_channel, mock_queues):
        """
        Verifies that EnclaveApp allows mock attestation in DEV.
        """
        # Mock Registry Verification to succeed
        mock_verifier.return_value.verify.return_value = "active"
        
        # Configure SecureChannel mock
        mock_channel_instance = mock_secure_channel.return_value
        mock_channel_instance.establish.return_value = False # Stop the loop immediately
        
        with patch.dict(os.environ, {"MOCK_ATTESTATION_FOR_TESTS_ONLY": "1", "ENCLAVE_ENVIRONMENT": "DEV"}):
            try:
                app = EnclaveApp(*mock_queues)
                app.start()
            except RuntimeError as e:
                self.fail(f"EnclaveApp.start() raised RuntimeError unexpectedly: {e}")

