
import pytest
import tempfile
import os
from unittest.mock import MagicMock
from signal_assistant.enclave.privacy_core.core import IdentityMappingService, LE_REQUEST_TYPE, LE_RESPONSE
from signal_assistant.enclave.state_encryption import StateEncryptor

@pytest.fixture
def mock_state_encryptor():
    # Mock StateEncryptor with a dummy key
    return StateEncryptor(b'0'*32)

@pytest.fixture
def identity_db_path():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)
    if os.path.exists(path + ".tmp"):
        os.remove(path + ".tmp")

@pytest.fixture
def identity_service(mock_state_encryptor, identity_db_path):
    return IdentityMappingService(mock_state_encryptor, storage_path=identity_db_path)

def test_persistence(mock_state_encryptor, identity_db_path):
    # 1. Create service, map user
    svc1 = IdentityMappingService(mock_state_encryptor, storage_path=identity_db_path)
    internal_id = svc1.map_signal_id_to_internal_id("signal-123")
    
    # 2. Re-create service (simulate restart)
    svc2 = IdentityMappingService(mock_state_encryptor, storage_path=identity_db_path)
    svc2.load_state() # Must call load!
    
    # 3. Check mapping exists
    assert svc2._signal_to_internal.get("signal-123") == internal_id

def test_map_signal_id_to_internal_id(identity_service):
    signal_id = "+15550001234"
    internal_id = identity_service.map_signal_id_to_internal_id(signal_id)
    
    assert internal_id is not None
    assert isinstance(internal_id, str)
    assert internal_id != signal_id
    
    # Verify idempotency
    internal_id_2 = identity_service.map_signal_id_to_internal_id(signal_id)
    assert internal_id == internal_id_2

def test_delete_user_data(identity_service):
    signal_id = "+15550005678"
    internal_id = identity_service.map_signal_id_to_internal_id(signal_id)
    
    # Assert mapping exists
    assert identity_service._signal_to_internal.get(signal_id) == internal_id
    assert identity_service._internal_to_signal.get(internal_id) == signal_id
    
    # Delete
    identity_service.delete_user_data(internal_id)
    
    # Assert mapping is gone
    assert signal_id not in identity_service._signal_to_internal
    assert internal_id not in identity_service._internal_to_signal

def test_check_le_policy_unauthorized(identity_service):
    # No auth context
    decision = identity_service._check_le_policy(LE_REQUEST_TYPE.GET_LOGS, "some_id", {})
    assert decision is False

def test_check_le_policy_authorized_valid(identity_service):
    auth_context = {"is_authorized_multi_party": True}
    decision = identity_service._check_le_policy(LE_REQUEST_TYPE.GET_LOGS, "some_id", auth_context)
    assert decision is True

def test_check_le_policy_sensitive_data_denied(identity_service):
    # Even if authorized, sensitive data access should be denied
    auth_context = {"is_authorized_multi_party": True}
    decision = identity_service._check_le_policy(LE_REQUEST_TYPE.ACCESS_SENSITIVE_DATA, "some_id", auth_context)
    assert decision is False

def test_handle_le_request_get_signal_id(identity_service):
    signal_id = "+15559998888"
    internal_id = identity_service.map_signal_id_to_internal_id(signal_id)
    
    auth_context = {"is_authorized_multi_party": True}
    
    response = identity_service.handle_le_request(
        LE_REQUEST_TYPE.GET_EXTERNAL_ID, 
        internal_id, 
        auth_context
    )
    
    assert response.status == "GRANTED"
    assert response.data["external_id"] == signal_id

def test_handle_le_request_denied(identity_service):
    auth_context = {"is_authorized_multi_party": False}
    response = identity_service.handle_le_request(
        LE_REQUEST_TYPE.GET_LOGS, 
        "some_id", 
        auth_context
    )
    assert response.status == "DENIED"
