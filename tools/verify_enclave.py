#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

def load_registry(registry_path: Path) -> Dict[str, Any]:
    if not registry_path.exists():
        print(f"Error: Registry not found at {registry_path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(registry_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse registry: {e}", file=sys.stderr)
        sys.exit(1)

def get_remote_attestation(target: str) -> Dict[str, str]:
    """
    Simulates fetching an attestation quote from a remote Signal Assistant instance.
    """
    print(f"Connecting to {target} to retrieve attestation quote...")
    # Mock response
    return {
        "mrenclave": "sha256:simulated_mrenclave_for_dev",
        "quote": "mock_quote_bytes_base64",
        "public_key": "mock_public_key"
    }

def verify_mrenclave(mrenclave: str, registry: Dict[str, Any]) -> bool:
    print(f"Verifying MRENCLAVE: {mrenclave}")
    for m in registry.get("measurements", []):
        if m["mrenclave"] == mrenclave:
            if m["status"] == "active":
                print(f"SUCCESS: MRENCLAVE is trusted.")
                print(f"  Version: {m['version']}")
                print(f"  Profile: {m['profile']}")
                print(f"  Commit:  {m['git_commit']}")
                return True
            else:
                print(f"FAILURE: MRENCLAVE found but status is '{m['status']}'.")
                if m.get("revocation_reason"):
                    print(f"  Reason: {m['revocation_reason']}")
                return False
    
    print("FAILURE: MRENCLAVE not found in registry.")
    return False

def main():
    parser = argparse.ArgumentParser(description="Client-side Enclave Verification Tool")
    parser.add_argument("--target", required=True, help="URL/Address of the Signal Assistant")
    parser.add_argument("--registry", default="measurement_registry.json", help="Path to trusted registry")
    
    args = parser.parse_args()
    
    registry_path = Path(args.registry)
    if not registry_path.exists():
        # Try finding it in project root if running from tools/
        registry_path = Path(__file__).parent.parent / args.registry
    
    registry = load_registry(registry_path)
    
    quote_data = get_remote_attestation(args.target)
    mrenclave = quote_data["mrenclave"]
    
    if verify_mrenclave(mrenclave, registry):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
