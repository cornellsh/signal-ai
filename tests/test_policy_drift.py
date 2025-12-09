import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
import base64
from pathlib import Path
import os
import sys
import importlib
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from signal_assistant.invariant_manifest import InvariantManifest
from io import StringIO

class TestPolicyDrift(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.test_dir.name)
        self.registry_path = self.root_path / "measurement_registry.json"
        
        # Capture stdout/stderr
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self._new_stdout = StringIO()
        sys.stderr = self._new_stderr = StringIO()

        # Patch sys.exit to raise SystemExit with the correct code
        def mock_sys_exit_with_code(code=None):
            raise SystemExit(code)
        self.patcher_sys_exit = patch('sys.exit', side_effect=mock_sys_exit_with_code)
        self.mock_sys_exit = self.patcher_sys_exit.start()

        # Patch argparse.ArgumentParser.parse_args globally
        self.patcher_parse_args = patch("argparse.ArgumentParser.parse_args")
        self.mock_parse_args_obj = self.patcher_parse_args.start()
        self.mock_parse_args_obj.return_value = MagicMock(output=None) # Configure the mock

        # Dynamically import policy_drift_check and its main function
        tools_path = str(Path(__file__).parent.parent / "tools")
        sys.path.insert(0, tools_path)
        self.policy_drift_check = importlib.import_module("policy_drift_check")
        self.policy_drift_main = self.policy_drift_check.main

    def tearDown(self):
        self.test_dir.cleanup()
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        self.patcher_sys_exit.stop() # Stop patching sys.exit
        self.patcher_parse_args.stop() # Stop patching parse_args

        # Clean up dynamic import
        sys.path.pop(0)
        if "policy_drift_check" in sys.modules:
            del sys.modules["policy_drift_check"]
        if "tools.policy_drift_check" in sys.modules: # Ensure this is also cleaned up
            del sys.modules["tools.policy_drift_check"]


    def create_registry_with_manifest(self, mrenclave, version, profile, status, invariant_manifest_dict):
        registry = {
            "schema_version": "1.0",
            "measurements": [
                {
                    "mrenclave": mrenclave,
                    "version": version,
                    "git_commit": "mock_commit",
                    "build_timestamp": "2023-01-01T00:00:00Z",
                    "profile": profile,
                    "status": status,
                    "revocation_reason": None,
                    "invariant_manifest": invariant_manifest_dict
                }
            ],
            "signatures": [] # Signatures are not tested here, only manifest comparison
        }
        return registry

    def test_permissible_drift(self):
        with patch.object(self.policy_drift_check, "load_registry") as mock_load_registry, \
             patch.object(self.policy_drift_check, "CURRENT_INVARIANT_MANIFEST") as mock_current_manifest:
            # Configure mock_load_registry to return our test registry
            registry_content = self.create_registry_with_manifest("mrenclave_old", "1.0.0", "PROD", "active", 
                InvariantManifest(
                    max_log_level_prod="INFO",
                    le_response_types=frozenset(["ALLOW", "BLOCK"]),
                    pii_sanitization_level="HIGH",
                    attestation_required_for_sensitive_keys=True,
                    registry_verification_required=True,
                    dangerous_capabilities_allowed_in_prod=False
                ).to_dict()
            )
            mock_load_registry.return_value = registry_content

            # Current manifest (new, no weakening, some strengthening is fine)
            new_manifest = InvariantManifest(
                max_log_level_prod="WARNING", # Stronger than INFO
                le_response_types=frozenset(["ALLOW", "BLOCK", "NEW_TYPE"]), # Allowed to add
                pii_sanitization_level="HIGH",
                attestation_required_for_sensitive_keys=True,
                registry_verification_required=True,
                dangerous_capabilities_allowed_in_prod=False
            )
            # Configure mock_current_manifest to mirror new_manifest attributes
            mock_current_manifest.max_log_level_prod = new_manifest.max_log_level_prod
            mock_current_manifest.le_response_types = new_manifest.le_response_types
            mock_current_manifest.pii_sanitization_level = new_manifest.pii_sanitization_level
            mock_current_manifest.attestation_required_for_sensitive_keys = new_manifest.attestation_required_for_sensitive_keys
            mock_current_manifest.registry_verification_required = new_manifest.registry_verification_required
            mock_current_manifest.dangerous_capabilities_allowed_in_prod = new_manifest.dangerous_capabilities_allowed_in_prod
            mock_current_manifest.to_dict.return_value = new_manifest.to_dict() # to_dict is still a method

            self.policy_drift_main()
            self.assertIn("SUCCESS: No policy drift", self._new_stdout.getvalue())

    def test_impermissible_drift_log_level(self):
        with patch.object(self.policy_drift_check, "load_registry") as mock_load_registry, \
             patch.object(self.policy_drift_check, "CURRENT_INVARIANT_MANIFEST") as mock_current_manifest:
            registry_content = self.create_registry_with_manifest("mrenclave_old", "1.0.0", "PROD", "active", 
                InvariantManifest(max_log_level_prod="INFO").to_dict()
            )
            mock_load_registry.return_value = registry_content

            new_manifest = InvariantManifest(max_log_level_prod="DEBUG") # Weakening
            # Configure mock_current_manifest to mirror new_manifest attributes
            mock_current_manifest.max_log_level_prod = new_manifest.max_log_level_prod
            mock_current_manifest.le_response_types = new_manifest.le_response_types
            mock_current_manifest.pii_sanitization_level = new_manifest.pii_sanitization_level
            mock_current_manifest.attestation_required_for_sensitive_keys = new_manifest.attestation_required_for_sensitive_keys
            mock_current_manifest.registry_verification_required = new_manifest.registry_verification_required
            mock_current_manifest.dangerous_capabilities_allowed_in_prod = new_manifest.dangerous_capabilities_allowed_in_prod
            mock_current_manifest.to_dict.return_value = new_manifest.to_dict()

            with self.assertRaises(SystemExit) as cm:
                self.policy_drift_main()
            self.assertEqual(cm.exception.code, 1) # Should fail (exit 1)
            self.assertIn("DRIFT: max_log_level_prod weakened", self._new_stdout.getvalue())
            self.assertIn("FAILURE: Policy Drift Detected!", self._new_stdout.getvalue())

    def test_impermissible_drift_pii_level(self):
        with patch.object(self.policy_drift_check, "load_registry") as mock_load_registry, \
             patch.object(self.policy_drift_check, "CURRENT_INVARIANT_MANIFEST") as mock_current_manifest:
            registry_content = self.create_registry_with_manifest("mrenclave_old", "1.0.0", "PROD", "active", 
                InvariantManifest(pii_sanitization_level="HIGH").to_dict()
            )
            mock_load_registry.return_value = registry_content

            new_manifest = InvariantManifest(pii_sanitization_level="MEDIUM") # Weakening
            # Configure mock_current_manifest to mirror new_manifest attributes
            mock_current_manifest.max_log_level_prod = new_manifest.max_log_level_prod
            mock_current_manifest.le_response_types = new_manifest.le_response_types
            mock_current_manifest.pii_sanitization_level = new_manifest.pii_sanitization_level
            mock_current_manifest.attestation_required_for_sensitive_keys = new_manifest.attestation_required_for_sensitive_keys
            mock_current_manifest.registry_verification_required = new_manifest.registry_verification_required
            mock_current_manifest.dangerous_capabilities_allowed_in_prod = new_manifest.dangerous_capabilities_allowed_in_prod
            mock_current_manifest.to_dict.return_value = new_manifest.to_dict()

            with self.assertRaises(SystemExit) as cm:
                self.policy_drift_main()
            self.assertEqual(cm.exception.code, 1) # Should fail (exit 1)
            self.assertIn("DRIFT: pii_sanitization_level weakened", self._new_stdout.getvalue())
            self.assertIn("FAILURE: Policy Drift Detected!", self._new_stdout.getvalue())
        
    def test_impermissible_drift_attestation_required(self):
        with patch.object(self.policy_drift_check, "load_registry") as mock_load_registry, \
             patch.object(self.policy_drift_check, "CURRENT_INVARIANT_MANIFEST") as mock_current_manifest:
            registry_content = self.create_registry_with_manifest("mrenclave_old", "1.0.0", "PROD", "active", 
                InvariantManifest(attestation_required_for_sensitive_keys=True).to_dict()
            )
            mock_load_registry.return_value = registry_content

            new_manifest = InvariantManifest(attestation_required_for_sensitive_keys=False) # Weakening
            # Configure mock_current_manifest to mirror new_manifest attributes
            mock_current_manifest.max_log_level_prod = new_manifest.max_log_level_prod
            mock_current_manifest.le_response_types = new_manifest.le_response_types
            mock_current_manifest.pii_sanitization_level = new_manifest.pii_sanitization_level
            mock_current_manifest.attestation_required_for_sensitive_keys = new_manifest.attestation_required_for_sensitive_keys
            mock_current_manifest.registry_verification_required = new_manifest.registry_verification_required
            mock_current_manifest.dangerous_capabilities_allowed_in_prod = new_manifest.dangerous_capabilities_allowed_in_prod
            mock_current_manifest.to_dict.return_value = new_manifest.to_dict()

            with self.assertRaises(SystemExit) as cm:
                self.policy_drift_main()
            self.assertEqual(cm.exception.code, 1) # Should fail (exit 1)
            self.assertIn("DRIFT: attestation_required_for_sensitive_keys changed from True to False", self._new_stdout.getvalue())
            self.assertIn("FAILURE: Policy Drift Detected!", self._new_stdout.getvalue())

    def test_impermissible_drift_dangerous_capabilities_allowed(self):
        with patch.object(self.policy_drift_check, "load_registry") as mock_load_registry, \
             patch.object(self.policy_drift_check, "CURRENT_INVARIANT_MANIFEST") as mock_current_manifest:
            registry_content = self.create_registry_with_manifest("mrenclave_old", "1.0.0", "PROD", "active", 
                InvariantManifest(dangerous_capabilities_allowed_in_prod=False).to_dict()
            )
            mock_load_registry.return_value = registry_content

            new_manifest = InvariantManifest(dangerous_capabilities_allowed_in_prod=True) # Weakening
            # Configure mock_current_manifest to mirror new_manifest attributes
            mock_current_manifest.max_log_level_prod = new_manifest.max_log_level_prod
            mock_current_manifest.le_response_types = new_manifest.le_response_types
            mock_current_manifest.pii_sanitization_level = new_manifest.pii_sanitization_level
            mock_current_manifest.attestation_required_for_sensitive_keys = new_manifest.attestation_required_for_sensitive_keys
            mock_current_manifest.registry_verification_required = new_manifest.registry_verification_required
            mock_current_manifest.dangerous_capabilities_allowed_in_prod = new_manifest.dangerous_capabilities_allowed_in_prod
            mock_current_manifest.to_dict.return_value = new_manifest.to_dict()

            with self.assertRaises(SystemExit) as cm:
                self.policy_drift_main()
            self.assertEqual(cm.exception.code, 1) # Should fail (exit 1)
            self.assertIn("DRIFT: dangerous_capabilities_allowed_in_prod changed from False to True", self._new_stdout.getvalue())
            self.assertIn("FAILURE: Policy Drift Detected!", self._new_stdout.getvalue())
