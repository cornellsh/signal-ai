# tests/test_enclave_host_comm.py
import pytest
import threading
import time
import copy # For deepcopying messages to simulate tampering
import os
import re
from unittest.mock import patch, MagicMock

from signal_assistant.host.proxy import EnclaveProxy
from signal_assistant_enclave.app import EnclaveApp
from signal_assistant_enclave.transport import SecureChannel as EnclaveSecureChannel
from signal_assistant.host.transport import SecureChannel as HostSecureChannel
from signal_assistant_enclave.serialization import CommandSerializer # Import for testing serialization directly
from signal_assistant_enclave.signal_lib import SignalLib # Import for direct testing of SignalLib encryption
from signal_assistant_enclave.kms import KeyManager
from signal_assistant_enclave.privacy_core.core import IdentityMappingService

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
    
    # Enable mock attestation for the module-scoped enclave instance
    os.environ["MOCK_ATTESTATION_FOR_TESTS_ONLY"] = "1"
    
    host_to_enclave_queue.clear()
    enclave_to_host_queue.clear()

    enclave_app_instance = EnclaveApp(host_to_enclave_queue, enclave_to_host_queue)
    
    # Patch the key_manager for the module-level enclave_app_instance
    with patch.object(enclave_app_instance, 'key_manager', spec=KeyManager) as mock_key_manager:
        mock_key_manager.get_key.return_value = os.urandom(32) # Must be 32 bytes for AES-256
        mock_key_manager.generate_key.return_value = os.urandom(32) # Must be 32 bytes for AES-256
        mock_key_manager.set_registry_status("active")
        
        # Also mock IdentityMappingService to be available
        with patch.object(enclave_app_instance, 'identity_service', spec=IdentityMappingService) as mock_identity_service:
            mock_identity_service.map_signal_id_to_internal_id.return_value = "internal-user-mock"
            mock_identity_service.handle_le_request.return_value = MagicMock(status="DENIED") # Default LE denied
            
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
        
        # Cleanup env var
        if "MOCK_ATTESTATION_FOR_TESTS_ONLY" in os.environ:
            del os.environ["MOCK_ATTESTATION_FOR_TESTS_ONLY"]

# --- Existing Tests ---

