# Design: Governance and Boundary Hardening

## Architecture

### 1. Registry Integrity & Enclave Status
*   **Signed Registry:** The `measurement_registry.json` will be signed (e.g., detached signature) or served via a trusted, attested path.
*   **Enclave-Side Check:** The enclave will ingest the registry (or a cryptographic proof of status) during initialization.
*   **KMS Gating:** The `KeyManagementService` will check `registry.get_status(mrenclave) == "active"` before unsealing any keys (SPK, ESSK).

### 2. Environment & Capabilities
*   **`DangerousCapabilities` Manifest:** A static Python class or frozen configuration defining flags like `MOCK_ATTESTATION`, `LE_SIMULATION`.
*   **Environment Binding:**
    *   `PROD`: Manifest must be empty/false.
    *   `DEV/TEST`: Manifest may be populated.
*   **Enforcement:**
    *   **Build-time:** CI inspects the manifest against the target profile.
    *   **Run-time:** Enclave panic if `settings.environment == PROD` but manifest has enabled flags.

### 3. Policy Drift & Invariants
*   **`InvariantManifest`:** A machine-readable definition of privacy rules (e.g., `max_log_len=0`, `le_response_types=['ALLOW', 'BLOCK']`).
*   **Release Gate:** `policy_drift_check.py` diffs the current code/config against the `InvariantManifest` of the previous active release. Any weakening requires an associated `openspec` delta.

### 4. Enclave OSS Boundary
*   **Package Separation:**
    *   `signal-assistant-enclave`: The trusted codebase (`src/signal_assistant/enclave`).
    *   `signal-assistant-host`: The untrusted host infrastructure.
*   **Dependency Rule:** `enclave` -> `host` imports are strictly forbidden.
*   **Shared Contracts:** Types and serialization logic move to a shared root or stay in enclave if minimal.

## Dependencies
*   Existing `measurement_registry.json` structure.
*   Existing `EnclaveSettings` and `SignalProxy`.
*   OpenSpec validation tooling.
