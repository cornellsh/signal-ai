import pytest
from unittest.mock import MagicMock, patch
import os

from signal_assistant.enclave.kms import AttestationError, KeyManager
from signal_assistant.enclave.app import EnclaveApp
from signal_assistant.host.proxy import EnclaveProxy
from signal_assistant.enclave.secure_config import SecureConfig # For instantiating inside the test
from signal_assistant.enclave.bot.llm import LLMClient # Import LLMClient for patching


# --- Fixtures ---

@pytest.fixture
def mock_secure_channel_host_side():
    """Mocks the SecureChannel on the Host side."""
    mock_channel = MagicMock()
    mock_channel.establish.return_value = True
    # Simulate the Enclave sending back a response to PROVISION_EAK
    mock_channel.send.return_value = None # Host sends command
    mock_channel.receive.return_value = b"EAK Provisioned" # Enclave responds positively
    return mock_channel

@pytest.fixture
def mock_secure_channel_enclave_side():
    """Mocks the SecureChannel on the Enclave side."""
    mock_channel = MagicMock()
    mock_channel.establish.return_value = True
    # Simulate the Enclave receiving command
    mock_channel.receive.return_value = None 
    mock_channel.send.return_value = None # Enclave sends response
    return mock_channel

@pytest.fixture
def host_proxy_instance(mock_secure_channel_host_side):
    """Provides a Host EnclaveProxy instance with a mocked SecureChannel."""
    proxy = EnclaveProxy(MagicMock(), MagicMock()) # Pass dummy queues
    proxy.secure_channel = mock_secure_channel_host_side
    return proxy

@pytest.fixture
def enclave_app_instance(mock_secure_channel_enclave_side):
    """Provides an EnclaveApp instance with mocked SecureChannel."""
    # We will patch specific methods of this instance later
    app = EnclaveApp(MagicMock(), MagicMock())
    app.secure_channel = mock_secure_channel_enclave_side
    return app


# --- Test Cases ---

def test_host_refuses_eak_provisioning_on_failed_attestation(host_proxy_instance):
    """
    Scenario 1: Host-side attestation fails, so Host refuses to send EAK to Enclave.
    """
    test_eak = "fake-llm-api-key-123"
    attestation_status_from_host = False # Simulate host attestation failure
    
    success = host_proxy_instance.send_eak_to_enclave(test_eak, attestation_status_from_host)
    
    assert not success
    # Ensure send_command was NOT called, as it should be gated earlier
    host_proxy_instance.secure_channel.send.assert_not_called()


def test_enclave_blocks_sensitive_key_access_on_failed_internal_attestation(enclave_app_instance):
    """
    Scenario 2: Enclave's internal attestation fails.
    Sensitive key access (e.g., LLM API key) should be blocked.
    """
    # Simulate EnclaveApp's internal attestation failing
    with patch.object(enclave_app_instance, '_perform_attestation_verification', return_value=False):
        enclave_app_instance.start() # This will set attestation_is_verified to False

        assert not enclave_app_instance.attestation_is_verified

        # Mock LLMClient.generate_response to check what it receives
        # We need to ensure that the process_user_request method of the LLMPipeline (which lives inside enclave_app_instance)
        # gets called, and it in turn calls llm.generate_response, which will try to get the EAK.
        with patch.object(enclave_app_instance.llm_pipeline.llm, 'generate_response', autospec=True) as mock_generate_response:
            # We don't expect generate_response to be called successfully,
            # but rather to return an error from LLMPipeline due to AttestationError
            mock_generate_response.return_value = "Should not be called if attestation fails"

            user_message = "What is the capital of France?"
            sender_id = "test-user-123"

            # Call the LLMPipeline through EnclaveApp's process_user_request simulation
            response = enclave_app_instance.llm_pipeline.process_user_request(
                internal_user_id=sender_id,
                user_message=user_message,
                attestation_verified=enclave_app_instance.attestation_is_verified # Pass the failed attestation status
            )

            assert "Error: LLM access denied due to attestation failure." in response
            mock_generate_response.assert_called_once() # It should be called, but fail internally
            
            # Additional check: The arguments passed to generate_response should contain the
            # attestation_verified=False flag.
            args, kwargs = mock_generate_response.call_args
            assert kwargs.get('attestation_verified') is False


def test_enclave_allows_sensitive_key_access_on_successful_internal_attestation(enclave_app_instance):
    """
    Scenario 3: Enclave's internal attestation succeeds.
    Sensitive key access should be allowed.
    """
    # Simulate EnclaveApp's internal attestation succeeding
    with patch.object(enclave_app_instance, '_perform_attestation_verification', return_value=True):
        enclave_app_instance.start() # This will set attestation_is_verified to True

        assert enclave_app_instance.attestation_is_verified

        with patch.object(enclave_app_instance.llm_pipeline.llm, 'generate_response', autospec=True) as mock_generate_response:
            # For successful attestation, it should return a normal mock response
            mock_generate_response.return_value = "This is a mock AI response to: What is the capital of France?"

            user_message = "What is the capital of France?"
            sender_id = "test-user-456"

            response = enclave_app_instance.llm_pipeline.process_user_request(
                internal_user_id=sender_id,
                user_message=user_message,
                attestation_verified=enclave_app_instance.attestation_is_verified # Pass the successful attestation status
            )

            assert "Error: LLM access denied due to attestation failure." not in response
            assert "mock AI response to:" in response # Expect a normal mock LLM response
            mock_generate_response.assert_called_once()
            
            # Additional check: The arguments passed to generate_response should contain the
            # attestation_verified=True flag.
            args, kwargs = mock_generate_response.call_args
            assert kwargs.get('attestation_verified') is True