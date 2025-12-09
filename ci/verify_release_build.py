#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

from signal_assistant.enclave.capabilities import CURRENT_CAPABILITIES
from signal_assistant.invariant_manifest import CURRENT_INVARIANT_MANIFEST

SRC_DIR = Path("src/signal_assistant")


def normalize_tag(version: str) -> str:
    normalized = version.strip()
    if normalized.startswith("v"):
        return normalized
    return f"v{normalized}"

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

def check_dirty_submodule(submodule_path: Path):
    """
    Checks if the specified git submodule is in a dirty state (uncommitted changes or untracked files).
    Exits with an error if the submodule is dirty.
    """
    print(f"Checking submodule status for: {submodule_path}")
    try:
        # Check for uncommitted changes or untracked files
        # The --ignore-submodules=dirty is not used here because we specifically WANT to check if THIS submodule is dirty
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=submodule_path,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"VIOLATION: Enclave submodule at {submodule_path} is dirty. "
                  "Please commit or stash changes in the submodule, or update the submodule to a clean commit.")
            print("Dirty submodule status:\n", result.stdout)
            sys.exit(1)
        print(f"Submodule {submodule_path} is clean.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Could not check submodule status for {submodule_path}: {e}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: git command not found. Ensure git is installed and in PATH.")
        sys.exit(1)

