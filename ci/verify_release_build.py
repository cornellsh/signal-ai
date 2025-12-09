#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

SRC_DIR = Path("src/signal_assistant")

def compute_mrenclave(src_path: Path) -> str:
    """
    Simulates MRENCLAVE computation by hashing all files in src/signal_assistant.
    In a real SGX build, this would be the measurement of the signed enclave binary.
    """
    hasher = hashlib.sha256()
    for root, _, files in os.walk(src_path):
        for file in sorted(files):
            if file.endswith(".py"): # Only hash python files for this simulation
                path = Path(root) / file
                with open(path, "rb") as f:
                    hasher.update(f.read())
    return "sha256:" + hasher.hexdigest()

def check_forbidden_patterns(src_path: Path, profile: str):
    """
    Checks for forbidden code patterns based on the profile.
    """
    if profile != "PROD":
        return

    forbidden_strings = [
        "MOCK_ATTESTATION_FOR_TESTS_ONLY",
        "MOCK_ATTESTATION = True",
    ]

    found_violations = False
    for root, _, files in os.walk(src_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            path = Path(root) / file
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for fs in forbidden_strings:
                        if fs in content:
                            print(f"VIOLATION: Found '{fs}' in {path} (Forbidden in PROD)")
                            found_violations = True
            except Exception as e:
                print(f"Warning: Could not read {path}: {e}")

    if found_violations:
        print("Build Verification FAILED: Forbidden patterns found in PROD build.")
        sys.exit(1)

def get_git_info() -> Dict[str, str]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        # Clean checking is optional for now
        return {"commit": commit}
    except subprocess.CalledProcessError:
        return {"commit": "unknown"}

def main():
    parser = argparse.ArgumentParser(description="Verify Signal Assistant Enclave Build")
    parser.add_argument("--profile", required=True, choices=["DEV", "TEST", "STAGE", "PROD"], help="Target Build Profile")
    parser.add_argument("--version", required=True, help="Semantic Version")
    parser.add_argument("--output", help="Output file for candidate registry entry")
    
    args = parser.parse_args()

    print(f"Verifying build for profile: {args.profile}")
    
    # 1. Check constraints
    check_forbidden_patterns(SRC_DIR, args.profile)
    
    # 2. Compute Measurement
    mrenclave = compute_mrenclave(SRC_DIR)
    print(f"Computed MRENCLAVE: {mrenclave}")
    
    # 3. Generate Artifact
    git_info = get_git_info()
    
    candidate = {
        "mrenclave": mrenclave,
        "version": args.version,
        "git_commit": git_info["commit"],
        "build_timestamp": "TODO:Timestamp", 
        "profile": args.profile,
        "status": "active",
        "revocation_reason": None
    }
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(candidate, f, indent=2)
        print(f"Candidate entry written to {args.output}")

if __name__ == "__main__":
    main()
