#!/usr/bin/env python3
import argparse
import json
import sys
import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent.parent / "measurement_registry.json"

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        print(f"Error: Registry not found at {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse registry: {e}", file=sys.stderr)
        sys.exit(1)

def save_registry(registry: Dict[str, Any]):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
        f.write("\n") # Add trailing newline

def cmd_add(args):
    registry = load_registry()
    
    # Check if mrenclave already exists
    for m in registry.get("measurements", []):
        if m["mrenclave"] == args.mrenclave:
            print(f"Error: Measurement {args.mrenclave} already exists in registry.", file=sys.stderr)
            sys.exit(1)

    new_entry = {
        "mrenclave": args.mrenclave,
        "version": args.version,
        "git_commit": args.commit,
        "build_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "profile": args.profile,
        "status": args.status,
        "revocation_reason": None
    }
    
    registry.setdefault("measurements", []).append(new_entry)
    save_registry(registry)
    print(f"Added measurement: {args.mrenclave} ({args.version})")

def cmd_verify(args):
    registry = load_registry()
    found = False
    for m in registry.get("measurements", []):
        if m["mrenclave"] == args.mrenclave:
            found = True
            if m["status"] == "active":
                print(f"VERIFIED: {args.mrenclave} is ACTIVE (Version: {m['version']}, Profile: {m['profile']})")
                sys.exit(0)
            else:
                print(f"FAILED: {args.mrenclave} is found but status is '{m['status']}'")
                if m.get("revocation_reason"):
                    print(f"Reason: {m['revocation_reason']}")
                sys.exit(1)
    
    print(f"FAILED: {args.mrenclave} not found in registry.")
    sys.exit(1)

def cmd_list(args):
    registry = load_registry()
    measurements = registry.get("measurements", [])
    
    if args.active_only:
        measurements = [m for m in measurements if m["status"] == "active"]
        
    if not measurements:
        print("No measurements found.")
        return

    print(f"{'VERSION':<10} {'PROFILE':<8} {'STATUS':<10} {'MRENCLAVE'}")
    print("-" * 80)
    for m in measurements:
        print(f"{m['version']:<10} {m['profile']:<8} {m['status']:<10} {m['mrenclave']}")

def main():
    parser = argparse.ArgumentParser(description="Manage the Signal Assistant Enclave Measurement Registry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new measurement")
    add_parser.add_argument("--mrenclave", required=True, help="The MRENCLAVE hash (e.g., sha256:...")
    add_parser.add_argument("--version", required=True, help="Semantic version")
    add_parser.add_argument("--commit", required=True, help="Git commit SHA")
    add_parser.add_argument("--profile", required=True, choices=["DEV", "TEST", "STAGE", "PROD"], help="Build profile")
    add_parser.add_argument("--status", default="active", choices=["active", "deprecated", "revoked"], help="Initial status")
    add_parser.set_defaults(func=cmd_add)

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a measurement")
    verify_parser.add_argument("mrenclave", help="The MRENCLAVE hash to verify")
    verify_parser.set_defaults(func=cmd_verify)

    # List command
    list_parser = subparsers.add_parser("list", help="List measurements")
    list_parser.add_argument("--all", action="store_false", dest="active_only", help="Show all measurements (including revoked)")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
