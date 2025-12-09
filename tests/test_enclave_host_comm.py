# tests/test_enclave_host_comm.py
import pytest
import threading
import time
import copy # For deepcopying messages to simulate tampering

from signal_assistant.host.proxy import EnclaveProxy
from signal_assistant.enclave.app import EnclaveApp
from signal_assistant.enclave.transport import SecureChannel as EnclaveSecureChannel
from signal_assistant.host.transport import SecureChannel as HostSecureChannel
from signal_assistant.enclave.serialization import CommandSerializer # Import for testing serialization directly
from signal_assistant.enclave.signal_lib import SignalLib # Import for direct testing of SignalLib encryption

# These lists will act as our simulated message queues
host_to_enclave_queue = []
enclave_to_host_queue = []

# EnclaveApp instance and its thread
enclave_app_instance = None
enclave_thread_instance = None

def run_enclave_app_in_thread(app):
    app.start()

@pytest.fixture(scope="module", autouse=True)
def setup_enclave_app_module():
    global enclave_app_instance, enclave_thread_instance
    print("\nSetting up EnclaveApp for module...")
    
    host_to_enclave_queue.clear()
    enclave_to_host_queue.clear()

    enclave_app_instance = EnclaveApp(host_to_enclave_queue, enclave_to_host_queue)
    enclave_thread_instance = threading.Thread(target=run_enclave_app_in_thread, args=(enclave_app_instance,))
    enclave_thread_instance.daemon = True
    enclave_thread_instance.start()
    time.sleep(1)  # Give enclave a moment to start
    yield
    print("Tearing down EnclaveApp for module...")
    if enclave_app_instance:
        enclave_app_instance.stop()
    if enclave_thread_instance and enclave_thread_instance.is_alive():
        enclave_thread_instance.join(timeout=2)

# --- Existing Tests ---

