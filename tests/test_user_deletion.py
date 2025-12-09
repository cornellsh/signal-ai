
import pytest
from unittest.mock import MagicMock
from signal_assistant.enclave.privacy_core.core import IdentityMappingService
from signal_assistant.enclave.state_encryption import StateEncryptor

@pytest.fixture
def identity_service():
    state_encryptor = StateEncryptor(b'0'*32)
    return IdentityMappingService(state_encryptor)

def test_user_deletion_scenario(identity_service):
    """
    Task 4.3: Integration Test for User Deletion
    Simulates a user interaction cycle followed by a deletion request.
    """
    # 1. User interacts (Mapping is created)
    signal_id = "+15551234567"
    internal_id = identity_service.map_signal_id_to_internal_id(signal_id)
    
    assert internal_id is not None
    # Verify mapping exists
    assert identity_service.map_signal_id_to_internal_id(signal_id) == internal_id
    
    # 2. User initiates deletion request
    identity_service.delete_user_data(internal_id)
    
    # 3. Assert mapping is purged
    # Accessing internal storage directly to verify absence
    assert signal_id not in identity_service._signal_to_internal
    assert internal_id not in identity_service._internal_to_signal
    
    # Verify re-mapping creates a NEW internal ID (implying old one is truly gone/forgotten)
    new_internal_id = identity_service.map_signal_id_to_internal_id(signal_id)
    assert new_internal_id != internal_id
