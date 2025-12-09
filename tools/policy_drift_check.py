#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from signal_assistant.invariant_manifest import InvariantManifest, CURRENT_INVARIANT_MANIFEST

REGISTRY_PATH = Path(__file__).parent.parent / "measurement_registry.json"

def load_registry() -> Dict[str, Any]:
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)

def get_last_active_measurement(registry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    measurements = registry.get("measurements", [])
    for m in reversed(measurements):
        if m["status"] == "active":
            return m
    return None

def compare_manifests(old_manifest: InvariantManifest, current_manifest: InvariantManifest) -> bool:
    """
    Compares two InvariantManifests and returns True if current_manifest represents a weakening,
    False otherwise.
    """
    drift_detected = False

    # max_log_level_prod
    log_level_order = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
    old_level = log_level_order.get(old_manifest.max_log_level_prod, -1)
    current_level = log_level_order.get(current_manifest.max_log_level_prod, -1)
    if current_level < old_level: # e.g., INFO (1) -> DEBUG (0)
        print(f"DRIFT: max_log_level_prod weakened from {old_manifest.max_log_level_prod} to {current_manifest.max_log_level_prod}")
        drift_detected = True

    # le_response_types
    if old_manifest.le_response_types != current_manifest.le_response_types:
        if (frozenset(["BLOCK", "ALLOW"]) <= old_manifest.le_response_types) and \
           not (frozenset(["BLOCK", "ALLOW"]) <= current_manifest.le_response_types):
            print(f"DRIFT: le_response_types changed from {old_manifest.le_response_types} to {current_manifest.le_response_types} (removed core types)")
            drift_detected = True
        elif not (current_manifest.le_response_types <= old_manifest.le_response_types):
             # Only if current is not a subset of old (i.e. additions)
             # And only if no core types were removed (already handled by the first if)
             print(f"INFO: le_response_types added new types {current_manifest.le_response_types - old_manifest.le_response_types}. Manual review may be required.")
             # drift_detected remains False for additions that don't weaken existing policies


    # pii_sanitization_level
    sanitization_level_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    old_san_level = sanitization_level_order.get(old_manifest.pii_sanitization_level, -1)
    current_san_level = sanitization_level_order.get(current_manifest.pii_sanitization_level, -1)
    if current_san_level < old_san_level: # e.g., HIGH (2) -> MEDIUM (1)
        print(f"DRIFT: pii_sanitization_level weakened from {old_manifest.pii_sanitization_level} to {current_manifest.pii_sanitization_level}")
        drift_detected = True

    # attestation_required_for_sensitive_keys
    if old_manifest.attestation_required_for_sensitive_keys and not current_manifest.attestation_required_for_sensitive_keys:
        print("DRIFT: attestation_required_for_sensitive_keys changed from True to False")
        drift_detected = True

    # registry_verification_required
    if old_manifest.registry_verification_required and not current_manifest.registry_verification_required:
        print("DRIFT: registry_verification_required changed from True to False")
        drift_detected = True
        
    # dangerous_capabilities_allowed_in_prod
    if not old_manifest.dangerous_capabilities_allowed_in_prod and current_manifest.dangerous_capabilities_allowed_in_prod:
        print("DRIFT: dangerous_capabilities_allowed_in_prod changed from False to True")
        drift_detected = True


    return drift_detected

def main():
    print("Checking for Policy Drift in Invariant Manifest...")
    
    registry = load_registry()
    last_active_measurement = get_last_active_measurement(registry)
    
    if not last_active_measurement:
        print("No active measurements with InvariantManifest found in registry. Skipping baseline check.")
        sys.exit(0)
        
    print(f"Baseline commit: {last_active_measurement.get('git_commit', 'unknown')} (Profile: {last_active_measurement.get('profile')})")
    
    old_manifest_dict = last_active_measurement.get("invariant_manifest")
    if not old_manifest_dict:
        print("WARNING: Baseline measurement has no invariant_manifest. Cannot check for drift.")
        sys.exit(0) # Not a failure, but a warning
        
    old_manifest = InvariantManifest.from_dict(old_manifest_dict)
    current_manifest = CURRENT_INVARIANT_MANIFEST

    print(f"\nBaseline Manifest:\n{json.dumps(old_manifest.to_dict(), indent=2)}")
    print(f"\nCurrent Manifest:\n{json.dumps(current_manifest.to_dict(), indent=2)}")

    if compare_manifests(old_manifest, current_manifest):
        print("\nFAILURE: Policy Drift Detected! Weakening of invariants found.")
        sys.exit(1)
    else:
        print("\nSUCCESS: No policy drift (no weakening of invariants) detected.")

if __name__ == "__main__":
    main()
