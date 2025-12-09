# tests/test_kms.py
import pytest
import os
from unittest.mock import MagicMock, patch

from signal_assistant.enclave.kms import KeyManager, AttestationError
from signal_assistant.enclave.secure_config import KMS_MASTER_KEY # For direct KeyManager tests
from cryptography.fernet import Fernet

@pytest.fixture
def key_manager():
    # Clear any previous state for isolated tests
    km = KeyManager()
    km._sealed_keys.clear()
    return km

@pytest.fixture
def master_cipher_suite():
    return Fernet(KMS_MASTER_KEY)

def test_generate_key(key_manager):
    key_id = "test_key_1"
    key = key_manager.generate_key(key_id, attestation_verified=True)
    assert isinstance(key, bytes)
    assert len(key) == 32 # AES-256 key size
    assert key_id in key_manager._sealed_keys
    # Verify that the key stored is sealed (i.e., not the raw key)
    # This also implicitly checks that generate_key internally calls _check_permission successfully
    assert key_manager._sealed_keys[key_id] != key

def test_get_key(key_manager):
    key_id = "test_key_2"
    generated_key = key_manager.generate_key(key_id, attestation_verified=True)
    retrieved_key = key_manager.get_key(key_id, attestation_verified=True)
    assert retrieved_key == generated_key

def test_get_non_existent_key_raises_error(key_manager):
    with pytest.raises(KeyError, match="Key with ID 'non_existent_key' not found."):
        key_manager.get_key("non_existent_key", attestation_verified=True)

def test_generate_duplicate_key_raises_error(key_manager):
    key_id = "test_key_3"
    key_manager.generate_key(key_id, attestation_verified=True)
    with pytest.raises(ValueError, match=f"Key with ID '{key_id}' already exists."):
        key_manager.generate_key(key_id, attestation_verified=True)

def test_delete_key(key_manager):
    key_id = "test_key_4"
    key_manager.generate_key(key_id, attestation_verified=True)
    key_manager.delete_key(key_id, attestation_verified=True)
    assert key_id not in key_manager._sealed_keys

def test_delete_non_existent_key_raises_error(key_manager):
    with pytest.raises(KeyError, match="Key with ID 'non_existent_key_to_delete' not found."):
        key_manager.delete_key("non_existent_key_to_delete", attestation_verified=True)

@patch('signal_assistant.enclave.kms.KeyManager._check_permission', return_value=False)
def test_permission_denied_generate_key_raises_error(mock_check_permission, key_manager):
    key_id = "denied_key_gen"
    with pytest.raises(PermissionError, match="Permission denied to generate key"):
        key_manager.generate_key(key_id, attestation_verified=True)
    mock_check_permission.assert_called_once_with(key_id, "generate", True)

@patch('signal_assistant.enclave.kms.KeyManager._check_permission', return_value=False)
def test_permission_denied_get_key_raises_error(mock_check_permission, key_manager, master_cipher_suite):
    key_id = "denied_key_get"
    # Manually add a sealed key to simulate it existing
    dummy_key = os.urandom(32)
    key_manager._sealed_keys[key_id] = master_cipher_suite.encrypt(dummy_key)
    
    with pytest.raises(PermissionError, match="Permission denied to get key"):
        key_manager.get_key(key_id, attestation_verified=True)
    mock_check_permission.assert_called_once_with(key_id, "get", True)

@patch('signal_assistant.enclave.kms.KeyManager._check_permission', return_value=False)
def test_permission_denied_delete_key_raises_error(mock_check_permission, key_manager, master_cipher_suite):
    key_id = "denied_key_delete"
    # Manually add a sealed key to simulate it existing
    dummy_key = os.urandom(32)
    key_manager._sealed_keys[key_id] = master_cipher_suite.encrypt(dummy_key)
    
    with pytest.raises(PermissionError, match="Permission denied to delete key"):
        key_manager.delete_key(key_id, attestation_verified=True) # Pass attestation=True to bypass _check_permission mock
    mock_check_permission.assert_called_once_with(key_id, "delete", True)

def test_sensitive_key_generate_fails_without_attestation(key_manager):
    sensitive_key_id = "ESSK_my_sensitive_key"
    with pytest.raises(AttestationError, match="Attestation required and failed for sensitive key"):
        key_manager.generate_key(sensitive_key_id, attestation_verified=False)

def test_sensitive_key_get_fails_without_attestation(key_manager):
    sensitive_key_id = "SPK_another_sensitive_key"
    key_manager.generate_key(sensitive_key_id, attestation_verified=True) # Generate with attestation
    
    with pytest.raises(AttestationError, match="Attestation required and failed for sensitive key"):
        key_manager.get_key(sensitive_key_id, attestation_verified=False)

def test_sensitive_key_delete_fails_without_attestation(key_manager):
    sensitive_key_id = "EAK_yet_another_key"
    key_manager.generate_key(sensitive_key_id, attestation_verified=True) # Generate with attestation
    
    with pytest.raises(AttestationError, match="Attestation required and failed for sensitive key"):
        key_manager.delete_key(sensitive_key_id, attestation_verified=False)

def test_non_sensitive_key_operations_without_attestation(key_manager):
    non_sensitive_key_id = "NON_SENSITIVE_KEY"
    
    # Generate
    key = key_manager.generate_key(non_sensitive_key_id, attestation_verified=False)
    assert isinstance(key, bytes)
    
    # Get
    retrieved_key = key_manager.get_key(non_sensitive_key_id, attestation_verified=False)
    assert retrieved_key == key
    
    # Delete
    key_manager.delete_key(non_sensitive_key_id, attestation_verified=False)
    assert non_sensitive_key_id not in key_manager._sealed_keys
