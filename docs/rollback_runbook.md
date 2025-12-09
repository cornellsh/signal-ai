# Signal Assistant Rollback Runbook

This guide describes how to safely rollback the Enclave to a previous version in the event of a critical regression or security incident.

## Scenario A: Functional Regression (Safe Rollback)
*The new version 1.2.0 is crashing or behaving incorrectly, but is NOT malicious.*

1.  **Identify Target Version:** Locate the previous stable version in `measurement_registry.json` (e.g., 1.1.0).
2.  **Deploy Old Binary:** Re-deploy the Docker image / binary for version 1.1.0.
3.  **No Registry Change Needed:** Since 1.1.0 is still "active" in the registry, the Host will accept it.

## Scenario B: Security Revocation (Hard Rollback)
*Version 1.2.0 has a privacy vulnerability (e.g., leaked keys, broken sanitization).*

1.  **Revoke the Vulnerable Measurement:**
    Mark the bad measurement as `revoked`. This prevents any Host from starting it ever again.

    ```bash
    # Manually edit measurement_registry.json
    # Find entry for v1.2.0
    # Set "status": "revoked"
    # Set "revocation_reason": "CVE-2025-XXXX: Privacy Leak"
    ```

2.  **Publish Revocation:**
    Commit and push the registry change immediately.
    
    ```bash
    git commit -S -m "security: revoke enclave v1.2.0"
    git push origin main
    ```

3.  **Redeploy Previous Version:**
    Deploy the binary for the last known good version (e.g., 1.1.0).

4.  **Verify:**
    Attempt to start the revoked version (1.2.0) in a test environment. Ensure it fails to start or receive keys.

## Policy Drift
If a rollback re-introduces a removed privacy feature, the `tools/policy_drift_check.py` script will warn during the next forward deployment, but does not block rollback.
