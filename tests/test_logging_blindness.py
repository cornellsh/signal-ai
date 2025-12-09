import pytest
import logging
from unittest.mock import MagicMock, patch
import io
import re
import json

# Assume these modules exist and are the ones using the new logging interfaces
from signal_assistant.host.logging_client import LoggingClient
from signal_assistant.enclave.secure_logging import info as secure_info, error as secure_error
from signal_assistant.host.proxy import EnclaveProxy # Assuming EnclaveProxy is the Host's interface to Enclave
from signal_assistant.enclave.app import EnclaveApp # Assuming EnclaveApp is the main Enclave logic
from signal_assistant.enclave.serialization import CommandSerializer # For serializing/deserializing commands

# --- Test Data ---
SYNTHETIC_SIGNAL_ID = "signal-id-12345"
SYNTHETIC_INTERNAL_USER_ID = "internal-user-abcde" # Simulated internal user ID for enclave
SYNTHETIC_PII_MESSAGE = "My name is John Doe, my email is john.doe@example.com and my phone is 555-123-4567. My secret is XYZ."
SYNTHETIC_NON_PII_MESSAGE = "Hello, assistant! Please tell me about the weather."
EXPECTED_REDACTED_MESSAGE_PARTIAL_NAME = "My name is [REDACTED], my email is [REDACTED] and my phone is [REDACTED]. My secret is XYZ."


# --- Fixtures ---

@pytest.fixture
def host_logger_capture():
    """
    Fixture to capture logs from the Host's LoggingClient.
    Configures a dedicated handler for the LoggingClient's logger.
    """
    log_stream = io.StringIO()
    # Get the specific logger instance used by LoggingClient in proxy.py and transport.py
    host_client_logger = logging.getLogger("HostApp") 
    host_client_logger.propagate = False # Prevent logs from going to root logger

    # Ensure no other handlers interfere
    if host_client_logger.handlers:
        for handler in host_client_logger.handlers:
            host_client_logger.removeHandler(handler)

    handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    host_client_logger.addHandler(handler)
    host_client_logger.setLevel(logging.DEBUG) # Capture all levels for testing

    # Instantiate the LoggingClient to ensure the logger is setup
    # This is important to ensure the host_logger instance in proxy/transport is initialized
    _ = LoggingClient("HostApp") 

    yield log_stream

    # Clean up: remove handler and reset level
    host_client_logger.removeHandler(handler)
    host_client_logger.setLevel(logging.NOTSET)
    host_client_logger.propagate = True


@pytest.fixture
def mock_secure_channel_host_side():
    """Mocks the SecureChannel on the Host side."""
    mock_channel = MagicMock()
    # Mock establish to return True for successful establishment
    mock_channel.establish.return_value = True
    return mock_channel

@pytest.fixture
def mock_secure_channel_enclave_side():
    """Mocks the SecureChannel on the Enclave side."""
    mock_channel = MagicMock()
    # Mock establish to return True for successful establishment
    mock_channel.establish.return_value = True
    return mock_channel


@pytest.fixture
def mock_enclave_app(mock_secure_channel_enclave_side):
    """
    Mocks the EnclaveApp instance to control its internal behavior,
    especially for simulating message processing and sanitization.
    """
    # Create the EnclaveApp instance outside the patch context first
    enclave_app = EnclaveApp(MagicMock(), MagicMock()) # Pass dummy queues
    
    # Patch the *instance's* signal_lib and PIISanitizer
    with patch.object(enclave_app, 'signal_lib') as mock_signal_lib_instance:
        # Mock decrypt_envelope to return synthetic sender and message (as string)
        mock_signal_lib_instance.decrypt_envelope.return_value = (SYNTHETIC_SIGNAL_ID, SYNTHETIC_PII_MESSAGE)
        
        with patch('signal_assistant.enclave.app.PIISanitizer') as MockPIISanitizer:
            # When PIISanitizer.sanitize is called, it should return our mocked value
            MockPIISanitizer.sanitize.return_value = EXPECTED_REDACTED_MESSAGE_PARTIAL_NAME

            # Replace the EnclaveApp's secure_channel with our mock
            enclave_app.secure_channel = mock_secure_channel_enclave_side

            yield enclave_app

@pytest.fixture
def host_proxy_instance(mock_secure_channel_host_side):
    """Provides a Host EnclaveProxy instance with a mocked SecureChannel."""
    proxy = EnclaveProxy(MagicMock(), MagicMock()) # Pass dummy queues
    proxy.secure_channel = mock_secure_channel_host_side
    return proxy