def test_enclave_status_command():
    print("\nRunning test_enclave_status_command...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    status = proxy.get_enclave_status()
    assert status == "Enclave Status: Enclave is Operational"

def test_unknown_command():
    print("\nRunning test_unknown_command...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    payload = {"data": "some_data"}
    unknown_response = proxy.send_command("UNKNOWN_CMD", payload)
    assert unknown_response.decode() == "Unknown Command"

def test_inbound_message_processing():
    print("\nRunning test_inbound_message_processing...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    
    # SignalLib now expects and returns plaintext bytes
    sender_id_mock = "mock_sender_id" # This is the hardcoded sender_id in SignalLib.encrypt_message
    plaintext_message = "Hello from mock sender!"
    # The payload will be the *plaintext* envelope bytes from an external source
    # For this test, we simulate the external source generating this "envelope"
    mock_envelope_bytes = f"{sender_id_mock}:{plaintext_message}".encode('utf-8')

    payload = {"encrypted_envelope": mock_envelope_bytes} # Renamed for clarity, it's now mock raw bytes
    response = proxy.send_command("INBOUND_MESSAGE", payload)
    assert f"Message processed from {sender_id_mock}" in response.decode()


def test_outbound_message_processing():
    print("\nRunning test_outbound_message_processing...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    recipient = "+1234567890"
    plaintext = "This is a secret message."
    payload = {"recipient_id": recipient, "plaintext": plaintext}
    # SignalLib in EnclaveApp will handle encryption internally
    response = proxy.send_command("OUTBOUND_MESSAGE", payload)
    assert f"Outbound message encrypted for {recipient}" in response.decode()

def test_law_enforcement_policy_check():
    print("\nRunning test_law_enforcement_policy_check...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    denied_request = "access_sensitive_data_user_123"
    payload_denied = {"policy_request": denied_request}
    response_denied = proxy.send_command("CHECK_LE_POLICY", payload_denied)
    assert "LE Policy: Access Denied" in response_denied.decode()

    granted_request = "check_public_record_user_456"
    payload_granted = {"policy_request": granted_request}
    response_granted = proxy.send_command("CHECK_LE_POLICY", payload_granted)
    assert "LE Policy: Access Granted" in response_granted.decode()

def test_secure_logging_and_storage():
    print("\nRunning test_secure_logging_and_storage...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    test_signal_id = "user123_encrypted_state"
    test_encrypted_data = b"encrypted_blob_for_user123" # This is now raw bytes, will be base64 encoded by serializer
    payload = {"signal_id": test_signal_id, "encrypted_data": test_encrypted_data}
    response = proxy.send_command("STORE_ENCRYPTED_DATA", payload)
    assert f"Encrypted data for {test_signal_id} sent to host storage." in response.decode()

# --- New Test Cases for Secure Channel ---

def test_secure_channel_end_to_end_encryption():
    print("\nRunning test_secure_channel_end_to_end_encryption...")
    # Create isolated queues for this specific test
    test_host_to_enclave_q = []
    test_enclave_to_host_q = []

    host_channel = HostSecureChannel(test_enclave_to_host_q, test_host_to_enclave_q)
    enclave_channel = EnclaveSecureChannel(test_host_to_enclave_q, test_enclave_to_host_q)

    # Establish channels (just prints for now)
    host_channel.establish()
    enclave_channel.establish()

    original_message = b"This is a secret message from host to enclave."
    host_channel.send(original_message)

    # Enclave receives and decrypts
    received_message_by_enclave = enclave_channel.receive()
    assert received_message_by_enclave == original_message

    original_response = b"Enclave's secret reply."
    enclave_channel.send(original_response)

    # Host receives and decrypts
    received_response_by_host = host_channel.receive()
    assert received_response_by_host == original_response

def test_secure_channel_tampering_detection():
    print("\nRunning test_secure_channel_tampering_detection...")
    test_host_to_enclave_q = []
    test_enclave_to_host_q = []

    host_channel = HostSecureChannel(test_enclave_to_host_q, test_host_to_enclave_q)
    enclave_channel = EnclaveSecureChannel(test_host_to_enclave_q, test_enclave_to_host_q)

    host_channel.establish()
    enclave_channel.establish()

    original_message = b"Message to be tampered with."
    host_channel.send(original_message)

    # Simulate tampering: get the encrypted message from the queue and alter it
    encrypted_message = test_host_to_enclave_q.pop(0)
    tampered_message = bytearray(encrypted_message)
    tampered_message[0] = (tampered_message[0] + 1) % 256 # Simple byte flip
    
    # Put the tampered message back into the queue for the enclave to receive
    test_host_to_enclave_q.append(bytes(tampered_message))

    # Enclave attempts to receive and decrypt the tampered message
    # It should return None due to decryption failure (MAC check failing)
    received_message_by_enclave = enclave_channel.receive()
    assert received_message_by_enclave is None

def test_command_serialization_tampering_detection():
    print("\nRunning test_command_serialization_tampering_detection...")
    original_command = "TEST_COMMAND"
    original_payload = {"key": "value", "binary_data": b"some_bytes"}
    
    serialized_data = CommandSerializer.serialize(original_command, original_payload)
    
    # Simulate tampering by altering a byte in the serialized data
    tampered_data = bytearray(serialized_data)
    tampered_data[len(tampered_data) // 2] = (tampered_data[len(tampered_data) // 2] + 1) % 256
    
    # Attempt to deserialize the tampered data - should fail or raise an error
    # Because Fernet (used by SecureChannel) also includes a MAC, tampering with the encrypted
    # command directly will cause a decryption failure before deserialization.
    # So, we expect SecureChannel.receive to return None.
    
    test_host_to_enclave_q = []
    test_enclave_to_host_q = []
    host_channel = HostSecureChannel(test_enclave_to_host_q, test_host_to_enclave_q)
    enclave_channel = EnclaveSecureChannel(test_host_to_enclave_q, test_enclave_to_host_q)

    host_channel.establish()
    enclave_channel.establish()
    
    # Send the tampered data through the *encrypted* channel
    # First, encrypt the ORIGINAL data.
    original_encrypted_command = host_channel.cipher_suite.encrypt(serialized_data)
    
    # NOW tamper with the ENCRYPTED data
    tampered_encrypted_command = bytearray(original_encrypted_command)
    tampered_encrypted_command[0] = (tampered_encrypted_command[0] + 1) % 256
    
    test_host_to_enclave_q.append(bytes(tampered_encrypted_command))
    
    # Enclave attempts to receive and decrypt
    received_plaintext = enclave_channel.receive()
    assert received_plaintext is None