import pytest
from unittest.mock import MagicMock, patch
import os

from signal_assistant_enclave.kms import AttestationError, KeyManager
from signal_assistant_enclave.app import EnclaveApp
from signal_assistant.host.proxy import EnclaveProxy
from signal_assistant_enclave.secure_config import SecureConfig # For instantiating inside the test
from signal_assistant_enclave.bot.llm import LLMClient # Import LLMClient for patching
from signal_assistant_enclave.privacy_core.core import IdentityMappingService # Added import


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


@patch('signal_assistant_enclave.bot.orchestrator.LLMPipeline')


@patch('signal_assistant_enclave.privacy_core.core.IdentityMappingService')


@patch('signal_assistant_enclave.kms.KeyManager')


def test_enclave_blocks_sensitive_key_access_on_failed_internal_attestation(mock_key_manager_class, mock_identity_service_class, mock_llm_pipeline_class, enclave_app_instance):


        """


        Scenario 2: Enclave's internal attestation fails.


        Sensitive key access (e.g., LLM API key) should be blocked.


        """


        # Configure mock KeyManager to simulate KMS restriction


        mock_key_manager_instance = mock_key_manager_class.return_value


        def kms_side_effect(key_id, attestation_verified):


            if key_id.startswith("LLM_API_KEY_"):


                raise AttestationError("KMS restriction for sensitive LLM key.")


            elif key_id == "ESSK_IDENTITY_MAPPING":


                return os.urandom(32) # Allow IdentityMappingService to initialize


            return os.urandom(32) # Default for other non-sensitive keys


        mock_key_manager_instance.get_key.side_effect = kms_side_effect


        mock_key_manager_instance.generate_key.side_effect = kms_side_effect


        mock_key_manager_instance.set_registry_status("verification_failed") # Simulate failed registry





    # Configure mock IdentityMappingService to be available


    mock_identity_service_instance = mock_identity_service_class.return_value


    mock_identity_service_instance.map_signal_id_to_internal_id.return_value = "internal-user-mock"


    mock_identity_service_instance.handle_le_request.return_value = MagicMock(status="GRANTED")





    # Configure mock LLMPipeline to return an error when its process_user_request is called (if it were initialized)


    mock_llm_pipeline_instance = mock_llm_pipeline_class.return_value


    mock_llm_pipeline_instance.process_user_request.return_value = "Error: LLM access denied due to attestation failure."





    # Prevent EnclaveApp.start() from entering the infinite loop


    enclave_app_instance.secure_channel.establish.return_value = False





    with patch.object(enclave_app_instance, '_perform_attestation_verification', return_value=False):


        enclave_app_instance.start() # This will set attestation_is_verified to False and llm_pipeline to None





        assert not enclave_app_instance.attestation_is_verified


        assert enclave_app_instance.llm_pipeline is None





        with patch.object(enclave_app_instance.signal_lib, 'decrypt_envelope', return_value=("mock_sender", "mock_message")):


            # Simulate an INBOUND_MESSAGE command


            mock_command_bytes = b'{"command": "INBOUND_MESSAGE", "payload": {"encrypted_envelope": "dummy_encrypted_envelope"}}'





            # Mock SecureChannel's receive to return the command and send to capture the response


            with patch.object(enclave_app_instance.secure_channel, 'receive', return_value=mock_command_bytes):


                with patch.object(enclave_app_instance.secure_channel, 'send') as mock_send:


                    enclave_app_instance._process_command(mock_command_bytes)


                    mock_send.assert_called_once_with(b"Error: LLM Pipeline Unavailable")


@patch('signal_assistant_enclave.bot.orchestrator.LLMPipeline')
@patch('signal_assistant_enclave.privacy_core.core.IdentityMappingService')
@patch('signal_assistant_enclave.kms.KeyManager')
def test_enclave_allows_sensitive_key_access_on_successful_internal_attestation(mock_key_manager_class, mock_identity_service_class, mock_llm_pipeline_class, enclave_app_instance):
    """
    Scenario 3: Enclave's internal attestation succeeds.
    Sensitive key access should be allowed.
    """
    # Configure mock KeyManager to simulate normal access
    mock_key_manager_instance = mock_key_manager_class.return_value
    mock_key_manager_instance.get_key.return_value = b'mock_llm_api_key_123456789012345678901234567890'
    mock_key_manager_instance.generate_key.return_value = b'mock_new_key_123456789012345678901234567890'
    mock_key_manager_instance.set_registry_status("active") # Simulate active registry

    # Configure mock LLMPipeline to return a successful response
    mock_llm_pipeline_instance = mock_llm_pipeline_class.return_value
    mock_llm_pipeline_instance.process_user_request.return_value = "This is a mock AI response to: What is the capital of France?"
    
    # Configure mock IdentityMappingService to be available
    mock_identity_service_instance = mock_identity_service_class.return_value
    mock_identity_service_instance.map_signal_id_to_internal_id.return_value = "internal-user-mock"
    mock_identity_service_instance.handle_le_request.return_value = MagicMock(status="GRANTED")


    # Prevent EnclaveApp.start() from entering the infinite loop
    enclave_app_instance.secure_channel.establish.return_value = False

    with patch.object(enclave_app_instance, '_perform_attestation_verification', return_value=True):
        enclave_app_instance.start() # This will set attestation_is_verified to True

        assert enclave_app_instance.attestation_is_verified
        assert enclave_app_instance.llm_pipeline is not None # LLMPipeline should be initialized

        with patch.object(enclave_app_instance.signal_lib, 'decrypt_envelope', return_value=("mock_sender", "mock_message")):
            # Simulate an INBOUND_MESSAGE command
            mock_command_bytes = b'{"command": "INBOUND_MESSAGE", "payload": {"encrypted_envelope": "dummy_encrypted_envelope"}}'

            # Mock SecureChannel's receive to return the command and send to capture the response
            with patch.object(enclave_app_instance.secure_channel, 'receive', return_value=mock_command_bytes):
                with patch.object(enclave_app_instance.secure_channel, 'send') as mock_send:
                    enclave_app_instance._process_command(mock_command_bytes)
                    mock_send.assert_called_once()
                    sent_response = mock_send.call_args[0][0].decode()
                    assert "Message processed from" in sent_response