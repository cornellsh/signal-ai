
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

def test_persistence_across_restart(tmp_path):
    """
    Verifies that the IdentityMappingService persists state to disk
    and correctly restores it upon restart.
    """
    storage_path = str(tmp_path / "identity.enc")
    state_encryptor = StateEncryptor(b'0'*32)
    
    # 1. Start Service, Create Mapping
    service1 = IdentityMappingService(state_encryptor, storage_path=storage_path)
    service1.load_state() # Simulate app start
    
    signal_id = "+19998887777"
    internal_id_1 = service1.map_signal_id_to_internal_id(signal_id)
    assert internal_id_1 is not None
    
    # 2. Simulate Restart (New Instance, same path)
    service2 = IdentityMappingService(state_encryptor, storage_path=storage_path)
    service2.load_state()
    
    # Verify mapping persisted
    # Note: accessing private member to verify it loaded
    assert service2._signal_to_internal.get(signal_id) == internal_id_1
    assert service2.map_signal_id_to_internal_id(signal_id) == internal_id_1
    
    # 3. Delete User in Service 2
    service2.delete_user_data(internal_id_1)
    
    # 4. Simulate Restart again
    service3 = IdentityMappingService(state_encryptor, storage_path=storage_path)
    service3.load_state()
    
    # Verify mapping is gone
    assert signal_id not in service3._signal_to_internal
    
    # 5. Create new mapping for same user -> Should be NEW InternalID
    internal_id_2 = service3.map_signal_id_to_internal_id(signal_id)
    assert internal_id_2 != internal_id_1
