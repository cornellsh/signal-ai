#!/usr/bin/env python3
import argparse
import json
import sys
import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64

REGISTRY_PATH = Path(__file__).parent.parent / "measurement_registry.json"


def normalize_tag(version: str) -> str:
    version = version.strip()
    if version.startswith("v"):
        return version
    return f"v{version}"

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

    tag = args.tag or normalize_tag(args.version)

    new_entry = {
        "name": args.name,
        "mrenclave": args.mrenclave,
        "version": args.version,
        "tag": tag,
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

def cmd_keygen(args):
    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    
    priv_bytes = priv_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    pub_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "registry.key", "wb") as f:
        f.write(priv_bytes)
    
    with open(out_dir / "registry.pub", "wb") as f:
        f.write(pub_bytes)
        
    print(f"Keys generated in {out_dir}")

def _get_canonical_bytes(registry):
    # Canonicalize measurements for signing
    # Simple approach: serialize the 'measurements' list with sort_keys=True
    measurements = registry.get("measurements", [])
    return json.dumps(measurements, sort_keys=True).encode('utf-8')

def cmd_sign(args):
    registry = load_registry()
    
    with open(args.key, "rb") as f:
        priv_key = serialization.load_pem_private_key(f.read(), password=None)
    
    data = _get_canonical_bytes(registry)
    signature = priv_key.sign(data)
    
    sig_b64 = base64.b64encode(signature).decode('utf-8')
    
    new_sig_entry = {
        "signature": sig_b64,
        "algorithm": "ed25519"
    }
    
    # Overwrite signatures for now
    registry["signatures"] = [new_sig_entry]
    
    save_registry(registry)
    print("Registry signed.")

def cmd_verify_signature(args):
    registry = load_registry()
    if not registry.get("signatures"):
        print("No signatures found in registry.")
        sys.exit(1)
        
    with open(args.key, "rb") as f:
        pub_key = serialization.load_pem_public_key(f.read())
        
    data = _get_canonical_bytes(registry)
    
    # Verify the first signature
    sig_entry = registry["signatures"][0]
    sig_bytes = base64.b64decode(sig_entry["signature"])
    
    try:
        pub_key.verify(sig_bytes, data)
        print("Signature VERIFIED.")
    except Exception as e:
        print(f"Signature verification FAILED: {e}")
        sys.exit(1)

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
    add_parser.add_argument("--name", default="signal-assistant-enclave", help="Identifier for this measurement entry")
    add_parser.add_argument("--tag", help="Git tag that corresponds to this measurement (defaults to v<version>)")
    add_parser.set_defaults(func=cmd_add)

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a measurement")
    verify_parser.add_argument("mrenclave", help="The MRENCLAVE hash to verify")
    verify_parser.set_defaults(func=cmd_verify)

    # List command
    list_parser = subparsers.add_parser("list", help="List measurements")
    list_parser.add_argument("--all", action="store_false", dest="active_only", help="Show all measurements (including revoked)")
    list_parser.set_defaults(func=cmd_list)

    # Keygen command
    keygen_parser = subparsers.add_parser("keygen", help="Generate a signing key pair")
    keygen_parser.add_argument("--out-dir", default=".", help="Directory to output keys")
    keygen_parser.set_defaults(func=cmd_keygen)

    # Sign command
    sign_parser = subparsers.add_parser("sign", help="Sign the registry")
    sign_parser.add_argument("--key", required=True, help="Path to private key")
    sign_parser.set_defaults(func=cmd_sign)

    # Verify Signature command
    verify_sig_parser = subparsers.add_parser("verify-signature", help="Verify registry signature")
    verify_sig_parser.add_argument("--key", required=True, help="Path to public key")
    verify_sig_parser.set_defaults(func=cmd_verify_signature)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
