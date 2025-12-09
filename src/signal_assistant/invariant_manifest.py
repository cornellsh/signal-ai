# src/signal_assistant/invariant_manifest.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, FrozenSet

@dataclass(frozen=True)
class InvariantManifest:
    """
    Defines security and privacy invariants that must hold true for the enclave.
    Any changes to these values that weaken security or privacy require an OpenSpec delta.
    """
    max_log_level_prod: str = "INFO" # Max logging level allowed in PROD
    le_response_types: FrozenSet[str] = field(default_factory=lambda: frozenset(["ALLOW", "BLOCK"]))
    pii_sanitization_level: str = "HIGH" # Level of PII sanitization (e.g., "HIGH", "MEDIUM", "LOW")
    attestation_required_for_sensitive_keys: bool = True # KMS requires attestation for sensitive keys
    registry_verification_required: bool = True # Enclave verifies measurement registry
    dangerous_capabilities_allowed_in_prod: bool = False # No dangerous capabilities in PROD
    
    # Add other invariants as needed

    def to_dict(self) -> Dict[str, Any]:
        """Converts the manifest to a dictionary for serialization."""
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, frozenset):
                data[key] = sorted(list(value)) # Convert frozenset to sorted list for stable serialization
            else:
                data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvariantManifest":
        """Constructs an InvariantManifest from a dictionary."""
        # Convert lists back to frozensets if necessary
        processed_data = data.copy()
        for key, value in processed_data.items():
            if key == "le_response_types" and isinstance(value, list):
                processed_data[key] = frozenset(value)
        return cls(**processed_data)

# This manifest represents the currently enforced invariants.
# It should be updated manually (or via build process) and committed.
# The policy_drift_check.py tool will compare this against previous versions.
CURRENT_INVARIANT_MANIFEST = InvariantManifest()