# --- Helper to simulate the full flow ---
def simulate_full_message_flow(host_proxy: EnclaveProxy, enclave_app: EnclaveApp, 
                                signal_id: str, message: str, 
                                host_logger_output: io.StringIO):
    """
    Simulates the full message flow from Host (receiving user input) to Enclave and back.
    The mock_enclave_app is used to process the command sent by host_proxy.
    """
    # Host serializes and sends command to Enclave
    # In a real scenario, host_proxy.send_command would send bytes to a queue
    # which enclave_app.secure_channel.receive would pick up.
    # Here, we directly call enclave_app._process_command with simulated serialized data.

    # 1. Host side: Prepare command and payload
    command_name = "INBOUND_MESSAGE"
    payload_data = {
        # EnclaveApp expects encrypted_envelope for INBOUND_MESSAGE
        # We simulate this as the raw message for testing PII blindness in logs
        "encrypted_envelope": message.encode('utf-8') 
    }
    
    # This is what EnclaveProxy.send_command *would* do
    message_to_enclave_bytes = CommandSerializer.serialize(command_name, payload_data)
    
    # Intercept the send and directly feed it to the Enclave's processing method.
    # This bypasses the actual SecureChannel transport but simulates the data flow.
    host_proxy.secure_channel.send.return_value = None # No actual send needed
    host_proxy.secure_channel.receive.return_value = b"Enclave processed: (simulated response)"

    # Simulate the host sending the command (which internally logs via logging_client)
    host_proxy.send_command(command_name, payload_data)
    
    # Simulate the Enclave receiving and processing the command
    enclave_app._process_command(message_to_enclave_bytes)

    # Note: EnclaveApp sends response back via its secure_channel.send,
    # which the Host's secure_channel.receive would then pick up.
    # For this test, we are primarily interested in the Host's logs *before*
    # the final response, but also the overall process.
    
    # We return the captured logs for assertions
    return host_logger_output.getvalue()


# --- Test Cases ---

def test_host_logging_blindness_with_pii(host_logger_capture, host_proxy_instance, mock_enclave_app):
    """
    Tests that the Host does not log plaintext PII or raw SignalID when processing a message
    that originates with PII and a SignalID.
    """
    # Simulate the full flow and get captured Host logs
    captured_logs = simulate_full_message_flow(
        host_proxy_instance, 
        mock_enclave_app, 
        SYNTHETIC_SIGNAL_ID, 
        SYNTHETIC_PII_MESSAGE, 
        host_logger_capture
    )

    # Assertions:
    # 1. No plaintext PII should appear in Host logs
    assert SYNTHETIC_PII_MESSAGE not in captured_logs
    assert "John Doe" not in captured_logs
    assert "john.doe@example.com" not in captured_logs
    assert "555-123-4567" not in captured_logs

    # 2. Raw SignalID should not appear in Host logs
    # The host proxy logs payload_keys, but not the values.
    assert SYNTHETIC_SIGNAL_ID not in captured_logs
    
    # Check for direct logging of 'signal_id' keyword in host logs
    assert "signal_id" not in captured_logs.lower() # To catch even if case changes

    # 3. Expect to see the Host logging *something* related to processing, but securely.
    assert "Host SecureChannel established." in captured_logs
    assert "Host EnclaveProxy sending command: INBOUND_MESSAGE" in captured_logs
    assert "Host EnclaveProxy received response." in captured_logs
    
    # The mock enclave returns a simulated response that might contain a "processed" message
    # but it should not contain the original PII.
    assert EXPECTED_REDACTED_MESSAGE_PARTIAL_NAME not in captured_logs # Host shouldn't log the sanitized content directly either

def test_host_logging_blindness_with_non_pii(host_logger_capture, host_proxy_instance, mock_enclave_app):
    """
    Tests that the Host logs non-PII messages without issues and no false positives.
    SignalID should still not be logged explicitly by the Host.
    """
    # Simulate the full flow with a non-PII message
    captured_logs = simulate_full_message_flow(
        host_proxy_instance, 
        mock_enclave_app, 
        "non-pii-signal-id-1", 
        SYNTHETIC_NON_PII_MESSAGE, 
        host_logger_capture
    )

    # Assertions:
    assert SYNTHETIC_NON_PII_MESSAGE not in captured_logs # Host should not log the raw message content
    assert "non-pii-signal-id-1" not in captured_logs # SignalID should still not be logged
    assert "signal_id" not in captured_logs.lower()

    assert "Host SecureChannel established." in captured_logs
    assert "Host EnclaveProxy sending command: INBOUND_MESSAGE" in captured_logs
    assert "Host EnclaveProxy received response." in captured_logs
