
import pytest
from signal_assistant.enclave.privacy_core.core import IdentityMappingService, LE_REQUEST_TYPE
from signal_assistant.enclave.state_encryption import StateEncryptor

@pytest.fixture
def identity_service():
    state_encryptor = StateEncryptor(b'0'*32)
    return IdentityMappingService(state_encryptor)

def test_le_control_path_scenario(identity_service):
    """
    Task 4.4: Integration Test for LE Control Path
    """
    signal_id = "+15559876543"
    internal_id = identity_service.map_signal_id_to_internal_id(signal_id)
    
    # 1. Valid Request
    valid_auth = {"is_authorized_multi_party": True}
    response = identity_service.handle_le_request(
        LE_REQUEST_TYPE.GET_EXTERNAL_ID, 
        internal_id, 
        valid_auth
    )
    assert response.status == "GRANTED"
    assert response.data["external_id"] == signal_id
    
    # 2. Invalid Request (Unauthorized)
    invalid_auth = {"is_authorized_multi_party": False}
    response = identity_service.handle_le_request(
        LE_REQUEST_TYPE.GET_EXTERNAL_ID, 
        internal_id, 
        invalid_auth
    )
    assert response.status == "DENIED"
    assert response.data is None
    
    # 3. Invalid Request (Forbidden Type)
    response = identity_service.handle_le_request(
        LE_REQUEST_TYPE.ACCESS_SENSITIVE_DATA, 
        internal_id, 
        valid_auth
    )
    assert response.status == "DENIED"
    
    # 4. Unknown User
    response = identity_service.handle_le_request(
        LE_REQUEST_TYPE.GET_EXTERNAL_ID, 
        "unknown-uuid", 
        valid_auth
    )
    assert response.status == "DENIED"