def test_enclave_status_command():
    print("\nRunning test_enclave_status_command...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    # Sync key
    proxy.secure_channel.fernet = enclave_app_instance.secure_channel.cipher_suite
    
    status = proxy.get_enclave_status()
    assert status == "Enclave Status: Enclave is Operational"

def test_unknown_command():
    print("\nRunning test_unknown_command...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    proxy.secure_channel.fernet = enclave_app_instance.secure_channel.cipher_suite
    
    payload = {"data": "some_data"}
    unknown_response = proxy.send_command("UNKNOWN_CMD", payload)
    assert unknown_response.decode() == "Unknown Command"

def test_inbound_message_processing():
    print("\nRunning test_inbound_message_processing...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    proxy.secure_channel.fernet = enclave_app_instance.secure_channel.cipher_suite
    
    # SignalLib now expects and returns plaintext bytes
    sender_id_mock = "mock_sender_id" # This is the hardcoded sender_id in SignalLib.encrypt_message
    plaintext_message = "Hello from mock sender!"
    # The payload will be the *plaintext* envelope bytes from an external source
    # For this test, we simulate the external source generating this "envelope"
    mock_envelope_bytes = f"{sender_id_mock}:{plaintext_message}".encode('utf-8')

    payload = {"encrypted_envelope": mock_envelope_bytes} # Renamed for clarity, it's now mock raw bytes
    response = proxy.send_command("INBOUND_MESSAGE", payload)
    # The response should contain an Internal User ID (UUID), NOT the SignalID
    assert "Message processed from" in response.decode()
    assert sender_id_mock not in response.decode() # SignalID must not be returned


def test_outbound_message_processing():
    print("\nRunning test_outbound_message_processing...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    proxy.secure_channel.fernet = enclave_app_instance.secure_channel.cipher_suite
    
    recipient = "+1234567890"
    plaintext = "This is a secret message."
    payload = {"recipient_id": recipient, "plaintext": plaintext}
    # SignalLib in EnclaveApp will handle encryption internally
    response = proxy.send_command("OUTBOUND_MESSAGE", payload)
    assert f"Outbound message encrypted for {recipient}" in response.decode()

def test_law_enforcement_policy_check():
    print("\nRunning test_law_enforcement_policy_check...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    proxy.secure_channel.fernet = enclave_app_instance.secure_channel.cipher_suite
    
    denied_request = "access_sensitive_data_user_123"
    payload_denied = {"policy_request": denied_request}
    response_denied = proxy.send_command("CHECK_LE_POLICY", payload_denied)
    assert "LE Policy: Access Denied" in response_denied.decode()

    granted_request = "check_public_record_user_456"
    payload_granted = {"policy_request": granted_request}
    response_granted = proxy.send_command("CHECK_LE_POLICY", payload_granted)
    # Default is now DENY because auth context is hardcoded to False in EnclaveApp
    assert "LE Policy: Access Denied" in response_granted.decode()

def test_secure_logging_and_storage():
    print("\nRunning test_secure_logging_and_storage...")
    proxy = EnclaveProxy(host_to_enclave_queue, enclave_to_host_queue)
    proxy.secure_channel.fernet = enclave_app_instance.secure_channel.cipher_suite
    
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

    # Sync keys for testing
    host_channel.fernet = enclave_channel.cipher_suite

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

    # Sync keys for testing
    host_channel.fernet = enclave_channel.cipher_suite

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
    
    # Sync keys for testing
    host_channel.fernet = enclave_channel.cipher_suite
    
    # Send the tampered data through the *encrypted* channel
    # First, encrypt the ORIGINAL data.
    original_encrypted_command = host_channel.fernet.encrypt(serialized_data)
    
    # NOW tamper with the ENCRYPTED data
    tampered_encrypted_command = bytearray(original_encrypted_command)
    tampered_encrypted_command[0] = (tampered_encrypted_command[0] + 1) % 256
    
    test_host_to_enclave_q.append(bytes(tampered_encrypted_command))
    
    # Enclave attempts to receive and decrypt
    received_plaintext = enclave_channel.receive()
    assert received_plaintext is None

def test_identity_mapping_persistence():
    print("\nRunning test_identity_mapping_persistence...")
    
    # Use a temporary file for IdentityMappingService state
    temp_state_file = "/tmp/test_enclave_identity.enc"
    if os.path.exists(temp_state_file):
        os.remove(temp_state_file) # Ensure clean state

    # Mock attestation for this specific test
    os.environ["MOCK_ATTESTATION_FOR_TESTS_ONLY"] = "1"
    
    # Use a fixed key for persistence test
    fixed_key = os.urandom(32)
    
    # Patch KeyManager.generate_key to return the fixed key
    with patch('signal_assistant_enclave.kms.KeyManager.generate_key', return_value=fixed_key):
        # --- First Enclave Run: Create a mapping ---
        host_to_enclave_q1 = []
        enclave_to_host_q1 = []
        
        # Patch the storage_path for IdentityMappingService to use our temp file
        # Capture original init to avoid recursion
        original_init = IdentityMappingService.__init__
        
        with patch('signal_assistant_enclave.privacy_core.core.IdentityMappingService.__init__', autospec=True) as mock_init:
            # Define side effect to call original init with modified storage_path
            def side_effect(self, state_encryptor, storage_path="/tmp/enclave_identity.enc"):
                return original_init(self, state_encryptor, storage_path=temp_state_file)
            
            mock_init.side_effect = side_effect
            
            enclave_app1 = EnclaveApp(host_to_enclave_q1, enclave_to_host_q1)
            # Ensure enclave_app1 has an active key_manager for IdentityMappingService to init
            with patch.object(enclave_app1, 'key_manager', spec=KeyManager) as mock_key_manager_app1:
                mock_key_manager_app1.get_key.return_value = fixed_key
                mock_key_manager_app1.generate_key.return_value = fixed_key
                mock_key_manager_app1.set_registry_status("active")
                
                enclave_thread1 = threading.Thread(target=run_enclave_app_in_thread, args=(enclave_app1,))
                enclave_thread1.daemon = True
                enclave_thread1.start()
                time.sleep(1) # Give enclave time to start
                
                proxy1 = EnclaveProxy(host_to_enclave_q1, enclave_to_host_q1)
                proxy1.secure_channel.fernet = enclave_app1.secure_channel.cipher_suite # SYNC KEYS
                
                sender_id_mock = "mock_sender_id_persist"
                plaintext_message = "Hello, create my ID!"
                mock_envelope_bytes = f"{sender_id_mock}:{plaintext_message}".encode('utf-8')
                payload = {"encrypted_envelope": mock_envelope_bytes}
                response1 = proxy1.send_command("INBOUND_MESSAGE", payload)
                
                # Extract the internal_user_id from the response (UUID format)
                match = re.search(r"Message processed from ([a-f0-9-]{36})", response1.decode())
                assert match
                first_internal_user_id = match.group(1)
                
                enclave_app1.stop()
                enclave_thread1.join(timeout=2)
            
        # --- Second Enclave Run: Verify persistence ---
        host_to_enclave_q2 = []
        enclave_to_host_q2 = []
        
        # Ensure the IdentityMappingService uses the SAME temp file
        with patch('signal_assistant_enclave.privacy_core.core.IdentityMappingService.__init__', autospec=True) as mock_init:
            def side_effect(self, state_encryptor, storage_path="/tmp/enclave_identity.enc"):
                return original_init(self, state_encryptor, storage_path=temp_state_file)
            mock_init.side_effect = side_effect
            
            enclave_app2 = EnclaveApp(host_to_enclave_q2, enclave_to_host_q2)
            # Ensure enclave_app2 has an active key_manager for IdentityMappingService to init
            with patch.object(enclave_app2, 'key_manager', spec=KeyManager) as mock_key_manager_app2:
                mock_key_manager_app2.get_key.return_value = fixed_key
                mock_key_manager_app2.generate_key.return_value = fixed_key
                mock_key_manager_app2.set_registry_status("active")

                enclave_thread2 = threading.Thread(target=run_enclave_app_in_thread, args=(enclave_app2,))
                enclave_thread2.daemon = True
                enclave_thread2.start()
                time.sleep(1) # Give enclave time to start
                
                proxy2 = EnclaveProxy(host_to_enclave_q2, enclave_to_host_q2)
                proxy2.secure_channel.fernet = enclave_app2.secure_channel.cipher_suite # SYNC KEYS
                
                # Send another message from the same sender_id
                plaintext_message2 = "Hello again, I should have the same ID!"
                mock_envelope_bytes2 = f"{sender_id_mock}:{plaintext_message2}".encode('utf-8')
                payload2 = {"encrypted_envelope": mock_envelope_bytes2}
                response2 = proxy2.send_command("INBOUND_MESSAGE", payload2)
                
                match2 = re.search(r"Message processed from ([a-f0-9-]{36})", response2.decode())
                assert match2
                second_internal_user_id = match2.group(1)
                
                assert first_internal_user_id == second_internal_user_id
                
                enclave_app2.stop()
                enclave_thread2.join(timeout=2)

    # Clean up
    if os.path.exists(temp_state_file):
        os.remove(temp_state_file)
    del os.environ["MOCK_ATTESTATION_FOR_TESTS_ONLY"] # Clean up env var