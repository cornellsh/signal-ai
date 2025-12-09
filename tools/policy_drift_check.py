#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

REGISTRY_PATH = Path(__file__).parent.parent / "measurement_registry.json"
SANITIZER_PATH = "src/signal_assistant/enclave/privacy_core/sanitizer.py"

def load_registry():
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)

def get_last_active_commit(registry) -> Optional[str]:
    # Measurements are a list. We assume the last one in the list is the most recent.
    # Or we verify by version. For simplicity, take the last 'active' one.
    measurements = registry.get("measurements", [])
    for m in reversed(measurements):
        if m["status"] == "active":
            return m["git_commit"]
    return None

def get_file_at_commit(commit: str, path: str) -> str:
    try:
        return subprocess.check_output(["git", "show", f"{commit}:{path}"], stderr=subprocess.STDOUT).decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching file at commit {commit}: {e.output.decode()}", file=sys.stderr)
        return ""

def main():
    print("Checking for Policy Drift in PII Sanitization...")
    
    registry = load_registry()
    last_commit = get_last_active_commit(registry)
    
    if not last_commit:
        print("No active measurements found in registry. Skipping baseline check.")
        # This is strictly speaking a pass since there is no policy to drift from.
        sys.exit(0)
        
    print(f"Baseline commit: {last_commit}")
    
    old_content = get_file_at_commit(last_commit, SANITIZER_PATH)
    if not old_content:
        print("Could not retrieve baseline file.")
        sys.exit(1)
        
    try:
        with open(SANITIZER_PATH, "r") as f:
            new_content = f.read()
    except FileNotFoundError:
        print(f"Current sanitizer file not found at {SANITIZER_PATH}")
        sys.exit(1)

    # Simple heuristic: Check if count of "REGEX" definitions decreased
    old_regex_count = old_content.count("_REGEX =")
    new_regex_count = new_content.count("_REGEX =")
    
    print(f"Regex count (Baseline): {old_regex_count}")
    print(f"Regex count (Current):  {new_regex_count}")
    
    if new_regex_count < old_regex_count:
        print("FAILURE: Potential Policy Drift Detected! Number of Regex definitions decreased.")
        sys.exit(1)
        
    print("SUCCESS: No obvious policy drift detected (regex count stable or increased).")

if __name__ == "__main__":
    main()
