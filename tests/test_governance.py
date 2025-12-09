import pytest
import os
from unittest.mock import patch, MagicMock
from signal_assistant.enclave.app import EnclaveApp
from signal_assistant.config import EnclaveSettings

@pytest.fixture
def mock_queues():
    return MagicMock(), MagicMock()

def test_prod_env_rejects_mock_attestation(mock_queues):
    """
    Verifies that EnclaveApp refuses to start if ENVIRONMENT=PROD
    and MOCK_ATTESTATION_FOR_TESTS_ONLY is set.
    """
    with patch.dict(os.environ, {"MOCK_ATTESTATION_FOR_TESTS_ONLY": "1"}):
        with patch("signal_assistant.enclave.app.enclave_settings") as mock_settings:
            mock_settings.environment = "PROD"
            
            app = EnclaveApp(*mock_queues)
            
            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Security Violation: Mock Attestation in PROD"):
                app.start()

def test_dev_env_allows_mock_attestation(mock_queues):
    """
    Verifies that EnclaveApp allows mock attestation in DEV.
    """
    with patch.dict(os.environ, {"MOCK_ATTESTATION_FOR_TESTS_ONLY": "1"}):
        with patch("signal_assistant.enclave.app.enclave_settings") as mock_settings:
            mock_settings.environment = "DEV"
            
            app = EnclaveApp(*mock_queues)
            
            # Mock secure_channel.establish to return False so loop doesn't run
            app.secure_channel.establish = MagicMock(return_value=False)
            
            # Should NOT raise
            try:
                app.start()
            except RuntimeError:
                pytest.fail("Should not raise RuntimeError in DEV")