def get_submodule_commit(submodule_path: Path) -> str:
    """Gets the current commit SHA of the specified submodule."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=submodule_path
        ).decode().strip()
        return commit
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Could not get submodule commit for {submodule_path}: {e}")
        sys.exit(1)

def check_enclave_registry_consistency(enclave_submodule_path: Path, registry_path: Path):
    """
    Checks consistency between measurement_registry.json and the enclave submodule's state.
    """
    print(f"\nChecking measurement registry consistency for {enclave_submodule_path}...")

    if not registry_path.exists():
        print(f"ERROR: Measurement registry file not found at {registry_path}")
        sys.exit(1)

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse {registry_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not read {registry_path}: {e}")
        sys.exit(1)

    measurements = registry_data.get("measurements", [])
    if not measurements:
        print(f"WARNING: No measurements defined in {registry_path}.")
        return

    submodule_commit = get_submodule_commit(enclave_submodule_path)
    head_entry = None

    def _commit_exists(commit: str) -> bool:
        try:
            subprocess.run(
                ["git", "cat-file", "-t", commit],
                cwd=enclave_submodule_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _tags_for_commit(commit: str) -> list[str]:
        try:
            output = subprocess.check_output(
                ["git", "tag", "--points-at", commit],
                cwd=enclave_submodule_path,
                text=True,
            )
            return [tag.strip() for tag in output.splitlines() if tag.strip()]
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Could not query tags for commit {commit}: {e}")
            print(f"Stderr: {e.stderr}")
            sys.exit(1)

    for entry in measurements:
        name = entry.get("name", "unnamed-enclave-measurement")
        git_commit = entry.get("git_commit")
        version = entry.get("version")
        status = entry.get("status", "unknown").lower()

        print(f"Verifying measurement '{name}' ({version}) -> commit {git_commit} [{status}]")

        if not git_commit or not version:
            print(f"VIOLATION: Measurement '{name}' is missing git_commit or version.")
            sys.exit(1)

        if not _commit_exists(git_commit):
            print(f"VIOLATION: Commit {git_commit} from measurement '{name}' is not available in {enclave_submodule_path}.")
            sys.exit(1)

        if git_commit == submodule_commit:
            head_entry = entry

        if status == "active":
            tags = _tags_for_commit(git_commit)
            if not tags:
                print(f"VIOLATION: No git tags point to commit {git_commit} for measurement '{name}'.")
                sys.exit(1)
            expected_tags = {version.strip(), normalize_tag(version)}
            if entry.get("tag"):
                expected_tags.add(entry["tag"].strip())

            matched = set(tags) & expected_tags
            if not matched:
                print(f"VIOLATION: Measurement '{name}' (version {version}) is not represented by a tag pointing at {git_commit}.")
                print(f"Available tags: {tags}")
                print(f"Expected tags: {sorted(expected_tags)}")
                sys.exit(1)
            print(f"  Measurement '{name}' matches tags {sorted(matched)}.")

    if head_entry is None:
        print(f"VIOLATION: Enclave submodule commit {submodule_commit} is not tracked in {registry_path}.")
        sys.exit(1)

    if head_entry.get("status", "").lower() != "active":
        print(f"VIOLATION: Enclave submodule commit {submodule_commit} maps to a measurement entry with status '{head_entry.get('status')}'. It must be 'active'.")
        sys.exit(1)

    print(f"Measurement registry consistency check PASSED for enclave submodule.")

def main():
    parser = argparse.ArgumentParser(description="Verify Signal Assistant Enclave Build")
    parser.add_argument("--profile", required=True, choices=["DEV", "TEST", "STAGE", "PROD"], help="Target Build Profile")
    parser.add_argument("--version", required=True, help="Semantic Version")
    parser.add_argument("--output", help="Output file for candidate registry entry")
    
    args = parser.parse_args()

    print(f"Verifying build for profile: {args.profile}")

    # Define submodule path
    ENCLAVE_SUBMODULE_PATH = Path("enclave_package")
    MEASUREMENT_REGISTRY_PATH = Path("measurement_registry.json")

    # 0. Check submodule state
    if not ENCLAVE_SUBMODULE_PATH.exists():
        print(f"ERROR: Enclave submodule directory not found at {ENCLAVE_SUBMODULE_PATH}. "
              "Please ensure the submodule is initialized and updated (e.g., `git submodule update --init --recursive`).")
        sys.exit(1)
    check_dirty_submodule(ENCLAVE_SUBMODULE_PATH)
    
    # 1. Check constraints
    check_forbidden_patterns(SRC_DIR, args.profile)
    
    # Check DangerousCapabilities
    sys.path.append(str(Path("src").resolve()))
    try:
        from signal_assistant.enclave.capabilities import CURRENT_CAPABILITIES
    except ImportError as e:
        print(f"Error importing capabilities: {e}")
        sys.exit(1)
        
    if args.profile == "PROD":
        if not CURRENT_CAPABILITIES.is_empty():
            print(f"VIOLATION: DangerousCapabilities detected in PROD build: {CURRENT_CAPABILITIES}")
            sys.exit(1)
    
    # Run OpenSpec validation
    print("\nRunning OpenSpec validation...")
    try:
        subprocess.run(["openspec", "validate", "signal-assistant-enclave-submodule-integration", "--strict"], check=True, capture_output=True, text=True)
        print("OpenSpec validation PASSED.")
    except subprocess.CalledProcessError as e:
        print(f"OpenSpec validation FAILED: {e.stderr}")
        sys.exit(1)

    # Run Policy Drift Check
    print("\nRunning Policy Drift Check...")
    try:
        # Assuming policy_drift_check.py is in the tools directory relative to the project root
        policy_drift_check_script = Path(__file__).parent.parent / "tools" / "policy_drift_check.py"
        subprocess.run([sys.executable, str(policy_drift_check_script)], check=True, capture_output=True, text=True)
        print("Policy Drift Check PASSED.")
    except subprocess.CalledProcessError as e:
        print(f"Policy Drift Check FAILED: {e.stdout}{e.stderr}")
        sys.exit(1)

    # Run Enclave Import Check
    print("\nRunning Enclave Import Check...")
    try:
        enclave_import_check_script = Path(__file__).parent / "static_analysis" / "check_enclave_imports.py"
        subprocess.run([sys.executable, str(enclave_import_check_script)], check=True, capture_output=True, text=True)
        print("Enclave Import Check PASSED.")
    except subprocess.CalledProcessError as e:
        print(f"Enclave Import Check FAILED: {e.stdout}{e.stderr}")
        sys.exit(1)

    # Run Enclave Registry Consistency Check
    check_enclave_registry_consistency(ENCLAVE_SUBMODULE_PATH, MEASUREMENT_REGISTRY_PATH)

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
        "revocation_reason": None,
        "invariant_manifest": CURRENT_INVARIANT_MANIFEST.to_dict()
    }
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(candidate, f, indent=2)
        print(f"Candidate entry written to {args.output}")

if __name__ == "__main__":
    main()
